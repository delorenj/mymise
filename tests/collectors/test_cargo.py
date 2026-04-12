import subprocess
from unittest.mock import MagicMock, patch

from mymise.collectors.cargo import CargoCollector
from mymise.models import ToolSource


def test_cargo_collector_name():
    collector = CargoCollector()
    assert collector.name == "cargo"


def test_cargo_collector_available_true():
    with patch("shutil.which", return_value="/usr/bin/cargo"):
        collector = CargoCollector()
        assert collector.available() is True


def test_cargo_collector_available_false():
    with patch("shutil.which", return_value=None):
        collector = CargoCollector()
        assert collector.available() is False


def test_cargo_collector_collect_success():
    # Mocking cargo install --list output
    mock_output = "bat v0.24.0:\n    bat\nripgrep v14.1.0:\n    rg\nfd-find v9.0.0:\n    fd\n"

    with patch("shutil.which", return_value="/usr/bin/cargo"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)

        collector = CargoCollector()
        tools = collector.collect()

        assert len(tools) == 3
        # We'll use crate names as tool names for consistency with other pkg managers
        tool_names = {t.name for t in tools}
        assert "bat" in tool_names
        assert "ripgrep" in tool_names
        assert "fd-find" in tool_names
        assert all(t.sources == [ToolSource.CARGO] for t in tools)


def test_cargo_collector_collect_timeout():
    with (
        patch("shutil.which", return_value="/usr/bin/cargo"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="cargo install --list", timeout=10)),
    ):
        collector = CargoCollector()
        tools = collector.collect()
        assert tools == []


def test_cargo_collector_collect_not_available():
    with patch("shutil.which", return_value=None):
        collector = CargoCollector()
        tools = collector.collect()
        assert tools == []


def test_cargo_collector_collect_error():
    with patch("shutil.which", return_value="/usr/bin/cargo"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="error: cargo failed", returncode=1)

        collector = CargoCollector()
        tools = collector.collect()
        assert tools == []
