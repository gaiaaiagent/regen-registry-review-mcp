# Testing Guide for Registry Review MCP

This guide explains how to run tests efficiently to avoid expensive API calls and long runtimes.

## Quick Reference

| Command | Tests Run | Runtime | Cost | Use Case |
|---------|-----------|---------|------|----------|
| `pytest` | 220 (fast only) | ~6s | $0.00 | ✅ Default - use this! |
| `pytest -m ""` | 274 (ALL tests) | ~200s+ | $0.05+ | ⚠️ Expensive - avoid! |
| `pytest -m expensive` | 32 (LLM tests) | ~2min | $0.05 | Weekly only |
| `pytest -m marker -n 0` | 4 (PDF tests) | ~2min | $0.00 | Nightly only |
| `pytest -m expensive --sample=0.25` | 8 (sampled) | ~30s | $0.01 | CI nightly |

## Understanding Test Markers

The test suite uses markers to categorize expensive tests:

- **No marker** (default): Fast tests (~220 tests, 6s, $0.00)
- **`expensive`**: LLM API tests (32 tests, 2min, $0.05)
- **`marker`**: PDF conversion tests (4 tests, 2min, 8GB RAM)
- **`accuracy`**: Ground truth validation (4 tests, included in expensive)
- **`integration`**: Full system tests

## Default Behavior (Recommended)

```bash
# Just run pytest with no arguments
pytest
```

**What happens:**
- Runs 220 fast tests only
- Takes ~6 seconds
- Costs $0.00
- Skips expensive LLM and marker tests

**This is controlled by `pytest.ini` line 25:**
```ini
-m "not expensive and not integration and not accuracy and not marker"
```

## Common Mistakes

### ❌ DON'T: Override marker filter with `-m ""`

```bash
# This runs ALL 274 tests including expensive ones!
pytest -m ""

# Takes 200+ seconds
# Costs $0.05+ per run
# Loads 8GB marker models
# Makes expensive LLM API calls
```

**If you see 274 tests collected, you're running expensive tests!**

### ❌ DON'T: Run expensive tests locally without sampling

```bash
# This runs all 32 LLM tests
pytest -m expensive

# Takes ~2 minutes
# Costs $0.05
# Should only run weekly in CI
```

### ✅ DO: Use the default command

```bash
# Fast, free, efficient
pytest

# Should see: "220/274 tests collected (54 deselected)"
# Takes ~6 seconds
# Costs $0.00
```

## When to Run Expensive Tests

### Local Development (You)

**Fast tests (always):**
```bash
pytest
```

**Specific test file:**
```bash
pytest tests/test_document_processing.py -v
```

**Markdown helper tests (fast, no API):**
```bash
pytest tests/test_marker_real.py::TestMarkdownHelpers -v -m ""
```

**Single expensive test (when debugging LLM issues):**
```bash
# Only run one test, not the whole suite
pytest tests/test_botany_farm_accuracy.py::TestBotanyFarmAccuracy::test_date_extraction_accuracy -v -m ""
```

### CI/CD

**Pull Request (every commit):**
```bash
pytest  # Fast tests only
```

**Nightly (daily):**
```bash
# Sample 25% of expensive tests (8/32)
pytest -m expensive --sample=0.25

# Run marker integration tests
pytest -m marker -n 0
```

**Weekly (before release):**
```bash
# Run all expensive tests
pytest -m expensive

# Run accuracy validation
pytest -m accuracy -n 0 -m ""
```

## Understanding Test Output

### Good (Fast Tests)

```
collected 220/274 tests (54 deselected) in 0.09s
...
215 passed, 5 failed in 6.27s
```

- **220 tests collected** = Fast tests only ✅
- **~6 seconds** = Normal runtime ✅
- **$0.00 cost** ✅

### Warning (All Tests)

```
collected 274 tests in 0.09s
...
passed in 205.78s
```

- **274 tests collected** = ALL tests including expensive ⚠️
- **200+ seconds** = Expensive tests ran ⚠️
- **$0.05+ cost** = LLM API calls made ⚠️

**If you see this, you ran expensive tests by mistake!**

## Sampling for Cost Control

The test suite includes a sampling plugin for running expensive tests efficiently.

### Automatic Sampling in CI

```bash
# In CI environment (CI=1)
CI=1 pytest -m expensive

# Automatically samples 25% (8/32 tests)
# Output shows:
# 🎲 Sampling Strategy:
#    • Total expensive tests: 32
#    • Sample rate: 25%
#    • Running: 8 tests
#    • Skipping: 24 tests
```

### Manual Sampling

```bash
# Run 25% of expensive tests
pytest -m expensive --sample=0.25

# Run 50% of expensive tests
pytest -m expensive --sample=0.50

# Run all expensive tests
pytest -m expensive --sample=1.0
# (or just: pytest -m expensive)
```

### Daily Rotation

Sampling uses a daily seed (YYYYMMDD) so:
- Same tests run throughout the day (reproducible)
- Different tests run each day (good coverage over time)
- Over 4 days, all expensive tests are covered

## Test Architecture

### Fast Tests (Tier 1) - 220 tests
- Unit tests with mocks
- Integration tests with cached data
- No real API calls
- No heavy model loading
- **Runtime**: ~6s
- **Cost**: $0.00
- **When**: Every commit

### Markdown Helpers (Tier 2) - 5 tests
- Fast parsing utilities
- No PDF loading
- No marker models
- Included in fast tests by default
- **Runtime**: < 1s
- **Cost**: $0.00
- **When**: Every commit

### Sampled Expensive (Tier 3) - 8 of 32 tests
- Random 25% sample of LLM tests
- Daily rotation
- Cache-friendly
- **Runtime**: ~30s
- **Cost**: ~$0.01
- **When**: Nightly CI

### Full Expensive (Tier 4) - 32 tests
- All LLM API tests
- Date extraction, tenure, project IDs
- High cache hit rate
- **Runtime**: ~2min
- **Cost**: ~$0.05
- **When**: Weekly CI, pre-release

### Accuracy Validation (Tier 5) - 4 tests
- Ground truth validation
- Uses real documents
- LLM extraction enabled
- **Runtime**: ~40s
- **Cost**: ~$0.02
- **When**: Weekly, after major changes

### Marker Integration (Tier 6) - 4 tests
- Real PDF to markdown conversion
- Loads 8GB marker models
- Requires significant RAM
- **Runtime**: 1-2min (sequential)
- **Cost**: $0.00 (CPU/RAM only)
- **When**: Nightly CI, pre-release

## Debugging Test Failures

### If fast tests fail

```bash
# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_document_processing.py::test_discover_documents -v

# Show full tracebacks
pytest --tb=long
```

### If expensive tests are needed

```bash
# Run single expensive test for debugging
pytest tests/test_botany_farm_accuracy.py::test_date_extraction_accuracy -v -m ""

# Check API costs after
cat test_costs_report.json
```

### If marker tests are needed

```bash
# Run marker tests sequentially (they load 8GB models)
pytest -m marker -n 0 -v

# Run just markdown helpers (fast, no models)
pytest tests/test_marker_real.py::TestMarkdownHelpers -v -m ""
```

## Cost Tracking

The test suite automatically tracks API costs.

### View Cost Report

After running expensive tests:
```bash
cat test_costs_report.json
```

Example output:
```json
{
  "timestamp": "2025-11-20T15:00:00",
  "duration_seconds": 104.5,
  "total_cost_usd": 0.047,
  "total_api_calls": 12,
  "cached_calls": 8,
  "total_input_tokens": 45000,
  "total_output_tokens": 2500
}
```

### Cost Summary (Printed After Tests)

```
================================================================================
API COST SUMMARY
================================================================================
Total API Calls: 12
  - Real API calls: 4
  - Cached calls: 8
Total Tokens: 47,500
  - Input: 45,000
  - Output: 2,500
Total Cost: $0.0470
Cache Hit Rate: 66.7%
Test Duration: 104.5s
================================================================================
```

## Environment Variables

### API Configuration

```bash
# Required for expensive tests
export ANTHROPIC_API_KEY="your-key"
export LLM_EXTRACTION_ENABLED=true

# Run expensive tests
pytest -m expensive
```

### CI Configuration

```bash
# Enable auto-sampling
export CI=1

# This will sample 25% automatically
pytest -m expensive
```

## Pre-existing Test Failures

The following 5 test failures are known and pre-existing (not related to recent changes):

1. `test_initialize_workflow.py::test_new_session_has_all_workflow_stages`
   - Missing 'complete' workflow stage

2. `test_upload_tools.py::test_detect_existing_session_basic`
   - KeyError: 'existing_session_detected'

3-5. Evidence extraction/report tests
   - "Requirement mapping not complete" errors
   - Workflow stage dependencies not met

These should be addressed separately and are not blockers for normal development.

## Summary: What Command Should I Run?

**For local development:**
```bash
pytest  # Fast tests only, 6s, $0.00
```

**If you accidentally ran expensive tests:**
- You'll see "274 tests collected"
- Takes 200+ seconds
- Costs $0.05+
- **Solution**: Just run `pytest` (no extra flags!)

**For CI/CD:**
- PR checks: `pytest` (fast only)
- Nightly: `pytest -m expensive --sample=0.25` (sampled)
- Weekly: `pytest -m expensive` (full suite)

**Remember:** The default `pytest` command is optimized for speed and cost. Only override markers when you specifically need to run expensive tests.
