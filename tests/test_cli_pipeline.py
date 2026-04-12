from typer.testing import CliRunner

from mymise.cli import app

runner = CliRunner()


def test_all_command_placeholder(tmp_path):
    """Verify that 'all' command currently returns placeholder message and exit code 1."""
    # Note: Currently it's implemented, so it should return 0
    result = runner.invoke(app, ["all", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Pipeline Complete!" in result.output


def test_all_pipeline_success(tmp_path, monkeypatch):
    """Test successful end-to-end pipeline execution."""
    # Mock some history if needed, or just let it run if it's safe
    result = runner.invoke(app, ["all", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0

    # Check intermediate files
    assert (tmp_path / "mymise-discovery.json").exists()
    assert (tmp_path / "mymise-resolved.json").exists()

    # Check final artifacts
    assert (tmp_path / "mise.toml").exists()
    assert (tmp_path / "shorthands.toml").exists()
    assert (tmp_path / "bootstrap.sh").exists()
