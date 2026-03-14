"""Collector protocol - interface for all tool discovery collectors."""

from typing import Protocol

from mymise.models import DiscoveredTool


class Collector(Protocol):
    """Interface for tool discovery collectors.

    Each collector discovers tools from a specific source (shell history,
    PATH scan, package manager, etc).
    """

    name: str

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered by this collector."""
        ...

    def available(self) -> bool:
        """Return True if this collector can run on the current system."""
        ...
