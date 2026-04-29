from datetime import UTC, datetime
from unittest.mock import patch

from typer.testing import CliRunner

from mymise.cli import app
from mymise.models import DiscoveryResult, ResolutionResult

runner = CliRunner()


def _empty_discovery() -> DiscoveryResult:
    return DiscoveryResult(
        scan_timestamp=datetime.now(UTC),
        hostname="test",
        user="test",
        scan_duration_seconds=0.0,
        tools=[],
    )


def _empty_resolution() -> ResolutionResult:
    return ResolutionResult(
        resolution_timestamp=datetime.now(UTC),
        resolved=[],
        unresolved=[],
        resolution_rate=0.0,
    )


@patch("mymise.cli.run_resolve")
@patch("mymise.cli.run_scan")
def test_all_command_placeholder(mock_scan, mock_resolve, tmp_path):
    """Pipeline succeeds end-to-end when all stages return clean results."""
    mock_scan.return_value = _empty_discovery()
    mock_resolve.return_value = _empty_resolution()

    result = runner.invoke(app, ["all", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Pipeline Complete!" in result.output


@patch("mymise.cli.run_resolve")
@patch("mymise.cli.run_scan")
def test_all_pipeline_json_stdout(mock_scan, mock_resolve, tmp_path):
    """`mymise --json all` outputs the final registration result as JSON to stdout."""
    mock_scan.return_value = _empty_discovery()
    mock_resolve.return_value = _empty_resolution()

    result = runner.invoke(app, ["--json", "all", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0

    # Should output RegistrationResult JSON to stdout
    assert '"artifacts":' in result.output
    assert '"mise.toml":' in result.output

    # Should NOT contain Rich summaries or Step progress
    assert "Step 1/3" not in result.output
    assert "Scan Complete!" not in result.output
    assert "Resolution Complete!" not in result.output
    assert "Registration Complete!" not in result.output


@patch("mymise.cli.run_scan")
def test_all_pipeline_partial_failure(mock_scan, tmp_path):
    """Test 'mymise all' exits with code 1 on partial failure."""
    mock_scan.return_value = DiscoveryResult(
        scan_timestamp=datetime.now(),
        hostname="test",
        user="test",
        scan_duration_seconds=1.0,
        tools=[],
        errors=["Collector failed"],
    )

    result = runner.invoke(app, ["all", "--output-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "Collector failed" in result.output
