import subprocess
from unittest.mock import MagicMock, patch

from mymise.collectors.uv import UvCollector
from mymise.models import ToolSource


def test_uv_collector_name():
    collector = UvCollector()
    assert collector.name == "uv"


def test_uv_collector_available_true():
    with patch("shutil.which", return_value="/usr/bin/uv"):
        collector = UvCollector()
        assert collector.available() is True


def test_uv_collector_available_false():
    with patch("shutil.which", return_value=None):
        collector = UvCollector()
        assert collector.available() is False


def test_uv_collector_collect_success():
    mock_output = """agentrules v3.1.9
- agentrules
basedpyright v1.32.1
- basedpyright
- basedpyright-langserver
"""
    with patch("shutil.which", return_value="/usr/bin/uv"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)

        collector = UvCollector()
        tools = collector.collect()

        assert len(tools) == 2
        names = {t.name for t in tools}
        assert "agentrules" in names
        assert "basedpyright" in names
        assert all(t.sources == [ToolSource.UV] for t in tools)


def test_uv_collector_collect_empty():
    with patch("shutil.which", return_value="/usr/bin/uv"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

        collector = UvCollector()
        tools = collector.collect()
        assert tools == []


def test_uv_collector_collect_timeout():
    with (
        patch("shutil.which", return_value="/usr/bin/uv"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="uv tool list", timeout=10)),
    ):
        collector = UvCollector()
        tools = collector.collect()
        assert tools == []
