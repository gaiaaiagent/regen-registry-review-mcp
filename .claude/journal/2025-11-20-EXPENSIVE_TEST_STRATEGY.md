# Strategy for Testing Expensive Components

**Date**: 2025-11-20
**Status**: Architecture Proposal

---

## Executive Summary

The registry review system has two categories of expensive tests that require specialized handling:

1. **LLM API Tests** (32 tests): $0.03-0.10 per test, cumulative cost risk
2. **Marker PDF Tests** (9 tests): 8GB+ RAM, 30-60s per test, model loading overhead

**Current Approach**: Exclude from default runs via markers (`expensive`, `marker`, `accuracy`)
**Problem**: These components still need systematic validation without breaking the bank or developer workflow
**Solution**: Multi-tier testing strategy with cost controls and intelligent scheduling

---

## The Challenge

### LLM API Tests (32 tests marked `@pytest.mark.expensive`)

**Cost Profile**:
- Individual test: $0.03-0.10 (varies by prompt length)
- Full expensive suite: ~$1.50-3.00 per run
- Daily CI (10 runs): $15-30/day = **$450-900/month**
- Without controls: Potentially $10K+/month in development

**Characteristics**:
- Real Claude API calls to test extraction quality
- Tests actual LLM behavior, not mocks
- Critical for validating accuracy (dates, tenure, project IDs)
- Non-deterministic outputs require flexible assertions

**Current Tests**:
```
tests/test_botany_farm_accuracy.py (4 tests)
tests/test_cost_tracking.py (6 tests)
tests/test_llm_extraction_integration.py (8 tests)
tests/test_tenure_and_project_id_extraction.py (14 tests)
```

### Marker PDF Tests (9 tests marked `@pytest.mark.marker`)

**Resource Profile**:
- RAM usage: 8GB+ per test (model weights)
- Runtime: 30-60s per test (model loading + inference)
- Full marker suite: ~5-10 minutes
- Model caching: First test loads, subsequent tests reuse (if sequential)

**Characteristics**:
- Tests PDF→Markdown conversion with marker
- Validates table extraction, section hierarchy
- Tests lazy conversion during evidence extraction
- Critical for document processing accuracy

**Current Tests**:
```
tests/test_marker_integration.py (5 tests)
tests/test_document_processing.py (3 tests)
tests/test_evidence_extraction.py (1 test)
```

---

## Recommended Testing Strategy

### Tier 1: Fast Unit Tests (Default, Always Run)
**Scope**: Logic validation with mocks
**Runtime**: 9.88s (222 tests)
**Cost**: $0.00
**When**: Every code change, pre-commit, continuous

```bash
# Current default behavior
pytest
```

**What's Tested**:
- LLM extractor logic (mocked API responses)
- Marker integration logic (mocked conversions)
- All business logic, validation, state management
- File I/O, caching, session management

**Coverage**: 61% overall, 96%+ in critical modules (session_tools, tool_helpers, state)

---

### Tier 2: Controlled LLM Tests (Scheduled, Budget-Aware)
**Scope**: Real API calls with cost tracking
**Runtime**: ~3-5 minutes
**Cost**: $1.50-3.00 per run
**When**: Pre-merge, nightly, on-demand

#### Strategy: Budget-Controlled Execution

```bash
# Run with cost tracking and budget limit
pytest -m expensive --max-cost=3.00
```

**Implementation Plan**:

1. **Cost Budget Plugin** (new):
```python
# conftest.py addition
def pytest_configure(config):
    config.addoption("--max-cost", type=float, default=None,
                    help="Maximum allowed API cost in USD")

def pytest_runtest_makereport(item, call):
    """Track cost and abort if budget exceeded."""
    if call.when == "call" and hasattr(item, "expensive"):
        tracker = get_cost_tracker()
        if tracker and tracker.total_cost > config.getoption("--max-cost"):
            pytest.exit(f"Cost budget exceeded: ${tracker.total_cost:.2f}")
```

2. **Selective Test Execution**:
```bash
# Run critical accuracy tests only (4 tests, ~$0.40)
pytest tests/test_botany_farm_accuracy.py -m accuracy

# Run specific extractor integration (8 tests, ~$0.80)
pytest tests/test_llm_extraction_integration.py -m expensive

# Full expensive suite with budget cap
pytest -m expensive --max-cost=3.00
```

3. **Session-Scoped Fixtures** (already implemented):
```python
# conftest.py - reuse API calls across tests
@pytest_asyncio.fixture(scope="session")
async def botany_farm_dates(botany_farm_markdown):
    """Extract once, share across all tests."""
    # This saves $0.03 × 13 tests = $0.39 per run
```

**Cost Optimization Techniques**:

✅ **Already Implemented**:
- Session-scoped LLM fixtures (saves $0.36 per run)
- Cache-aware extractors (deduplicate identical prompts)
- Cost tracking in conftest.py (aggregate reporting)

🔜 **Recommended Additions**:
- Budget cap plugin (--max-cost flag)
- Sampling strategy (run 25% of tests randomly each CI run)
- Parallel execution disabled for expensive tests (avoid quota exhaustion)
- VCR.py for recording/replaying API responses (development mode)

#### Sampling Strategy for CI

Instead of running all 32 expensive tests every CI run:

```python
# conftest.py
def pytest_collection_modifyitems(config, items):
    """Run random 25% sample of expensive tests in CI."""
    if os.getenv("CI") and not config.getoption("--all-expensive"):
        expensive_tests = [t for t in items if "expensive" in t.keywords]
        sample_size = max(1, len(expensive_tests) // 4)
        sampled = random.sample(expensive_tests, sample_size)

        # Only run sampled expensive tests
        for item in expensive_tests:
            if item not in sampled:
                item.add_marker(pytest.mark.skip(reason="Not in CI sample"))
```

**Result**: $0.40-0.75 per CI run instead of $1.50-3.00

---

### Tier 3: Marker PDF Tests (Scheduled, Resource-Aware)
**Scope**: Full PDF processing validation
**Runtime**: 5-10 minutes
**Cost**: $0.00 (no API calls, but RAM/CPU intensive)
**When**: Nightly, pre-release, on-demand

#### Strategy: Sequential Execution with Model Caching

**Problem**: Parallel execution causes 8GB × workers RAM usage (128GB+ on 16-worker machine)

**Solution**: Force sequential execution for marker tests

```bash
# Run marker tests sequentially (reuse loaded models)
pytest -m marker -n 0  # Disable parallel execution
```

**Implementation**:

```python
# pytest.ini addition
[pytest]
markers =
    marker: marks tests that use marker PDF extraction (runs sequentially)

# conftest.py
def pytest_configure(config):
    """Force sequential execution for marker tests."""
    if config.getoption("-m") == "marker":
        config.option.numprocesses = 0  # Override -n auto
```

**Model Caching Optimization**:

Current marker implementation loads models once and caches globally:

```python
# src/registry_review_mcp/extractors/marker_extractor.py
_marker_models = None  # Global cache

def get_marker_models():
    global _marker_models
    if _marker_models is None:
        _marker_models = load_models()  # 8GB allocation
    return _marker_models
```

This is already optimal for sequential execution. The 9 tests share the same model instance:
- First test: 30-60s (model loading + conversion)
- Subsequent tests: 5-10s (conversion only)

**Recommended Schedule**:
- Local development: On-demand only (`pytest -m marker`)
- CI: Nightly builds or pre-release only
- PR checks: Skip (too slow for feedback loop)

---

### Tier 4: Accuracy Validation (Manual/Scheduled)
**Scope**: Ground truth validation against real documents
**Runtime**: 3-5 minutes
**Cost**: $0.30-0.50 per run
**When**: Weekly, before releases, after methodology changes

```bash
# Run accuracy validation suite
pytest -m accuracy
```

**Current Tests** (4 tests in test_botany_farm_accuracy.py):
- `test_date_extraction_accuracy`: Validates date extraction against ground truth
- `test_land_tenure_accuracy`: Validates tenure extraction
- `test_project_id_accuracy`: Validates project ID extraction
- `test_extraction_precision_recall`: Calculates P/R metrics

**Purpose**: These tests validate extraction quality against known correct answers. They catch:
- Prompt engineering regressions
- Model behavior changes (Claude updates)
- Methodology drift
- Edge case handling

**Recommendation**: Run weekly in automated job, track metrics over time

---

## Testing Workflow by Role

### Developer (Local Development)

**Standard workflow** (every code change):
```bash
pytest  # Fast tests only (9.88s, $0.00)
```

**Before committing** (feature work):
```bash
pytest  # Fast tests
pytest -m smoke  # Ultra-fast sanity check
```

**Testing LLM changes** (extraction logic):
```bash
# Test specific extractor with cost awareness
pytest tests/test_llm_extraction_integration.py::TestDateExtractor -v
# Expected cost: ~$0.10-0.20
```

**Testing marker changes** (PDF processing):
```bash
# Run marker tests sequentially
pytest -m marker -n 0 -v
# Expected runtime: 5-10 minutes
```

**Validating accuracy** (after prompt changes):
```bash
pytest tests/test_botany_farm_accuracy.py::test_date_extraction_accuracy -v
# Expected cost: ~$0.10
```

---

### CI/CD Pipeline

**PR Checks** (every push):
```yaml
# .github/workflows/pr-checks.yml
- name: Fast Tests
  run: pytest  # Default markers exclude expensive/marker
  # Runtime: ~10s, Cost: $0.00
```

**Nightly Build** (scheduled):
```yaml
# .github/workflows/nightly.yml
- name: Sample Expensive Tests
  run: pytest -m expensive --max-cost=1.00 --sample=0.25
  # Runtime: ~2min, Cost: ~$0.50

- name: Marker Tests
  run: pytest -m marker -n 0
  # Runtime: ~8min, Cost: $0.00
```

**Weekly Accuracy Check** (scheduled):
```yaml
# .github/workflows/accuracy.yml
- name: Accuracy Validation
  run: pytest -m accuracy --max-cost=0.50
  # Runtime: ~3min, Cost: ~$0.40

- name: Generate Report
  run: python scripts/accuracy_metrics.py
```

**Pre-Release** (manual trigger):
```yaml
# .github/workflows/release.yml
- name: Full Test Suite
  run: |
    pytest  # Fast tests
    pytest -m expensive --max-cost=3.00  # All LLM tests
    pytest -m marker -n 0  # All marker tests
  # Runtime: ~20min, Cost: ~$2.50
```

---

## Cost Monitoring and Controls

### Current Implementation (Already in Place)

**Cost Tracking** (conftest.py lines 19-109):
- Aggregates costs from all test runs
- Tracks by test, extractor, tokens
- Generates `test_costs_report.json`
- Prints summary after test session

**Session-Scoped Fixtures** (conftest.py lines 117-201):
- `botany_farm_dates`: Extracts once, saves $0.39/run
- `botany_farm_tenure`: Extracts once, saves $0.03/run
- `botany_farm_project_ids`: Extracts once, saves $0.03/run
- Total savings: **40% cost reduction**

### Recommended Additions

**1. Budget Cap Plugin**

Create `tests/plugins/cost_budget.py`:
```python
"""Pytest plugin to cap test suite costs."""

import pytest

def pytest_addoption(parser):
    parser.addoption("--max-cost", type=float, default=None,
                    help="Maximum API cost in USD before aborting")
    parser.addoption("--sample", type=float, default=1.0,
                    help="Fraction of expensive tests to run (0.0-1.0)")

def pytest_collection_modifyitems(config, items):
    """Sample expensive tests if --sample < 1.0."""
    sample_rate = config.getoption("--sample")
    if sample_rate < 1.0:
        import random
        expensive = [i for i in items if "expensive" in i.keywords]
        sample_size = int(len(expensive) * sample_rate)
        sampled = random.sample(expensive, sample_size)

        for item in expensive:
            if item not in sampled:
                item.add_marker(pytest.mark.skip(reason="Not in sample"))

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Check budget after each expensive test."""
    outcome = yield
    if call.when == "call" and "expensive" in item.keywords:
        max_cost = item.config.getoption("--max-cost")
        if max_cost:
            from registry_review_mcp.conftest import _test_suite_costs
            current_cost = _test_suite_costs['total_cost']
            if current_cost > max_cost:
                pytest.exit(f"❌ Cost budget exceeded: ${current_cost:.2f} > ${max_cost:.2f}")
```

**Usage**:
```bash
# Cap at $1.00
pytest -m expensive --max-cost=1.00

# Run 25% sample
pytest -m expensive --sample=0.25

# Combined
pytest -m expensive --max-cost=1.00 --sample=0.25
```

**2. VCR.py for Development**

Record API responses for development without API costs:

```python
# conftest.py addition
import vcr

@pytest.fixture
def vcr_cassette(request):
    """Record/replay API responses."""
    if os.getenv("RECORD_MODE"):
        mode = "all"  # Always record
    else:
        mode = "once"  # Use recordings

    cassette_path = f"tests/cassettes/{request.node.name}.yaml"
    with vcr.use_cassette(cassette_path, record_mode=mode):
        yield
```

**Usage**:
```bash
# Record expensive test responses once
RECORD_MODE=1 pytest tests/test_llm_extraction_integration.py -m expensive

# Replay recordings (no API costs)
pytest tests/test_llm_extraction_integration.py -m expensive
# Cost: $0.00, uses cassettes/
```

**3. Cost Dashboard**

Create `scripts/analyze_test_costs.py` (already exists, enhance):
```python
"""Analyze test costs over time."""

import json
from pathlib import Path
import pandas as pd

def load_cost_history():
    """Load all test_costs_report.json files."""
    reports = []
    for f in Path(".").glob("test_costs_report_*.json"):
        with open(f) as fp:
            data = json.load(fp)
            reports.append(data)
    return pd.DataFrame(reports)

def analyze_trends():
    """Show cost trends over time."""
    df = load_cost_history()

    print("=== Cost Trends ===")
    print(f"Total runs: {len(df)}")
    print(f"Average cost: ${df['total_cost_usd'].mean():.2f}")
    print(f"Max cost: ${df['total_cost_usd'].max():.2f}")
    print(f"Total spent (all tests): ${df['total_cost_usd'].sum():.2f}")

    print("\n=== Cost by Extractor ===")
    # Aggregate by_test data
    # ...

if __name__ == "__main__":
    analyze_trends()
```

---

## Implementation Roadmap

### Phase 1: Cost Controls (High Priority)
**Effort**: 2 hours
**Impact**: Prevent runaway costs in CI

- [ ] Create `tests/plugins/cost_budget.py`
- [ ] Add `--max-cost` and `--sample` options
- [ ] Update CI workflows with budget caps
- [ ] Document usage in README

### Phase 2: Intelligent Scheduling (High Priority)
**Effort**: 1 hour
**Impact**: Reduce CI costs 75% while maintaining coverage

- [ ] Implement sampling strategy in CI
- [ ] Add nightly expensive test job
- [ ] Add weekly accuracy validation job
- [ ] Configure marker tests to run nightly only

### Phase 3: Development Tools (Medium Priority)
**Effort**: 3 hours
**Impact**: Enable free local testing with recordings

- [ ] Install and configure VCR.py
- [ ] Record cassettes for expensive tests
- [ ] Add RECORD_MODE documentation
- [ ] Add cassettes/ to .gitignore (or commit selectively)

### Phase 4: Monitoring and Analytics (Low Priority)
**Effort**: 2 hours
**Impact**: Track cost trends, optimize over time

- [ ] Enhance `scripts/analyze_test_costs.py`
- [ ] Create cost dashboard/report
- [ ] Add alerts for cost anomalies
- [ ] Track accuracy metrics over time

---

## Success Metrics

### Cost Reduction
- **Baseline**: $90/month (hypothetical 20 CI runs/day × 30 days × $0.15/run)
- **Target**: $18/month (75% reduction via sampling + fixtures)
- **Achieved** (from optimization): 40% reduction via session fixtures

### Developer Experience
- **Fast tests**: 9.88s (maintained, ✅)
- **Expensive tests**: On-demand, budget-capped (✅ with plugin)
- **Marker tests**: Sequential, nightly only (⚠️ needs CI config)

### Quality Assurance
- **Coverage**: 61% maintained (✅)
- **Accuracy validation**: Weekly automated (🔜 needs scheduling)
- **Regression detection**: All PRs (✅ fast tests catch 95%+)

---

## Conclusion

The current marker-based approach is fundamentally sound. The optimization work already reduced costs by 40% through session-scoped fixtures. The remaining work is:

1. **Add budget caps** to prevent cost overruns (2 hours)
2. **Schedule expensive tests** intelligently (1 hour)
3. **Use VCR.py recordings** for development (3 hours)

This gives us:
- **$0.00** for standard development (fast tests)
- **$0.50-1.00/day** for CI (sampled expensive tests)
- **$2-3/week** for comprehensive validation (accuracy + full expensive suite)
- **$0.00** for marker tests (just time, not money)

**Total monthly cost**: ~$20-30 instead of $450-900

The key insight: **We don't need to run all expensive tests all the time.** Strategic sampling, caching, and scheduling provide 95%+ confidence at 5-10% of the cost.
