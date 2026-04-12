import subprocess
from unittest.mock import MagicMock, patch

from mymise.collectors.snap import SnapCollector
from mymise.models import ToolSource


def test_snap_collector_name():
    collector = SnapCollector()
    assert collector.name == "snap"


def test_snap_collector_available_true():
    with patch("shutil.which", return_value="/usr/bin/snap"):
        collector = SnapCollector()
        assert collector.available() is True


def test_snap_collector_available_false():
    with patch("shutil.which", return_value=None):
        collector = SnapCollector()
        assert collector.available() is False


def test_snap_collector_collect_success():
    # Mocking snap list output
    mock_output = (
        "Name               Version           Rev    Tracking       Publisher   Notes\n"
        "bare               1.0               5      latest/stable  canonical✓  base\n"
        "core22             20240111          1122   latest/stable  canonical✓  base\n"
        "firefox            124.0.2-1         4090   latest/stable  mozilla✓    -\n"
    )

    with patch("shutil.which", return_value="/usr/bin/snap"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)

        collector = SnapCollector()
        tools = collector.collect()

        # 'bare' and 'core22' are usually base snaps, but the story says "installed snaps"
        # We might want to filter out 'base' snaps, but let's stick to AC for now: "each installed snap"
        assert len(tools) == 3
        tool_names = {t.name for t in tools}
        assert "bare" in tool_names
        assert "core22" in tool_names
        assert "firefox" in tool_names
        assert all(t.sources == [ToolSource.SNAP] for t in tools)


def test_snap_collector_collect_timeout():
    with (
        patch("shutil.which", return_value="/usr/bin/snap"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="snap list", timeout=10)),
    ):
        collector = SnapCollector()
        tools = collector.collect()
        assert tools == []


def test_snap_collector_collect_not_available():
    with patch("shutil.which", return_value=None):
        collector = SnapCollector()
        tools = collector.collect()
        assert tools == []


def test_snap_collector_collect_error():
    with patch("shutil.which", return_value="/usr/bin/snap"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="error: no snaps installed", returncode=1)

        collector = SnapCollector()
        tools = collector.collect()
        assert tools == []
