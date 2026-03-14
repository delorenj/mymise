import pytest

from mymise.models import DiscoveredTool, ToolSource


@pytest.fixture
def sample_tool() -> DiscoveredTool:
    return DiscoveredTool(
        name="bat",
        sources=[ToolSource.HISTORY, ToolSource.CARGO],
        frequency=42,
        installed_by=[ToolSource.CARGO],
    )
