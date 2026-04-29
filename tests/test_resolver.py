from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from mymise.models import BackendType, DiscoveredTool, DiscoveryResult, ToolCategory, ToolSource
from mymise.resolver import resolve


@pytest.fixture
def discovery_result():
    return DiscoveryResult(
        scan_timestamp=datetime.now(),
        hostname="test-host",
        user="test-user",
        scan_duration_seconds=1.5,
        tools=[
            DiscoveredTool(name="python", sources=[ToolSource.PATH], frequency=10, category=ToolCategory.LANGUAGE_TOOL),
            DiscoveredTool(name="unknown-tool", sources=[ToolSource.PATH], frequency=1, category=ToolCategory.CLI_TOOL),
        ],
    )


def test_resolver_happy_path(discovery_result):
    with patch("subprocess.run") as mock_run:
        # Mock successful mise registry lookup for python
        # Mock failure for unknown-tool
        def side_effect(cmd, **kwargs):
            if cmd == ["mise", "registry", "python"]:
                return MagicMock(returncode=0, stdout="python\tcore:python\n", stderr="")
            else:
                return MagicMock(returncode=1, stdout="", stderr="error")

        mock_run.side_effect = side_effect

        result = resolve(discovery_result)

        assert len(result.resolved) == 1
        assert result.resolved[0].name == "python"
        assert result.resolved[0].backend == BackendType.CORE
        assert result.resolved[0].registry_entry == "python"

        assert len(result.unresolved) == 1
        assert result.unresolved[0].name == "unknown-tool"
        assert result.resolution_rate == 0.5


def test_resolver_timeout(discovery_result):
    with patch("subprocess.run") as mock_run:
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["mise"], timeout=10)

        result = resolve(discovery_result)

        assert len(result.resolved) == 0
        assert len(result.unresolved) == 2
        assert result.resolution_rate == 0.0


def test_resolver_dry_run(discovery_result):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="python\tcore:python\n", stderr="")

        # We just want to check that it still runs subprocess
        result = resolve(discovery_result, dry_run=True)

        assert len(result.resolved) > 0


def test_resolver_unknown_backend(discovery_result):
    """When mise emits only backends our enum doesn't know, the parser falls through to 'format unrecognized'."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="unknown_backend:python\n", stderr="")

        result = resolve(discovery_result)

        assert len(result.unresolved) == 2
        assert any("unrecognized" in r.suggested_actions[0] for r in result.unresolved if r.name == "python")


def test_resolver_unrecognized_format(discovery_result):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="bad_format_no_colons\n", stderr="")

        result = resolve(discovery_result)

        assert len(result.unresolved) == 2
        assert any("unrecognized" in r.suggested_actions[0] for r in result.unresolved if r.name == "python")


def test_resolver_generic_exception(discovery_result):
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Surprise!")

        result = resolve(discovery_result)

        assert len(result.resolved) == 0
        assert len(result.unresolved) == 2


def test_resolver_empty_discovery():
    discovery = DiscoveryResult(
        scan_timestamp=datetime.now(), hostname="test-host", user="test-user", scan_duration_seconds=0.1, tools=[]
    )
    result = resolve(discovery)
    assert len(result.resolved) == 0
    assert len(result.unresolved) == 0


def test_resolver_propagates_partial_failure_on_timeout(discovery_result):
    """Timeouts must surface in ResolutionResult.errors and partial_failure, not be silently swallowed."""
    import subprocess

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["mise"], timeout=10)
        result = resolve(discovery_result)

    assert result.partial_failure is True
    assert len(result.errors) == len(discovery_result.tools)
    assert all("Timeout" in err for err in result.errors)


def test_resolver_propagates_partial_failure_on_unrecognized_format(discovery_result):
    """When mise output has no recognizable backend, the parser must surface a partial failure."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="not_a_real_backend:python\n", stderr="")
        result = resolve(discovery_result)

    assert result.partial_failure is True
    assert any("unrecognized" in err for err in result.errors)


def test_resolver_parses_real_mise_format_single_entry(discovery_result):
    """Real `mise registry node` returns 'core:node' with no leading tool-name or tabs."""
    from mymise.models import BackendType

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="core:python\n", stderr="")
        result = resolve(discovery_result)

    assert len(result.resolved) == 2
    assert all(r.backend == BackendType.CORE for r in result.resolved)
    assert all(r.registry_entry == "python" for r in result.resolved)


def test_resolver_parses_real_mise_format_multiple_backends(discovery_result):
    """Real `mise registry rg` returns 'aqua:BurntSushi/ripgrep asdf:... cargo:ripgrep' on one line."""
    from mymise.models import BackendType

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="aqua:BurntSushi/ripgrep asdf:https://gitlab.com/wt0f/asdf-ripgrep cargo:ripgrep\n",
            stderr="",
        )
        result = resolve(discovery_result)

    # Parser prefers the first valid entry (aqua) since mise lists by registry preference
    assert len(result.resolved) == 2
    assert all(r.backend == BackendType.AQUA for r in result.resolved)
    assert all(r.registry_entry == "BurntSushi/ripgrep" for r in result.resolved)


def test_resolver_skips_unknown_backends_picks_first_known(discovery_result):
    """If first entry has an unknown backend, parser falls through to the next valid one."""
    from mymise.models import BackendType

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="weirdbackend:foo cargo:python\n", stderr="")
        result = resolve(discovery_result)

    assert len(result.resolved) == 2
    assert all(r.backend == BackendType.CARGO for r in result.resolved)
    assert all(r.registry_entry == "python" for r in result.resolved)
    # No error tracking when a fallback succeeds
    assert result.partial_failure is False


def test_resolver_clean_run_has_no_errors(discovery_result):
    """A pure not-found-in-registry result is not an error and must not trip partial_failure."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        result = resolve(discovery_result)

    assert result.partial_failure is False
    assert result.errors == []
    assert result.resolution_rate == 0.0
