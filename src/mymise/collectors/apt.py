from mymise.models import DiscoveredTool


class AptCollector:
    name = "apt"

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError
