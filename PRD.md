---
stepsCompleted: [executive-summary, success-criteria, scope, user-journeys, functional-requirements, non-functional-requirements]
inputDocuments: [Braindump.md]
workflowType: 'prd'
---

# Product Requirements Document - mymise

**Author:** Jarad DeLorenzo
**Date:** 2026-03-14

## Executive Summary

**mymise** is a Python CLI that reverse-engineers a developer's entire CLI toolchain from shell history and system state, then resolves each tool against the mise registry ecosystem to produce a reproducible, portable developer environment specification.

**Vision:** One command captures your CLI genome. One command reproduces it on any machine.

**Differentiator:** Unlike dotfile managers (chezmoi, yadm) that track config files, or Nix that requires learning a DSL, mymise works backwards from *what you actually use* -- mining your shell history and installed binaries -- to generate a mise-native toolchain manifest. Zero upfront curation required.

**Target Users:**
- Power-user developers with 50+ CLI tools accumulated organically across package managers
- Developers who rebuild machines or onboard to new hardware regularly
- Teams wanting to standardize developer tooling without imposing a package manager

**Core Problem:** Developer environments accumulate tools from 6+ package managers (apt, cargo, npm, pipx, go install, mise, snap, manual curl installs). Rebuilding a machine means days of "wait, what was that tool called?" Sharing environments means prose READMEs that rot.

## Success Criteria

| ID | Metric | Target | Measurement |
|----|--------|--------|-------------|
| SC-1 | Tool discovery completeness | ≥90% of actively-used CLI tools captured from a test machine | Compare mymise output against manual audit of 50 known-installed tools |
| SC-2 | Registry resolution rate | ≥70% of discovered tools resolve to a mise-installable backend | Count resolved vs unresolved in M2 output |
| SC-3 | Bootstrap reproducibility | A fresh machine can install all resolved tools from mymise output | Run `mise install` from generated config on clean Ubuntu container |
| SC-4 | Scan-to-output time | <30 seconds for full scan + resolution pipeline | Wall clock on reference machine (~10K history entries, ~80 mise tools) |
| SC-5 | Zero false positives | No shell builtins, aliases, or non-tool commands appear in output | Validate against known-bad list (cd, ls, echo, etc.) |

## Product Scope

### Milestone 1 (MVP) — Discovery

Scan shell history and system state. Produce a JSON manifest of every CLI tool on the system, with metadata about where it was found.

### Milestone 2 — Resolution

Take M1's JSON manifest, resolve each tool against mise's built-in registry and aqua registry. Produce two lists:
1. **Resolved:** Tools where `mise install <tool>@latest` succeeds (or has a known registry entry)
2. **Unresolved:** Tools that have no mise registry mapping

### Milestone 3 — Registration

For unresolved tools, provide pathways to register them:
1. Auto-generate personal registry entries (shorthands.toml) for tools with GitHub releases
2. Suggest aqua registry contributions for popular tools
3. Generate a bootstrap script that installs everything

### Out of Scope (Future)
- Multi-machine merge (combining manifests from different hosts)
- Version pinning from history frequency analysis
- GUI/TUI interactive mode
- Team registry server

## User Journeys

### UJ-1: First-Time Discovery

**Persona:** Developer with 3+ years of accumulated tools on a Linux workstation.

**Flow:**
1. User runs `mymise scan`
2. mymise parses `~/.zsh_history` (format: `: <timestamp>:<duration>;command`)
3. mymise scans PATH directories for executables
4. mymise queries package managers (apt, cargo, npm, pipx, mise, snap, go, uv)
5. mymise merges, deduplicates, and classifies each tool
6. Output: `mymise-discovery.json` with tool name, source(s), frequency, last-used timestamp

**Success:** User sees a complete inventory of their CLI toolchain in <30 seconds.

### UJ-2: Registry Resolution

**Persona:** Same developer, wants to know which tools mise can manage.

**Flow:**
1. User runs `mymise resolve` (or `mymise resolve --input mymise-discovery.json`)
2. mymise loads discovery JSON
3. For each tool, queries `mise registry <tool>` to check for a registry entry
4. For tools not in registry, attempts `mise install <tool>@latest --dry-run` (or equivalent)
5. Classifies each tool as resolved (mise-installable) or unresolved
6. Output: `mymise-resolved.json` with two lists + backend info for resolved tools

**Success:** User sees exactly which tools mise can manage today.

### UJ-3: Registration & Bootstrap

**Persona:** Developer ready to create a portable toolchain.

**Flow:**
1. User runs `mymise register` (or `mymise register --input mymise-resolved.json`)
2. For unresolved tools with GitHub repos, generates personal registry entries
3. For remaining tools, suggests package manager install commands
4. Generates `mise.toml` with all resolved tools
5. Generates `shorthands.toml` with personal registry entries
6. Generates `bootstrap.sh` for tools that need non-mise installation
7. Output: Complete reproducible environment specification

**Success:** Running the generated artifacts on a fresh machine installs the full toolchain.

## Functional Requirements

### FR-1: Shell History Parsing

- Parses zsh extended history format: `: <timestamp>:<duration>;command_text`
- Extracts first token (binary name) from each command
- Handles multi-line commands (backslash continuation)
- Filters shell builtins: cd, ls, echo, exit, clear, history, pwd, export, source, alias, unalias, set, unset, type, which, where, command, builtin, eval, exec, trap
- Filters common non-tool commands: sudo (extracts next token), git subcommands (keeps git), pipe chains (extracts each command)
- Records usage frequency (count of invocations per tool)
- Records last-used timestamp from history metadata
- Configurable history file path (default: `~/.zsh_history`)

### FR-2: PATH Binary Scanning

- Scans all directories in `$PATH`
- Identifies executable files (not directories, not symlinks-to-directories)
- Follows symlinks to resolve actual binary location
- Records binary path for provenance tracking
- Deduplicates across PATH directories (first match wins, consistent with shell behavior)

### FR-3: Package Manager Inventory

- Queries installed packages from: apt, snap, cargo, pipx, npm (global), mise, go/bin, uv tool
- Records which package manager installed each tool
- Handles missing package managers gracefully (skip with warning, not error)
- Maps package names to binary names where they differ (e.g., `python3-pip` → `pip3`)

### FR-4: Merge & Classification

- Merges results from FR-1, FR-2, FR-3 into unified tool list
- Each tool entry contains: name, source(s), frequency, last_used, binary_path, installed_by
- Deduplicates by canonical tool name
- Classifies tools by category: runtime, package-manager, cli-tool, language-tool, system-utility

### FR-5: Discovery Output

- Outputs JSON file (`mymise-discovery.json`) conforming to a Pydantic model schema
- JSON includes metadata: scan timestamp, hostname, user, tool count, scan duration
- Supports `--output` flag for custom output path
- Supports `--format` flag for JSON (default) or TOML output
- Pretty-prints summary to stderr via Rich: tool count by category, top 10 most-used

### FR-6: Registry Resolution

- For each discovered tool, runs `mise registry <tool>` to check for registry entry
- Parses `mise registry` output format: `tool_name    backend:owner/repo`
- Classifies result: resolved (has registry entry) or unresolved (no entry)
- For resolved tools, records backend type (aqua, github, asdf, core, etc.)
- Handles `mise registry` failures gracefully (timeout, parse errors)
- Supports `--dry-run` to skip actual install attempts

### FR-7: Resolution Output

- Outputs JSON file (`mymise-resolved.json`) with two top-level lists: `resolved`, `unresolved`
- Each resolved entry includes: tool name, backend, registry entry, install command
- Each unresolved entry includes: tool name, original source, suggested actions
- Pretty-prints summary: N resolved, M unresolved, resolution percentage

### FR-8: Personal Registry Generation

- For unresolved tools with identifiable GitHub repos, generates `shorthands.toml` entries
- Format: `tool_name = "github:owner/repo"` or `tool_name = "aqua:owner/repo"`
- Generates `mise.toml` section with all resolved tools at `@latest`
- Generates `bootstrap.sh` with fallback install commands for truly unresolvable tools
- All generated files include header comments explaining provenance

### FR-9: CLI Interface

- Built with Typer, three subcommands: `scan`, `resolve`, `register`
- `scan` accepts: `--history-file`, `--output`, `--format`, `--skip-pkg-managers`
- `resolve` accepts: `--input`, `--output`, `--dry-run`, `--timeout`
- `register` accepts: `--input`, `--output-dir`, `--shorthands-file`
- `mymise all` runs the full pipeline (scan → resolve → register)
- `--verbose` flag enables debug logging
- `--json` flag outputs machine-readable JSON to stdout (suppresses Rich formatting)

## Non-Functional Requirements

### NFR-1: Performance

- Full scan completes in <30 seconds on a system with ~10K history entries and ~80 installed tools
- Registry resolution for 200 tools completes in <60 seconds (parallelizable)
- Memory usage stays under 100MB for scan phase

### NFR-2: Reliability

- Graceful degradation: if any package manager query fails, scan continues with others
- All subprocess calls have 10-second timeouts
- Exit code 0 on success, 1 on partial failure (with warnings), 2 on fatal error

### NFR-3: Compatibility

- Runs on Linux (primary target: Ubuntu/Debian)
- Python 3.12+ (managed by mise)
- Requires mise installed and on PATH
- No root/sudo required for scan or resolve operations

### NFR-4: Extensibility

- Package manager scanners are pluggable (each is a function conforming to a Protocol)
- Output format is schema-versioned (schema_version field in JSON output)
- New package managers can be added without modifying core logic

### NFR-5: Data Integrity

- JSON output validates against Pydantic models before writing
- Schema version bumps on breaking changes
- Tool names are normalized to lowercase, stripped of path prefixes
