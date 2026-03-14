from mymise.models import DiscoveredTool


class MiseCollector:
    name = "mise"

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError
