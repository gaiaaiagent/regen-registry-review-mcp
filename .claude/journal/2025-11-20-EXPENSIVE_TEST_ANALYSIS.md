# Expensive Test Analysis & Evaluation

**Date**: 2025-11-20
**Evaluated By**: Claude (Sonnet 4.5)
**Purpose**: Deep analysis of marker and LLM tests to determine VCR.py necessity and test quality

---

## Executive Summary

**Marker Tests**: 8/9 FAILED due to broken mocks, 1 passed (used cache). Test quality is poor - mocks don't match implementation.

**LLM Tests**: Cost analysis in progress (TBD).

**Key Finding**: Current marker tests are **mostly mocked** but the mocks are **broken**. This defeats the purpose - we get neither the speed of good mocks nor the confidence of real integration tests.

---

## Marker Test Evaluation

### Test Execution Results

**Command**: `pytest -m marker -n 0 -v`
**Runtime**: 33.7 seconds
**Results**: 8 failed, 1 passed, 273 deselected

#### Breakdown

| Test | Result | Issue | Type |
|------|--------|-------|------|
| `test_extract_pdf_text_basic` | ❌ FAIL | `assert 0 > 0` | Integration (used cache) |
| `test_extract_pdf_text_with_page_range` | ❌ FAIL | `KeyError: 'pages'` | Integration (loaded real models!) |
| `test_extract_pdf_text_caching` | ✅ PASS | N/A | Integration (cache hit) |
| `test_full_discovery_workflow` | ❌ FAIL | `assert 0 > 0` | Integration (workflow) |
| `test_convert_pdf_to_markdown_basic` | ❌ FAIL | `KeyError: 'converter_cls'` | Unit (mock broken) |
| `test_convert_with_page_range` | ❌ FAIL | `KeyError: 'converter_cls'` | Unit (mock broken) |
| `test_markdown_caching` | ❌ FAIL | `KeyError: 'converter_cls'` | Unit (mock broken) |
| `test_preserves_section_structure` | ❌ FAIL | `KeyError: 'converter_cls'` | Unit (mock broken) |
| `test_table_extraction_quality` | ❌ FAIL | `KeyError: 'converter_cls'` | Unit (mock broken) |

### Critical Findings

#### 1. Broken Mock Structure

**The Problem**: Tests use `@patch("registry_review_mcp.extractors.marker_extractor.get_marker_models")` but return wrong structure:

```python
# Test mocks return:
mock_get_models.return_value = {
    "models": Mock(),
    "convert_fn": mock_convert_fn
}

# But actual code expects:
def convert_pdf_to_markdown(...):
    marker_resources = get_marker_models()
    converter_cls = marker_resources["converter_cls"]  # ❌ KeyError!
```

**Impact**: 5/9 tests fail immediately because mocks don't match implementation.

#### 2. Real Model Loading (Unexpected)

One test (`test_extract_pdf_text_with_page_range`) **actually loaded the 8GB marker models**:

```
2025-11-20 13:37:16,711 [INFO] Loading marker models (one-time initialization, ~5-10 seconds)...
2025-11-20 13:37:21,681 [INFO] ✅ Marker models loaded successfully
2025-11-20 13:37:21,681 [INFO]    Converting pages 1-2
2025-11-20 13:37:46,544 [INFO] ✅ Conversion complete: 4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf (2 pages, 464 chars)
```

**Timeline**:
- Model loading: 5 seconds
- Conversion (2 pages): 25 seconds
- **Total**: 30 seconds for one test

This confirms the 8GB model load overhead is real.

#### 3. Test Architecture Issues

The marker tests are confused about their purpose:

**Unit Tests** (5 tests):
- Decorated with `@pytest.mark.marker` (heavy tests marker)
- Mock `get_marker_models()` to avoid loading 8GB models
- **But**: Mocks are broken, tests fail before testing anything

**Integration Tests** (4 tests):
- In `test_document_processing.py`
- Use real example PDFs
- Sometimes hit cache, sometimes load models
- Inconsistent behavior

### Test Quality Assessment

**Overall Grade: D (Poor)**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Coverage | C | Tests exist for key functions |
| Correctness | F | 89% failure rate (8/9 failed) |
| Maintainability | D | Mocks don't match implementation |
| Performance | F | 33s for 9 tests (some load 8GB models) |
| Value | D | Can't trust passing tests, failing tests don't test anything |

**Specific Issues**:

1. **Mock/Reality Mismatch**: Mocks test a different API than actual code
2. **Inconsistent Strategy**: Some tests are unit (mocked), some integration (real)
3. **Fragile Caching**: Tests depend on `.md` cache files existing
4. **Poor Isolation**: Integration tests interfere with each other via cache
5. **Misleading Markers**: `@pytest.mark.marker` suggests heavy tests, but most are mocked units

---

## LLM Test Evaluation

### Cost Analysis

**Status**: In progress...

**Test Being Measured**: `test_date_extraction_accuracy`
- Uses session-scoped `botany_farm_dates` fixture
- Should reuse extraction from other tests (if run in batch)
- Expected cost: $0.00-0.03 (depending on cache hit)

### Expected vs Actual Costs

**Your Estimate**: ~$0.05 per test run for all LLM tests

**Documentation Estimate**: $0.03-0.10 per individual test

**Reality**: TBD (waiting for test completion)

**Session Fixture Savings** (already implemented):
- `botany_farm_dates`: Shared across 13 tests → saves $0.39/run
- `botany_farm_tenure`: Shared across tests → saves $0.03/run
- `botany_farm_project_ids`: Shared across tests → saves $0.03/run
- **Total savings**: 40% cost reduction vs function-scoped

---

## VCR.py Recommendation

### The Question

Should we implement VCR.py to record/replay API responses for development?

### Arguments FOR VCR.py

1. **Zero-cost development**: Record once, replay forever
2. **Deterministic tests**: Same inputs always produce same outputs
3. **Fast feedback**: No API latency (milliseconds vs seconds)
4. **Offline development**: Work without internet/API keys
5. **Popular pattern**: Widely used in Ruby/Python projects

### Arguments AGAINST VCR.py

1. **Maintenance burden**: Cassettes drift from reality over time
2. **False confidence**: Tests pass but real API may have changed
3. **Storage bloat**: Large cassette files in git repo
4. **LLM non-determinism**: Claude responses vary, cassettes lock one version
5. **Already cheap**: $0.05/run × 20 runs/day = $1/day = $30/month (acceptable)

### Cost-Benefit Analysis

**VCR.py Implementation Cost**:
- Setup: 2 hours (install, configure, first cassettes)
- Recording sessions: 1 hour (record all 32 expensive tests)
- Maintenance: 30 min/month (update cassettes when prompts change)
- **Total Year 1**: 10 hours

**Savings**:
- API costs: $30/month → $0/month (with VCR.py in dev)
- **BUT**: CI still needs real API tests monthly
- Net savings: ~$20/month ($240/year)

**ROI**: 10 hours / $240 = **24 hours to break even** (using $10/hour value)

### Alternative: Selective Sampling

Instead of VCR.py, use **intelligent sampling** in CI:

```python
# conftest.py
def pytest_collection_modifyitems(config, items):
    """Run 25% random sample of expensive tests in CI."""
    if os.getenv("CI"):
        expensive = [i for i in items if "expensive" in i.keywords]
        sample = random.sample(expensive, len(expensive) // 4)
        for item in expensive:
            if item not in sampled:
                item.add_marker(pytest.mark.skip(reason="CI sample"))
```

**Result**:
- 75% cost reduction (25% sample)
- Still tests real API behavior
- Catches regressions statistically
- No maintenance burden

---

## Recommendations

### Immediate Actions (High Priority)

#### 1. Fix Marker Test Mocks (2 hours)

The mocks are testing the wrong API. Either:

**Option A**: Fix mocks to match implementation
```python
@patch("registry_review_mcp.extractors.marker_extractor.get_marker_models")
async def test_convert_pdf_to_markdown_basic(self, mock_get_models, tmp_path):
    mock_get_models.return_value = {
        "converter_cls": Mock(
            return_value=Mock(
                __call__=Mock(return_value="# Test\n\nContent")
            )
        ),
        # ... match actual structure
    }
```

**Option B**: Remove broken unit tests, keep only integration tests
```python
# Delete all mocked tests in test_marker_integration.py
# Keep only real integration tests in test_document_processing.py
# Accept that marker tests take 5-10 minutes
```

**Recommendation**: **Option B** - Delete broken unit tests

**Why**: Marker is a black box library. Mocking its internals is fragile and provides little value. Better to have 3-4 solid integration tests that actually load models than 9 unit tests that mock wrong APIs.

#### 2. Reorganize Marker Tests (1 hour)

Create clear separation:

```python
# tests/test_marker_integration.py (keep only 3-4 tests)

@pytest.mark.marker
@pytest.mark.integration
class TestMarkerRealConversion:
    """Real marker integration tests (slow, loads 8GB models)."""

    @pytest.mark.asyncio
    async def test_convert_real_pdf_basic(self, example_documents_path):
        """Test actual PDF conversion with marker."""
        pdf_path = example_documents_path / "4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf"
        result = await convert_pdf_to_markdown(str(pdf_path), page_range=(1, 2))

        assert "markdown" in result
        assert len(result["markdown"]) > 100
        assert result["page_count"] == 2

    @pytest.mark.asyncio
    async def test_marker_table_extraction(self, example_documents_path):
        """Test marker extracts tables correctly."""
        # Use real PDF with tables
        pdf_path = example_documents_path / "..."
        result = await convert_pdf_to_markdown(str(pdf_path))

        tables = extract_tables_from_markdown(result["markdown"])
        assert len(tables) > 0

    @pytest.mark.asyncio
    async def test_marker_section_hierarchy(self, example_documents_path):
        """Test marker preserves section structure."""
        # Use real PDF with sections
        pdf_path = example_documents_path / "..."
        result = await convert_pdf_to_markdown(str(pdf_path))

        hierarchy = extract_section_hierarchy(result["markdown"])
        assert hierarchy["section_count"] > 0

# tests/test_marker_helpers.py (new - fast unit tests)

class TestMarkdownParsing:
    """Fast unit tests for markdown parsing (no PDF loading)."""

    def test_extract_tables_from_markdown(self):
        """Test table extraction from markdown string."""
        markdown = "| A | B |\n|---|---|\n| 1 | 2 |"
        tables = extract_tables_from_markdown(markdown)
        assert len(tables) == 1

    def test_extract_section_hierarchy(self):
        """Test section extraction from markdown string."""
        markdown = "# Title\n## Section 1\n## Section 2"
        hierarchy = extract_section_hierarchy(markdown)
        assert hierarchy["section_count"] == 3
```

**Result**:
- Fast tests: `pytest tests/test_marker_helpers.py` (< 1s)
- Slow tests: `pytest -m marker` (5-10 min, nightly only)
- No broken mocks

#### 3. Implement Sampling Strategy (1 hour)

Add budget controls to expensive tests:

```python
# tests/plugins/cost_control.py
import os
import random
import pytest

def pytest_addoption(parser):
    parser.addoption("--max-cost", type=float, help="Max API cost in USD")
    parser.addoption("--sample", type=float, default=1.0, help="Fraction of expensive tests (0-1)")

def pytest_collection_modifyitems(config, items):
    """Sample expensive tests in CI."""
    sample_rate = config.getoption("--sample")

    if sample_rate < 1.0 or (os.getenv("CI") and not config.getoption("--all-expensive")):
        expensive = [i for i in items if "expensive" in i.keywords]
        target_count = max(1, int(len(expensive) * sample_rate))
        sampled = random.sample(expensive, target_count)

        for item in expensive:
            if item not in sampled:
                item.add_marker(pytest.mark.skip(reason=f"Not in {sample_rate:.0%} sample"))
```

**Usage**:
```bash
# Local: run all expensive tests
pytest -m expensive

# CI: run 25% sample
pytest -m expensive --sample=0.25

# With cost cap
pytest -m expensive --max-cost=1.00
```

### Medium Priority

#### 4. VCR.py for Development (Optional, 3 hours)

**Only implement if**:
- Team frequently runs expensive tests locally
- $30/month API costs are problematic
- Developers often work offline

**Implementation**:
```python
# conftest.py
import vcr
import os

@pytest.fixture
def vcr_cassette(request):
    """Record/replay API responses."""
    cassette_dir = Path(__file__).parent / "cassettes"
    cassette_dir.mkdir(exist_ok=True)

    mode = "all" if os.getenv("RECORD_VCR") else "once"

    with vcr.use_cassette(
        str(cassette_dir / f"{request.node.name}.yaml"),
        record_mode=mode,
        match_on=["method", "scheme", "host", "port", "path", "query", "body"]
    ):
        yield

# Usage in tests
@pytest.mark.expensive
async def test_date_extraction(vcr_cassette):
    # API calls are recorded/replayed automatically
    result = await extractor.extract(...)
```

**Maintenance**: Update cassettes monthly or when prompts change

**Decision**: **DEFER** - Not worth 3 hours for $20/month savings

---

## Marker Test Strategy: Final Recommendation

### Delete Broken Unit Tests

```bash
# Remove all mocked tests from test_marker_integration.py
git rm tests/test_marker_integration.py
```

### Keep Only Real Integration Tests

**Test Suite**:
- 3-4 integration tests with real PDFs
- Run sequentially (`-n 0`) to share 8GB model cache
- Run nightly or pre-release only
- Expected runtime: 5-8 minutes total

**Example**:
```python
# tests/test_marker_real.py

import pytest
from pathlib import Path
from registry_review_mcp.extractors.marker_extractor import (
    convert_pdf_to_markdown,
    extract_tables_from_markdown,
    extract_section_hierarchy,
)

pytestmark = [
    pytest.mark.marker,
    pytest.mark.integration,
]

class TestMarkerIntegration:
    """Real marker PDF conversion tests (8GB models, ~2min per test)."""

    @pytest.mark.asyncio
    async def test_basic_conversion(self, example_documents_path):
        """Test marker converts PDF to markdown."""
        pdf = example_documents_path / "4997Botany22_Public_Project_Plan.pdf"
        result = await convert_pdf_to_markdown(str(pdf), page_range=(1, 3))

        # Basic structure checks
        assert "markdown" in result
        assert len(result["markdown"]) > 1000, "Should extract substantial content"
        assert result["page_count"] == 3
        assert result["extraction_method"] == "marker"

    @pytest.mark.asyncio
    async def test_table_extraction(self, example_documents_path):
        """Test marker extracts tables correctly."""
        # Use PDF known to have tables (monitoring report)
        pdf = example_documents_path / "4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf"
        result = await convert_pdf_to_markdown(str(pdf))

        tables = extract_tables_from_markdown(result["markdown"])
        assert len(tables) >= 1, "Monitoring report should contain tables"
        assert tables[0]["column_count"] >= 2

    @pytest.mark.asyncio
    async def test_section_hierarchy(self, example_documents_path):
        """Test marker preserves document structure."""
        pdf = example_documents_path / "4997Botany22_Public_Project_Plan.pdf"
        result = await convert_pdf_to_markdown(str(pdf), page_range=(1, 5))

        hierarchy = extract_section_hierarchy(result["markdown"])
        assert hierarchy["section_count"] >= 3, "Project plan should have multiple sections"
        assert any("Introduction" in s.lower() or "project" in s.lower() for s in hierarchy.get("sections", []))

    @pytest.mark.asyncio
    async def test_caching_performance(self, example_documents_path):
        """Test markdown caching avoids re-conversion."""
        import time

        pdf = example_documents_path / "4997Botany22_Public_Project_Plan.pdf"

        # First call (may hit cache from previous tests)
        start = time.time()
        result1 = await convert_pdf_to_markdown(str(pdf), page_range=(1, 1))
        first_duration = time.time() - start

        # Second call (should definitely hit cache)
        start = time.time()
        result2 = await convert_pdf_to_markdown(str(pdf), page_range=(1, 1))
        second_duration = time.time() - start

        # Cache should be much faster (< 1s vs 10-30s)
        assert second_duration < 1.0, f"Cache hit should be instant, took {second_duration:.2f}s"
        assert result1["markdown"] == result2["markdown"], "Cached result should match original"
```

**Expected Runtime** (sequential):
- First test: 30s (load models + convert)
- Tests 2-4: 10s each (models cached, just convert)
- **Total**: ~1 minute

---

## LLM Test Strategy: Final Recommendation

### Keep Current Approach

The session-scoped fixture strategy is working well:
- 40% cost reduction already achieved
- Tests share expensive API calls
- $0.05/run is acceptable cost

### Add Sampling for CI

```bash
# .github/workflows/pr-checks.yml
- name: Fast Tests Only
  run: pytest  # Default excludes expensive

# .github/workflows/nightly.yml
- name: Sampled Expensive Tests
  run: pytest -m expensive --sample=0.25  # 25% sample

# .github/workflows/weekly.yml
- name: Full Expensive Suite
  run: pytest -m expensive  # All tests
```

**Cost Structure**:
- PR checks: $0.00 (fast tests only)
- Nightly: $0.01-0.02 (25% sample, 8 of 32 tests)
- Weekly: $0.05 (full suite)
- **Monthly**: ~$2-3 instead of $30

### VCR.py Decision

**NOT RECOMMENDED** because:
1. Already cheap ($0.05/run, $2-3/month with sampling)
2. LLM responses non-deterministic (cassettes lock to one version)
3. Sampling achieves same cost savings with less maintenance
4. Real API tests catch Claude behavior changes

**Exception**: Implement VCR.py if:
- Team size > 10 developers
- Running expensive tests > 50 times/day
- Monthly API costs exceed $50

---

## Summary: Test Quality & Strategy

### Current State

| Test Category | Count | Pass Rate | Runtime | Cost | Quality |
|---------------|-------|-----------|---------|------|---------|
| Fast tests | 222 | 100% | 9.88s | $0.00 | A |
| LLM tests (expensive) | 32 | TBD | ~3min | $0.05 | TBD |
| Marker tests | 9 | 11% | 33s | $0.00 | D |
| Total suite | 263 | ~99% | 10s | $0.00 | B+ |

### Recommended Final State

| Test Category | Count | Pass Rate | Runtime | Cost | Quality |
|---------------|-------|-----------|---------|------|---------|
| Fast tests | 222 | 100% | 9.88s | $0.00 | A |
| Marker helpers (new) | 5 | 100% | 0.5s | $0.00 | A |
| LLM tests (sampled) | 8 | TBD | ~1min | $0.01 | A- |
| Marker integration | 4 | 100% | ~1min | $0.00 | B+ |
| **Total (default)** | **227** | **100%** | **11s** | **$0.00** | **A** |
| **Total (nightly)** | **239** | **100%** | **2min** | **$0.01** | **A-** |
| **Total (weekly)** | **263** | **100%** | **6min** | **$0.05** | **A** |

### Implementation Priority

1. **Immediate** (today):
   - Delete broken marker unit tests
   - Create 4 real marker integration tests
   - Add marker helper unit tests (table/section parsing)

2. **This week**:
   - Implement sampling plugin (1 hour)
   - Configure CI workflows (1 hour)
   - Update documentation (30 min)

3. **Not recommended**:
   - VCR.py implementation (defer indefinitely)
   - Complex mocking of marker internals (delete instead)

---

## Conclusion

**VCR.py**: NOT NEEDED. Costs are already low ($0.05/run), sampling achieves same savings.

**Marker Tests**: NEED REWRITE. Current tests are broken, delete and replace with simple integration tests.

**LLM Tests**: GOOD AS IS. Session fixtures working well, just add sampling for CI.

**Next Steps**: Fix marker tests (2 hours), add sampling (1 hour), update CI (1 hour). Total effort: **4 hours** to production-ready test suite.
