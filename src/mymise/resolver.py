import logging
import subprocess
from datetime import UTC, datetime

from mymise.models import BackendType, DiscoveryResult, ResolutionResult, ResolvedTool, UnresolvedTool

logger = logging.getLogger(__name__)


class Resolver:
    def __init__(self, timeout: int = 10, dry_run: bool = False):
        self.timeout = timeout
        self.dry_run = dry_run
        # Per-resolve() error tracking; reset on each call
        self._errors: list[str] = []

    def _lookup_registry(self, tool_name: str) -> str | None:
        """Run `mise registry <tool_name>` and return the output. Records errors to self._errors."""
        if self.dry_run:
            logger.info(f"Planned registry lookup for {tool_name}", extra={"dry_run": True})

        try:
            result = subprocess.run(
                ["mise", "registry", tool_name], capture_output=True, text=True, timeout=self.timeout, check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except subprocess.TimeoutExpired:
            msg = f"Timeout (>{self.timeout}s) looking up {tool_name} in mise registry"
            logger.warning(msg)
            self._errors.append(msg)
            return None
        except Exception as e:
            msg = f"Error looking up {tool_name} in mise registry: {e}"
            logger.error(msg)
            self._errors.append(msg)
            return None

    def resolve(self, discovery: DiscoveryResult) -> ResolutionResult:
        # Reset error tracker for this resolve pass
        self._errors = []
        resolved = []
        unresolved = []

        for tool in discovery.tools:
            output = self._lookup_registry(tool.name)
            if output:
                # Expected format: tool_name\tbackend:owner/repo
                parts = output.split("\t")
                if len(parts) >= 2 and ":" in parts[1]:
                    backend_part, registry_entry = parts[1].split(":", 1)

                    try:
                        backend = BackendType(backend_part)
                    except ValueError:
                        msg = f"Unknown backend '{backend_part}' for tool '{tool.name}'"
                        logger.warning(msg)
                        self._errors.append(msg)
                        unresolved.append(
                            UnresolvedTool(
                                name=tool.name, original=tool, suggested_actions=[f"Unknown backend: {backend_part}"]
                            )
                        )
                        continue

                    resolved.append(
                        ResolvedTool(
                            name=tool.name,
                            backend=backend,
                            registry_entry=registry_entry,
                            install_command=f"mise install {tool.name}@latest",
                            original=tool,
                        )
                    )
                else:
                    msg = f"Mise registry output format unrecognized for '{tool.name}': {output!r}"
                    logger.warning(msg)
                    self._errors.append(msg)
                    unresolved.append(
                        UnresolvedTool(
                            name=tool.name,
                            original=tool,
                            suggested_actions=["Mise registry output format unrecognized"],
                        )
                    )
            else:
                unresolved.append(
                    UnresolvedTool(name=tool.name, original=tool, suggested_actions=["Not found in mise registry"])
                )

        total = len(discovery.tools)
        resolution_rate = len(resolved) / total if total > 0 else 0.0

        return ResolutionResult(
            resolution_timestamp=datetime.now(UTC),
            resolved=resolved,
            unresolved=unresolved,
            resolution_rate=resolution_rate,
            partial_failure=len(self._errors) > 0,
            errors=list(self._errors),
        )


def resolve(discovery: DiscoveryResult, timeout: int = 10, dry_run: bool = False) -> ResolutionResult:
    resolver = Resolver(timeout=timeout, dry_run=dry_run)
    return resolver.resolve(discovery)
