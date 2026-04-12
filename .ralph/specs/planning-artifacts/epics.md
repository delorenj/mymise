---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
inputDocuments: [PRD.md, Architecture.md]
---

# mymise - Epics & Stories

## Overview

Complete epic and story breakdown for mymise. 4 epics, 19 stories. All 9 FRs covered (fully specified at story level after 2026-04-09 Implementation Readiness remediation).

## Requirements Inventory

### Functional Requirements

| ID | Requirement | Summary |
|----|-------------|---------|
| FR-1 | Shell History Parsing | Parse zsh extended history, extract binaries, filter builtins, record frequency/timestamps |
| FR-2 | PATH Binary Scanning | Scan PATH dirs, identify executables, follow symlinks, deduplicate |
| FR-3 | Package Manager Inventory | Query apt/snap/cargo/pipx/npm/mise/go/uv, handle missing gracefully |
| FR-4 | Merge & Classification | Merge all sources, deduplicate by canonical name, classify by category |
| FR-5 | Discovery Output | JSON output (Pydantic schema), metadata, --output/--format flags, Rich summary |
| FR-6 | Registry Resolution | Run `mise registry <tool>`, parse output, classify resolved/unresolved |
| FR-7 | Resolution Output | JSON with resolved/unresolved lists, backend info, summary stats |
| FR-8 | Personal Registry Generation | Generate shorthands.toml, mise.toml fragment, bootstrap.sh for unresolved |
| FR-9 | CLI Interface | Typer app with scan/resolve/register/all subcommands, --verbose/--json flags |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Performance | <30s scan, <60s resolution, <100MB memory |
| NFR-2 | Reliability | Graceful degradation, 10s subprocess timeouts, exit codes 0/1/2 |
| NFR-3 | Compatibility | Linux (Ubuntu/Debian), Python 3.12+, mise on PATH |
| NFR-4 | Extensibility | Pluggable collectors via Protocol, schema-versioned output |
| NFR-5 | Data Integrity | Pydantic validation before write, schema versioning, name normalization |

### Architecture Requirements

| ID | Source | Requirement |
|----|--------|-------------|
| AR-1 | Architecture | Collector Protocol pattern (base.py with `collect()` + `available()`) |
| AR-2 | Architecture | Scanner pipeline orchestration (instantiate, filter, collect, merge, filter builtins) |
| AR-3 | Architecture | JSON interchange between pipeline stages |
| AR-4 | Architecture | Rich stderr / JSON stdout output routing |
| AR-5 | Architecture | Subprocess interaction for mise (no FFI) |

### FR Coverage Map

```
FR-1 -> Epic 1, Story 1.1
FR-2 -> Epic 1, Story 1.2
FR-3 -> Epic 1, Stories 1.3a + 1.3b + 1.3c + 1.4a + 1.4b + 1.4c + 1.4d + 1.4e
FR-4 -> Epic 1, Story 1.5
FR-5 -> Epic 1, Story 1.6
FR-6 -> Epic 2, Story 2.1
FR-7 -> Epic 2, Story 2.2
FR-8 -> Epic 3, Stories 3.1 + 3.2
FR-9 -> Epic 1 (Story 1.6), Epic 2 (Story 2.2), Epic 3 (Story 3.2), Epic 4 (Stories 4.1 + 4.2)
```

---

## Epic 1: Tool Discovery

**User Outcome:** Developer runs `mymise scan` and gets a complete inventory of every CLI tool on their system, with source provenance and usage frequency.

**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-9 (partial, scan subcommand flags)
**NFRs addressed:** NFR-1, NFR-2, NFR-4, NFR-5
**Arch requirements:** AR-1, AR-2, AR-3, AR-4

**Dependencies:** None (first epic)

### Story 1.1: Implement Zsh History Collector

**Status:** Draft

As a developer,
I want mymise to parse my zsh history and extract every CLI tool I've used,
So that frequently-used tools are prioritized in my tool inventory.

**Tasks:**

1. Implement `available()` to check `~/.zsh_history` exists and is readable
2. Implement `collect()` to parse zsh extended history format (`: <timestamp>:<duration>;command`)
3. Extract first binary from each command line, handling pipes and subshells
4. Build frequency counts and track last_used timestamps per binary
5. Filter shell builtins (cd, echo, export, alias, source, etc.)
6. Write unit tests with fixture history files

**Acceptance Criteria:**

- **Given** a zsh extended history file with entries in `: <timestamp>:<duration>;command` format
  **When** the HistoryCollector runs
  **Then** it returns a list of DiscoveredTool objects with source=HISTORY, frequency counts, and last_used timestamps
  **And** shell builtins (cd, echo, export, etc.) are excluded from results

- **Given** the history file does not exist or is unreadable
  **When** `available()` is called
  **Then** it returns False

- **Given** a history entry with pipes or subshells (e.g., `cat foo | grep bar`)
  **When** the collector parses the entry
  **Then** it extracts all binaries in the pipeline (both `cat` and `grep`)

**Refs:** FR-1, AR-1 | Files: `src/mymise/collectors/history.py`, `tests/collectors/test_history.py`

---

### Story 1.2: Implement PATH Binary Collector

**Status:** Draft

As a developer,
I want mymise to scan my PATH directories and identify all executable binaries,
So that I have a complete picture of what's installed regardless of usage history.

**Tasks:**

1. Implement `available()` to always return True (PATH always exists)
2. Implement `collect()` to iterate PATH directories from `os.environ["PATH"]`
3. For each directory, list executables and follow symlinks
4. Deduplicate by resolved target (symlinks to same binary = one tool)
5. Set binary_path on each DiscoveredTool
6. Skip non-existent PATH directories silently
7. Write unit tests with mock PATH directories

**Acceptance Criteria:**

- **Given** a system with multiple PATH directories
  **When** the PathCollector runs
  **Then** it returns DiscoveredTool objects for each executable found, with source=PATH and binary_path set

- **Given** a PATH entry contains symlinks
  **When** the collector scans that directory
  **Then** it follows symlinks and deduplicates by resolved target

- **Given** a PATH directory does not exist
  **When** the collector scans PATH
  **Then** it skips that directory silently and continues

**Refs:** FR-2, AR-1 | Files: `src/mymise/collectors/path.py`, `tests/collectors/test_path.py`

---

### Story 1.3a: Implement Apt Collector

**Status:** Draft

As a developer,
I want mymise to inventory tools installed via apt,
So that Debian/Ubuntu system packages are captured with provenance.

**Tasks:**

1. Implement `AptCollector.available()` to check `shutil.which("dpkg-query")`
2. Implement `collect()` to run `dpkg-query -W -f='${binary:Package}\n'` (or equivalent) with a 10s timeout
3. Parse output and emit `DiscoveredTool` objects with `source=APT`
4. Handle missing binary gracefully (`available()` returns False)
5. Write unit tests with mock subprocess output covering success, missing binary, and timeout cases

**Acceptance Criteria:**

- **Given** apt is available on the system
  **When** the AptCollector runs
  **Then** it returns `DiscoveredTool` objects with `source=APT` for each installed package that provides an executable

- **Given** apt is not installed
  **When** `available()` is called
  **Then** it returns False and the collector is skipped gracefully

- **Given** the dpkg-query subprocess exceeds 10 seconds
  **When** the timeout fires
  **Then** the collector returns an empty list and logs a warning via the project's structured logger

**Refs:** FR-3, AR-1, NFR-2 | Files: `src/mymise/collectors/apt.py`, `tests/collectors/test_apt.py`

---

### Story 1.3b: Implement Snap Collector

**Status:** Draft

As a developer,
I want mymise to inventory tools installed via snap,
So that snap-managed applications are captured with provenance.

**Tasks:**

1. Implement `SnapCollector.available()` to check `shutil.which("snap")`
2. Implement `collect()` to run `snap list` with a 10s timeout and parse tabular output
3. Emit `DiscoveredTool` objects with `source=SNAP`
4. Handle missing binary gracefully (`available()` returns False)
5. Write unit tests with mock subprocess output

**Acceptance Criteria:**

- **Given** snap is available on the system
  **When** the SnapCollector runs
  **Then** it returns `DiscoveredTool` objects with `source=SNAP` for each installed snap

- **Given** snap is not installed
  **When** `available()` is called
  **Then** it returns False and the collector is skipped gracefully

- **Given** the snap subprocess exceeds 10 seconds
  **When** the timeout fires
  **Then** the collector returns an empty list and logs a warning via the project's structured logger

**Refs:** FR-3, AR-1, NFR-2 | Files: `src/mymise/collectors/snap.py`, `tests/collectors/test_snap.py`

---

### Story 1.3c: Implement Mise Collector

**Status:** Draft

As a developer,
I want mymise to inventory tools already managed by mise,
So that the mise-native toolchain is captured alongside everything else.

**Tasks:**

1. Implement `MiseCollector.available()` to check `shutil.which("mise")`
2. Implement `collect()` to run `mise list` with a 10s timeout and parse output
3. Emit `DiscoveredTool` objects with `source=MISE`
4. Handle missing binary gracefully (`available()` returns False)
5. Write unit tests with mock subprocess output

**Acceptance Criteria:**

- **Given** mise is available on the system
  **When** the MiseCollector runs
  **Then** it returns `DiscoveredTool` objects with `source=MISE` for each tool managed by mise

- **Given** mise is not installed
  **When** `available()` is called
  **Then** it returns False and the collector is skipped gracefully

- **Given** the mise subprocess exceeds 10 seconds
  **When** the timeout fires
  **Then** the collector returns an empty list and logs a warning via the project's structured logger

**Refs:** FR-3, AR-1, NFR-2 | Files: `src/mymise/collectors/mise.py`, `tests/collectors/test_mise.py`

---

### Story 1.4a: Implement Cargo Collector

**Status:** Draft

As a developer,
I want mymise to inventory tools installed via cargo,
So that Rust toolchain binaries are captured with provenance.

**Tasks:**

1. Implement `CargoCollector.available()` to check `shutil.which("cargo")`
2. Implement `collect()` to list `~/.cargo/bin/` or run `cargo install --list` with a 10s timeout
3. Emit `DiscoveredTool` objects with `source=CARGO`
4. Handle missing binary gracefully
5. Write unit tests with mock subprocess output

**Acceptance Criteria:**

- **Given** cargo is available
  **When** the CargoCollector runs
  **Then** it returns `DiscoveredTool` objects with `source=CARGO` for installed cargo binaries

- **Given** cargo is not on PATH
  **When** `available()` is called
  **Then** it returns False and the scan continues without error

- **Given** the cargo subprocess exceeds 10 seconds
  **When** the timeout fires
  **Then** the collector returns an empty list and logs a warning via the project's structured logger

**Refs:** FR-3, AR-1, NFR-2 | Files: `src/mymise/collectors/cargo.py`, `tests/collectors/test_cargo.py`

---

### Story 1.4b: Implement Npm Collector

**Status:** Draft

As a developer,
I want mymise to inventory tools installed via npm globally,
So that global Node.js CLI tools are captured with provenance.

**Tasks:**

1. Implement `NpmCollector.available()` to check `shutil.which("npm")`
2. Implement `collect()` to run `npm list -g --depth=0` with a 10s timeout
3. Emit `DiscoveredTool` objects with `source=NPM`
4. Handle missing binary gracefully
5. Write unit tests with mock subprocess output

**Acceptance Criteria:**

- **Given** npm is available
  **When** the NpmCollector runs
  **Then** it returns `DiscoveredTool` objects with `source=NPM` for globally installed npm packages

- **Given** npm is not on PATH
  **When** `available()` is called
  **Then** it returns False and the scan continues without error

- **Given** the npm subprocess exceeds 10 seconds
  **When** the timeout fires
  **Then** the collector returns an empty list and logs a warning via the project's structured logger

**Refs:** FR-3, AR-1, NFR-2 | Files: `src/mymise/collectors/npm.py`, `tests/collectors/test_npm.py`

---

### Story 1.4c: Implement Pipx Collector

**Status:** Draft

As a developer,
I want mymise to inventory tools installed via pipx,
So that isolated Python CLI applications are captured with provenance.

**Tasks:**

1. Implement `PipxCollector.available()` to check `shutil.which("pipx")`
2. Implement `collect()` to run `pipx list --short` with a 10s timeout
3. Emit `DiscoveredTool` objects with `source=PIPX`
4. Handle missing binary gracefully
5. Write unit tests with mock subprocess output

**Acceptance Criteria:**

- **Given** pipx is available
  **When** the PipxCollector runs
  **Then** it returns `DiscoveredTool` objects with `source=PIPX` for installed pipx applications

- **Given** pipx is not on PATH
  **When** `available()` is called
  **Then** it returns False and the scan continues without error

- **Given** the pipx subprocess exceeds 10 seconds
  **When** the timeout fires
  **Then** the collector returns an empty list and logs a warning via the project's structured logger

**Refs:** FR-3, AR-1, NFR-2 | Files: `src/mymise/collectors/pipx.py`, `tests/collectors/test_pipx.py`

---

### Story 1.4d: Implement Go Collector

**Status:** Draft

As a developer,
I want mymise to inventory tools installed via `go install`,
So that Go ecosystem binaries are captured with provenance.

**Tasks:**

1. Implement `GoCollector.available()` to check `shutil.which("go")`
2. Implement `collect()` to list `$GOPATH/bin/` or `~/go/bin/`
3. Emit `DiscoveredTool` objects with `source=GO`
4. Handle missing binary gracefully
5. Write unit tests with mock filesystem fixtures

**Acceptance Criteria:**

- **Given** go is available
  **When** the GoCollector runs
  **Then** it returns `DiscoveredTool` objects with `source=GO` for installed go binaries

- **Given** go is not on PATH
  **When** `available()` is called
  **Then** it returns False and the scan continues without error

- **Given** `$GOPATH/bin` does not exist
  **When** the collector runs
  **Then** it returns an empty list without raising

**Refs:** FR-3, AR-1, NFR-2 | Files: `src/mymise/collectors/go.py`, `tests/collectors/test_go.py`

---

### Story 1.4e: Implement Uv Collector

**Status:** Draft

As a developer,
I want mymise to inventory tools installed via `uv tool`,
So that uv-managed Python CLI applications are captured with provenance.

**Tasks:**

1. Implement `UvCollector.available()` to check `shutil.which("uv")`
2. Implement `collect()` to run `uv tool list` with a 10s timeout
3. Emit `DiscoveredTool` objects with `source=UV`
4. Handle missing binary gracefully
5. Write unit tests with mock subprocess output

**Acceptance Criteria:**

- **Given** uv is available
  **When** the UvCollector runs
  **Then** it returns `DiscoveredTool` objects with `source=UV` for installed uv tools

- **Given** uv is not on PATH
  **When** `available()` is called
  **Then** it returns False and the scan continues without error

- **Given** the uv subprocess exceeds 10 seconds
  **When** the timeout fires
  **Then** the collector returns an empty list and logs a warning via the project's structured logger

**Refs:** FR-3, AR-1, NFR-2 | Files: `src/mymise/collectors/uv.py`, `tests/collectors/test_uv.py`

---

### Story 1.5: Implement Scanner Orchestration with Merge and Deduplication

**Status:** Draft

As a developer,
I want all collectors to run and merge their results into a unified tool list,
So that I get one deduplicated inventory with all sources and the highest frequency for each tool.

**Tasks:**

1. Implement scanner.py `scan()` function to instantiate all collectors
2. Filter collectors by `available()` before running
3. Call `collect()` on each available collector, catch exceptions per-collector
4. Merge results by tool name: union sources, max frequency, latest last_used
5. Populate DiscoveryResult metadata (hostname, user, timestamp, duration)
6. Write integration tests that verify merge logic with overlapping tool results

**Acceptance Criteria:**

- **Given** multiple collectors return overlapping tools (e.g., `rg` found in PATH and cargo)
  **When** the Scanner merges results
  **Then** each tool appears once with sources as the union of all discovered sources
  **And** frequency is the max across sources
  **And** last_used is the most recent timestamp

- **Given** a collector raises an exception during collection
  **When** the Scanner runs
  **Then** it logs a warning via the project's structured logger (including collector name and exception type), returns an empty list for that collector, and continues with remaining collectors

- **Given** the scan completes
  **When** the Scanner builds the DiscoveryResult
  **Then** it populates hostname, user, scan_timestamp, and scan_duration_seconds metadata

**Refs:** FR-4, AR-2, NFR-2, NFR-5 | Files: `src/mymise/scanner.py`, `tests/test_scanner.py`

---

### Story 1.6: Wire Scan CLI Command with JSON/TOML Output, Flags, and Rich Summary

**Status:** Draft

As a developer,
I want to run `mymise scan` with the full documented flag set and see a Rich summary on stderr with the serialized manifest written to a file,
So that I can control input sources, output format, and package manager inclusion.

**Tasks:**

1. Wire `cli.py` `scan` command to call `scanner.scan()` with parameters derived from CLI flags
2. Implement `--history-file` flag (default `~/.zsh_history`) passed to the HistoryCollector
3. Implement `--skip-pkg-managers` flag (comma-separated list) that excludes named package manager collectors from the scan
4. Implement `--output` flag (default `mymise-discovery.json`) for output file path
5. Implement `--format` flag accepting `json` (default) or `toml`; serialize via Pydantic `.model_dump_json()` for JSON or `tomli_w` for TOML
6. Implement global `--json` flag that writes JSON to stdout instead of a file (Rich summary suppressed on stderr)
7. Build Rich table for stderr: tool count, source breakdown, top 10 by frequency
8. Set exit code based on collector success (0 = all ok, 1 = partial)
9. Write CLI integration tests with `CliRunner` covering all flag combinations

**Acceptance Criteria:**

- **Given** the user runs `mymise scan`
  **When** the scan completes
  **Then** the DiscoveryResult is written to `mymise-discovery.json` (default) or the path specified by `--output`

- **Given** the user passes `--history-file /custom/path`
  **When** the scan runs
  **Then** the HistoryCollector reads from the specified path instead of `~/.zsh_history`

- **Given** the user passes `--skip-pkg-managers cargo,npm`
  **When** the scan runs
  **Then** the CargoCollector and NpmCollector are excluded from the collector list
  **And** all other collectors run normally

- **Given** the user passes `--format toml`
  **When** the scan completes
  **Then** the DiscoveryResult is serialized as TOML and written to the output path

- **Given** the user passes `--json`
  **When** the scan completes
  **Then** the JSON is written to stdout instead of a file
  **And** Rich formatting is suppressed on stderr

- **Given** a successful scan without `--json`
  **When** results are displayed
  **Then** a Rich table on stderr shows tool count, source breakdown, and top 10 by frequency

- **Given** the scan has partial failures (some collectors failed)
  **When** the command exits
  **Then** exit code is 1 (partial failure) and warnings are printed to stderr via the project's structured logger

**Refs:** FR-5, FR-9, AR-3, AR-4, NFR-2 | Files: `src/mymise/cli.py`, `tests/test_cli.py`

---

## Epic 2: Registry Resolution

**User Outcome:** Developer runs `mymise resolve` and knows exactly which tools mise can manage today vs. which need manual handling.

**FRs covered:** FR-6, FR-7, FR-9 (partial, resolve subcommand flags)
**NFRs addressed:** NFR-1, NFR-2
**Arch requirements:** AR-3, AR-5

**Dependencies:** Reads `mymise-discovery.json` from Epic 1

### Story 2.1: Implement Resolver with Mise Registry Lookup and Dry-Run Mode

**Status:** Draft

As a developer,
I want mymise to check each discovered tool against the mise registry (with a dry-run preview mode),
So that I know which tools can be managed by mise and I can preview the resolution plan without side effects.

**Tasks:**

1. Implement `resolve()` to accept a DiscoveryResult (or load from JSON file)
2. For each tool, run `mise registry <tool_name>` via `subprocess.run` with a configurable timeout (default 10s)
3. Parse tab-separated output: `tool_name\tbackend:owner/repo`
4. Classify resolved tools into `ResolvedTool` with backend, registry_entry, install_command
5. Classify unresolved tools (empty output or exit 1) into `UnresolvedTool`
6. Implement `dry_run: bool` parameter on `resolve()`: when True, suppresses any follow-up install probing, logs the planned registry lookups to the structured logger, and still emits the classification based on `mise registry` output
7. Handle timeouts gracefully: classify as unresolved with warning
8. Calculate `resolution_rate` as resolved / total
9. Write unit tests with mock subprocess responses covering happy path, empty-output, exit-1, timeout, and dry-run branches

**Acceptance Criteria:**

- **Given** a DiscoveryResult JSON file with discovered tools
  **When** the Resolver processes each tool
  **Then** it calls `mise registry <tool_name>` via subprocess for each tool
  **And** parses the tab-separated output to extract backend type and registry entry

- **Given** a tool that exists in the mise registry
  **When** the registry lookup succeeds
  **Then** the tool is classified as `ResolvedTool` with backend, registry_entry, and install_command populated

- **Given** a tool that does not exist in the mise registry
  **When** `mise registry <tool>` returns empty output or exit code 1
  **Then** the tool is classified as `UnresolvedTool` with `suggested_actions` populated

- **Given** `mise registry <tool>` hangs or times out
  **When** the subprocess timeout fires (configurable, default 10s)
  **Then** the tool is classified as unresolved with a timeout warning logged via the project's structured logger
  **And** resolution continues with remaining tools

- **Given** `dry_run=True` is passed to `resolve()`
  **When** resolution runs
  **Then** `mise registry <tool>` is still called for classification (read-only)
  **And** no install probing or mutating subprocess calls occur
  **And** the structured logger records the planned registry lookups with a `dry_run=true` tag

**Refs:** FR-6, AR-5, NFR-1, NFR-2 | Files: `src/mymise/resolver.py`, `tests/test_resolver.py`

---

### Story 2.2: Wire Resolve CLI Command with Flags and Rich Summary

**Status:** Draft

As a developer,
I want to run `mymise resolve` with configurable input, output, timeout, and dry-run flags,
So that I can control the resolution step from the command line.

**Tasks:**

1. Wire `cli.py` `resolve` command to load discovery JSON and call the resolver
2. Implement `--input` flag (default `mymise-discovery.json`) for reading the discovery JSON
3. Implement `--output` flag (default `mymise-resolved.json`) for writing the resolution JSON
4. Implement `--dry-run` flag that passes `dry_run=True` into the resolver
5. Implement `--timeout` flag (int seconds, default 10) that configures subprocess timeout per `mise registry` call
6. Serialize `ResolutionResult` to JSON via Pydantic
7. Honor the global `--json` flag: write JSON to stdout instead of a file and suppress Rich formatting
8. Build Rich summary: resolved count, unresolved count, resolution %, backend distribution
9. Handle missing input file with exit code 2 and a clear error message via Rich on stderr
10. Write CLI integration tests with `CliRunner` covering all flag combinations

**Acceptance Criteria:**

- **Given** a valid `mymise-discovery.json` exists
  **When** the user runs `mymise resolve`
  **Then** the ResolutionResult is written to `mymise-resolved.json` (default) or the path specified by `--output`

- **Given** the user passes `--input /custom/path.json`
  **When** the command runs
  **Then** the resolver loads discovery data from the specified path

- **Given** the user passes `--timeout 30`
  **When** the resolver processes each tool
  **Then** each `mise registry` subprocess call uses a 30-second timeout instead of the 10-second default

- **Given** the user passes `--dry-run`
  **When** the command runs
  **Then** the resolver is invoked with `dry_run=True`
  **And** no install probing occurs
  **And** the ResolutionResult still reflects classification from `mise registry` output

- **Given** a successful resolution without `--json`
  **When** results are displayed
  **Then** a Rich summary on stderr shows: resolved count, unresolved count, resolution percentage, and backend type distribution

- **Given** the user passes `--json`
  **When** the resolution completes
  **Then** JSON is written to stdout instead of a file
  **And** Rich formatting is suppressed on stderr

- **Given** the input discovery JSON does not exist
  **When** the user runs `mymise resolve`
  **Then** a clear error message is printed to stderr via Rich
  **And** exit code is 2 (fatal)

**Refs:** FR-7, FR-9, AR-3, AR-4, NFR-2 | Files: `src/mymise/cli.py`, `tests/test_cli.py`

---

## Epic 3: Registration & Bootstrap

**User Outcome:** Developer runs `mymise register` and gets a complete, portable environment specification (mise.toml + shorthands.toml + bootstrap.sh).

**FRs covered:** FR-8, FR-9 (partial, register subcommand flags)
**NFRs addressed:** NFR-5
**Arch requirements:** AR-3

**Dependencies:** Reads `mymise-resolved.json` from Epic 2

### Story 3.1: Implement Registrar Artifact Generation

**Status:** Draft

As a developer,
I want mymise to generate mise.toml, shorthands.toml, and bootstrap.sh from my resolution results,
So that I have a complete, portable environment specification I can use on any machine.

**Tasks:**

1. Implement `register()` to accept a ResolutionResult (or load from JSON)
2. Generate `mise.toml` fragment with resolved tools at `@latest`, including backend source comments
3. Generate `shorthands.toml` for unresolved tools with identifiable GitHub repos
4. Generate `bootstrap.sh` with fallback install commands for remaining unresolved tools
5. Add provenance headers (generation timestamp, mymise version) to all artifacts
6. Write unit tests verifying artifact content and format

**Acceptance Criteria:**

- **Given** a ResolutionResult with resolved tools
  **When** the Registrar runs
  **Then** it generates a `mise.toml` fragment listing all resolved tools at `@latest`
  **And** each entry includes a comment with the backend source

- **Given** a ResolutionResult with unresolved tools that have GitHub provenance
  **When** the Registrar runs
  **Then** it generates `shorthands.toml` entries in `tool_name = "github:owner/repo"` format

- **Given** unresolved tools without identifiable GitHub repos
  **When** the Registrar runs
  **Then** it generates `bootstrap.sh` with fallback install commands (e.g., `apt install`, `cargo install`)
  **And** the script includes header comments explaining provenance

- **Given** all three artifacts are generated
  **When** the output is written
  **Then** each file includes a header comment with generation timestamp and mymise version

**Refs:** FR-8, NFR-5 | Files: `src/mymise/registrar.py`, `tests/test_registrar.py`

---

### Story 3.2: Wire Register CLI Command with Flags and Output Routing

**Status:** Draft

As a developer,
I want to run `mymise register` with configurable input, output directory, and shorthands filename,
So that I can route the generated artifacts anywhere I need them.

**Tasks:**

1. Wire `cli.py` `register` command to load resolution JSON and call the registrar
2. Implement `--input` flag (default `mymise-resolved.json`) for reading the resolution JSON
3. Implement `--output-dir` flag (default current working directory) for artifact destination
4. Implement `--shorthands-file` flag (default `shorthands.toml`) that overrides the shorthands artifact filename
5. Build Rich summary: files generated, tool counts per artifact, output paths
6. Handle missing input file with exit code 2 and a clear error message via Rich on stderr
7. Write CLI integration tests with `CliRunner` covering all flag combinations

**Acceptance Criteria:**

- **Given** a valid `mymise-resolved.json` exists
  **When** the user runs `mymise register`
  **Then** artifacts are written to the current directory (default) or the path specified by `--output-dir`

- **Given** the user passes `--input /custom/path.json`
  **When** the command runs
  **Then** the registrar loads resolution data from the specified path

- **Given** the user passes `--shorthands-file custom-shorthands.toml`
  **When** the command runs
  **Then** the personal registry entries are written to `<output-dir>/custom-shorthands.toml` instead of the default filename

- **Given** a successful registration
  **When** results are displayed
  **Then** a Rich summary on stderr shows: files generated, tool counts per artifact, and output paths

- **Given** the input resolution JSON does not exist
  **When** the user runs `mymise register`
  **Then** a clear error message is printed via Rich on stderr
  **And** exit code is 2 (fatal)

**Refs:** FR-8, FR-9, AR-4, NFR-2 | Files: `src/mymise/cli.py`, `tests/test_cli.py`

---

## Epic 4: CLI Integration & Full Pipeline

**User Outcome:** Developer runs `mymise all` and the entire scan-resolve-register pipeline executes end-to-end.

**FRs covered:** FR-9
**NFRs addressed:** NFR-2, NFR-3
**Arch requirements:** AR-4

**Dependencies:** All of Epics 1-3

### Story 4.1: Implement End-to-End Pipeline Command

**Status:** Draft

As a developer,
I want to run `mymise all` and have the entire scan-resolve-register pipeline execute in sequence,
So that I can go from zero to a complete environment specification in one command.

**Tasks:**

1. Wire `cli.py` `all` command to call scan, resolve, register in sequence
2. Pass intermediate results between stages (in-memory, also write JSON)
3. Support `--verbose` for debug logging across all stages
4. Handle partial failures: continue pipeline, aggregate warnings
5. Write integration test for full pipeline with mock subprocess

**Acceptance Criteria:**

- **Given** a system with shell history and installed tools
  **When** the user runs `mymise all`
  **Then** the scan, resolve, and register stages execute in sequence
  **And** intermediate JSON files are written to the output directory
  **And** final artifacts (mise.toml, shorthands.toml, bootstrap.sh) are generated

- **Given** the `--verbose` flag is passed
  **When** the pipeline runs
  **Then** debug-level logging is enabled for all stages

- **Given** a partial failure occurs (e.g., some collectors fail)
  **When** the pipeline completes
  **Then** exit code is 1 (partial failure) with warnings on stderr
  **And** the pipeline continues through all stages rather than aborting

**Refs:** FR-9, NFR-2 | Files: `src/mymise/cli.py`, `tests/test_cli.py`

---

### Story 4.2: CLI Polish and Error Handling

**Status:** Draft

As a developer,
I want consistent error handling, exit codes, and output routing across all commands,
So that mymise behaves predictably and integrates well with other CLI tools.

**Tasks:**

1. Audit all exit code paths: 0 (success), 1 (partial), 2 (fatal)
2. Ensure Rich output goes to stderr, never stdout
3. Ensure `--json` suppresses Rich formatting and routes JSON to stdout
4. Validate JSON output against Pydantic models before writing
5. Add `--verbose` support to all commands (debug logging to stderr)
6. Write integration tests verifying exit codes and output routing for each code path

**Acceptance Criteria:**

- **Given** any subcommand completes successfully
  **When** no warnings occurred
  **Then** exit code is 0

- **Given** any subcommand encounters partial failures
  **When** the command completes
  **Then** exit code is 1 and all warnings are printed to stderr

- **Given** a fatal error occurs (missing input file, invalid JSON)
  **When** the error is caught
  **Then** exit code is 2 and a clear error message is printed to stderr via Rich

- **Given** `--json` flag is passed to any command
  **When** output is generated
  **Then** Rich formatting is suppressed on stderr and JSON goes to stdout
  **And** the emitted JSON is produced by `model.model_dump_json()` on the corresponding Pydantic model, guaranteeing runtime-validated output that conforms to the schema

**Refs:** FR-9, AR-4, NFR-2 | Files: `src/mymise/cli.py`, `tests/test_cli.py`

---

## Validation Summary

### FR Coverage (must be 100%)

| FR | Epic | Story | Covered |
|----|------|-------|---------|
| FR-1 | 1 | 1.1 | Yes |
| FR-2 | 1 | 1.2 | Yes |
| FR-3 | 1 | 1.3a + 1.3b + 1.3c + 1.4a + 1.4b + 1.4c + 1.4d + 1.4e | Yes |
| FR-4 | 1 | 1.5 | Yes |
| FR-5 | 1 | 1.6 (JSON + TOML output) | Yes |
| FR-6 | 2 | 2.1 (includes `--dry-run`) | Yes |
| FR-7 | 2 | 2.2 | Yes |
| FR-8 | 3 | 3.1 + 3.2 | Yes |
| FR-9 | 1 + 2 + 3 + 4 | 1.6 + 2.2 + 3.2 (per-subcommand flags) + 4.1 + 4.2 (global flags + exit codes) | Yes |

### NFR Coverage

| NFR | Stories Addressing |
|-----|-------------------|
| NFR-1 | 2.1 (resolution perf, configurable timeout), 1.5 (scan perf) |
| NFR-2 | 1.3a-c, 1.4a-e, 1.5, 2.1, 2.2, 3.2, 4.1, 4.2 (graceful degradation, 10s timeouts, exit codes) |
| NFR-3 | 4.1 (Linux/Python/mise compatibility) |
| NFR-4 | 1.1, 1.2, 1.3a-c, 1.4a-e (collector Protocol pattern) |
| NFR-5 | 1.5, 1.6, 3.1 (Pydantic validation, schema versioning) |

### Story Dependency Chain

```
Epic 1:
  1.1, 1.2, 1.3a, 1.3b, 1.3c, 1.4a, 1.4b, 1.4c, 1.4d, 1.4e  (parallel)
  -> 1.5
  -> 1.6
Epic 2: 2.1 -> 2.2 (requires Epic 1 output)
Epic 3: 3.1 -> 3.2 (requires Epic 2 output)
Epic 4: 4.1 -> 4.2 (requires Epics 1-3)
```

### Totals

- **Epics:** 4
- **Stories:** 19 (post 2026-04-09 IR remediation: 1.3 split into 1.3a/b/c; 1.4 split into 1.4a/b/c/d/e)
- **FR coverage:** 9/9 (100%)
- **FR specification completeness at story level:** 100% (all PRD-promised flags surfaced in story ACs)
- **Orphaned FRs:** None
- **Implementation-leaking stories:** None

### 2026-04-09 Implementation Readiness Remediation Log

Applied fixes from `implementation-readiness-report-2026-04-09.md`:

1. **Split Story 1.3** into 1.3a AptCollector / 1.3b SnapCollector / 1.3c MiseCollector
2. **Split Story 1.4** into 1.4a CargoCollector / 1.4b NpmCollector / 1.4c PipxCollector / 1.4d GoCollector / 1.4e UvCollector
3. **Story 1.6** added `--history-file`, `--skip-pkg-managers`, `--format toml` tasks and ACs (FR-5 + FR-9)
4. **Story 2.1** added `--dry-run` task and AC (FR-6)
5. **Story 2.2** added `--input`, `--timeout`, `--dry-run` tasks and ACs (FR-9)
6. **Story 3.2** added `--input`, `--shorthands-file` tasks and ACs (FR-9)
7. **Story 1.5** tightened logger AC to reference structured logger with collector name + exception type
8. **Story 4.2** tightened `--json` Pydantic validation AC to specify `model_dump_json()` runtime guarantee
9. **PRD NFR-1** "parallelizable" claim reconciled in PRD.md (see PRD changelog)
