import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mymise.cli import app

runner = CliRunner()

@pytest.fixture
def mock_resolution_json(tmp_path):
    data = {
        "resolution_timestamp": "2024-04-12T12:00:00",
        "resolved": [
            {
                "name": "gh", 
                "backend": "asdf", 
                "registry_entry": "github-cli",
                "install_command": "asdf install github-cli latest",
                "original": {"name": "gh", "sources": ["path"], "frequency": 1}
            }
        ],
        "unresolved": [
            {
                "name": "not-found",
                "suggested_actions": ["apt install not-found"],
                "original": {"name": "not-found", "sources": ["path"], "frequency": 1}
            },
            {
                "name": "custom-github",
                "suggested_actions": ["Try github:user/repo"],
                "original": {"name": "custom-github", "sources": ["path"], "frequency": 1}
            }
        ],
        "resolution_rate": 0.33
    }
    path = tmp_path / "mymise-resolved.json"
    path.write_text(json.dumps(data))
    return path

def test_register_missing_input_file():
    """Test that register fails with exit code 2 if input file is missing."""
    result = runner.invoke(app, ["register", "--input", "non-existent.json"])
    assert result.exit_code == 2
    assert "error" in result.output.lower()
    assert "non-existent.json not found" in result.output.lower()

def test_register_success_default_paths(mock_resolution_json, tmp_path, monkeypatch):
    """Test successful register with default paths."""
    # Change current working directory to tmp_path so default output-dir is tested
    monkeypatch.chdir(tmp_path)
    
    # We need to make sure the default "mymise-resolved.json" exists in the current dir
    default_input = tmp_path / "mymise-resolved.json"
    if not default_input.exists():
        default_input.write_text(mock_resolution_json.read_text())

    result = runner.invoke(app, ["register"])
    
    assert result.exit_code == 0
    assert "Registration Complete!" in result.output
    
    # Check generated files
    assert (tmp_path / "mise.toml").exists()
    assert (tmp_path / "shorthands.toml").exists()
    assert (tmp_path / "bootstrap.sh").exists()
    
    # Check content of mise.toml
    mise_content = (tmp_path / "mise.toml").read_text()
    assert 'gh = "latest"' in mise_content
    assert "asdf:github-cli" in mise_content

def test_register_custom_flags(mock_resolution_json, tmp_path):
    """Test register with custom --input, --output-dir, and --shorthands-file."""
    output_dir = tmp_path / "output"
    shorthands_name = "custom-shorthands.toml"
    
    result = runner.invoke(app, [
        "register",
        "--input", str(mock_resolution_json),
        "--output-dir", str(output_dir),
        "--shorthands-file", shorthands_name
    ])
    
    assert result.exit_code == 0
    assert "Registration Complete!" in result.output
    
    # Check generated files in custom dir
    assert (output_dir / "mise.toml").exists()
    assert (output_dir / shorthands_name).exists()
    assert (output_dir / "bootstrap.sh").exists()
    
    # Check shorthands content
    shorthands_content = (output_dir / shorthands_name).read_text()
    assert 'custom-github = "github:user/repo"' in shorthands_content
