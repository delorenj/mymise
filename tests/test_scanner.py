import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from mymise.models import DiscoveredTool, ToolSource
from mymise.scanner import scan


@pytest.fixture
def mock_collectors():
    """Mock collector classes with predefined discovery results."""
    # Collector A finds 'rg' with source 'cargo'
    tool_rg_cargo = DiscoveredTool(
        name="rg",
        sources=[ToolSource.CARGO],
        installed_by=[ToolSource.CARGO],
        frequency=5,
        last_used=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    mock_cargo_cls = MagicMock()
    mock_cargo_cls.__name__ = "CargoCollector"
    mock_cargo_cls.name = "cargo"
    mock_cargo_instance = mock_cargo_cls.return_value
    mock_cargo_instance.name = "cargo"
    mock_cargo_instance.available.return_value = True
    mock_cargo_instance.collect.return_value = [tool_rg_cargo]

    # Collector B finds 'rg' with source 'path' and 'bat' with source 'path'
    tool_rg_path = DiscoveredTool(
        name="rg",
        sources=[ToolSource.PATH],
        installed_by=[ToolSource.PATH],
        frequency=10,
        last_used=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
    )
    tool_bat_path = DiscoveredTool(
        name="bat",
        sources=[ToolSource.PATH],
        installed_by=[ToolSource.PATH],
        frequency=2,
        last_used=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    mock_path_cls = MagicMock()
    mock_path_cls.__name__ = "PathCollector"
    mock_path_cls.name = "path"
    mock_path_instance = mock_path_cls.return_value
    mock_path_instance.name = "path"
    mock_path_instance.available.return_value = True
    mock_path_instance.collect.return_value = [tool_rg_path, tool_bat_path]

    # Collector C is not available
    mock_apt_cls = MagicMock()
    mock_apt_cls.__name__ = "AptCollector"
    mock_apt_cls.name = "apt"
    mock_apt_instance = mock_apt_cls.return_value
    mock_apt_instance.name = "apt"
    mock_apt_instance.available.return_value = False
    
    # Collector D raises an exception
    mock_npm_cls = MagicMock()
    mock_npm_cls.__name__ = "NpmCollector"
    mock_npm_cls.name = "npm"
    mock_npm_instance = mock_npm_cls.return_value
    mock_npm_instance.name = "npm"
    mock_npm_instance.available.return_value = True
    mock_npm_instance.collect.side_effect = Exception("NPM failure")

    return {
        "CargoCollector": mock_cargo_cls,
        "PathCollector": mock_path_cls,
        "AptCollector": mock_apt_cls,
        "NpmCollector": mock_npm_cls,
    }


def test_scan_merges_and_deduplicates(mock_collectors):
    """Verify that scan() merges tools from multiple collectors correctly."""
    with patch("mymise.scanner.COLLECTORS", [
        mock_collectors["CargoCollector"],
        mock_collectors["PathCollector"],
        mock_collectors["AptCollector"],
    ]):
        result = scan()

        # Should have 2 unique tools: rg and bat
        assert len(result.tools) == 2
        
        # Verify 'rg' merge logic
        rg = next(t for t in result.tools if t.name == "rg")
        assert set(rg.sources) == {ToolSource.CARGO, ToolSource.PATH}
        assert rg.frequency == 10  # max(5, 10)
        assert rg.last_used == datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)  # most recent
        assert set(rg.installed_by) == {ToolSource.CARGO, ToolSource.PATH}

        # Verify 'bat' (only one source)
        bat = next(t for t in result.tools if t.name == "bat")
        assert bat.sources == [ToolSource.PATH]
        assert bat.frequency == 2


def test_scan_handles_collector_exceptions(mock_collectors, caplog):
    """Verify that scan() continues if a collector raises an exception."""
    with patch("mymise.scanner.COLLECTORS", [
        mock_collectors["PathCollector"],
        mock_collectors["NpmCollector"],
    ]):
        result = scan()

        # Should still have tools from PathCollector
        assert any(t.name == "bat" for t in result.tools)
        
        # Verify warning was logged
        assert "npm" in caplog.text
        assert "NPM failure" in caplog.text


def test_scan_populates_metadata(mock_collectors):
    """Verify that scan() populates DiscoveryResult metadata."""
    with patch("mymise.scanner.COLLECTORS", [mock_collectors["PathCollector"]]):
        result = scan()

        assert result.hostname
        assert result.user
        assert isinstance(result.scan_timestamp, datetime)
        assert result.scan_duration_seconds >= 0


def test_scan_passes_history_path_to_history_collector():
    """Verify that scan() passes the history_file argument to HistoryCollector."""
    mock_history_cls = MagicMock()
    mock_history_cls.__name__ = "HistoryCollector"
    mock_history_instance = mock_history_cls.return_value
    mock_history_instance.name = "history"
    mock_history_instance.available.return_value = True
    mock_history_instance.collect.return_value = []
    
    with patch("mymise.scanner.COLLECTORS", [mock_history_cls]):
        from mymise.collectors.history import HistoryCollector
        with patch("mymise.scanner.HistoryCollector", mock_history_cls):
            scan(history_file="/custom/path")
            mock_history_cls.assert_called_with(history_path="/custom/path")
