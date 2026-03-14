# mymise

Reverse-engineer your CLI toolchain from shell history and resolve against the mise registry.

## Usage

```bash
mymise scan      # Discover tools from history, PATH, package managers
mymise resolve   # Resolve discovered tools against mise registry
mymise register  # Generate registration artifacts for unresolved tools
mymise all       # Run full pipeline
```

## Development

```bash
uv sync --group dev   # Install dependencies
mise run test         # Run tests
mise run lint         # Run linter
mise run ci           # Run full CI
```
