from mymise.models import DiscoveredTool


class CargoCollector:
    name = "cargo"

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError
