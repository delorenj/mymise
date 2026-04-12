import logging
import shutil
import subprocess

from mymise.models import DiscoveredTool, ToolSource

logger = logging.getLogger(__name__)


class AptCollector:
    name = "apt"

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered via apt/dpkg."""
        if not self.available():
            return []

        try:
            # -W: show package, -f: format output
            # Status format: 'install ok installed'
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Package} ${Status}\\n"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            tools = []
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue

                parts = line.split(maxsplit=1)
                if len(parts) < 2:
                    continue

                pkg_name, status = parts
                if status == "install ok installed":
                    tools.append(
                        DiscoveredTool(
                            name=pkg_name,
                            sources=[ToolSource.APT],
                        )
                    )
            return tools

        except subprocess.TimeoutExpired:
            logger.warning("apt collector timed out after 10 seconds")
            return []
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning(f"apt collector failed: {e}")
            return []

    def available(self) -> bool:
        """Return True if apt/dpkg-query is available."""
        return shutil.which("dpkg-query") is not None
