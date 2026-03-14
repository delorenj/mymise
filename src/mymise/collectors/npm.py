from mymise.models import DiscoveredTool


class NpmCollector:
    name = "npm"

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError
