import json
import subprocess
from unittest.mock import MagicMock, patch

from mymise.collectors.pipx import PipxCollector
from mymise.models import ToolSource


def test_pipx_collector_name():
    collector = PipxCollector()
    assert collector.name == "pipx"


def test_pipx_collector_available_true():
    with patch("shutil.which", return_value="/usr/bin/pipx"):
        collector = PipxCollector()
        assert collector.available() is True


def test_pipx_collector_available_false():
    with patch("shutil.which", return_value=None):
        collector = PipxCollector()
        assert collector.available() is False


def test_pipx_collector_collect_success():
    # Mocking pipx list --json output
    mock_data = {
        "pipx_spec_version": "0.1",
        "venvs": {
            "catt": {
                "metadata": {
                    "main_package": {
                        "package": "catt",
                        "package_version": "0.13.1",
                        "apps": ["catt"]
                    }
                }
            },
            "black": {
                "metadata": {
                    "main_package": {
                        "package": "black",
                        "package_version": "24.1.1",
                        "apps": ["black", "blackd"]
                    }
                }
            }
        }
    }
    mock_output = json.dumps(mock_data)

    with patch("shutil.which", return_value="/usr/bin/pipx"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)

        collector = PipxCollector()
        tools = collector.collect()

        assert len(tools) == 2
        tool_names = {t.name for t in tools}
        assert "catt" in tool_names
        assert "black" in tool_names
        assert all(t.sources == [ToolSource.PIPX] for t in tools)
        assert all(t.installed_by == [ToolSource.PIPX] for t in tools)


def test_pipx_collector_collect_empty():
    mock_data = {"venvs": {}}
    mock_output = json.dumps(mock_data)

    with patch("shutil.which", return_value="/usr/bin/pipx"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)

        collector = PipxCollector()
        tools = collector.collect()
        assert tools == []


def test_pipx_collector_collect_timeout():
    with (
        patch("shutil.which", return_value="/usr/bin/pipx"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pipx list --json", timeout=10)),
    ):
        collector = PipxCollector()
        tools = collector.collect()
        assert tools == []


def test_pipx_collector_collect_not_available():
    with patch("shutil.which", return_value=None):
        collector = PipxCollector()
        tools = collector.collect()
        assert tools == []


def test_pipx_collector_collect_error():
    with patch("shutil.which", return_value="/usr/bin/pipx"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="error: pipx failed", returncode=1)

        collector = PipxCollector()
        tools = collector.collect()
        assert tools == []


def test_pipx_collector_collect_invalid_json():
    with patch("shutil.which", return_value="/usr/bin/pipx"), patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="not json", stderr="", returncode=0)

        collector = PipxCollector()
        tools = collector.collect()
        assert tools == []
