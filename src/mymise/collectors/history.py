from mymise.models import DiscoveredTool


class HistoryCollector:
    """Parses zsh extended history format: `: <timestamp>:<duration>;command_text`"""

    name = "history"

    def __init__(self, history_path: str = "~/.zsh_history") -> None:
        self.history_path = history_path

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError
