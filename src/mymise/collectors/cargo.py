import logging
import re
import shutil
import subprocess

from mymise.models import DiscoveredTool, ToolSource

logger = logging.getLogger(__name__)


class CargoCollector:
    name = "cargo"

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered via cargo."""
        if not self.available():
            return []

        try:
            result = subprocess.run(
                ["cargo", "install", "--list"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            tools = []
            # Lines look like: bat v0.24.0: or some-tool v1.2.3-beta.1:
            for line in result.stdout.splitlines():
                match = re.match(r"^([\w\-\.]+)\s+v([^:]+):$", line)
                if match:
                    pkg_name = match.group(1)
                    tools.append(
                        DiscoveredTool(
                            name=pkg_name,
                            sources=[ToolSource.CARGO],
                            installed_by=[ToolSource.CARGO],
                        )
                    )
            return tools

        except subprocess.TimeoutExpired:
            logger.warning("cargo collector timed out after 10 seconds")
            return []
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning(f"cargo collector failed: {e}")
            return []

    def available(self) -> bool:
        """Return True if cargo is available."""
        return shutil.which("cargo") is not None
