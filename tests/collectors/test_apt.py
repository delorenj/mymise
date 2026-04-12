import subprocess
from unittest.mock import MagicMock, patch

from mymise.collectors.apt import AptCollector
from mymise.models import ToolSource


def test_apt_collector_name():
    collector = AptCollector()
    assert collector.name == "apt"


def test_apt_collector_available_true():
    with patch("shutil.which", return_value="/usr/bin/apt"):
        collector = AptCollector()
        assert collector.available() is True


def test_apt_collector_available_false():
    with patch("shutil.which", return_value=None):
        collector = AptCollector()
        assert collector.available() is False


def test_apt_collector_collect_success():
    # Mocking dpkg-query -W -f='${Package} ${Status}\n' output
    # Status should be 'install ok installed'
    mock_output = (
        "bat install ok installed\n"
        "ripgrep install ok installed\n"
        "curl install ok installed\n"
        "not-installed unknown ok not-installed\n"
    )

    with patch("shutil.which", return_value="/usr/bin/apt"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)

        collector = AptCollector()
        tools = collector.collect()

        assert len(tools) == 3
        tool_names = {t.name for t in tools}
        assert "bat" in tool_names
        assert "ripgrep" in tool_names
        assert "curl" in tool_names
        assert all(t.sources == [ToolSource.APT] for t in tools)


def test_apt_collector_collect_timeout():
    with (
        patch("shutil.which", return_value="/usr/bin/apt"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="dpkg-query", timeout=10)),
    ):
        collector = AptCollector()
        # Should return empty list and not raise
        tools = collector.collect()
        assert tools == []


def test_apt_collector_collect_not_available():
    with patch("shutil.which", return_value=None):
        collector = AptCollector()
        tools = collector.collect()
        assert tools == []


def test_apt_collector_collect_error():
    with patch("shutil.which", return_value="/usr/bin/apt"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="some error", returncode=1)

        collector = AptCollector()
        tools = collector.collect()
        assert tools == []
