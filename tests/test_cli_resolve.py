import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from mymise.cli import app
from mymise.models import (
    BackendType,
    DiscoveredTool,
    DiscoveryResult,
    ResolutionResult,
    ResolvedTool,
    ToolSource,
    UnresolvedTool,
)

runner = CliRunner()


@pytest.fixture
def mock_discovery_result() -> DiscoveryResult:
    """Return a mock DiscoveryResult for testing."""
    return DiscoveryResult(
        scan_timestamp=datetime.now(UTC),
        hostname="test-host",
        user="test-user",
        scan_duration_seconds=1.5,
        tools=[
            DiscoveredTool(
                name="git",
                sources=[ToolSource.PATH],
                frequency=100,
            ),
            DiscoveredTool(
                name="unknown-tool",
                sources=[ToolSource.PATH],
                frequency=1,
            ),
        ],
    )


@pytest.fixture
def mock_resolution_result(mock_discovery_result: DiscoveryResult) -> ResolutionResult:
    """Return a mock ResolutionResult for testing."""
    return ResolutionResult(
        resolution_timestamp=datetime.now(UTC),
        resolved=[
            ResolvedTool(
                name="git",
                backend=BackendType.CORE,
                registry_entry="git",
                install_command="mise install git@latest",
                original=mock_discovery_result.tools[0],
            )
        ],
        unresolved=[
            UnresolvedTool(
                name="unknown-tool",
                original=mock_discovery_result.tools[1],
                suggested_actions=["Not found in mise registry"],
            )
        ],
        resolution_rate=0.5,
    )


@patch("mymise.cli.run_resolve")
def test_resolve_default(
    mock_resolve: MagicMock,
    mock_discovery_result: DiscoveryResult,
    mock_resolution_result: ResolutionResult,
    tmp_path: Path,
) -> None:
    """Test 'mymise resolve' with default parameters."""
    mock_resolve.return_value = mock_resolution_result
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create input file
        input_file = Path("mymise-discovery.json")
        input_file.write_text(mock_discovery_result.model_dump_json())
        
        result = runner.invoke(app, ["resolve"])
        assert result.exit_code == 0
        
        output_file = Path("mymise-resolved.json")
        assert output_file.exists()
        assert '"schema_version": "1.0.0"' in output_file.read_text()
        assert "git" in output_file.read_text()
        
        # Check output for summary
        assert "Resolution Complete!" in result.output
        assert "Resolved Tools" in result.output
        assert "1" in result.output  # count of resolved
        assert "Unresolved Tools" in result.output
        assert "1" in result.output  # count of unresolved
        assert "Resolution Rate" in result.output
        assert "50.0%" in result.output
        assert "Backend Distribution" in result.output
        assert "core" in result.output  # the backend type from mock_resolution_result


@patch("mymise.cli.run_resolve")
def test_resolve_custom_paths(
    mock_resolve: MagicMock,
    mock_discovery_result: DiscoveryResult,
    mock_resolution_result: ResolutionResult,
    tmp_path: Path,
) -> None:
    """Test 'mymise resolve' with custom input/output paths."""
    mock_resolve.return_value = mock_resolution_result
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        input_file = Path("custom-input.json")
        input_file.write_text(mock_discovery_result.model_dump_json())
        output_file = Path("custom-output.json")
        
        result = runner.invoke(app, ["resolve", "--input", str(input_file), "--output", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()


@patch("mymise.cli.run_resolve")
def test_resolve_timeout_and_dry_run(
    mock_resolve: MagicMock,
    mock_discovery_result: DiscoveryResult,
    mock_resolution_result: ResolutionResult,
    tmp_path: Path,
) -> None:
    """Test 'mymise resolve' with --timeout and --dry-run flags."""
    mock_resolve.return_value = mock_resolution_result
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        input_file = Path("mymise-discovery.json")
        input_file.write_text(mock_discovery_result.model_dump_json())
        
        result = runner.invoke(app, ["resolve", "--timeout", "30", "--dry-run"])
        assert result.exit_code == 0
        
        # Verify mock_resolve was called with correct parameters
        args, kwargs = mock_resolve.call_args
        assert kwargs["timeout"] == 30
        assert kwargs["dry_run"] is True


def test_resolve_input_missing(tmp_path: Path) -> None:
    """Test 'mymise resolve' with missing input file."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["resolve", "--input", "nonexistent.json"])
        assert result.exit_code == 2
        assert "error" in result.output.lower()
        assert "not found" in result.output.lower()


@patch("mymise.cli.run_resolve")
def test_resolve_json_stdout(
    mock_resolve: MagicMock,
    mock_discovery_result: DiscoveryResult,
    mock_resolution_result: ResolutionResult,
    tmp_path: Path,
) -> None:
    """Test 'mymise resolve --json' flag for stdout output."""
    mock_resolve.return_value = mock_resolution_result
    
    with runner.isolated_filesystem(temp_dir=tmp_path):
        input_file = Path("mymise-discovery.json")
        input_file.write_text(mock_discovery_result.model_dump_json())
        
        result = runner.invoke(app, ["--json", "resolve"])
        assert result.exit_code == 0
        
        # Output should be in result.output
        assert '"schema_version": "1.0.0"' in result.output
        # Should NOT contain Rich summary
        assert "Resolution Complete!" not in result.output
        # Should not create default file
        assert not Path("mymise-resolved.json").exists()
