import json
import logging
import shutil
import subprocess

from mymise.models import DiscoveredTool, ToolSource

logger = logging.getLogger(__name__)


class NpmCollector:
    name = "npm"

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered via npm."""
        if not self.available():
            return []

        try:
            result = subprocess.run(
                ["npm", "list", "-g", "--depth=0", "--json"],
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
                logger.warning("npm collector failed to parse JSON output")
                return []

            dependencies = data.get("dependencies", {})
            tools = []
            for pkg_name in dependencies:
                tools.append(
                    DiscoveredTool(
                        name=pkg_name,
                        sources=[ToolSource.NPM],
                        installed_by=[ToolSource.NPM],
                    )
                )
            return tools

        except subprocess.TimeoutExpired:
            logger.warning("npm collector timed out after 10 seconds")
            return []
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning(f"npm collector failed: {e}")
            return []

    def available(self) -> bool:
        """Return True if npm is available."""
        return shutil.which("npm") is not None
