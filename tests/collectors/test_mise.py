import json
import subprocess
from unittest.mock import MagicMock, patch

from mymise.collectors.mise import MiseCollector
from mymise.models import ToolSource


def test_mise_collector_name():
    collector = MiseCollector()
    assert collector.name == "mise"


def test_mise_collector_available_true():
    with patch("shutil.which", return_value="/usr/bin/mise"):
        collector = MiseCollector()
        assert collector.available() is True


def test_mise_collector_available_false():
    with patch("shutil.which", return_value=None):
        collector = MiseCollector()
        assert collector.available() is False


def test_mise_collector_collect_success():
    # Mocking mise ls --json output
    # Format: dict mapping tool names to lists of installed versions
    mock_data = {"node": [{"version": "20.11.1"}], "python": [{"version": "3.12.2"}], "bat": [{"version": "0.24.0"}]}
    mock_output = json.dumps(mock_data)

    with patch("shutil.which", return_value="/usr/bin/mise"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)

        collector = MiseCollector()
        tools = collector.collect()

        assert len(tools) == 3
        tool_names = {t.name for t in tools}
        assert "node" in tool_names
        assert "python" in tool_names
        assert "bat" in tool_names
        assert all(t.sources == [ToolSource.MISE] for t in tools)


def test_mise_collector_collect_timeout():
    with (
        patch("shutil.which", return_value="/usr/bin/mise"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="mise ls --json", timeout=10)),
    ):
        collector = MiseCollector()
        tools = collector.collect()
        assert tools == []


def test_mise_collector_collect_not_available():
    with patch("shutil.which", return_value=None):
        collector = MiseCollector()
        tools = collector.collect()
        assert tools == []


def test_mise_collector_collect_error():
    with patch("shutil.which", return_value="/usr/bin/mise"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="error: mise failed", returncode=1)

        collector = MiseCollector()
        tools = collector.collect()
        assert tools == []
