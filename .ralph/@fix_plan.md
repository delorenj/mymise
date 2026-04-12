# Ralph Fix Plan

## Stories to Implement

### Tool Discovery
> Goal: **User Outcome:** Developer runs `mymise scan` and gets a complete inventory of every CLI tool on their system, with source provenance and usage frequency. **FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-9 (partial, scan subcommand flags) **NFRs addressed:** NFR-1, NFR-2, NFR-4, NFR-5 **Arch requirements:** AR-1, AR-2, AR-3, AR-4 **Dependencies:** None (first epic)

- [x] Story 1.1: Implement Zsh History Collector
- [x] Story 1.2: Implement PATH Binary Collector
- [x] Story 1.3a: Implement Apt Collector
- [x] Story 1.3b: Implement Snap Collector
- [x] Story 1.3c: Implement Mise Collector
- [x] Story 1.4a: Implement Cargo Collector
- [x] Story 1.4b: Implement Npm Collector
- [x] Story 1.4c: Implement Pipx Collector
- [x] Story 1.4d: Implement Go Collector
- [x] Story 1.4e: Implement Uv Collector
- [x] Story 1.5: Implement Scanner Orchestration with Merge and Deduplication
- [x] Story 1.6: Wire Scan CLI Command with JSON/TOML Output, Flags, and Rich Summary
### Registry Resolution
> Goal: **User Outcome:** Developer runs `mymise resolve` and knows exactly which tools mise can manage today vs. which need manual handling. **FRs covered:** FR-6, FR-7, FR-9 (partial, resolve subcommand flags) **NFRs addressed:** NFR-1, NFR-2 **Arch requirements:** AR-3, AR-5 **Dependencies:** Reads `mymise-discovery.json` from Epic 1

- [x] Story 2.1: Implement Resolver with Mise Registry Lookup and Dry-Run Mode
- [x] Story 2.2: Wire Resolve CLI Command with Flags and Rich Summary
### Registration & Bootstrap
> Goal: **User Outcome:** Developer runs `mymise register` and gets a complete, portable environment specification (mise.toml + shorthands.toml + bootstrap.sh). **FRs covered:** FR-8, FR-9 (partial, register subcommand flags) **NFRs addressed:** NFR-5 **Arch requirements:** AR-3 **Dependencies:** Reads `mymise-resolved.json` from Epic 2

- [x] Story 3.1: Implement Registrar Artifact Generation
- [x] Story 3.2: Wire Register CLI Command with Flags and Output Routing

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

- [x] Story 4.1: Implement End-to-End Pipeline Command
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
