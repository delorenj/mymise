"""PATH binary scanner - discovers executables in PATH directories."""

from mymise.models import DiscoveredTool


class PathCollector:
    """Scan PATH directories for executables."""

    name = "path"

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        return True
