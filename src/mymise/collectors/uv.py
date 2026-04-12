import logging
import shutil
import subprocess

from mymise.models import DiscoveredTool, ToolSource

logger = logging.getLogger(__name__)


class UvCollector:
    name = "uv"

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered via uv tool."""
        if not self.available():
            return []

        try:
            result = subprocess.run(
                ["uv", "tool", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            tools = []
            # Lines look like: package vVERSION
            # Followed by lines starting with - which are executables
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line.startswith("-") and line:
                    # This is likely a package line
                    parts = line.split()
                    if parts:
                        pkg_name = parts[0]
                        tools.append(
                            DiscoveredTool(
                                name=pkg_name,
                                sources=[ToolSource.UV],
                                installed_by=[ToolSource.UV],
                            )
                        )
            return tools

        except subprocess.TimeoutExpired:
            logger.warning("uv collector timed out after 10 seconds")
            return []
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning(f"uv collector failed: {e}")
            return []

    def available(self) -> bool:
        """Return True if uv is available."""
        return shutil.which("uv") is not None
