# UV Commands Cheat Sheet for MCP Development

Quick reference for all UV commands you need for MCP server development.

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip (if needed)
pip install uv

# Verify installation
uv --version
```

## Project Initialization

```bash
# Create new package project
uv init my-mcp-server --package

# Create in current directory
uv init --package

# Create with specific Python version
uv init my-mcp-server --package --python 3.11

# Create simple script (no package structure)
uv init my-script
```

## Dependency Management

### Adding Dependencies

```bash
# Add production dependency
uv add mcp
uv add "mcp[cli]"           # With extras
uv add httpx pydantic       # Multiple at once

# Add with version constraint
uv add "mcp>=1.0.0"
uv add "httpx>=0.27.0,<0.28.0"

# Add development dependency
uv add --dev pytest
uv add --dev pytest pytest-asyncio ruff

# Add from git
uv add git+https://github.com/user/repo.git

# Add from local path
uv add --editable ./local-package
```

### Removing Dependencies

```bash
# Remove dependency
uv remove httpx

# Remove dev dependency
uv remove --dev pytest
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package mcp

# Update and sync
uv lock --upgrade && uv sync
```

### Installing Dependencies

```bash
# Install all dependencies
uv sync

# Install without dev dependencies
uv sync --no-dev

# Install with frozen lockfile (production)
uv sync --frozen

# Install only dev dependencies
uv sync --only-dev
```

## Python Version Management

```bash
# Install Python version
uv python install 3.11
uv python install 3.12

# List installed Python versions
uv python list

# Set project Python version (creates .python-version)
echo "3.11" > .python-version

# Pin Python version in pyproject.toml
# Add: requires-python = ">=3.10"
```

## Running Code

```bash
# Run Python script
uv run python script.py

# Run with specific Python version
uv run --python 3.11 python script.py

# Run module
uv run python -m my_module

# Run with additional dependencies (ephemeral)
uv run --with requests python script.py
uv run --with "httpx>=0.27.0" python script.py

# Run project command (from pyproject.toml)
uv run my-mcp-server

# Run with frozen lockfile
uv run --frozen python script.py

# Change directory before running
uv run --directory /path/to/project python script.py
```

## MCP-Specific Commands

### Development

```bash
# Run MCP server
uv run python server.py

# Run with MCP Inspector
npx @modelcontextprotocol/inspector uv run python server.py

# Run MCP dev server (if using mcp CLI)
uv run mcp dev server.py

# Run with frozen dependencies (test production)
uv run --frozen python server.py
```

### Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=my_package

# Run specific test file
uv run pytest tests/test_server.py

# Run with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/test_server.py::test_tool -v
```

### Linting and Formatting

```bash
# Check code with ruff
uv run ruff check .

# Format code with ruff
uv run ruff format .

# Check and fix automatically
uv run ruff check --fix .

# Type check with mypy
uv run mypy src/
```

## Virtual Environment Management

```bash
# Create virtual environment (usually automatic)
uv venv

# Create with specific Python
uv venv --python 3.11

# Activate (manual - usually unnecessary with uv run)
source .venv/bin/activate     # macOS/Linux
.venv\Scripts\activate        # Windows

# Deactivate
deactivate
```

## Lockfile Management

```bash
# Create/update lockfile
uv lock

# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package httpx

# Check if lockfile is up to date
uv lock --check

# Use frozen lockfile (production)
uv sync --frozen
```

## Cache Management

```bash
# Show cache directory
uv cache dir

# Show cache size
uv cache size

# Clean cache
uv cache clean

# Prune unnecessary cache entries
uv cache prune

# Prune for CI (keep expensive builds)
uv cache prune --ci
```

## Package Building and Publishing

```bash
# Build package
uv build

# Build wheel only
uv build --wheel

# Build source distribution only
uv build --sdist

# Publish to PyPI (requires credentials)
uv publish

# Publish to test PyPI
uv publish --publish-url https://test.pypi.org/legacy/
```

## Information Commands

```bash
# Show UV version
uv --version

# Show Python executable path
uv run python -c "import sys; print(sys.executable)"

# List installed packages
uv run python -m pip list

# Show package info
uv run python -m pip show mcp

# Tree of dependencies
uv tree

# Check UV environment
uv run python -c "import sys; print(sys.prefix)"
```

## Configuration

### Environment Variables

```bash
# Set UV cache directory
export UV_CACHE_DIR=/path/to/cache

# Disable cache
export UV_NO_CACHE=1

# Set Python preference
export UV_PYTHON=3.11

# Compile bytecode for faster startup
export UV_COMPILE_BYTECODE=1

# Use copy instead of symlinks (Docker)
export UV_LINK_MODE=copy

# Set project environment location
export UV_PROJECT_ENVIRONMENT=.venv
```

### Common Flags

```bash
--verbose               # Verbose output
--quiet                # Quiet output
--no-cache             # Disable cache
--frozen               # Use locked dependencies exactly
--no-dev               # Skip dev dependencies
--only-dev             # Only dev dependencies
--python 3.11          # Specify Python version
--directory /path      # Change directory first
--with package         # Add ephemeral dependency
```

## MCP Development Workflow

### Initial Setup

```bash
# 1. Create project
uv init mcp-weather --package
cd mcp-weather

# 2. Add dependencies
uv add "mcp[cli]" httpx pydantic

# 3. Add dev dependencies
uv add --dev pytest pytest-asyncio ruff mypy

# 4. Create .python-version
echo "3.11" > .python-version
```

### Development

```bash
# Run server
uv run python src/mcp_weather/server.py

# Test with Inspector
npx @modelcontextprotocol/inspector uv run python src/mcp_weather/server.py

# Run tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy src/
```

### Pre-Deployment

```bash
# Test with frozen lockfile
uv sync --frozen
uv run --frozen python src/mcp_weather/server.py

# Run full test suite
uv run pytest --cov=mcp_weather --cov-report=html

# Check for outdated dependencies
uv lock --upgrade --dry-run
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-weather",
        "run",
        "mcp-weather"
      ],
      "env": {
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

```bash
# Issue: Module not found
# Solution: Install dependencies
uv sync

# Issue: Wrong Python version
# Solution: Specify version
uv run --python 3.11 python script.py

# Issue: Lockfile out of sync
# Solution: Regenerate lockfile
uv lock

# Issue: Cache problems
# Solution: Clean cache
uv cache clean

# Issue: Permission errors
# Solution: Check cache directory permissions
uv cache dir
chmod -R u+w $(uv cache dir)
```

### Debug Commands

```bash
# Check UV environment
uv run python -c "import sys; print(sys.executable)"
uv run python -c "import sys; print(sys.path)"

# Verify MCP installation
uv run python -c "import mcp; print(mcp.__version__)"

# Check installed packages
uv run python -m pip list

# Verbose execution
uv run --verbose python script.py

# Check lockfile status
uv lock --check
```

## Performance Tips

### Optimization

```bash
# Use frozen mode in production
uv sync --frozen
uv run --frozen python server.py

# Compile bytecode for faster startup
export UV_COMPILE_BYTECODE=1

# Use copy mode in Docker
export UV_LINK_MODE=copy

# Keep cache on same filesystem as project
# (enables hardlinks/reflinking)

# Prune cache in CI
uv cache prune --ci
```

### Speed Benchmarks

```
First install (cold cache):    8-10x faster than pip
Subsequent installs (warm):    80-115x faster than pip
Environment creation:          80x faster than venv
Resolution:                    10-100x faster than pip
```

## Quick Reference Table

| Task | Command |
|------|---------|
| Create project | `uv init my-project --package` |
| Add dependency | `uv add package` |
| Add dev dependency | `uv add --dev package` |
| Install all | `uv sync` |
| Run script | `uv run python script.py` |
| Run tests | `uv run pytest` |
| Update deps | `uv lock --upgrade` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type check | `uv run mypy src/` |
| Clean cache | `uv cache clean` |
| Production sync | `uv sync --frozen --no-dev` |

## Resources

- **Official Docs:** https://docs.astral.sh/uv/
- **GitHub:** https://github.com/astral-sh/uv
- **Installation:** https://docs.astral.sh/uv/getting-started/installation/

## Remember

✅ Always use `uv run` (no manual venv activation needed)
✅ Use `--frozen` in production
✅ Commit `uv.lock` to version control
✅ Use absolute paths in MCP configurations
✅ Set UV_COMPILE_BYTECODE=1 for production
✅ Keep cache on same filesystem as projects

🚀 UV makes Python dependency management fast and reliable!
