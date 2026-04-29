import json
import subprocess
from unittest.mock import MagicMock, patch

from mymise.collectors.npm import NpmCollector
from mymise.models import ToolSource


def test_npm_collector_name():
    collector = NpmCollector()
    assert collector.name == "npm"


def test_npm_collector_available_true():
    with patch("shutil.which", return_value="/usr/bin/npm"):
        collector = NpmCollector()
        assert collector.available() is True


def test_npm_collector_available_false():
    with patch("shutil.which", return_value=None):
        collector = NpmCollector()
        assert collector.available() is False


def test_npm_collector_collect_success():
    # Mocking npm list -g --depth=0 --json output
    mock_data = {
        "dependencies": {
            "typescript": {"version": "5.3.3"},
            "ts-node": {"version": "10.9.2"},
            "npm": {"version": "10.2.4"},
        }
    }
    mock_output = json.dumps(mock_data)

    with patch("shutil.which", return_value="/usr/bin/npm"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)

        collector = NpmCollector()
        tools = collector.collect()

        assert len(tools) == 3
        tool_names = {t.name for t in tools}
        assert "typescript" in tool_names
        assert "ts-node" in tool_names
        assert "npm" in tool_names
        assert all(t.sources == [ToolSource.NPM] for t in tools)
        assert all(t.installed_by == [ToolSource.NPM] for t in tools)


def test_npm_collector_collect_empty():
    mock_data = {"dependencies": {}}
    mock_output = json.dumps(mock_data)

    with patch("shutil.which", return_value="/usr/bin/npm"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)

        collector = NpmCollector()
        tools = collector.collect()
        assert tools == []


def test_npm_collector_collect_timeout():
    with (
        patch("shutil.which", return_value="/usr/bin/npm"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="npm list -g --depth=0 --json", timeout=10)),
    ):
        collector = NpmCollector()
        tools = collector.collect()
        assert tools == []


def test_npm_collector_collect_not_available():
    with patch("shutil.which", return_value=None):
        collector = NpmCollector()
        tools = collector.collect()
        assert tools == []


def test_npm_collector_collect_error():
    with patch("shutil.which", return_value="/usr/bin/npm"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="error: npm failed", returncode=1)

        collector = NpmCollector()
        tools = collector.collect()
        assert tools == []


def test_npm_collector_collect_invalid_json():
    with patch("shutil.which", return_value="/usr/bin/npm"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="not json", stderr="", returncode=0)

        collector = NpmCollector()
        tools = collector.collect()
        assert tools == []
