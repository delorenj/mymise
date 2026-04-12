# Story 1.1: Implement Zsh History Collector

**Status:** ready-for-dev
**Epic:** 1 (Tool Discovery)
**Story Key:** `1-1-implement-zsh-history-collector`
**FR Coverage:** FR-1 | **AR Coverage:** AR-1
**Plane Ticket:** REQUIRED before first code change (e.g. `MYM-3`). Move to `In Progress`. Emergency bypass only: `ALLOW_NO_TICKET=1`.

---

## Story

As a **developer**,
I want **mymise to parse my zsh history and extract every CLI tool I've used**,
So that **frequently-used tools are prioritized in my tool inventory**.

---

## Acceptance Criteria

**AC-1:** **Given** a zsh extended history file with entries in `: <timestamp>:<duration>;command` format
**When** `HistoryCollector.collect()` runs
**Then** it returns `list[DiscoveredTool]` with `source=ToolSource.HISTORY`, accurate `frequency` counts, and `last_used` timestamps populated from the latest occurrence
**And** shell builtins (`cd`, `echo`, `export`, `alias`, `source`, etc.) are excluded from the returned list

**AC-2:** **Given** the history file does not exist, is not readable, or the path is empty
**When** `HistoryCollector.available()` is called
**Then** it returns `False` (and `collect()` must never be called by the scanner in this case)

**AC-3:** **Given** a history entry containing pipes or subshells (e.g. `cat foo | grep bar`, `$(which jq)`, `bat <(cmd)`)
**When** the collector parses the entry
**Then** it extracts **all** binaries in the pipeline (e.g. both `cat` and `grep`) as separate `DiscoveredTool` entries with frequency counted per binary

**AC-4 (implicit from NFR-2):** **Given** a malformed or corrupted history line (bad encoding, missing delimiter, truncated entry)
**When** the collector encounters it
**Then** it logs a warning and skips that line, continuing to process the rest of the file (never crashes)

---

## Tasks / Subtasks

- [ ] **Task 1: Implement `available()` guard** (AC: 2)
  - [ ] Expand `~/.zsh_history` via `pathlib.Path.expanduser()`
  - [ ] Return `False` if path missing, not a file, or not readable (`os.access(path, os.R_OK)`)
  - [ ] Return `True` otherwise
  - [ ] No exceptions propagated from this method

- [ ] **Task 2: Define zsh builtin filter set** (AC: 1)
  - [ ] Add module-level `ZSH_BUILTINS: frozenset[str]` constant in `history.py`
  - [ ] Populate with canonical zsh builtins (see Dev Notes for list)
  - [ ] Include shell keywords (`if`, `then`, `for`, `while`, etc.) since those can appear as first token in parsed commands

- [ ] **Task 3: Implement extended history line parser** (AC: 1, 3, 4)
  - [ ] Parse format `: <timestamp>:<duration>;<command>` using regex `^:\s*(\d+):(\d+);(.*)$`
  - [ ] Handle non-extended format fallback: if no match, treat entire line as command (so `setopt extendedhistory` isn't required)
  - [ ] Decode bytes with `errors="replace"` to tolerate encoding issues
  - [ ] On parse failure for a line: `logger.warning(...)` and continue (never raise)

- [ ] **Task 4: Implement command token extraction** (AC: 3)
  - [ ] Use `shlex.split(command, posix=True)` with exception fallback (if shlex fails, skip the command)
  - [ ] Extract the **first token** as the primary binary
  - [ ] Additionally split on shell separators (`|`, `&&`, `||`, `;`, `&`) **before** shlex to capture piped/chained binaries
  - [ ] For each pipeline segment, extract the first non-empty token that is not a shell keyword or builtin
  - [ ] Strip leading `sudo`, `nohup`, `time`, `exec`, `command`, `builtin`, `env` wrappers and take the next token
  - [ ] Skip tokens containing `=` (env var assignments like `FOO=bar cmd`) until a real command is found
  - [ ] Skip tokens starting with `-`, `/`, `$`, `.` (flags, paths, variables, relative scripts) unless they resolve to a known binary name

- [ ] **Task 5: Implement `collect()` aggregation** (AC: 1, 4)
  - [ ] Open history file with `open(path, encoding="utf-8", errors="replace")`
  - [ ] Iterate lines, extract tool names via parser + extractor
  - [ ] Maintain `dict[str, tuple[int, datetime | None]]` keyed by tool name
  - [ ] For each extracted name: increment frequency, update `last_used` to max of current and new timestamp
  - [ ] Filter out names in `ZSH_BUILTINS` before returning
  - [ ] Return `list[DiscoveredTool]` with `sources=[ToolSource.HISTORY]`, populated `frequency` and `last_used`

- [ ] **Task 6: Wire structured logging** (AC: 4)
  - [ ] Use `import logging; logger = logging.getLogger(__name__)`
  - [ ] Log at `WARNING` for parse failures (include line number, truncated excerpt)
  - [ ] Log at `DEBUG` for successful parses and tool counts

- [ ] **Task 7: Write unit tests** (AC: 1, 2, 3, 4)
  - [ ] Create `tests/collectors/test_history.py`
  - [ ] Fixture: temp file with known extended history entries (use `tmp_path`)
  - [ ] Test `available()` returns `True` for existing file, `False` for missing/unreadable
  - [ ] Test basic extraction with known count expectations
  - [ ] Test builtin filtering (`cd`, `echo`, `alias` excluded)
  - [ ] Test pipeline extraction (`cat foo | grep bar` yields both `cat` and `grep`)
  - [ ] Test sudo/env prefix stripping (`sudo apt install` yields `apt`, `FOO=1 bar baz` yields `bar`)
  - [ ] Test malformed line handling (garbage line does not raise)
  - [ ] Test empty history file returns empty list without error
  - [ ] Test `last_used` reflects the latest timestamp across multiple occurrences
  - [ ] Test encoding errors are tolerated (file with non-UTF8 bytes)

- [ ] **Task 8: Validate and ship**
  - [ ] Run `mise run lint` (must pass)
  - [ ] Run `mise run test` (must pass, story tests green)
  - [ ] Ensure coverage on `history.py` is ≥90% via `uv run pytest --cov=mymise.collectors.history tests/collectors/test_history.py`
  - [ ] Update story Status to `review` and move Plane ticket

---

## Dev Notes

### Architecture Context

- **Collector Protocol** (`src/mymise/collectors/base.py`): duck-typed `Protocol` with `name: str`, `collect() -> list[DiscoveredTool]`, `available() -> bool`. `HistoryCollector` already has `name = "history"` and accepts `history_path: str` in `__init__` (default `~/.zsh_history`). **Preserve this signature** — scanner.py (future Story 1.5) will instantiate it positionally.
- **No dynamic loading**: New collectors are added as modules + imported in `scanner.py`. This story does NOT modify `scanner.py` — that wiring happens in Story 1.5.
- **Subprocess-free**: History parsing reads a local file. No shelling out, no network. No async.
- **Failure mode**: Collectors that fail return `[]` and log a warning. `collect()` must NEVER raise.
- **Exit codes** (for future scanner): 0 success, 1 partial failure, 2 fatal. This collector contributes to "partial" only.

### Zsh Extended History Format

```
: 1712345678:0;git status
: 1712345679:2;cat foo.txt | grep TODO
: 1712345680:0;sudo apt install ripgrep
```

Format: `: <epoch-seconds>:<duration-seconds>;<command-text>`. Users enable this with `setopt extendedhistory` in `.zshrc`. The collector MUST also gracefully handle non-extended lines (`git status`) for users without `extendedhistory` — in that case, `last_used = None`.

### Zsh Builtins to Filter

Canonical list for `ZSH_BUILTINS` frozenset. Do NOT omit any — users type these constantly:

```python
ZSH_BUILTINS: frozenset[str] = frozenset({
    # Shell builtins
    "cd", "pwd", "echo", "export", "unset", "alias", "unalias",
    "source", "exec", "eval", "exit", "return", "break", "continue",
    "shift", "read", "print", "printf", "typeset", "local", "declare",
    "readonly", "trap", "wait", "let", "set", "umask", "hash", "help",
    "history", "fc", "emulate", "autoload", "bindkey", "builtin",
    "command", "compctl", "disable", "enable", "getopts", "jobs",
    "kill", "bg", "fg", "suspend", "type", "typeset", "ulimit", "zle",
    "setopt", "unsetopt", "zstyle", "zmodload", "functions", "which",
    "true", "false", "test", "[", "[[", ".", ":", "times", "noglob",
    # Shell keywords that can appear as first token after splitting
    "if", "then", "else", "elif", "fi", "for", "while", "until", "do",
    "done", "case", "esac", "in", "function", "select", "repeat",
    "time", "coproc", "nocorrect",
})
```

### Command Prefix Stripping

Strip these "wrapper" commands to get the real binary. Apply recursively:

```python
WRAPPER_COMMANDS: frozenset[str] = frozenset({
    "sudo", "nohup", "time", "exec", "command", "builtin", "env",
    "nice", "ionice", "timeout", "xargs", "watch", "strace", "ltrace",
})
```

Example: `sudo -E env FOO=1 nohup watch -n 5 btop` → strip `sudo`, skip `-E`, strip `env`, skip `FOO=1`, strip `nohup`, strip `watch`, skip `-n 5`, yield `btop`.

### Files to Touch

| File | Action | Notes |
|------|--------|-------|
| `src/mymise/collectors/history.py` | **Modify** | Replace stub `collect()` and `available()` bodies. Keep class name, `name` attr, `__init__` signature |
| `tests/collectors/test_history.py` | **Create** | New unit test file. Mirror `src/mymise/collectors/history.py` path |
| `src/mymise/models.py` | **DO NOT TOUCH** | `DiscoveredTool`, `ToolSource.HISTORY` already exist. Use them |
| `src/mymise/collectors/base.py` | **DO NOT TOUCH** | Protocol is stable |
| `src/mymise/scanner.py` | **DO NOT TOUCH** | Wiring happens in Story 1.5 |
| `tests/conftest.py` | **DO NOT TOUCH** | Global fixture exists; story tests use `tmp_path` directly |

### Existing Model Reference

```python
# src/mymise/models.py (already exists — do NOT modify)
class ToolSource(StrEnum):
    HISTORY = "history"  # use this
    ...

class DiscoveredTool(BaseModel):
    name: str
    sources: list[ToolSource]
    frequency: int = 0
    last_used: datetime | None = None
    binary_path: str | None = None       # leave None for history
    installed_by: list[ToolSource] = []  # leave empty for history
    category: ToolCategory | None = None # leave None for history
```

### Current Scaffold (what you're replacing)

```python
# src/mymise/collectors/history.py (CURRENT - replace bodies only)
class HistoryCollector:
    """Parses zsh extended history format: `: <timestamp>:<duration>;command_text`"""

    name = "history"

    def __init__(self, history_path: str = "~/.zsh_history") -> None:
        self.history_path = history_path

    def collect(self) -> list[DiscoveredTool]:
        raise NotImplementedError  # ← replace

    def available(self) -> bool:
        raise NotImplementedError  # ← replace
```

### Testing Standards

- **Framework:** `pytest>=8.0.0` (already in `[dependency-groups].dev`)
- **Coverage:** `pytest-cov>=5.0.0` available. Target ≥90% line coverage on `history.py`
- **Fixtures:** Use pytest `tmp_path` for filesystem isolation. Do NOT read user's real `~/.zsh_history` in tests
- **Pattern:** Each collector tested in isolation with fixture data. See Architecture.md §testing
- **Linter:** `ruff` with rules `E, F, I, UP, B, SIM`, line-length 120, target `py312`
- **Type hints:** Full type annotations required. Use `list[DiscoveredTool]`, `dict[str, int]`, `frozenset[str]`, `datetime | None` (3.12+ syntax)

### LLM Anti-Patterns to Avoid

1. **DO NOT** use async/await. All collectors are sync per Architecture §decision-1.
2. **DO NOT** import `subprocess` — this collector only reads a file.
3. **DO NOT** add new fields to `DiscoveredTool`. Schema is frozen for this story.
4. **DO NOT** modify `scanner.py` to register the collector — that's Story 1.5.
5. **DO NOT** create a new `ToolSource` enum value. `HISTORY` exists.
6. **DO NOT** use `regex` module — stdlib `re` is sufficient.
7. **DO NOT** add runtime dependencies. Stick to stdlib + pydantic (already imported).
8. **DO NOT** raise exceptions from `collect()` or `available()`. Log warnings, return empty/False.
9. **DO NOT** hardcode `/home/user/.zsh_history`. Use `self.history_path` and `expanduser()`.
10. **DO NOT** write fake tests that always pass. Each AC must have at least one asserting test.

### Project Structure Notes

- Source: `src/mymise/collectors/history.py`
- Tests: `tests/collectors/test_history.py`
- Mirror layout is enforced (see CLAUDE.md: "The `tests/collectors/` directory mirrors the `src/mymise/collectors/` structure")
- `tests/collectors/__init__.py` already exists — do not recreate it

### Commands (via `mise run <task>`)

```bash
mise run dev          # uv sync --group dev
mise run test         # uv run pytest -v
mise run lint         # uv run ruff check src/ tests/
mise run lint:fix     # auto-fix lint issues
mise run format       # uv run ruff format src/ tests/
mise run ci           # lint + test (run before marking review)
```

Single test run: `uv run pytest tests/collectors/test_history.py -v`

### References

- [Source: `Architecture.md` §System Overview, §Collector Protocol, §Scanner pipeline, §Testing Strategy]
- [Source: `_bmad-output/planning-artifacts/epics.md` §Epic 1 §Story 1.1]
- [Source: `src/mymise/collectors/base.py` — Protocol definition]
- [Source: `src/mymise/models.py` — `DiscoveredTool`, `ToolSource.HISTORY`]
- [Source: `CLAUDE.md` §Testing, §Architecture §Collector Protocol, §Workflow Requirements]
- [Source: `PRD.md` §FR-1 Shell History Parsing]

---

## Dev Agent Record

### Agent Model Used

_To be filled by dev agent._

### Debug Log References

_To be filled by dev agent._

### Completion Notes List

_To be filled by dev agent._

### File List

_To be filled by dev agent._

---

**Completion Note:** Ultimate context engine analysis completed — comprehensive developer guide created. Dev agent has everything required for flawless implementation with zero ambiguity.
