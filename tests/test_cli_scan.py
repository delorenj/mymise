import json
import tomli
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner
from mymise.cli import app
from mymise.models import DiscoveryResult, DiscoveredTool, ToolSource
from datetime import datetime, timezone
import pytest

runner = CliRunner(mix_stderr=False)

@pytest.fixture
def mock_scan_result():
    return DiscoveryResult(
        scan_timestamp=datetime.now(timezone.utc),
        hostname="test-host",
        user="test-user",
        scan_duration_seconds=1.5,
        tools=[
            DiscoveredTool(name="bat", sources=[ToolSource.PATH], frequency=1),
            DiscoveredTool(name="ls", sources=[ToolSource.HISTORY], frequency=10)
        ],
        errors=[]
    )

@pytest.fixture
def mock_partial_scan_result():
    return DiscoveryResult(
        scan_timestamp=datetime.now(timezone.utc),
        hostname="test-host",
        user="test-user",
        scan_duration_seconds=1.5,
        tools=[
            DiscoveredTool(name="ls", sources=[ToolSource.HISTORY], frequency=10)
        ],
        partial_failure=True,
        errors=["AptCollector failed (RuntimeError): Test error"]
    )

def test_scan_generates_default_file(tmp_path, monkeypatch, mock_scan_result):
    """AC: DiscoveryResult written to mymise-discovery.json by default."""
    monkeypatch.chdir(tmp_path)
    with patch("mymise.cli.run_scan", return_value=mock_scan_result):
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0
        assert (tmp_path / "mymise-discovery.json").exists()
        data = json.loads((tmp_path / "mymise-discovery.json").read_text())
        assert data["hostname"] == "test-host"

def test_scan_custom_output(tmp_path, monkeypatch, mock_scan_result):
    """AC: DiscoveryResult written to specified path via --output."""
    monkeypatch.chdir(tmp_path)
    custom_output = tmp_path / "custom.json"
    with patch("mymise.cli.run_scan", return_value=mock_scan_result):
        result = runner.invoke(app, ["scan", "--output", str(custom_output)])
        assert result.exit_code == 0
        assert custom_output.exists()

def test_scan_history_file_override(tmp_path, monkeypatch, mock_scan_result):
    """AC: --history-file reads from specified path instead of default."""
    monkeypatch.chdir(tmp_path)
    custom_history = tmp_path / ".custom_history"
    custom_history.write_text("ls\n")
    with patch("mymise.cli.run_scan", return_value=mock_scan_result) as mock_run:
        result = runner.invoke(app, ["scan", "--history-file", str(custom_history)])
        assert result.exit_code == 0
        mock_run.assert_called_once_with(history_file=str(custom_history), skip_pkg_managers=[])

def test_scan_skip_pkg_managers(tmp_path, monkeypatch, mock_scan_result):
    """AC: --skip-pkg-managers excludes specific collectors."""
    monkeypatch.chdir(tmp_path)
    with patch("mymise.cli.run_scan", return_value=mock_scan_result) as mock_run:
        result = runner.invoke(app, ["scan", "--skip-pkg-managers", "cargo,npm"])
        assert result.exit_code == 0
        kwargs = mock_run.call_args.kwargs
        assert kwargs["skip_pkg_managers"] == ["cargo", "npm"]

def test_scan_format_toml(tmp_path, monkeypatch, mock_scan_result):
    """AC: --format toml serializes as TOML and writes to output path."""
    monkeypatch.chdir(tmp_path)
    with patch("mymise.cli.run_scan", return_value=mock_scan_result):
        result = runner.invoke(app, ["scan", "--format", "toml", "--output", "out.toml"])
        assert result.exit_code == 0
        assert (tmp_path / "out.toml").exists()
        with open(tmp_path / "out.toml", "rb") as f:
            data = tomli.load(f)
        assert data["hostname"] == "test-host"
        assert len(data["tools"]) == 2

def test_scan_json_flag(tmp_path, monkeypatch, mock_scan_result):
    """AC: --json writes JSON to stdout, no file, suppresses Rich on stderr."""
    monkeypatch.chdir(tmp_path)
    with patch("mymise.cli.run_scan", return_value=mock_scan_result):
        result = runner.invoke(app, ["--json", "scan"])
        assert result.exit_code == 0
        
        # JSON should be in stdout
        data = json.loads(result.stdout)
        assert data["hostname"] == "test-host"
        
        # No file should be created
        assert not (tmp_path / "mymise-discovery.json").exists()
        
        # Rich summary should NOT be on stderr
        assert "Scan Complete!" not in result.stderr
        assert "Discovery" not in result.stderr

def test_scan_rich_summary_stderr(tmp_path, monkeypatch, mock_scan_result):
    """AC: Successful scan without --json shows Rich table on stderr."""
    monkeypatch.chdir(tmp_path)
    with patch("mymise.cli.run_scan", return_value=mock_scan_result):
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0
        
        # Rich summary should be on stderr
        assert "Scan Complete!" in result.stderr
        assert "Discovery" in result.stderr
        assert "Sources" in result.stderr
        assert "Top 10" in result.stderr
        # Tools count
        assert "Total Unique Tools Discovered: 2" in result.stderr

def test_scan_partial_failure_exit_code(tmp_path, monkeypatch, mock_partial_scan_result):
    """AC: Partial failures (some collectors failed) exit code 1 and warnings on stderr."""
    monkeypatch.chdir(tmp_path)
    with patch("mymise.cli.run_scan", return_value=mock_partial_scan_result):
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 1
        
        # Warnings on stderr
        assert "Warnings (Partial Failures):" in result.stderr
        assert "AptCollector failed (RuntimeError): Test error" in result.stderr
