from mymise.models import DiscoveredTool


class UvCollector:
    name = "uv"

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError
