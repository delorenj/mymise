#!/usr/bin/env bash
# Reality-drift guard: run mymise end-to-end against the real machine in an isolated tmp dir.
# Verifies that unit-test green doesn't mask broken UX. Pass --keep to inspect the artifacts.
set -euo pipefail

KEEP=0
HISTORY_FILE="${HISTORY_FILE:-$HOME/.zsh_history}"
for arg in "$@"; do
    case "$arg" in
        --keep) KEEP=1 ;;
        --history-file=*) HISTORY_FILE="${arg#*=}" ;;
        -h|--help)
            echo "Usage: $0 [--keep] [--history-file=PATH]"
            exit 0
            ;;
    esac
done

WORKDIR="$(mktemp -d -t mymise-testdrive-XXXXXX)"
trap '[[ $KEEP -eq 1 ]] || rm -rf "$WORKDIR"' EXIT

echo "==> Test drive workdir: $WORKDIR"
echo "==> History file: $HISTORY_FILE"

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"

# Run the full pipeline against the real machine, output to the tmp dir
echo "==> Running: uv run mymise all --output-dir $WORKDIR"
set +e
uv run mymise all \
    --history-file "$HISTORY_FILE" \
    --output-dir "$WORKDIR"
EXIT_CODE=$?
set -e

# Exit 0 = clean run, exit 1 = partial failure (still produced artifacts), 2 = fatal
if [[ $EXIT_CODE -ne 0 && $EXIT_CODE -ne 1 ]]; then
    echo "FAIL: mymise all exited with $EXIT_CODE (expected 0 or 1)"
    exit "$EXIT_CODE"
fi

# Assert all expected artifacts exist
echo "==> Checking artifacts..."
EXPECTED=(
    "$WORKDIR/mymise-discovery.json"
    "$WORKDIR/mymise-resolved.json"
    "$WORKDIR/mise.toml"
    "$WORKDIR/shorthands.toml"
    "$WORKDIR/bootstrap.sh"
)
MISSING=()
for path in "${EXPECTED[@]}"; do
    if [[ ! -f "$path" ]]; then
        MISSING+=("$path")
    fi
done
if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "FAIL: missing artifacts:"
    printf '  - %s\n' "${MISSING[@]}"
    exit 1
fi
echo "  OK: all 5 artifacts present"

# Validate bootstrap.sh: must start with shebang + strict mode, must parse
echo "==> Validating bootstrap.sh..."
BOOTSTRAP="$WORKDIR/bootstrap.sh"
if ! head -1 "$BOOTSTRAP" | grep -q '^#!/usr/bin/env bash'; then
    echo "FAIL: bootstrap.sh missing shebang"
    exit 1
fi
if ! grep -q '^set -euo pipefail' "$BOOTSTRAP"; then
    echo "FAIL: bootstrap.sh missing 'set -euo pipefail'"
    exit 1
fi
if ! bash -n "$BOOTSTRAP"; then
    echo "FAIL: bootstrap.sh has bash syntax errors"
    exit 1
fi
echo "  OK: bootstrap.sh has shebang, strict mode, and parses"

# Validate JSON outputs are well-formed
echo "==> Validating JSON output..."
for f in mymise-discovery.json mymise-resolved.json; do
    if ! python3 -m json.tool "$WORKDIR/$f" > /dev/null 2>&1; then
        echo "FAIL: $f is not valid JSON"
        exit 1
    fi
done
echo "  OK: JSON artifacts are well-formed"

# Validate mise.toml output parses as TOML
echo "==> Validating mise.toml output..."
if ! python3 -c "import tomllib; tomllib.loads(open('$WORKDIR/mise.toml').read())" > /dev/null 2>&1; then
    echo "FAIL: generated mise.toml is not valid TOML"
    exit 1
fi
echo "  OK: mise.toml parses"

# Sanity: confirm we did NOT clobber the project's own mise.toml
echo "==> Verifying project mise.toml not clobbered..."
if ! grep -q '\[tasks\.' "$PROJECT_ROOT/mise.toml"; then
    echo "FAIL: project mise.toml at $PROJECT_ROOT/mise.toml lost its [tasks.*] sections"
    echo "       The pipeline wrote into the project root instead of $WORKDIR"
    exit 1
fi
echo "  OK: project mise.toml intact"

DISCOVERY_COUNT=$(python3 -c "import json; print(len(json.load(open('$WORKDIR/mymise-discovery.json'))['tools']))")
RESOLVED_COUNT=$(python3 -c "import json; print(len(json.load(open('$WORKDIR/mymise-resolved.json'))['resolved']))")
UNRESOLVED_COUNT=$(python3 -c "import json; print(len(json.load(open('$WORKDIR/mymise-resolved.json'))['unresolved']))")

echo ""
echo "==> Test drive PASSED (exit=$EXIT_CODE)"
echo "    Discovered: $DISCOVERY_COUNT tools"
echo "    Resolved:   $RESOLVED_COUNT"
echo "    Unresolved: $UNRESOLVED_COUNT"
if [[ $KEEP -eq 1 ]]; then
    echo "    Artifacts kept at: $WORKDIR"
fi
