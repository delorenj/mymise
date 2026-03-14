from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(name="mymise", help="Reverse-engineer your CLI toolchain and resolve against mise registry.")
console = Console(stderr=True)

DEFAULT_HISTORY = Path.home() / ".zsh_history"


class AppState:
    def __init__(self, verbose: bool = False, json_output: bool = False) -> None:
        self.verbose = verbose
        self.json_output = json_output


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON to stdout"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj = AppState(verbose=verbose, json_output=json_output)


@app.command()
def scan(
    ctx: typer.Context,
    history_file: Path = typer.Option(DEFAULT_HISTORY, "--history", "-h", help="Path to shell history file"),
    output: Path = typer.Option("mymise-discovery.json", "--output", "-o", help="Output JSON file"),
) -> None:
    console.print("[bold]mymise scan[/] - not yet implemented", style="yellow")
    raise typer.Exit(1)


@app.command()
def resolve(
    ctx: typer.Context,
    input_file: Path = typer.Option("mymise-discovery.json", "--input", "-i", help="Discovery JSON from scan"),
    output: Path = typer.Option("mymise-resolved.json", "--output", "-o", help="Output JSON file"),
) -> None:
    console.print("[bold]mymise resolve[/] - not yet implemented", style="yellow")
    raise typer.Exit(1)


@app.command()
def register(
    ctx: typer.Context,
    input_file: Path = typer.Option("mymise-resolved.json", "--input", "-i", help="Resolution JSON from resolve"),
    output_dir: Path = typer.Option(".", "--output-dir", "-d", help="Output directory for artifacts"),
) -> None:
    console.print("[bold]mymise register[/] - not yet implemented", style="yellow")
    raise typer.Exit(1)


@app.command(name="all")
def run_all(
    ctx: typer.Context,
    history_file: Path = typer.Option(DEFAULT_HISTORY, "--history", "-h", help="Path to shell history file"),
    output_dir: Path = typer.Option(".", "--output-dir", "-d", help="Output directory for all artifacts"),
) -> None:
    console.print("[bold]mymise all[/] - not yet implemented", style="yellow")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
