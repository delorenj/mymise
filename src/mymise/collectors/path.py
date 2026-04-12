"""PATH binary scanner - discovers executables in PATH directories."""

import os
from pathlib import Path

from mymise.models import DiscoveredTool, ToolSource


class PathCollector:
    """Scan PATH directories for executables."""

    name = "path"

    def collect(self) -> list[DiscoveredTool]:
        """Discover executables in PATH."""
        path_env = os.environ.get("PATH", "")
        if not path_env:
            return []

        # resolved_path -> DiscoveredTool
        discovered = {}

        for path_str in path_env.split(os.pathsep):
            if not path_str:
                continue
            
            p = Path(path_str)
            if not p.exists() or not p.is_dir():
                continue

            try:
                for entry in p.iterdir():
                    if entry.is_file() and os.access(entry, os.X_OK):
                        try:
                            resolved = entry.resolve()
                            resolved_str = str(resolved)
                            
                            if resolved_str not in discovered:
                                discovered[resolved_str] = DiscoveredTool(
                                    name=entry.name,
                                    sources=[ToolSource.PATH],
                                    binary_path=resolved_str,
                                )
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        return list(discovered.values())

    def available(self) -> bool:
        """Always available on systems with a PATH."""
        return True
