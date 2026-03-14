import json

from mymise.models import (
    BackendType,
    DiscoveredTool,
    ToolCategory,
    ToolSource,
)


def test_discovered_tool_serialization_roundtrip(sample_tool: DiscoveredTool) -> None:
    json_str = sample_tool.model_dump_json()
    restored = DiscoveredTool.model_validate_json(json_str)
    assert restored == sample_tool


def test_discovered_tool_defaults() -> None:
    tool = DiscoveredTool(name="jq", sources=[ToolSource.PATH])
    assert tool.frequency == 0
    assert tool.last_used is None
    assert tool.binary_path is None
    assert tool.installed_by == []
    assert tool.category is None


def test_tool_category_values() -> None:
    assert ToolCategory.CLI_TOOL == "cli-tool"
    assert ToolCategory.RUNTIME == "runtime"


def test_backend_type_values() -> None:
    assert BackendType.AQUA == "aqua"
    assert BackendType.GITHUB == "github"


def test_discovered_tool_json_shape(sample_tool: DiscoveredTool) -> None:
    data = json.loads(sample_tool.model_dump_json())
    assert "name" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert data["name"] == "bat"
