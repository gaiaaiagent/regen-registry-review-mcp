# Testing Quick Reference Guide

**Quick Start**: Common testing commands and patterns for Registry Review MCP

---

## 🚀 Quick Commands

```bash
# Run all tests (default: skips expensive/slow tests)
pytest tests/

# Run with parallel execution (4x faster)
pytest tests/ -n 4

# Run specific test file
pytest tests/test_infrastructure.py

# Run specific test
pytest tests/test_infrastructure.py::TestCache::test_cache_set_and_get

# Run tests matching pattern
pytest tests/ -k "upload"

# Run only failed tests from last run
pytest --lf

# Run failed tests first, then others
pytest --ff

# Show test duration breakdown (top 20)
pytest tests/ --durations=20

# Verbose output with full tracebacks
pytest tests/ -vv --tb=long

# Run with coverage report
pytest tests/ --cov=src/registry_review_mcp --cov-report=html
```

---

## 🏷️ Test Markers

### Run by Category
```bash
# Run only unit tests (fast, no API calls)
pytest tests/ -m "unit"

# Skip slow tests (default)
pytest tests/ -m "not slow"

# Run only slow/expensive tests (before commits)
pytest tests/ -m "slow or expensive"

# Run integration tests
pytest tests/ -m "integration"

# Run accuracy validation tests
pytest tests/ -m "accuracy"

# Skip marker tests (requires 8GB RAM, PDF extraction)
pytest tests/ -m "not marker"
```

### Available Markers
- `unit`: Fast, isolated tests (no external dependencies)
- `slow`: Real API calls, takes >2s
- `expensive`: High API costs (LLM calls)
- `integration`: Full system integration tests
- `accuracy`: Ground truth validation tests
- `marker`: Marker PDF extraction tests (requires 8GB+ RAM)

---

## 📁 Test Organization

```
tests/
├── test_infrastructure.py        # Settings, state, cache (fast)
├── test_locking.py               # Lock mechanism tests (fast)
├── test_document_processing.py   # Document discovery (medium)
├── test_evidence_extraction.py   # Evidence extraction (medium)
├── test_validation.py            # Validation logic (fast)
├── test_upload_tools.py          # File upload (slow - 21s)
├── test_botany_farm_accuracy.py  # Ground truth tests (expensive)
└── conftest.py                   # Shared fixtures
```

---

## 🔧 Common Test Patterns

### Using Fixtures
```python
def test_with_temp_dir(temp_data_dir):
    """Use temporary data directory."""
    assert temp_data_dir.exists()
    # temp_data_dir is automatically cleaned up

def test_with_settings(test_settings):
    """Use test settings."""
    assert test_settings.log_level == "INFO"

async def test_with_botany_farm(botany_farm_markdown):
    """Use shared Botany Farm markdown (session-scoped)."""
    assert len(botany_farm_markdown) > 0
```

### Async Tests
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await some_async_function()
    assert result is not None
```

### Marking Tests
```python
@pytest.mark.slow
@pytest.mark.expensive
async def test_real_api_call():
    """This test makes real API calls."""
    # Skipped by default, run with: pytest -m "slow"
```

### Session Cleanup
```python
def test_with_cleanup(cleanup_examples_sessions):
    """Explicitly clean up example sessions."""
    # cleanup_examples_sessions fixture ensures cleanup
```

---

## 💰 Cost Tracking

### Automatic Cost Reports
After running tests, check:
```bash
cat test_costs_report.json

# Example output:
{
  "timestamp": "2025-11-20T18:00:00",
  "duration_seconds": 56.6,
  "total_cost_usd": 0.0,
  "total_api_calls": 0,
  "cached_calls": 0,
  "total_input_tokens": 0,
  "total_output_tokens": 0
}
```

### Monitor Costs During Development
```bash
# See cost summary at end of test run
pytest tests/ -v

# Output includes:
# ================================================================================
# API COST SUMMARY
# ================================================================================
# Total API Calls: 45
#   - Real API calls: 35
#   - Cached calls: 10
# Total Tokens: 78,543
# Total Cost: $0.7234
# ================================================================================
```

---

## 🐛 Debugging Tests

### Debug Failing Test
```bash
# Run with full output
pytest tests/test_file.py::test_name -vv --tb=long

# Drop into debugger on failure
pytest tests/test_file.py::test_name --pdb

# Show print statements
pytest tests/test_file.py::test_name -s

# Show local variables on failure
pytest tests/test_file.py::test_name -l
```

### Check Test Collection
```bash
# List all tests without running
pytest tests/ --collect-only

# Show test hierarchy
pytest tests/ --collect-only -q
```

### Verify Fixtures
```bash
# Show fixture setup/teardown
pytest tests/ --setup-show

# Show available fixtures
pytest --fixtures
```

---

## ⚡ Performance Tips

### During Development
```bash
# Skip slow tests (run in <10s)
pytest tests/ -m "not slow and not expensive"

# Run only failed tests from last run
pytest --lf

# Parallel execution (4x faster)
pytest tests/ -n 4
```

### Before Committing
```bash
# Run full suite (default: skips only marker tests)
pytest tests/

# Run with coverage check
pytest tests/ --cov=src/registry_review_mcp

# Run expensive tests too
pytest tests/ -m "slow or expensive"
```

### CI/CD
```bash
# Full validation with fresh cache
pytest tests/ -v --cache-clear

# Generate coverage report
pytest tests/ --cov=src/registry_review_mcp --cov-report=xml
```

---

## 📊 Test Metrics

### Current Performance (Baseline)
```
Total Tests:        223 active (273 total, 50 deselected)
Execution Time:     56.6s (baseline)
Slowest Test:       21.8s (test_start_review_full_workflow)
Async Tests:        104 (46.6%)
Pass Rate:          99.1% (221/223)
```

### Target Performance (After Optimization)
```
Execution Time:     <15s (goal)
With Parallel:      <10s (stretch goal)
```

---

## 🔍 Common Issues

### Issue: Session Pollution
**Symptom**: Tests pass individually but fail in suite
**Solution**: Ensure cleanup fixtures are used
```python
def test_something(cleanup_sessions):
    # cleanup_sessions autouse fixture handles cleanup
```

### Issue: Async Event Loop Errors
**Symptom**: `RuntimeError: Event loop is closed`
**Solution**: Use `@pytest.mark.asyncio` decorator
```python
@pytest.mark.asyncio
async def test_async():
    # pytest-asyncio handles event loop
```

### Issue: Slow Test Suite
**Symptom**: Tests take >60s to run
**Solution**: Skip expensive tests during development
```bash
pytest tests/ -m "not expensive"
```

### Issue: Missing Fixtures
**Symptom**: `fixture 'fixture_name' not found`
**Solution**: Check conftest.py or import fixture
```python
from tests.conftest import fixture_name
```

---

## 📚 Additional Resources

- Full test optimization report: `TEST_SUITE_OPTIMIZATION_REPORT.md`
- Implementation checklist: `TEST_OPTIMIZATION_CHECKLIST.md`
- Cost optimization guide: `docs/TEST_COST_OPTIMIZATION.md`
- Contributing guidelines: `CONTRIBUTING.md`

---

## 🎯 Testing Best Practices

1. **Write unit tests first** (fast, isolated)
2. **Mark expensive tests** with `@pytest.mark.expensive`
3. **Use shared fixtures** for expensive operations
4. **Run focused tests** during development (`pytest -k pattern`)
5. **Run full suite** before committing
6. **Check coverage** periodically (`pytest --cov`)
7. **Monitor costs** for API-based tests
8. **Keep tests isolated** (no shared state)
9. **Use descriptive names** (`test_should_do_something_when_condition`)
10. **Document complex setups** with docstrings

---

**Last Updated**: 2025-11-20
**Pytest Version**: 7.4+
**Python Version**: 3.13+
