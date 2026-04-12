from datetime import UTC
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from mymise.cli import app
from mymise.models import DiscoveredTool, DiscoveryResult, ToolSource

runner = CliRunner()


@pytest.fixture
def mock_discovery_result() -> DiscoveryResult:
    """Return a mock DiscoveryResult for testing."""
    from datetime import datetime
    return DiscoveryResult(
        scan_timestamp=datetime.now(UTC),
        hostname="test-host",
        user="test-user",
        scan_duration_seconds=1.5,
        tools=[
            DiscoveredTool(
                name="ls",
                sources=[ToolSource.PATH],
                frequency=100,
                last_used=datetime.now(UTC),
                binary_path="/usr/bin/ls",
                installed_by=[ToolSource.APT],
            ),
            DiscoveredTool(
                name="git",
                sources=[ToolSource.HISTORY, ToolSource.PATH],
                frequency=500,
                last_used=datetime.now(UTC),
                binary_path="/usr/bin/git",
                installed_by=[ToolSource.APT],
            ),
        ],
    )


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "mymise" in result.output.lower()


@patch("mymise.cli.run_scan")
def test_scan_default(mock_scan: MagicMock, mock_discovery_result: DiscoveryResult, tmp_path: Path) -> None:
    """Test 'mymise scan' with default parameters."""
    mock_scan.return_value = mock_discovery_result
    
    # Change to temp directory so output file is created there
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0
        
        output_file = Path("mymise-discovery.json")
        assert output_file.exists()
        assert '"schema_version": "1.0.0"' in output_file.read_text()
        assert "ls" in output_file.read_text()
        assert "git" in output_file.read_text()


@patch("mymise.cli.run_scan")
def test_scan_custom_output(mock_scan: MagicMock, mock_discovery_result: DiscoveryResult, tmp_path: Path) -> None:
    """Test 'mymise scan --output' flag."""
    mock_scan.return_value = mock_discovery_result
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        output_file = Path("custom.json")
        result = runner.invoke(app, ["scan", "--output", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()
        assert '"schema_version": "1.0.0"' in output_file.read_text()


@patch("mymise.cli.run_scan")
def test_scan_skip_pkg_managers(mock_scan: MagicMock, mock_discovery_result: DiscoveryResult, tmp_path: Path) -> None:
    """Test 'mymise scan --skip-pkg-managers' flag."""
    mock_scan.return_value = mock_discovery_result
    
    runner.invoke(app, ["scan", "--skip-pkg-managers", "apt,snap"])
    
    # Verify mock_scan was called with skip_pkg_managers=["apt", "snap"]
    args, kwargs = mock_scan.call_args
    assert kwargs["skip_pkg_managers"] == ["apt", "snap"]


@patch("mymise.cli.run_scan")
def test_scan_format_toml(mock_scan: MagicMock, mock_discovery_result: DiscoveryResult, tmp_path: Path) -> None:
    """Test 'mymise scan --format toml' flag."""
    mock_scan.return_value = mock_discovery_result
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["scan", "--format", "toml", "--output", "discovery.toml"])
        assert result.exit_code == 0
        output_file = Path("discovery.toml")
        assert output_file.exists()
        assert 'schema_version = "1.0.0"' in output_file.read_text()


@patch("mymise.cli.run_scan")
def test_scan_json_stdout(mock_scan: MagicMock, mock_discovery_result: DiscoveryResult, tmp_path: Path) -> None:
    """Test 'mymise scan --json' flag for stdout output."""
    mock_scan.return_value = mock_discovery_result
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["--json", "scan"])
        assert result.exit_code == 0
        # Output should be in result.output (stdout)
        assert '"schema_version": "1.0.0"' in result.output
        # Should not create default file if it's JSON output to stdout
        assert not Path("mymise-discovery.json").exists()


@patch("mymise.cli.run_scan")
def test_scan_rich_summary(mock_scan: MagicMock, mock_discovery_result: DiscoveryResult, tmp_path: Path) -> None:
    """Test 'mymise scan' rich summary output on stderr."""
    mock_scan.return_value = mock_discovery_result
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0
        assert "Scan Complete!" in result.output
        assert "ls" in result.output
        assert "git" in result.output


@patch("mymise.cli.run_scan")
def test_scan_partial_failure(mock_scan: MagicMock, mock_discovery_result: DiscoveryResult, tmp_path: Path) -> None:
    """Test 'mymise scan' with partial failure exit code."""
    mock_discovery_result.errors = ["Some collector failed"]
    mock_scan.return_value = mock_discovery_result
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 1
        assert "Some collector failed" in result.output
        assert "!" in result.output


def test_all_not_implemented() -> None:
    result = runner.invoke(app, ["all"])
    assert result.exit_code == 1
