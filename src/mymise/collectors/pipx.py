import json
import logging
import shutil
import subprocess

from mymise.models import DiscoveredTool, ToolSource

logger = logging.getLogger(__name__)


class PipxCollector:
    name = "pipx"

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered via pipx."""
        if not self.available():
            return []

        try:
            result = subprocess.run(
                ["pipx", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            if not result.stdout.strip():
                return []

            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.warning("pipx collector failed to parse JSON output")
                return []

            venvs = data.get("venvs", {})
            tools = []
            for venv_name in venvs:
                # We use the venv name as the tool name, which matches
                # how pipx manages tools (one venv per main tool).
                tools.append(
                    DiscoveredTool(
                        name=venv_name,
                        sources=[ToolSource.PIPX],
                        installed_by=[ToolSource.PIPX],
                    )
                )
            return tools

        except subprocess.TimeoutExpired:
            logger.warning("pipx collector timed out after 10 seconds")
            return []
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning(f"pipx collector failed: {e}")
            return []

    def available(self) -> bool:
        """Return True if pipx is available."""
        return shutil.which("pipx") is not None
