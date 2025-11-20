# Testing Quick Reference

## TL;DR: Fastest Way to Test

```bash
make smoke     # 1.83s - Use this for rapid TDD
make fast      # 37.9s - Before committing
make parallel  # 31.4s - Before pushing
```

## Common Commands

### During Development
```bash
# After every change (1.83s)
make smoke

# Continuous testing (auto-runs on file save)
make watch
# or: ptw -- -m smoke

# Only tests for files you changed
make changed
# or: pytest --picked -n auto
```

### Before Committing
```bash
# Run fast tests
make fast

# With coverage
make coverage
```

### Before Pushing
```bash
# Full suite in parallel
make parallel

# Or if parallel has issues
make full
```

## Test Tiers

| Tier | Command | Tests | Time | When to Use |
|------|---------|-------|------|-------------|
| **Smoke** | `make smoke` | 11 | 1.83s | After every code change |
| **Fast** | `make fast` | 234 | 37.9s | Before commit |
| **Full** | `make full` | 223 | 34s | Before push |
| **Parallel** | `make parallel` | 234 | 31.4s | CI/CD, before merge |

## Markers

```bash
# Smoke tests (critical path)
pytest -m smoke -v

# Unit tests (pure Python, no I/O)
pytest -m unit -v

# Integration tests
pytest -m integration -v

# Exclude slow tests
pytest -m "not slow" -v

# Exclude expensive API tests
pytest -m "not expensive" -v
```

## Workflow Examples

### Rapid TDD Loop
```bash
# Terminal 1: Watch mode
make watch

# Terminal 2: Edit code
# ... save file ...
# Tests auto-run in < 2s
```

### Feature Development
```bash
# After making changes
make smoke        # Quick validation

# When feature is complete
make fast         # Comprehensive check

# Ready to commit
git add .
git commit -m "Add feature X"
```

### Pre-Push Checklist
```bash
make parallel     # Full suite (~30s)
# If all pass
git push
```

## Optimization Plugins (Optional)

### Install
```bash
pip install pytest-picked pytest-testmon pytest-watch pytest-sugar
```

### Usage
```bash
# Only changed files
pytest --picked

# Intelligent test selection
pytest --testmon

# Watch mode
ptw -- -m smoke

# Better output (automatic)
pytest -v  # pytest-sugar enhances this
```

## Debugging

### Run Single Test
```bash
pytest tests/test_smoke.py::TestCoreInfrastructure::test_settings_initialize -v
```

### Run Single Test File
```bash
pytest tests/test_smoke.py -v
```

### Run Tests Matching Pattern
```bash
pytest -k "citation" -v
```

### Show Print Statements
```bash
pytest -s -v
```

### Stop on First Failure
```bash
pytest -x
```

### Run Last Failed Tests
```bash
pytest --lf
```

## Performance Tips

### Avoid Overhead
```bash
# Don't use this for single test
pytest tests/test_smoke.py::test_one -v  # 1.8s overhead

# Instead, run whole module
pytest tests/test_smoke.py -v            # Same 1.8s for all tests
```

### Use Parallel for Large Suites
```bash
# Serial: 34s
pytest tests/ -v

# Parallel: 31s
pytest tests/ -n auto -v
```

### Cache Test Results
```bash
# First run: normal
pytest --testmon

# Subsequent runs: only affected tests
pytest --testmon
```

## Troubleshooting

### Smoke Tests Slow
```bash
# Check if pytest is finding too many tests
pytest -m smoke --collect-only

# Should show: "11 selected"
# If more, check test markers
```

### Parallel Tests Failing
```bash
# Run in serial to verify test logic
pytest tests/ -v

# If passes, issue is parallelism (shared state)
# Solution: Use session factories (see tests/factories.py)
```

### Import Errors
```bash
# Ensure you're in correct directory
cd /home/ygg/Workspace/RegenAI/regen-registry-review-mcp

# Check PYTHONPATH
echo $PYTHONPATH

# Run with explicit path
PYTHONPATH=src pytest tests/ -v
```

## What to Run When

| Situation | Command | Time | Coverage |
|-----------|---------|------|----------|
| Just changed one line | `make smoke` | 1.83s | Critical path |
| Refactoring a module | `make fast` | 37.9s | Most tests |
| About to commit | `make changed` | Varies | Changed files |
| About to push | `make parallel` | 31.4s | Full suite |
| CI/CD | `make parallel` | 31.4s | Full suite |
| Debugging one test | `pytest tests/test_X.py::test_y -v` | Seconds | Single test |

## Coverage Report

```bash
# Generate coverage
make coverage

# Opens in browser (Linux/Mac)
# Or manually open: htmlcov/index.html
```

## Clean Up

```bash
# Remove test artifacts
make clean

# Removes:
# - .pytest_cache
# - htmlcov
# - .coverage
# - test_costs_report.json
# - __pycache__ directories
```

## Cheat Sheet

```bash
# Development
make smoke                    # Quick check
make watch                    # Auto-run
make changed                  # Git changes only

# Pre-commit
make fast                     # Full fast tests

# Pre-push
make parallel                 # Full parallel

# Debug
pytest tests/test_X.py -v -s  # Single file, verbose, show prints
pytest -k "pattern" -v        # Pattern match
pytest --lf -x                # Last failed, stop on first

# Optimization
pytest --picked               # Changed files
pytest --testmon              # Intelligent selection
ptw -- -m smoke              # Continuous watch

# Coverage
make coverage                 # Generate report

# Cleanup
make clean                    # Remove artifacts
```

## Help

```bash
# Show all make targets
make help

# Show pytest options
pytest --help

# Show markers
pytest --markers
```

## Files Reference

| File | Purpose |
|------|---------|
| `tests/test_smoke.py` | 11 smoke tests (< 2s) |
| `pytest.ini` | Pytest configuration |
| `Makefile` | Test shortcuts |
| `docs/TESTING_SPEED_STRATEGY.md` | Comprehensive strategy |
| `docs/TESTING_SPEED_RESULTS.md` | Implementation results |
| `docs/TESTING_QUICK_REFERENCE.md` | This file |

## Remember

- **Smoke tests** are for instant feedback during development
- **Fast tests** are for pre-commit validation
- **Full suite** is for pre-push/CI validation
- **Watch mode** eliminates pytest overhead after first run
- **Parallel execution** is fastest for full suite validation

**When in doubt**: `make smoke` (1.83s)
