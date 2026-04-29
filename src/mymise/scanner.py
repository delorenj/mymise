import getpass
import logging
import socket
import time
from datetime import UTC, datetime

from mymise.collectors.apt import AptCollector
from mymise.collectors.base import Collector
from mymise.collectors.cargo import CargoCollector
from mymise.collectors.go import GoCollector
from mymise.collectors.history import HistoryCollector
from mymise.collectors.mise import MiseCollector
from mymise.collectors.npm import NpmCollector
from mymise.collectors.path import PathCollector
from mymise.collectors.pipx import PipxCollector
from mymise.collectors.snap import SnapCollector
from mymise.collectors.uv import UvCollector
from mymise.models import DiscoveredTool, DiscoveryResult

logger = logging.getLogger(__name__)

# List of collector classes to be instantiated during scan
COLLECTORS: list[type[Collector]] = [
    HistoryCollector,
    PathCollector,
    AptCollector,
    CargoCollector,
    NpmCollector,
    PipxCollector,
    MiseCollector,
    SnapCollector,
    GoCollector,
    UvCollector,
]


def scan(history_file: str = "~/.zsh_history", skip_pkg_managers: list[str] | None = None) -> DiscoveryResult:
    """Orchestrate all collectors and merge results into a DiscoveryResult.

    Args:
        history_file: Path to the shell history file (used by HistoryCollector).
        skip_pkg_managers: List of package manager collector names to skip (e.g., ['cargo', 'npm']).

    Returns:
        A DiscoveryResult containing the merged list of discovered tools and metadata.
    """
    start_time = time.perf_counter()
    scan_timestamp = datetime.now(UTC)

    all_discovered_tools: list[DiscoveredTool] = []
    errors: list[str] = []
    skip_list = skip_pkg_managers or []

    for collector_cls in COLLECTORS:
        collector_name = getattr(collector_cls, "name", collector_cls.__name__)
        if collector_name.lower() in [s.lower() for s in skip_list]:
            logger.info(f"Skipping collector: {collector_name}")
            continue

        try:
            # Instantiate collector
            if collector_cls == HistoryCollector:
                # HistoryCollector takes history_path as an argument
                collector = collector_cls(history_path=history_file)  # type: ignore
            else:
                collector = collector_cls()

            if not collector.available():
                continue

            logger.info(f"Running collector: {collector.name}")
            tools = collector.collect()
            all_discovered_tools.extend(tools)
        except Exception as e:
            # Log warning and track error
            error_msg = f"Collector {collector_name} failed ({type(e).__name__}): {e}"
            logger.warning(error_msg)
            errors.append(error_msg)
            continue

    # Merge and deduplicate tools by name
    merged_tools = _merge_tools(all_discovered_tools)

    duration = time.perf_counter() - start_time

    return DiscoveryResult(
        scan_timestamp=scan_timestamp,
        hostname=socket.gethostname(),
        user=getpass.getuser(),
        scan_duration_seconds=duration,
        tools=merged_tools,
        partial_failure=len(errors) > 0,
        errors=errors,
    )


def _merge_tools(tools: list[DiscoveredTool]) -> list[DiscoveredTool]:
    """Merge tools by name: union sources, max frequency, latest last_used.

    Args:
        tools: A flat list of tools from all collectors.

    Returns:
        A list of deduplicated DiscoveredTool objects.
    """
    merged: dict[str, DiscoveredTool] = {}

    for tool in tools:
        name = tool.name
        if name not in merged:
            # First time seeing this tool, add a copy
            merged[name] = tool.model_copy(deep=True)
            continue

        existing = merged[name]

        # Union of sources and installed_by
        existing.sources = sorted(list(set(existing.sources) | set(tool.sources)))
        existing.installed_by = sorted(list(set(existing.installed_by) | set(tool.installed_by)))

        # Max frequency
        existing.frequency = max(existing.frequency, tool.frequency)

        # Latest last_used timestamp
        if tool.last_used and (not existing.last_used or tool.last_used > existing.last_used):
            existing.last_used = tool.last_used

        # Prefer non-None binary_path and category if not already set
        if not existing.binary_path and tool.binary_path:
            existing.binary_path = tool.binary_path
        if not existing.category and tool.category:
            existing.category = tool.category

    # Return tools sorted by name
    return sorted(list(merged.values()), key=lambda x: x.name)
