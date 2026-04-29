# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Requirements

- No engineering work without an active Plane ticket at `https://plane.delo.sh/33god/`
- Branch and commit messages must include ticket reference (e.g. `MYM-123`)
- Move ticket to `In Progress` before first code change
- Emergency bypass only: `ALLOW_NO_TICKET=1`

### Reality-Drift Guard: Test Drive

Unit tests prove correctness in isolation. They do **not** prove the feature works against a real machine. Mock-only test suites are the #1 source of "ships green, behaves broken" regressions.

**Before marking any story `review` or `done`:**

1. Run `mise run testdrive` (end-to-end against the real system in an isolated tmp dir)
2. Triage any new findings into the backlog, even if the script exits 0
3. Note the finding count in the story's Completion Notes

The test drive script is at `scripts/testdrive.sh`. It runs the full pipeline (`mymise all`), validates artifacts, and confirms no clobbering of project files. Pass `--keep` to retain output for inspection.

## Commands

All tasks are defined in `mise.toml` and run via `mise run <task>`:

```bash
mise run dev          # uv sync --group dev (install deps)
mise run test         # uv run pytest -v
mise run lint         # uv run ruff check src/ tests/
mise run lint:fix     # uv run ruff check --fix src/ tests/
mise run format       # uv run ruff format src/ tests/
mise run ci           # lint + test
mise run scan         # uv run mymise scan
mise run resolve      # uv run mymise resolve
mise run testdrive    # E2E smoke test against real machine in isolated tmp dir
```

Run a single test file: `uv run pytest tests/test_cli.py -v`
Run a single test: `uv run pytest tests/test_cli.py::test_cli_help -v`

## Architecture

mymise is a single-process Python CLI with no server, database, or network services. It implements a three-stage pipeline where each stage reads/writes JSON for independent execution:

```
scan -> mymise-discovery.json -> resolve -> mymise-resolved.json -> register -> artifacts
```

### Pipeline Stages

- **Scanner** (`scanner.py`): Orchestrates all collectors, merges results by tool name (union of sources, max frequency, latest timestamp), returns `DiscoveryResult`
- **Resolver** (`resolver.py`): Shells out to `mise registry <tool_name>` for each discovered tool, classifies as resolved/unresolved, returns `ResolutionResult`
- **Registrar** (`registrar.py`): Generates `mise.toml` fragment, `shorthands.toml` entries, and `bootstrap.sh` for unresolved tools

### Collector Protocol

`collectors/base.py` defines a `Protocol` with two methods: `collect() -> list[DiscoveredTool]` and `available() -> bool`. All collectors in `collectors/` follow this interface. New collector = new file + add to collector list in `scanner.py`. No dynamic loading.

Collectors: `history` (zsh history parser), `path` (PATH binary scan), `apt`, `cargo`, `npm`, `pipx`, `mise`, `snap`, `go`, `uv`

### Key Design Decisions

- **mise interaction via subprocess**: `mise registry <tool>` called via `subprocess.run`, never FFI. Tab-separated output: `tool_name\tbackend:owner/repo`. Empty output or exit 1 = not in registry.
- **Output routing**: Rich console to stderr, JSON to stdout (with `--json` flag) or file (default). This follows Unix conventions.
- **Error handling**: Collectors that fail return empty list and log a warning -- they never crash the scan. Exit codes: 0 = success, 1 = partial failure, 2 = fatal.
- **No async**: All subprocess calls are synchronous. Parallelism deferred until needed.

### Data Models (`models.py`)

All shapes are Pydantic v2 models. Key types:
- `DiscoveredTool` - tool name + sources + frequency + optional binary path/category
- `DiscoveryResult` - scan metadata + list of `DiscoveredTool`
- `ResolvedTool` - wraps `DiscoveredTool` with backend type + registry entry + install command
- `ResolutionResult` - resolved + unresolved lists + resolution rate

### CLI (`cli.py`)

Typer app with `AppState` on `ctx.obj` for shared `--verbose` / `--json` flags. All four subcommands (`scan`, `resolve`, `register`, `all`) are currently scaffold stubs that raise `NotImplementedError`.

## Testing

Tests use `typer.testing.CliRunner` for CLI tests and pytest fixtures in `conftest.py` for model fixtures. The `tests/collectors/` directory mirrors the `src/mymise/collectors/` structure.

## BMAD-METHOD Integration

Use `/bmalph` to navigate phases. Use `/bmad-help` to discover all commands. Use `/bmalph-status` for a quick overview. See `_bmad/COMMANDS.md` for a full command reference.

### Phases

| Phase | Focus | Key Commands |
|-------|-------|-------------|
| 1. Analysis | Understand the problem | `/create-brief`, `/brainstorm-project`, `/market-research` |
| 2. Planning | Define the solution | `/create-prd`, `/create-ux` |
| 3. Solutioning | Design the architecture | `/create-architecture`, `/create-epics-stories`, `/implementation-readiness` |
| 4. Implementation | Build it | `/sprint-planning`, `/create-story`, then `/bmalph-implement` for Ralph |

### Workflow

1. Work through Phases 1-3 using BMAD agents and workflows (interactive, command-driven)
2. Run `/bmalph-implement` to transition planning artifacts into Ralph format, then start Ralph

### Management Commands

| Command | Description |
|---------|-------------|
| `/bmalph-status` | Show current phase, Ralph progress, version info |
| `/bmalph-implement` | Transition planning artifacts → prepare Ralph loop |
| `/bmalph-upgrade` | Update bundled assets to match current bmalph version |
| `/bmalph-doctor` | Check project health and report issues |

### Available Agents

| Command | Agent | Role |
|---------|-------|------|
| `/analyst` | Analyst | Research, briefs, discovery |
| `/architect` | Architect | Technical design, architecture |
| `/pm` | Product Manager | PRDs, epics, stories |
| `/sm` | Scrum Master | Sprint planning, status, coordination |
| `/dev` | Developer | Implementation, coding |
| `/ux-designer` | UX Designer | User experience, wireframes |
| `/qa` | QA Engineer | Test automation, quality assurance |
