# Test Suite Optimization Checklist

**Goal**: Reduce test execution time from 56.6s to <15s
**Strategy**: Three-tier implementation (Quick Wins → Structural → Advanced)

---

## ✅ TIER 1: Quick Wins (Target: 20-25s) - 1-2 hours

### [ ] 1. Enable Parallel Execution (saves 31-36s)
```bash
# Install pytest-xdist
pip install pytest-xdist

# Test with 4 workers
pytest tests/ -n 4 --tb=short

# If successful, add to pyproject.toml or pytest.ini
[tool.pytest.ini_options]
addopts = ["-n", "auto"]
```

**Validation**:
- Run 3 times to ensure no race conditions
- Check that all 223 tests still pass
- Verify execution time < 25s

---

### [ ] 2. Optimize Cleanup Fixture Scope (saves 2-3s)

**File**: `tests/conftest.py`, line 271

**Change**:
```python
# Before
@pytest.fixture(autouse=True, scope="function")
def cleanup_sessions():
    # ... runs 223 times per suite

# After
@pytest.fixture(autouse=True, scope="module")
def cleanup_sessions():
    # ... runs 23 times per suite
```

**Validation**:
- Run full suite twice
- Verify no session pollution between tests
- Check that test isolation is preserved

---

### [ ] 3. Skip Marker Tests by Default (saves 5.8s)

**File**: `pytest.ini`, line 24

**Change**:
```python
# Before
-m "not expensive and not integration and not accuracy and not marker"

# After
-m "not expensive and not integration and not accuracy and not marker"
```

**Validation**:
- Run default suite: `pytest tests/`
- Verify marker tests are skipped (should see "50 deselected")
- Test marker tests separately: `pytest tests/ -m marker`

---

**Tier 1 Target**: 56.6s → 20-25s (55-65% improvement)

---

## 🎯 TIER 2: Structural Improvements (Target: 12-15s) - 3-4 hours

### [ ] 4. Split Large Test File (improves load balancing)

**File**: `tests/test_upload_tools.py` (1,083 lines)

**Action**: Split into 3 files:
- `tests/upload/test_upload_creation.py` (create_session_from_uploads tests)
- `tests/upload/test_upload_additional.py` (upload_additional_files tests)
- `tests/upload/test_upload_workflow.py` (start_review_from_uploads tests)

**Validation**:
- All tests still pass
- Better distribution across parallel workers
- Improved code navigation

---

### [ ] 5. Optimize Slowest Test (saves 13-16s)

**File**: `tests/test_upload_tools.py::TestStartReviewFromUploads::test_start_review_full_workflow`
**Current**: 21.8s

**Action**: Split into two tests:
```python
# Fast test (creation + upload + discovery)
async def test_start_review_workflow_base(...):
    result = await start_review_from_uploads(
        ...,
        auto_extract=False  # Skip expensive extraction
    )
    assert result["success"]
    assert result["documents_found"] > 0

# Expensive test (with extraction)
@pytest.mark.expensive
async def test_start_review_workflow_with_extraction(...):
    result = await start_review_from_uploads(
        ...,
        auto_extract=True  # Full workflow
    )
    # Validate extraction results
```

**Validation**:
- Both tests pass
- Default run skips expensive test
- Coverage maintained

---

### [ ] 6. Cache Document Discovery (saves 3.1s)

**File**: `tests/conftest.py`

**Action**: Add session-scoped fixture:
```python
@pytest.fixture(scope="session")
def cached_botany_farm_documents():
    """Discover documents once, cache for all tests."""
    docs_path = Path(__file__).parent.parent / "examples/22-23/4997Botany22_Public_Project_Plan"

    from registry_review_mcp.tools import document_tools
    discovered = document_tools.discover_documents(str(docs_path))

    return discovered
```

**Update tests** to use cached fixture instead of re-discovering.

**Validation**:
- Discovery happens only once per suite
- All dependent tests pass
- Results are consistent

---

### [ ] 7. Implement Lazy Fixture Loading

**Install**: `pip install pytest-lazy-fixture`

**Action**: Update expensive fixtures to load conditionally:
```python
@pytest.mark.parametrize("extraction_fixture", [
    pytest.lazy_fixture("botany_farm_dates"),
    pytest.lazy_fixture("botany_farm_tenure"),
])
def test_extraction_validation(extraction_fixture):
    # Fixture only loads when test runs
    assert extraction_fixture is not None
```

**Validation**:
- Fixtures load only when needed
- Tests pass with lazy loading
- Faster test collection

---

**Tier 2 Target**: 25s → 12-15s (40-50% further reduction)

---

## 🔬 TIER 3: Advanced Optimizations (Target: 8-10s) - 6-8 hours

### [ ] 8. Session-Scope Extraction Fixtures (saves 2-3s)

**File**: `tests/conftest.py`, lines 135-186

**Action**: Change scope from `function` to `session`:
```python
# Before
@pytest_asyncio.fixture(scope="function")
async def botany_farm_dates(botany_farm_markdown):
    # Runs for each test

# After
@pytest_asyncio.fixture(scope="session")
async def botany_farm_dates(botany_farm_markdown, event_loop):
    # Runs once per suite
```

**Note**: Requires async event loop management at session scope.

**Validation**:
- Session-scoped async fixtures work correctly
- Results are consistent across tests
- No state pollution

---

### [ ] 9. Implement Test Result Caching

**Install**: `pip install pytest-cache`

**Action**: Configure in `pytest.ini`:
```ini
[pytest]
cache_dir = .pytest_cache
```

**Usage**:
```bash
# Run failed tests first
pytest --ff

# Run only last failed tests
pytest --lf
```

**Validation**:
- Cache directory populated
- Fast iteration on failed tests
- Cache invalidation works correctly

---

### [ ] 10. Optimize Async Execution

**File**: `tests/conftest.py`

**Action**: Add session-scoped event loop:
```python
@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.get_event_loop_policy()

@pytest.fixture(scope="session")
def event_loop(event_loop_policy):
    loop = event_loop_policy.new_event_loop()
    yield loop
    loop.close()
```

**Validation**:
- All async tests pass
- No event loop conflicts
- Proper cleanup

---

**Tier 3 Target**: 12-15s → 8-10s (20-40% further reduction)

---

## 📊 Validation & Benchmarking

After each tier, run:

```bash
# Full benchmarking suite
pytest tests/ --durations=20 --tb=short -v

# Performance regression check
pytest tests/ --durations=0 | grep "slowest durations" -A 20

# Parallel execution validation
pytest tests/ -n 4 --tb=short

# Coverage check (ensure no regression)
pytest tests/ --cov=src/registry_review_mcp --cov-report=term-missing
```

---

## 🎯 Success Criteria

### Primary Goal
- [ ] Test suite executes in <15 seconds
- [ ] All 223 tests pass
- [ ] No new test flakiness

### Secondary Goals
- [ ] Code coverage maintained (>80%)
- [ ] No race conditions in parallel execution
- [ ] Fixture cleanup works correctly
- [ ] Documentation updated

---

## 📝 Implementation Notes

### Best Practices
- Commit after each tier
- Run full suite 3 times to validate stability
- Document any breaking changes
- Update CONTRIBUTING.md with new testing guidelines

### Rollback Strategy
If any tier causes issues:
1. Revert the specific changes
2. Document the issue
3. Continue with remaining optimizations
4. Revisit problematic change later

### Performance Tracking
Create `test_performance.log` to track execution times:
```bash
date >> test_performance.log
pytest tests/ --tb=no -q 2>&1 | grep "passed" >> test_performance.log
```

---

## 📈 Expected Results

| Stage | Time (s) | Reduction | Cumulative |
|-------|----------|-----------|------------|
| Baseline | 56.6 | - | - |
| Tier 1 | 20-25 | 55-65% | 55-65% |
| Tier 2 | 12-15 | 40-50% | 73-79% |
| Tier 3 | 8-10 | 20-40% | 83-86% |

---

**Last Updated**: 2025-11-20
**Status**: Ready for implementation
**Next Review**: After Tier 1 completion
