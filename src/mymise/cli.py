import logging
import re
from enum import StrEnum
from pathlib import Path
from typing import Any

import tomli_w
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from mymise.models import DiscoveryResult, RegistrationResult, ResolutionResult
from mymise.registrar import register as run_register
from mymise.resolver import resolve as run_resolve
from mymise.scanner import scan as run_scan

app = typer.Typer(name="mymise", help="Reverse-engineer your CLI toolchain and resolve against mise registry.")
console = Console(stderr=True)

# Configure structured logger using RichHandler
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger("mymise")

DEFAULT_HISTORY = Path.home() / ".zsh_history"


class OutputFormat(StrEnum):
    JSON = "json"
    TOML = "toml"


def _remove_none_values(data: Any) -> Any:
    """Recursively remove None values from a dictionary or list."""
    if isinstance(data, dict):
        return {k: _remove_none_values(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [_remove_none_values(v) for v in data if v is not None]
    return data


def _print_scan_summary(result) -> None:
    """Print a rich summary of the scan results to stderr."""
    console.print(f"\n[bold green]Scan Complete![/] Duration: {result.scan_duration_seconds:.2f}s", style="green")
    console.print(f"Total Unique Tools Discovered: [bold]{len(result.tools)}[/]\n")

    # Source breakdown
    source_counts = {}
    for tool in result.tools:
        for source in tool.sources:
            source_counts[source] = source_counts.get(source, 0) + 1

    table = Table(title="Discovery Sources", box=None)
    table.add_column("Source", style="cyan")
    table.add_column("Count", justify="right", style="magenta")

    for source in sorted(source_counts.keys()):
        table.add_row(str(source), str(source_counts[source]))

    console.print(table)

    # Top 10 by frequency
    top_tools = sorted(result.tools, key=lambda x: x.frequency, reverse=True)[:10]
    if top_tools:
        console.print("\n[bold]Top 10 Most Frequent Tools:[/]")
        top_table = Table(box=None)
        top_table.add_column("Tool", style="yellow")
        top_table.add_column("Frequency", justify="right")
        top_table.add_column("Sources")

        for tool in top_tools:
            top_table.add_row(tool.name, str(tool.frequency), ", ".join(tool.sources))
        console.print(top_table)

    if result.errors:
        console.print("\n[bold yellow]Warnings (Partial Failures):[/]")
        for error in result.errors:
            console.print(f"  [yellow]![/] {error}")


def _print_resolve_summary(result) -> None:
    """Print a rich summary of the resolution results to stderr."""
    console.print("\n[bold green]Resolution Complete![/]", style="green")

    table = Table(box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="magenta")

    table.add_row("Resolved Tools", str(len(result.resolved)))
    table.add_row("Unresolved Tools", str(len(result.unresolved)))
    table.add_row("Resolution Rate", f"{result.resolution_rate * 100:.1f}%")

    console.print(table)

    # Backend distribution
    backend_counts = {}
    for tool in result.resolved:
        backend_counts[tool.backend] = backend_counts.get(tool.backend, 0) + 1

    if backend_counts:
        console.print("\n[bold]Backend Distribution:[/]")
        b_table = Table(box=None)
        b_table.add_column("Backend", style="yellow")
        b_table.add_column("Count", justify="right")

        for backend in sorted(backend_counts.keys()):
            b_table.add_row(str(backend), str(backend_counts[backend]))
        console.print(b_table)

    if result.errors:
        console.print("\n[bold yellow]Warnings (Partial Failures):[/]")
        for error in result.errors:
            console.print(f"  [yellow]![/] {error}")


def _print_register_summary(result: RegistrationResult) -> None:
    """Print a rich summary of the registration results to stderr."""
    console.print("\n[bold green]Registration Complete![/]", style="green")

    table = Table(box=None)
    table.add_column("Artifact", style="cyan")
    table.add_column("Tools", justify="right", style="magenta")
    table.add_column("Output Path", style="dim")

    for name, path in result.artifacts.items():
        count = 0
        if name == "mise.toml":
            count = result.resolved_count
        elif name == "bootstrap.sh":
            count = result.bootstrap_count
        else:
            # Assumed shorthands file
            count = result.shorthands_count

        table.add_row(name, str(count), str(path))

    console.print(table)
    console.print(f"\nTotal Artifacts Generated: [bold]{len(result.artifacts)}[/]\n")

    if result.errors:
        console.print("\n[bold yellow]Warnings (Partial Failures):[/]")
        for error in result.errors:
            console.print(f"  [yellow]![/] {error}")


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    json: bool = typer.Option(False, "--json", "-j", help="Output JSON to stdout and suppress summary"),
) -> None:
    if verbose:
        logger.setLevel(logging.DEBUG)


@app.command()
def scan(
    ctx: typer.Context,
    history_file: Path = typer.Option(DEFAULT_HISTORY, "--history-file", "-h", help="Path to shell history file"),
    output: Path = typer.Option("mymise-discovery.json", "--output", "-o", help="Output file"),
    skip_pkg_managers: str = typer.Option("", "--skip-pkg-managers", help="Comma-separated list of pkg-mgrs to skip"),
    format: OutputFormat = typer.Option(OutputFormat.JSON, "--format", "-f", help="Output format (json or toml)"),
) -> None:
    """Scan the system for CLI tools."""
    skip_list = [s.strip() for s in skip_pkg_managers.split(",") if s.strip()]

    result = run_scan(history_file=str(history_file), skip_pkg_managers=skip_list)

    if ctx.parent and ctx.parent.params.get("json"):
        # Output JSON to stdout, suppress everything else
        print(result.model_dump_json(indent=2))
    else:
        # File output
        if format == OutputFormat.TOML:
            # Pydantic model to dict for TOML serialization
            # Using mode="json" handles datetime objects
            data = result.model_dump(mode="json")
            # TOML doesn't support null/None, so we must remove them
            data = _remove_none_values(data)
            output_content = tomli_w.dumps(data)
            output.write_text(output_content)
        else:
            output.write_text(result.model_dump_json(indent=2))

        # Summary to stderr
        _print_scan_summary(result)

    if result.errors:
        raise typer.Exit(1)


@app.command()
def resolve(
    ctx: typer.Context,
    input_file: Path = typer.Option("mymise-discovery.json", "--input", "-i", help="Discovery JSON from scan"),
    output: Path = typer.Option("mymise-resolved.json", "--output", "-o", help="Output JSON file"),
    timeout: int = typer.Option(10, "--timeout", "-t", help="Timeout for each mise registry call"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Skip install probing, only classify"),
) -> None:
    """Resolve discovered tools against mise registry."""
    if not input_file.exists():
        console.print(f"[bold red]Error:[/] Input file {input_file} not found.", style="red")
        raise typer.Exit(2)

    try:
        discovery = DiscoveryResult.model_validate_json(input_file.read_text())
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to parse discovery file: {e}", style="red")
        raise typer.Exit(2) from e

    result = run_resolve(discovery, timeout=timeout, dry_run=dry_run)

    if ctx.parent and ctx.parent.params.get("json"):
        print(result.model_dump_json(indent=2))
    else:
        output.write_text(result.model_dump_json(indent=2))
        _print_resolve_summary(result)
        
    if result.errors or result.partial_failure:
        raise typer.Exit(1)


@app.command()
def register(
    ctx: typer.Context,
    input_file: Path = typer.Option("mymise-resolved.json", "--input", "-i", help="Resolution JSON from resolve"),
    output_dir: Path = typer.Option(".", "--output-dir", "-d", help="Output directory for artifacts"),
    shorthands_file: str = typer.Option(
        "shorthands.toml", "--shorthands-file", help="Filename for personal registry shorthands"
    ),
) -> None:
    """Generate mise artifacts from resolution results."""
    if not input_file.exists():
        console.print(f"[bold red]Error:[/] Input file {input_file} not found.", style="red")
        raise typer.Exit(2)

    try:
        resolution = ResolutionResult.model_validate_json(input_file.read_text())
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to parse resolution file: {e}", style="red")
        raise typer.Exit(2) from e

    result = run_register(resolution, output_dir=output_dir, shorthands_file=shorthands_file)

    if ctx.parent and ctx.parent.params.get("json"):
        print(result.model_dump_json(indent=2))
    else:
        _print_register_summary(result)

    if result.errors or result.partial_failure:
        raise typer.Exit(1)


@app.command(name="all")
def run_all(
    ctx: typer.Context,
    history_file: Path = typer.Option(DEFAULT_HISTORY, "--history-file", "-h", help="Path to shell history file"),
    output_dir: Path = typer.Option(".", "--output-dir", "-d", help="Output directory for all artifacts"),
    skip_pkg_managers: str = typer.Option("", "--skip-pkg-managers", help="Comma-separated list of pkg-mgrs to skip"),
) -> None:
    """Run full scan -> resolve -> register pipeline."""
    is_json = ctx.parent and ctx.parent.params.get("json")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. SCAN
    if not is_json:
        console.print("[bold cyan]>>> Step 1/3: Scanning system...[/]")
    
    skip_list = [s.strip() for s in skip_pkg_managers.split(",") if s.strip()]
    discovery = run_scan(history_file=str(history_file), skip_pkg_managers=skip_list)

    if not is_json:
        discovery_path = output_dir / "mymise-discovery.json"
        discovery_path.write_text(discovery.model_dump_json(indent=2))
        _print_scan_summary(discovery)

    # 2. RESOLVE
    if not is_json:
        console.print("\n[bold cyan]>>> Step 2/3: Resolving tools against mise registry...[/]")
    
    resolution = run_resolve(discovery)

    if not is_json:
        resolution_path = output_dir / "mymise-resolved.json"
        resolution_path.write_text(resolution.model_dump_json(indent=2))
        _print_resolve_summary(resolution)

    # 3. REGISTER
    if not is_json:
        console.print("\n[bold cyan]>>> Step 3/3: Generating mise artifacts...[/]")
    
    registration = run_register(resolution, output_dir=output_dir)
    
    if is_json:
        print(registration.model_dump_json(indent=2))
    else:
        _print_register_summary(registration)
        console.print(f"\n[bold green]Pipeline Complete![/] All files generated in [bold]{output_dir}[/]")

    # Check for partial failures in any step
    has_errors = (
        discovery.errors or discovery.partial_failure or
        resolution.errors or resolution.partial_failure or
        registration.errors or registration.partial_failure
    )
    if has_errors:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
