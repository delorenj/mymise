---
stepsCompleted: [system-overview, component-design, data-models, cli-interface]
inputDocuments: [PRD.md, Braindump.md]
workflowType: 'architecture'
---

# Architecture - mymise

**Date:** 2026-03-14

## System Overview

mymise is a single-process Python CLI. No server, no database, no network services. It shells out to system commands (`mise registry`, package manager queries) and reads local files (shell history, PATH dirs).

```
┌─────────────────────────────────────────────────┐
│                   mymise CLI                     │
│  (Typer app: scan / resolve / register / all)    │
├─────────┬───────────┬───────────┬───────────────┤
│ Scanner │ Resolver  │ Registrar │  Output       │
│ Pipeline│ Pipeline  │ Pipeline  │  Formatters   │
├─────────┴───────────┴───────────┴───────────────┤
│              Core Models (Pydantic)              │
├─────────────────────────────────────────────────┤
│         Collectors (pluggable scanners)          │
│  history │ path │ apt │ cargo │ npm │ mise │ ... │
└─────────────────────────────────────────────────┘
```

## Project Structure

```
mymise/
├── pyproject.toml          # uv project config
├── mise.toml               # mise tasks + tool versions
├── .plane.json             # Plane project link
├── src/
│   └── mymise/
│       ├── __init__.py
│       ├── cli.py           # Typer app, subcommands
│       ├── models.py        # Pydantic models (all data shapes)
│       ├── scanner.py       # Scan pipeline orchestrator
│       ├── resolver.py      # Resolution pipeline orchestrator
│       ├── registrar.py     # Registration/output generator
│       ├── collectors/      # Pluggable tool collectors
│       │   ├── __init__.py
│       │   ├── base.py      # Collector Protocol
│       │   ├── history.py   # Shell history parser
│       │   ├── path.py      # PATH binary scanner
│       │   ├── apt.py       # apt package list
│       │   ├── cargo.py     # cargo install --list
│       │   ├── npm.py       # npm list -g
│       │   ├── pipx.py      # pipx list
│       │   ├── mise.py      # mise ls --installed
│       │   ├── snap.py      # snap list
│       │   ├── go.py        # go/bin scanner
│       │   └── uv.py        # uv tool list
│       └── utils.py         # Shared helpers (subprocess, normalization)
└── tests/
    ├── conftest.py
    ├── test_cli.py
    ├── test_scanner.py
    ├── test_resolver.py
    ├── test_registrar.py
    └── collectors/
        ├── test_history.py
        ├── test_path.py
        └── ...
```

## Component Design

### CLI Layer (`cli.py`)

Typer app with callback for shared state:

```python
app = typer.Typer()

@app.callback()
def main(ctx: typer.Context, verbose: bool = False, json_output: bool = False):
    ctx.obj = AppState(verbose=verbose, json_output=json_output)

@app.command()
def scan(ctx: typer.Context, history_file: Path = DEFAULT_HISTORY, output: Path = "mymise-discovery.json"):
    ...

@app.command()
def resolve(ctx: typer.Context, input: Path = "mymise-discovery.json", output: Path = "mymise-resolved.json"):
    ...

@app.command()
def register(ctx: typer.Context, input: Path = "mymise-resolved.json", output_dir: Path = "."):
    ...

@app.command()
def all(ctx: typer.Context, history_file: Path = DEFAULT_HISTORY, output_dir: Path = "."):
    # Runs scan -> resolve -> register pipeline
    ...
```

### Collector Protocol (`collectors/base.py`)

Each collector implements a simple protocol:

```python
from typing import Protocol

class Collector(Protocol):
    name: str  # e.g. "history", "apt", "cargo"

    def collect(self) -> list[DiscoveredTool]:
        """Return tools discovered by this collector."""
        ...

    def available(self) -> bool:
        """Return True if this collector can run (e.g. apt exists on system)."""
        ...
```

### Scanner Pipeline (`scanner.py`)

Orchestrates collectors, merges results:

1. Instantiate all collectors
2. Filter to `available()` collectors
3. Run each collector's `collect()` (log warnings for failures)
4. Merge results by tool name (union of sources, max frequency, latest timestamp)
5. Apply filters (remove builtins, normalize names)
6. Return `DiscoveryResult` model

### Resolver Pipeline (`resolver.py`)

Takes discovery output, resolves against mise:

1. Load `DiscoveryResult` from JSON
2. For each tool, run `mise registry <tool_name>` and parse output
3. Classify: resolved (has registry entry with backend) or unresolved
4. For resolved tools, extract backend type and install spec
5. Return `ResolutionResult` model with two lists

Key implementation detail for `mise registry` parsing:
- Output format: `tool_name    backend:owner/repo` (tab-separated)
- Empty output or exit code 1 = not found
- Parse backend type from prefix before colon

### Registrar Pipeline (`registrar.py`)

Takes resolution output, generates artifacts:

1. Load `ResolutionResult` from JSON
2. Generate `mise.toml` fragment with all resolved tools
3. For unresolved tools with GitHub provenance, generate `shorthands.toml` entries
4. For remaining unresolved, generate `bootstrap.sh` install commands
5. Write all artifacts to output directory

## Data Models (`models.py`)

```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class ToolCategory(str, Enum):
    RUNTIME = "runtime"           # python, node, ruby, go, rust
    PACKAGE_MANAGER = "pkg-mgr"   # pip, npm, cargo, uv
    CLI_TOOL = "cli-tool"         # bat, ripgrep, fd, jq
    LANGUAGE_TOOL = "lang-tool"   # pytest, eslint, rustfmt
    SYSTEM_UTILITY = "sys-util"   # curl, wget, tar, gzip

class ToolSource(str, Enum):
    HISTORY = "history"
    PATH = "path"
    APT = "apt"
    CARGO = "cargo"
    NPM = "npm"
    PIPX = "pipx"
    MISE = "mise"
    SNAP = "snap"
    GO = "go"
    UV = "uv"

class DiscoveredTool(BaseModel):
    name: str
    sources: list[ToolSource]
    frequency: int = 0           # usage count from history
    last_used: datetime | None = None
    binary_path: str | None = None
    installed_by: list[ToolSource] = []
    category: ToolCategory | None = None

class DiscoveryResult(BaseModel):
    schema_version: str = "1.0.0"
    scan_timestamp: datetime
    hostname: str
    user: str
    scan_duration_seconds: float
    tools: list[DiscoveredTool]

class BackendType(str, Enum):
    AQUA = "aqua"
    GITHUB = "github"
    ASDF = "asdf"
    CORE = "core"
    PIPX = "pipx"
    CARGO = "cargo"
    NPM = "npm"
    GO = "go"

class ResolvedTool(BaseModel):
    name: str
    backend: BackendType
    registry_entry: str          # e.g. "aqua:sharkdp/bat"
    install_command: str         # e.g. "mise install bat@latest"
    original: DiscoveredTool

class UnresolvedTool(BaseModel):
    name: str
    original: DiscoveredTool
    suggested_actions: list[str]  # e.g. ["Add to shorthands.toml as github:owner/repo"]

class ResolutionResult(BaseModel):
    schema_version: str = "1.0.0"
    resolution_timestamp: datetime
    resolved: list[ResolvedTool]
    unresolved: list[UnresolvedTool]
    resolution_rate: float       # percentage resolved
```

## Key Design Decisions

### 1. Subprocess for mise interaction (not library import)

mise is a Rust binary. We interact via `subprocess.run(["mise", "registry", tool_name])` rather than any FFI. This keeps mymise decoupled from mise internals and version-independent.

### 2. Collectors are pluggable, not plugin-based

Each collector is a Python module in `collectors/`. No dynamic loading, no plugin registry. Just import and instantiate. New collectors = new file + add to collector list in `scanner.py`. Simple beats clever.

### 3. JSON as interchange format

Each pipeline stage reads/writes JSON. This means:
- Stages can run independently (`mymise scan` today, `mymise resolve` tomorrow)
- Output is inspectable with `jq`
- Easy to test (fixture files)
- Future tools can consume the same artifacts

### 4. Rich for human output, JSON for machine output

`--json` flag suppresses Rich formatting and outputs pure JSON to stdout. Without it, Rich panels/tables go to stderr, JSON goes to file. This follows Unix conventions (data to stdout, UI to stderr).

### 5. No async

All subprocess calls are synchronous with timeouts. The scan phase runs collectors sequentially (simplicity). Resolution could benefit from parallelism (100+ `mise registry` calls) but we start sequential and optimize if SC-4 (30s target) is at risk.

## Dependencies

```toml
[project]
requires-python = ">=3.12"

[project.scripts]
mymise = "mymise.cli:app"

dependencies = [
    "typer>=0.12.0",
    "pydantic>=2.6.0",
    "rich>=13.7.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
]
```

## Testing Strategy

- **Unit tests:** Each collector tested in isolation with fixture data (mock subprocess output)
- **Integration tests:** Full pipeline test with real shell history (user's machine)
- **Model tests:** Pydantic serialization/deserialization roundtrip
- **CLI tests:** Typer `CliRunner` for subcommand invocation

## Error Handling

- Collectors that fail log a warning and return empty list (never crash the scan)
- Subprocess calls wrapped with `try/except subprocess.TimeoutExpired` and `subprocess.CalledProcessError`
- All errors surfaced via Rich console with `[yellow]WARNING[/]` or `[red]ERROR[/]` styling
- Exit codes: 0 = success, 1 = partial (some collectors/resolutions failed), 2 = fatal
