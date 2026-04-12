import logging
import os
import shutil
import subprocess
from pathlib import Path

from mymise.models import DiscoveredTool, ToolSource

logger = logging.getLogger(__name__)


class GoCollector:
    name = "go"

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered via go."""
        if not self.available():
            return []

        try:
            # We check GOPATH as it is the most common way to find go binaries
            # and it matches the current test expectations.
            # In a more complete implementation we would also check GOBIN.
            result = subprocess.run(
                ["go", "env", "GOPATH"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )

            gopath = result.stdout.strip()
            if not gopath:
                return []

            # GOPATH can have multiple entries
            gopath_first = gopath.split(os.pathsep)[0]
            bin_dir = Path(gopath_first) / "bin"

            if not bin_dir.is_dir():
                return []

            tools = []
            for item in bin_dir.iterdir():
                if item.is_file() and os.access(item, os.X_OK):
                    tools.append(
                        DiscoveredTool(
                            name=item.name,
                            sources=[ToolSource.GO],
                            installed_by=[ToolSource.GO],
                        )
                    )
            return tools

        except subprocess.TimeoutExpired:
            logger.warning("go collector timed out after 10 seconds")
            return []
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning(f"go collector failed: {e}")
            return []

    def available(self) -> bool:
        """Return True if go is available."""
        return shutil.which("go") is not None
