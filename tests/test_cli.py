from typer.testing import CliRunner

from mymise.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "mymise" in result.output.lower()


def test_scan_not_implemented() -> None:
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 1


def test_resolve_not_implemented() -> None:
    result = runner.invoke(app, ["resolve"])
    assert result.exit_code == 1


def test_register_not_implemented() -> None:
    result = runner.invoke(app, ["register"])
    assert result.exit_code == 1
