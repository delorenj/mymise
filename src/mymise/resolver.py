import logging
import subprocess
from datetime import datetime

from mymise.models import BackendType, DiscoveryResult, ResolutionResult, ResolvedTool, UnresolvedTool

logger = logging.getLogger(__name__)

class Resolver:
    def __init__(self, timeout: int = 10, dry_run: bool = False):
        self.timeout = timeout
        self.dry_run = dry_run

    def _lookup_registry(self, tool_name: str) -> str | None:
        """Run `mise registry <tool_name>` and return the output."""
        if self.dry_run:
            logger.info(f"Planned registry lookup for {tool_name}", extra={"dry_run": True})

        try:
            result = subprocess.run(
                ["mise", "registry", tool_name],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return None
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout (>{self.timeout}s) looking up {tool_name} in mise registry")
            return None
        except Exception as e:
            logger.error(f"Error looking up {tool_name} in mise registry: {e}")
            return None

    def resolve(self, discovery: DiscoveryResult) -> ResolutionResult:
        resolved = []
        unresolved = []

        for tool in discovery.tools:
            output = self._lookup_registry(tool.name)
            if output:
                # Expected format: tool_name\tbackend:owner/repo
                parts = output.split("\t")
                if len(parts) >= 2:
                    entry = parts[1]
                    backend_part, registry_entry = entry.split(":", 1) if ":" in entry else (entry, entry)
                    
                    try:
                        backend = BackendType(backend_part)
                    except ValueError:
                        logger.warning(f"Unknown backend '{backend_part}' for tool '{tool.name}'")
                        # Fallback or treat as unresolved? The story says extract backend type.
                        # I'll treat as unresolved if the backend isn't in our BackendType enum.
                        unresolved.append(UnresolvedTool(
                            name=tool.name,
                            original=tool,
                            suggested_actions=[f"Unknown backend: {backend_part}"]
                        ))
                        continue

                    resolved.append(ResolvedTool(
                        name=tool.name,
                        backend=backend,
                        registry_entry=registry_entry,
                        install_command=f"mise install {tool.name}@latest",
                        original=tool
                    ))
                else:
                    unresolved.append(UnresolvedTool(
                        name=tool.name,
                        original=tool,
                        suggested_actions=["Mise registry output format unrecognized"]
                    ))
            else:
                unresolved.append(UnresolvedTool(
                    name=tool.name,
                    original=tool,
                    suggested_actions=["Not found in mise registry"]
                ))

        total = len(discovery.tools)
        resolution_rate = len(resolved) / total if total > 0 else 0.0

        return ResolutionResult(
            resolution_timestamp=datetime.now(),
            resolved=resolved,
            unresolved=unresolved,
            resolution_rate=resolution_rate
        )

def resolve(discovery: DiscoveryResult, timeout: int = 10, dry_run: bool = False) -> ResolutionResult:
    resolver = Resolver(timeout=timeout, dry_run=dry_run)
    return resolver.resolve(discovery)
