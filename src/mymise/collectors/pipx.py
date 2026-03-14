from mymise.models import DiscoveredTool


class PipxCollector:
    name = "pipx"

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError
