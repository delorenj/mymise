from mymise.models import DiscoveredTool


class GoCollector:
    name = "go"

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError
