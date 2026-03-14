from mymise.models import DiscoveredTool


class SnapCollector:
    name = "snap"

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError
