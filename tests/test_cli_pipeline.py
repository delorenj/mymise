from unittest.mock import patch
from datetime import datetime
from typer.testing import CliRunner

from mymise.cli import app

runner = CliRunner()


def test_all_command_placeholder(tmp_path):
    """Verify that 'all' command currently returns placeholder message and exit code 1."""
    # Note: Currently it's implemented, so it should return 0
    result = runner.invoke(app, ["all", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Pipeline Complete!" in result.output


from mymise.models import DiscoveryResult, RegistrationResult

def test_all_pipeline_json_stdout(tmp_path):
    """Test 'mymise --json all' outputs the final registration result as JSON."""
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
    from datetime import datetime
    mock_scan.return_value = DiscoveryResult(
        scan_timestamp=datetime.now(),
        hostname="test",
        user="test",
        scan_duration_seconds=1.0,
        tools=[],
        errors=["Collector failed"]
    )
    
    result = runner.invoke(app, ["all", "--output-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "Collector failed" in result.output
