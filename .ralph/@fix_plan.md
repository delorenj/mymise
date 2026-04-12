# Ralph Fix Plan

## Stories to Implement

### Tool Discovery
> Goal: **User Outcome:** Developer runs `mymise scan` and gets a complete inventory of every CLI tool on their system, with source provenance and usage frequency. **FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-9 (partial, scan subcommand flags) **NFRs addressed:** NFR-1, NFR-2, NFR-4, NFR-5 **Arch requirements:** AR-1, AR-2, AR-3, AR-4 **Dependencies:** None (first epic)

- [x] Story 1.1: Implement Zsh History Collector
- [x] Story 1.2: Implement PATH Binary Collector
- [x] Story 1.3a: Implement Apt Collector
- [x] Story 1.3b: Implement Snap Collector
- [x] Story 1.3c: Implement Mise Collector
  > As a developer, I want mymise to inventory tools already managed by mise, so that the mise-native toolchain is captured alongside everything else.
  > AC: Given mise is available, When the MiseCollector runs, Then it returns DiscoveredTool objects with source=MISE for each tool managed by mise
  > AC: Given mise is not installed, When available() is called, Then it returns False and the collector is skipped gracefully
  > AC: Given the mise subprocess exceeds 10 seconds, When the timeout fires, Then the collector returns an empty list and logs a warning
  > Spec: specs/planning-artifacts/epics.md#story-1-3c | Files: src/mymise/collectors/mise.py, tests/collectors/test_mise.py
- [ ] Story 1.4a: Implement Cargo Collector
  > As a developer, I want mymise to inventory tools installed via cargo, so that Rust toolchain binaries are captured with provenance.
  > AC: Given cargo is available, When the CargoCollector runs, Then it returns DiscoveredTool objects with source=CARGO for installed cargo binaries
  > AC: Given cargo is not on PATH, When available() is called, Then it returns False and the scan continues without error
  > AC: Given the cargo subprocess exceeds 10 seconds, When the timeout fires, Then the collector returns an empty list and logs a warning
  > Spec: specs/planning-artifacts/epics.md#story-1-4a | Files: src/mymise/collectors/cargo.py, tests/collectors/test_cargo.py
- [ ] Story 1.4b: Implement Npm Collector
  > As a developer, I want mymise to inventory tools installed via npm globally, so that global Node.js CLI tools are captured with provenance.
  > AC: Given npm is available, When the NpmCollector runs, Then it returns DiscoveredTool objects with source=NPM for globally installed npm packages
  > AC: Given npm is not on PATH, When available() is called, Then it returns False and the scan continues without error
  > AC: Given the npm subprocess exceeds 10 seconds, When the timeout fires, Then the collector returns an empty list and logs a warning
  > Spec: specs/planning-artifacts/epics.md#story-1-4b | Files: src/mymise/collectors/npm.py, tests/collectors/test_npm.py
- [ ] Story 1.4c: Implement Pipx Collector
  > As a developer, I want mymise to inventory tools installed via pipx, so that isolated Python CLI applications are captured with provenance.
  > AC: Given pipx is available, When the PipxCollector runs, Then it returns DiscoveredTool objects with source=PIPX for installed pipx applications
  > AC: Given pipx is not on PATH, When available() is called, Then it returns False and the scan continues without error
  > AC: Given the pipx subprocess exceeds 10 seconds, When the timeout fires, Then the collector returns an empty list and logs a warning
  > Spec: specs/planning-artifacts/epics.md#story-1-4c | Files: src/mymise/collectors/pipx.py, tests/collectors/test_pipx.py
- [ ] Story 1.4d: Implement Go Collector
  > As a developer, I want mymise to inventory tools installed via go install, so that Go ecosystem binaries are captured with provenance.
  > AC: Given go is available, When the GoCollector runs, Then it returns DiscoveredTool objects with source=GO for installed go binaries
  > AC: Given go is not on PATH, When available() is called, Then it returns False and the scan continues without error
  > AC: Given $GOPATH/bin does not exist, When the collector runs, Then it returns an empty list without raising
  > Spec: specs/planning-artifacts/epics.md#story-1-4d | Files: src/mymise/collectors/go.py, tests/collectors/test_go.py
- [ ] Story 1.4e: Implement Uv Collector
  > As a developer, I want mymise to inventory tools installed via uv tool, so that uv-managed Python CLI applications are captured with provenance.
  > AC: Given uv is available, When the UvCollector runs, Then it returns DiscoveredTool objects with source=UV for installed uv tools
  > AC: Given uv is not on PATH, When available() is called, Then it returns False and the scan continues without error
  > AC: Given the uv subprocess exceeds 10 seconds, When the timeout fires, Then the collector returns an empty list and logs a warning
  > Spec: specs/planning-artifacts/epics.md#story-1-4e | Files: src/mymise/collectors/uv.py, tests/collectors/test_uv.py
- [ ] Story 1.5: Implement Scanner Orchestration with Merge and Deduplication
  > **Status:** Draft As a developer
  > I want all collectors to run and merge their results into a unified tool list
  > So that I get one deduplicated inventory with all sources and the highest frequency for each tool.
  > AC: Given multiple collectors return overlapping tools (e.g., `rg` found in PATH and cargo), When the Scanner merges results, Then each tool appears once with sources as the union of all discovered sources, And frequency is the max across sources, And last_used is the most recent timestamp
  > AC: Given a collector raises an exception during collection, When the Scanner runs, Then it logs a warning via the project's structured logger (including collector name and exception type), returns an empty list for that collector, and continues with remaining collectors
  > AC: Given the scan completes, When the Scanner builds the DiscoveryResult, Then it populates hostname, user, scan_timestamp, and scan_duration_seconds metadata
  > Spec: specs/planning-artifacts/epics.md#story-1-5
- [ ] Story 1.6: Wire Scan CLI Command with JSON/TOML Output, Flags, and Rich Summary
  > **Status:** Draft As a developer
  > I want to run `mymise scan` with the full documented flag set and see a Rich summary on stderr with the serialized manifest written to a file
  > So that I can control input sources, output format, and package manager inclusion.
  > AC: Given the user runs `mymise scan`, When the scan completes, Then the DiscoveryResult is written to `mymise-discovery.json` (default) or the path specified by `--output`
  > AC: Given the user passes `--history-file /custom/path`, When the scan runs, Then the HistoryCollector reads from the specified path instead of `~/.zsh_history`
  > AC: Given the user passes `--skip-pkg-managers cargo,npm`, When the scan runs, Then the CargoCollector and NpmCollector are excluded from the collector list, And all other collectors run normally
  > AC: Given the user passes `--format toml`, When the scan completes, Then the DiscoveryResult is serialized as TOML and written to the output path
  > AC: Given the user passes `--json`, When the scan completes, Then the JSON is written to stdout instead of a file, And Rich formatting is suppressed on stderr
  > AC: Given a successful scan without `--json`, When results are displayed, Then a Rich table on stderr shows tool count, source breakdown, and top 10 by frequency
  > AC: Given the scan has partial failures (some collectors failed), When the command exits, Then exit code is 1 (partial failure) and warnings are printed to stderr via the project's structured logger
  > Spec: specs/planning-artifacts/epics.md#story-1-6
### Registry Resolution
> Goal: **User Outcome:** Developer runs `mymise resolve` and knows exactly which tools mise can manage today vs. which need manual handling. **FRs covered:** FR-6, FR-7, FR-9 (partial, resolve subcommand flags) **NFRs addressed:** NFR-1, NFR-2 **Arch requirements:** AR-3, AR-5 **Dependencies:** Reads `mymise-discovery.json` from Epic 1

- [ ] Story 2.1: Implement Resolver with Mise Registry Lookup and Dry-Run Mode
  > **Status:** Draft As a developer
  > I want mymise to check each discovered tool against the mise registry (with a dry-run preview mode)
  > So that I know which tools can be managed by mise and I can preview the resolution plan without side effects.
  > AC: Given a DiscoveryResult JSON file with discovered tools, When the Resolver processes each tool, Then it calls `mise registry <tool_name>` via subprocess for each tool, And parses the tab-separated output to extract backend type and registry entry
  > AC: Given a tool that exists in the mise registry, When the registry lookup succeeds, Then the tool is classified as `ResolvedTool` with backend, registry_entry, and install_command populated
  > AC: Given a tool that does not exist in the mise registry, When `mise registry <tool>` returns empty output or exit code 1, Then the tool is classified as `UnresolvedTool` with `suggested_actions` populated
  > AC: Given `mise registry <tool>` hangs or times out, When the subprocess timeout fires (configurable, default 10s), Then the tool is classified as unresolved with a timeout warning logged via the project's structured logger, And resolution continues with remaining tools
  > AC: Given `dry_run=True` is passed to `resolve()`, When resolution runs, Then `mise registry <tool>` is still called for classification (read-only), And no install probing or mutating subprocess calls occur, And the structured logger records the planned registry lookups with a `dry_run=true` tag
  > Spec: specs/planning-artifacts/epics.md#story-2-1
- [ ] Story 2.2: Wire Resolve CLI Command with Flags and Rich Summary
  > **Status:** Draft As a developer
  > I want to run `mymise resolve` with configurable input, output, timeout, and dry-run flags
  > So that I can control the resolution step from the command line.
  > AC: Given a valid `mymise-discovery.json` exists, When the user runs `mymise resolve`, Then the ResolutionResult is written to `mymise-resolved.json` (default) or the path specified by `--output`
  > AC: Given the user passes `--input /custom/path.json`, When the command runs, Then the resolver loads discovery data from the specified path
  > AC: Given the user passes `--timeout 30`, When the resolver processes each tool, Then each `mise registry` subprocess call uses a 30-second timeout instead of the 10-second default
  > AC: Given the user passes `--dry-run`, When the command runs, Then the resolver is invoked with `dry_run=True`, And no install probing occurs, And the ResolutionResult still reflects classification from `mise registry` output
  > AC: Given a successful resolution without `--json`, When results are displayed, Then a Rich summary on stderr shows: resolved count, unresolved count, resolution percentage, and backend type distribution
  > AC: Given the user passes `--json`, When the resolution completes, Then JSON is written to stdout instead of a file, And Rich formatting is suppressed on stderr
  > AC: Given the input discovery JSON does not exist, When the user runs `mymise resolve`, Then a clear error message is printed to stderr via Rich, And exit code is 2 (fatal)
  > Spec: specs/planning-artifacts/epics.md#story-2-2
### Registration & Bootstrap
> Goal: **User Outcome:** Developer runs `mymise register` and gets a complete, portable environment specification (mise.toml + shorthands.toml + bootstrap.sh). **FRs covered:** FR-8, FR-9 (partial, register subcommand flags) **NFRs addressed:** NFR-5 **Arch requirements:** AR-3 **Dependencies:** Reads `mymise-resolved.json` from Epic 2

- [ ] Story 3.1: Implement Registrar Artifact Generation
  > **Status:** Draft As a developer
  > I want mymise to generate mise.toml, shorthands.toml, and bootstrap.sh from my resolution results
  > So that I have a complete, portable environment specification I can use on any machine.
  > AC: Given a ResolutionResult with resolved tools, When the Registrar runs, Then it generates a `mise.toml` fragment listing all resolved tools at `@latest`, And each entry includes a comment with the backend source
  > AC: Given a ResolutionResult with unresolved tools that have GitHub provenance, When the Registrar runs, Then it generates `shorthands.toml` entries in `tool_name = "github:owner/repo"` format
  > AC: Given unresolved tools without identifiable GitHub repos, When the Registrar runs, Then it generates `bootstrap.sh` with fallback install commands (e.g., `apt install`, `cargo install`), And the script includes header comments explaining provenance
  > AC: Given all three artifacts are generated, When the output is written, Then each file includes a header comment with generation timestamp and mymise version
  > Spec: specs/planning-artifacts/epics.md#story-3-1
- [ ] Story 3.2: Wire Register CLI Command with Flags and Output Routing
  > **Status:** Draft As a developer
  > I want to run `mymise register` with configurable input, output directory, and shorthands filename
  > So that I can route the generated artifacts anywhere I need them.
  > AC: Given a valid `mymise-resolved.json` exists, When the user runs `mymise register`, Then artifacts are written to the current directory (default) or the path specified by `--output-dir`
  > AC: Given the user passes `--input /custom/path.json`, When the command runs, Then the registrar loads resolution data from the specified path
  > AC: Given the user passes `--shorthands-file custom-shorthands.toml`, When the command runs, Then the personal registry entries are written to `<output-dir>/custom-shorthands.toml` instead of the default filename
  > AC: Given a successful registration, When results are displayed, Then a Rich summary on stderr shows: files generated, tool counts per artifact, and output paths
  > AC: Given the input resolution JSON does not exist, When the user runs `mymise register`, Then a clear error message is printed via Rich on stderr, And exit code is 2 (fatal)
  > Spec: specs/planning-artifacts/epics.md#story-3-2
### CLI Integration & Full Pipeline
> Goal: **User Outcome:** Developer runs `mymise all` and the entire scan-resolve-register pipeline executes end-to-end. **FRs covered:** FR-9 **NFRs addressed:** NFR-2, NFR-3 **Arch requirements:** AR-4 **Dependencies:** All of Epics 1-3

- [ ] Story 4.1: Implement End-to-End Pipeline Command
  > **Status:** Draft As a developer
  > I want to run `mymise all` and have the entire scan-resolve-register pipeline execute in sequence
  > So that I can go from zero to a complete environment specification in one command.
  > AC: Given a system with shell history and installed tools, When the user runs `mymise all`, Then the scan, resolve, and register stages execute in sequence, And intermediate JSON files are written to the output directory, And final artifacts (mise.toml, shorthands.toml, bootstrap.sh) are generated
  > AC: Given the `--verbose` flag is passed, When the pipeline runs, Then debug-level logging is enabled for all stages
  > AC: Given a partial failure occurs (e.g., some collectors fail), When the pipeline completes, Then exit code is 1 (partial failure) with warnings on stderr, And the pipeline continues through all stages rather than aborting
  > Spec: specs/planning-artifacts/epics.md#story-4-1
- [ ] Story 4.2: CLI Polish and Error Handling
  > **Status:** Draft As a developer
  > I want consistent error handling, exit codes, and output routing across all commands
  > So that mymise behaves predictably and integrates well with other CLI tools.
  > AC: Given any subcommand completes successfully, When no warnings occurred, Then exit code is 0
  > AC: Given any subcommand encounters partial failures, When the command completes, Then exit code is 1 and all warnings are printed to stderr
  > AC: Given a fatal error occurs (missing input file, invalid JSON), When the error is caught, Then exit code is 2 and a clear error message is printed to stderr via Rich
  > AC: Given `--json` flag is passed to any command, When output is generated, Then Rich formatting is suppressed on stderr and JSON goes to stdout, And the emitted JSON is produced by `model.model_dump_json()` on the corresponding Pydantic model, guaranteeing runtime-validated output that conforms to the schema
  > Spec: specs/planning-artifacts/epics.md#story-4-2

## Completed

## Notes
- Follow TDD methodology (red-green-refactor)
- One story per Ralph loop iteration
- Update this file after completing each story
