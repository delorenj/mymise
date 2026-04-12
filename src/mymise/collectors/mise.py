import json
import logging
import shutil
import subprocess

from mymise.models import DiscoveredTool, ToolSource

logger = logging.getLogger(__name__)


class MiseCollector:
    name = "mise"

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered via mise."""
        if not self.available():
            return []

        try:
            result = subprocess.run(
                ["mise", "ls", "--json"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            data = json.loads(result.stdout)
            tool_names = set()

            if isinstance(data, dict):
                tool_names = set(data.keys())
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "name" in item:
                        tool_names.add(item["name"])
                    elif isinstance(item, str):
                        tool_names.add(item)

            return [
                DiscoveredTool(
                    name=name,
                    sources=[ToolSource.MISE],
                )
                for name in tool_names
            ]

        except subprocess.TimeoutExpired:
            logger.warning("mise collector timed out after 10 seconds")
            return []
        except (subprocess.CalledProcessError, OSError, json.JSONDecodeError) as e:
            logger.warning(f"mise collector failed: {e}")
            return []

    def available(self) -> bool:
        """Return True if mise is available."""
        return shutil.which("mise") is not None
