import logging
import shutil
import subprocess

from mymise.models import DiscoveredTool, ToolSource

logger = logging.getLogger(__name__)


class SnapCollector:
    name = "snap"

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered via snap."""
        if not self.available():
            return []

        try:
            result = subprocess.run(
                ["snap", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            tools = []
            lines = result.stdout.splitlines()
            if not lines:
                return []

            # Skip header line
            for line in lines[1:]:
                if not line.strip():
                    continue

                parts = line.split()
                if not parts:
                    continue

                snap_name = parts[0]
                tools.append(
                    DiscoveredTool(
                        name=snap_name,
                        sources=[ToolSource.SNAP],
                    )
                )
            return tools

        except subprocess.TimeoutExpired:
            logger.warning("snap collector timed out after 10 seconds")
            return []
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning(f"snap collector failed: {e}")
            return []

    def available(self) -> bool:
        """Return True if snap is available."""
        return shutil.which("snap") is not None
