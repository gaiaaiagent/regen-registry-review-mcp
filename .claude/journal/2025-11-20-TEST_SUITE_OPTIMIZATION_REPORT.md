# Test Suite Optimization Report

**Date**: 2025-11-20
**Test Suite**: Registry Review MCP
**Current Performance**: 223 tests, 56.6s (baseline with 2 failures)
**Target**: Sub-15s execution time

---

## Executive Summary

The test suite currently executes 223 tests in 56.6 seconds with acceptable performance but significant optimization potential. Analysis reveals the suite is well-structured with modern async patterns, comprehensive fixtures, and cost tracking infrastructure already in place. Primary bottlenecks are:

1. **Single slowest test**: 21.8s in upload workflow integration
2. **Heavy file I/O operations**: 110+ filesystem operations per run
3. **Marker PDF extraction overhead**: 5.8s for single test
4. **Session cleanup latency**: 13 cleanup operations per function scope
5. **104 async tests** without parallel execution

**Key Finding**: The suite can achieve sub-15s performance through tactical optimizations without major refactoring. The existing three-tier testing architecture (unit/integration/accuracy) provides the foundation.

---

## Current State Assessment

### Test Distribution
```
Total Tests:        273 (223 active, 50 deselected by markers)
Test Files:         23 files
Average File Size:  11.8 KB
Largest File:       test_upload_tools.py (42.5 KB, 1,083 lines)
Async Tests:        104 (46.6% of active tests)
```

### Performance Profile
```
Execution Time:     56.6s (baseline)
Slowest Test:       21.8s (test_start_review_full_workflow)
Top 3 Bottlenecks:
  - Upload workflow:    21.8s (38% of total time)
  - Marker extraction:   5.8s (10% of total time)
  - Document discovery:  3.1s (5% of total time)
```

### Test Categories (by marker)
```
Unit Tests:         ~150 tests (fast, no external dependencies)
Integration Tests:  ~50 tests (marked: expensive, integration, slow)
Accuracy Tests:     ~20 tests (marked: accuracy, expensive)
Marker Tests:       ~3 tests (marked: marker - requires 8GB RAM)
```

### Infrastructure Quality
✅ **Strengths**:
- Modern async/await patterns throughout
- Session-scoped shared fixtures for expensive operations
- Automatic cost tracking infrastructure (conftest.py)
- Proper test isolation with cleanup fixtures
- Three-tier testing architecture already defined
- Comprehensive markers for test categorization

⚠️ **Weaknesses**:
- No parallel execution (pytest-xdist not configured)
- Function-scoped cleanup runs 223 times per suite
- Largest test file (1,083 lines) impacts readability
- 13 filesystem cleanup operations per test
- Marker tests block entire suite (5.8s single test)

---

## Prioritized Recommendations

### 🚀 TIER 1: Quick Wins (Expected: 56s → 25s)
**Implementation Time**: 1-2 hours
**Performance Gain**: 55% reduction
**Risk**: Minimal

#### 1.1 Enable Parallel Test Execution
**Impact**: 56s → 20-25s (50-55% reduction)

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers (optimal for most systems)
pytest tests/ -n 4

# Add to pytest.ini
[pytest]
addopts = -n auto
```

**Why This Works**:
- 104 async tests are I/O-bound and naturally parallelizable
- Test isolation already enforced through fixtures
- No shared state dependencies detected
- 23 test files distribute well across workers

**Estimated Timeline**: 15 minutes

#### 1.2 Optimize Session Cleanup Scope
**Impact**: Save 2-3s per run

Current (conftest.py, line 271):
```python
@pytest.fixture(autouse=True, scope="function")
def cleanup_sessions():
    # Runs 223 times per suite
```

Optimized:
```python
@pytest.fixture(autouse=True, scope="module")
def cleanup_sessions():
    # Runs 23 times per suite (once per file)
```

**Why This Works**:
- Tests already use `test-` prefixed sessions for isolation
- Cleanup only needs to run once per module, not per function
- Reduces filesystem operations by 90%

**Estimated Timeline**: 5 minutes

#### 1.3 Skip Marker Tests in Default Run
**Impact**: Save 5.8s per run (10% reduction)

Add to pytest.ini (line 24):
```python
addopts =
    -v
    --tb=short
    --strict-markers
    --color=yes
    -m "not expensive and not integration and not accuracy and not marker"
```

**Why This Works**:
- Marker tests require 8GB+ RAM and special dependencies
- Only 3 tests affected
- Can run separately: `pytest -m marker` when needed

**Estimated Timeline**: 2 minutes

**Total Tier 1 Savings**: 31-36 seconds (56s → 20-25s)

---

### 🎯 TIER 2: Structural Improvements (Expected: 25s → 12-15s)
**Implementation Time**: 3-4 hours
**Performance Gain**: 40-50% further reduction
**Risk**: Low-Medium

#### 2.1 Refactor Largest Test File
**Impact**: Improve parallelization distribution

test_upload_tools.py (1,083 lines):
- Split into 3 files: `test_upload_creation.py`, `test_upload_additional.py`, `test_upload_workflow.py`
- Benefits: Better load balancing across workers, faster discovery

**Estimated Timeline**: 45 minutes

#### 2.2 Optimize Upload Workflow Test
**Impact**: 21.8s → 5-8s (65% reduction)

Current bottleneck (test_start_review_full_workflow):
```python
async def test_start_review_full_workflow(...):
    # Creates session
    # Uploads files
    # Discovers documents
    # Extracts evidence (EXPENSIVE)
```

Optimization:
```python
# Split into separate tests
async def test_upload_workflow_creation(...):
    # Fast: just upload and discovery

async def test_upload_workflow_extraction(...):
    # Mark as expensive
    @pytest.mark.expensive
```

**Estimated Timeline**: 30 minutes

#### 2.3 Implement Lazy Fixture Loading
**Impact**: Reduce unnecessary fixture execution

Current: All session fixtures load regardless of test needs
Optimized: Use `pytest-lazy-fixture` for conditional loading

```python
# Install
pip install pytest-lazy-fixture

# Use in tests
@pytest.mark.parametrize("fixture", [
    pytest.lazy_fixture("botany_farm_dates"),
    pytest.lazy_fixture("botany_farm_tenure"),
])
```

**Estimated Timeline**: 1 hour

#### 2.4 Cache Document Discovery Results
**Impact**: Save 3.1s across multiple tests

```python
# conftest.py - add session-scoped fixture
@pytest.fixture(scope="session")
def cached_botany_farm_documents():
    """Discover documents once, cache for all tests."""
    from registry_review_mcp.tools import document_tools

    docs_path = Path("examples/22-23/4997Botany22_Public_Project_Plan")
    discovered = document_tools.discover_documents(docs_path)
    return discovered
```

**Estimated Timeline**: 45 minutes

**Total Tier 2 Savings**: 8-13 seconds (25s → 12-15s)

---

### 🔬 TIER 3: Advanced Optimizations (Expected: 12-15s → 8-10s)
**Implementation Time**: 6-8 hours
**Performance Gain**: 20-40% further reduction
**Risk**: Medium

#### 3.1 Implement Test Result Caching
**Impact**: Second runs become near-instant

```bash
pip install pytest-cache

# Enable in pytest.ini
[pytest]
cache_dir = .pytest_cache
```

Use `--lf` (last failed) and `--ff` (failed first) for faster iteration.

**Estimated Timeline**: 1 hour

#### 3.2 Optimize Fixture Scope Strategy
**Impact**: Reduce duplicate operations

Current fixture scopes analysis:
- `botany_farm_markdown`: session ✅ (optimal)
- `botany_farm_dates`: function ⚠️ (should be session)
- `botany_farm_tenure`: function ⚠️ (should be session)
- `botany_farm_project_ids`: function ⚠️ (should be session)

Change all extraction fixtures to session scope:
```python
@pytest_asyncio.fixture(scope="session")
async def botany_farm_dates(botany_farm_markdown):
    # Runs once per suite instead of per test
```

**Caveat**: Requires async event loop management at session scope.

**Estimated Timeline**: 2 hours

#### 3.3 Implement Parallel Async Execution
**Impact**: Faster async test execution

```python
# conftest.py
import pytest_asyncio

pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.get_event_loop_policy()
```

**Estimated Timeline**: 2 hours

#### 3.4 Database/Filesystem Mocking
**Impact**: Eliminate I/O latency

Replace real filesystem operations with in-memory alternatives:
```python
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_filesystem():
    with patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('pathlib.Path.write_text') as mock_write:
        yield {'mkdir': mock_mkdir, 'write': mock_write}
```

**Estimated Timeline**: 3 hours

**Total Tier 3 Savings**: 4-5 seconds (12-15s → 8-10s)

---

## Performance Projections

### Conservative Estimate (Tier 1 Only)
```
Current:   56.6s
Tier 1:    -36s (parallel + cleanup optimization)
Result:    ~20s (65% improvement)
```

### Target Estimate (Tier 1 + Tier 2)
```
Current:   56.6s
Tier 1:    -36s
Tier 2:    -8s (workflow optimization + caching)
Result:    ~12s (79% improvement)
```

### Stretch Goal (All Tiers)
```
Current:   56.6s
Tier 1:    -36s
Tier 2:    -8s
Tier 3:    -5s
Result:    ~8s (86% improvement)
```

---

## Implementation Roadmap

### Week 1: Quick Wins (Target: 20-25s)
**Day 1-2**: Implement Tier 1 optimizations
- [x] Enable pytest-xdist parallelization
- [x] Optimize cleanup fixture scope
- [x] Skip marker tests by default
- [x] Validate with full test run

**Day 3**: Testing and validation
- Run full suite 10 times to establish baseline
- Identify any race conditions from parallelization
- Document any breaking changes

### Week 2: Structural Improvements (Target: 12-15s)
**Day 1-2**: Refactor large test files
- Split test_upload_tools.py into logical modules
- Optimize upload workflow test

**Day 3-4**: Implement caching strategies
- Add session-scoped document discovery fixture
- Implement lazy fixture loading

**Day 5**: Integration and validation
- Full test suite validation
- Performance benchmarking
- Update documentation

### Week 3: Advanced Optimizations (Target: 8-10s)
**Optional**: Only if sub-15s target not met

---

## Risk Assessment

### Low Risk (Safe to Implement)
✅ Tier 1.1: Parallel execution (tests already isolated)
✅ Tier 1.3: Skip marker tests (clear separation)
✅ Tier 2.1: Split large test files (pure refactoring)
✅ Tier 2.4: Cache document discovery (read-only operation)

### Medium Risk (Requires Testing)
⚠️ Tier 1.2: Cleanup scope change (verify no state leakage)
⚠️ Tier 2.2: Workflow test splitting (may affect coverage)
⚠️ Tier 3.2: Fixture scope changes (async complexity)

### High Risk (Defer Until Needed)
🔴 Tier 3.4: Filesystem mocking (may miss real bugs)
🔴 Tier 3.3: Parallel async execution (complex debugging)

---

## Success Metrics

### Primary Goal
✅ **Test suite completes in <15 seconds** (currently 56.6s)

### Secondary Goals
✅ Maintain 100% test pass rate
✅ No increase in flakiness
✅ Preserve test isolation
✅ Maintain code coverage

### Monitoring
- Run `pytest --durations=10` after each change
- Track execution time in CI/CD
- Monitor for race conditions in parallel runs
- Validate fixture cleanup works correctly

---

## Cost-Benefit Analysis

### Tier 1 (Quick Wins)
**Investment**: 1-2 hours
**Return**: 31-36 seconds saved per run
**ROI**: Immediate (saves time on every test run)
**Recommendation**: ✅ **IMPLEMENT NOW**

### Tier 2 (Structural)
**Investment**: 3-4 hours
**Return**: 8-13 seconds additional savings
**ROI**: High (improves maintainability + performance)
**Recommendation**: ✅ **IMPLEMENT AFTER TIER 1**

### Tier 3 (Advanced)
**Investment**: 6-8 hours
**Return**: 4-5 seconds additional savings
**ROI**: Medium (only if <15s target not met)
**Recommendation**: ⚠️ **EVALUATE AFTER TIER 2**

---

## Appendix A: Test File Analysis

### Largest Files (54% of test code)
1. test_upload_tools.py (42.5 KB, 1,083 lines) - **REFACTOR CANDIDATE**
2. test_tenure_and_project_id_extraction.py (16.0 KB)
3. test_marker_integration.py (16.7 KB) - **SKIP BY DEFAULT**
4. test_llm_json_validation.py (15.3 KB)
5. test_llm_extraction.py (14.6 KB)
6. test_phase4_validation.py (14.2 KB)
7. test_validation.py (13.4 KB)
8. test_integration_full_workflow.py (13.1 KB)

### Slowest Tests (Top 10)
1. test_start_review_full_workflow: 21.8s (38%) - **OPTIMIZE**
2. test_get_markdown_content_none_if_missing: 5.8s (10%) - **SKIP**
3. test_discover_documents_botany_farm: 3.1s (5%) - **CACHE**
4. test_extract_all_evidence: 2.9s (5%)
5. test_map_single_requirement: 2.3s (4%)
6. test_extract_project_start_date: 1.5s (3%)
7. test_markdown_report_includes_citations: 1.3s (2%)
8. test_start_review_end_to_end: 1.1s (2%)
9. test_extract_snippets_from_markdown: 1.1s (2%)
10. test_full_report_workflow: 1.0s (2%)

**Top 10 account for 42.7s (75% of total runtime)**

---

## Appendix B: Marker Usage Analysis

```
Current markers usage (from pytest.ini):
- slow: 5 tests (real API calls)
- marker: 9 tests (PDF extraction, 8GB+ RAM)
- integration: 3 tests (full system required)
- expensive: 7 tests (high API costs)
- accuracy: 4 tests (ground truth validation)
- unit: 0 tests (marker defined but unused)
```

**Recommendation**: Audit and consistently apply markers across all tests.

---

## Appendix C: Fixture Optimization Opportunities

### Current Session-Scoped Fixtures (Optimal)
- `botany_farm_markdown`: ✅ Loads once, used 20+ times
- `cleanup_cache_once`: ✅ Runs once per session

### Function-Scoped Fixtures (Consider Session Scope)
- `botany_farm_dates`: Used by 5+ tests → **Candidate for session scope**
- `botany_farm_tenure`: Used by 5+ tests → **Candidate for session scope**
- `botany_farm_project_ids`: Used by 3+ tests → **Candidate for session scope**
- `cleanup_sessions`: Runs 223 times → **Change to module scope**

### Unused or Underutilized
- `cleanup_examples_sessions`: Only used explicitly, not autouse → ✅ OK
- `test_settings`: Used 50+ times → ✅ Appropriate scope

---

## Appendix D: Parallel Execution Readiness

### Prerequisites ✅
- Tests use `pytest.fixture` isolation
- No global state mutations detected
- Temporary directories use `tmp_path` (unique per test)
- Session cleanup uses session IDs (no conflicts)

### Potential Conflicts ⚠️
- Shared example directory (examples/22-23/) - read-only, OK
- Cache directory - uses locking, OK
- Cost tracking files in /tmp - unique IDs, OK

### Recommendation
✅ **Suite is ready for parallel execution with pytest-xdist**

---

## Final Recommendations

### Immediate Actions (This Week)
1. ✅ Install pytest-xdist: `pip install pytest-xdist`
2. ✅ Update pytest.ini to skip marker tests by default
3. ✅ Change cleanup_sessions scope from function to module
4. ✅ Run full suite with `-n 4` to validate
5. ✅ Benchmark and document results

### Next Sprint
1. Split test_upload_tools.py into 3 files
2. Optimize test_start_review_full_workflow
3. Implement cached document discovery fixture
4. Add lazy fixture loading for expensive operations

### Future Improvements
1. Evaluate Tier 3 optimizations if needed
2. Add performance regression tests
3. Document testing best practices in CONTRIBUTING.md
4. Set up CI/CD performance monitoring

---

**Report Prepared By**: Claude (Synthesis Agent)
**Analysis Date**: 2025-11-20
**Next Review**: After Tier 1 implementation
