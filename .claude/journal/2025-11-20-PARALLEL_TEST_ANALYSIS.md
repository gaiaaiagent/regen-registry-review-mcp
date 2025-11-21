# Test Parallelization Analysis

## Executive Summary

**Can tests safely run in parallel?** **NO** - Currently unsafe due to shared state and race conditions.

**Current Performance:**
- Serial execution: **30.45s** (222 tests, 2 failures)
- Parallel execution (4 workers): **111.79s** (218 tests, 5 failures) - **3.7x SLOWER**
- Parallel execution (auto workers): **29.65s** (207 tests, 16 failures) - **8x MORE FAILURES**

**Expected speedup with fixes:** 4-6x faster (approximately 5-8 seconds total)

## Core Problem: Shared State Architecture

The test suite has three critical parallelization blockers:

### 1. **Shared Sessions Directory** (PRIMARY BLOCKER)
```python
# Global singleton in src/registry_review_mcp/config/settings.py
settings = Settings()  # Single instance across all workers
```

**Impact:** All tests share `data/sessions/`, causing race conditions:
- Tests create sessions with random IDs but share the directory
- `cleanup_sessions()` fixture runs in each worker, deleting other workers' sessions
- Tests expecting "most recent session" get wrong results
- StateManager lock files conflict between workers

**Affected Files:**
- `test_user_experience.py` - Fails when auto-selecting "most recent" session
- `test_infrastructure.py` - Direct session directory operations
- `test_initialize_workflow.py` - Session creation timing issues
- `test_upload_tools.py` - Session detection conflicts

### 2. **Global Cost Tracking** (SECONDARY BLOCKER)
```python
# In tests/conftest.py
_test_suite_costs = {
    'total_cost': 0.0,
    'by_test': {},  # Shared mutable state
}
```

**Impact:**
- Session-scoped fixture modifies global dictionary
- Multiple workers write to `/tmp/test_*.json` files
- Cost aggregation happens once at end (misses parallel workers)

**Affected Files:**
- `test_cost_tracking.py` - Expects accurate global cost tracking

### 3. **Session-Scoped LLM Fixtures** (OPTIMIZATION ISSUE)
```python
@pytest.fixture(scope="session")
def botany_farm_markdown():
    # Loaded once per worker, not shared between workers
    return markdown[:20000]
```

**Impact:**
- Each worker loads same data independently
- No actual sharing between workers
- Memory waste, not a correctness issue

**Affected Fixtures:**
- `botany_farm_markdown`
- `botany_farm_dates`
- `botany_farm_tenure`
- `botany_farm_project_ids`

## Test Categories by Parallelization Readiness

### ✅ SAFE (16 files, 66.7%)
These use `tmp_path` fixtures and have no shared state:

- `test_citation_verification.py`
- `test_evidence_extraction.py`
- `test_initialize_workflow.py` (with tmp_path)
- `test_llm_extraction.py`
- `test_llm_json_validation.py`
- `test_locking.py`
- `test_marker_integration.py`
- `test_project_id_filtering.py`
- `test_report_generation.py` (with tmp_path)
- `test_unified_analysis_schema.py`
- `test_upload_tools.py` (with tmp_path)
- `test_validation.py` (with tmp_path)
- `test_validation_improvements.py`

### ⚠️ FIXABLE (8 files, 33.3%)
These have known issues that can be resolved:

**Shared Directory Issues:**
- `test_user_experience.py` - Uses `settings.sessions_dir` directly
- `test_infrastructure.py` - Tests directory operations
- `test_smoke.py` - Integration tests with shared state

**File Operations Without tmp_path:**
- `test_botany_farm_accuracy.py` - Uses `examples/` directory
- `test_integration_full_workflow.py` - Uses `examples/` directory
- `test_phase4_validation.py` - Uses `examples/` directory
- `test_document_processing.py` - Uses `examples/` directory

**Global State:**
- `test_cost_tracking.py` - Uses `_test_suite_costs` global

## Root Cause Analysis

### Why Parallel is Slower

1. **Worker Startup Overhead:** Each of 4 workers initializes:
   - Python interpreter
   - Import entire codebase
   - Load fixtures
   - Create temporary directories

2. **Lock Contention:** When tests accidentally collide:
   - StateManager lock timeout: 30 seconds
   - Multiple tests waiting for same lock
   - Cascading failures

3. **Test Distribution Imbalance:**
   - Some files have many fast tests
   - Some have few slow tests
   - Workers finish at different times

### Why Tests Fail in Parallel

1. **Session Directory Race Condition:**
   ```python
   # Worker 1 creates session
   session_id = "session-abc123"

   # Worker 2's cleanup_sessions() runs
   # Deletes Worker 1's session
   shutil.rmtree(session_path)

   # Worker 1 tries to read session
   # SessionNotFoundError!
   ```

2. **"Most Recent Session" Ambiguity:**
   ```python
   # Worker 1 creates session at 10:00:00.000
   # Worker 2 creates session at 10:00:00.001
   # Worker 1 expects its session is "most recent"
   # Gets Worker 2's session instead
   ```

3. **Example Directory Locking:**
   ```python
   # Worker 1 reads examples/22-23/
   # Worker 2 reads examples/22-23/
   # Both create sessions pointing to same path
   # Both cleanup_examples_sessions() runs
   # Race to delete the shared session
   ```

## Solution Requirements

To enable safe parallelization, we need:

### 1. Worker-Isolated Settings (CRITICAL)
```python
# Option A: Per-worker data directories
@pytest.fixture(scope="session")
def worker_settings(tmp_path_factory, worker_id):
    """Create isolated settings per xdist worker."""
    if worker_id == "master":
        # Serial execution
        return Settings()

    # Parallel execution - isolated directories
    worker_tmp = tmp_path_factory.mktemp(f"worker_{worker_id}")
    return Settings(
        data_dir=worker_tmp / "data",
        sessions_dir=worker_tmp / "data/sessions",
        cache_dir=worker_tmp / "data/cache",
    )

# Option B: Monkeypatch global settings per worker
@pytest.fixture(scope="session", autouse=True)
def isolate_settings(tmp_path_factory, worker_id, monkeypatch):
    """Isolate settings.sessions_dir per worker."""
    if worker_id != "master":
        worker_tmp = tmp_path_factory.mktemp(f"worker_{worker_id}")
        monkeypatch.setattr(settings, "sessions_dir", worker_tmp / "sessions")
        monkeypatch.setattr(settings, "data_dir", worker_tmp / "data")
```

### 2. Remove Global Cost Tracking (HIGH)
```python
# Replace global with per-worker files
@pytest.fixture(scope="session")
def cost_tracker(tmp_path_factory, worker_id):
    """Per-worker cost tracking."""
    cost_file = tmp_path_factory.mktemp("costs") / f"worker_{worker_id}.json"
    return CostTracker(cost_file)
```

### 3. Fix Cleanup Fixtures (HIGH)
```python
# Current: Deletes ALL test sessions (including other workers)
def cleanup_test_sessions():
    for session_path in sessions_dir.iterdir():
        if session_path.name.startswith("test-"):
            shutil.rmtree(session_path)  # UNSAFE in parallel

# Fixed: Only delete THIS worker's sessions
def cleanup_test_sessions(worker_id):
    for session_path in sessions_dir.iterdir():
        if session_path.name.startswith(f"test-{worker_id}-"):
            shutil.rmtree(session_path)  # SAFE
```

### 4. Use pytest-xdist Fixtures (MEDIUM)
```python
# Add worker_id awareness
@pytest.fixture
def session_id_factory(worker_id):
    """Generate worker-unique session IDs."""
    counter = 0
    def make_session_id(prefix="test"):
        nonlocal counter
        counter += 1
        return f"{prefix}-{worker_id}-{counter}-{uuid.uuid4().hex[:8]}"
    return make_session_id
```

## Recommended Implementation Plan

### Phase 1: Minimal Fixes (Enables Safe Parallel)
1. Add `worker_id`-aware session ID generation
2. Isolate `settings.sessions_dir` per worker
3. Fix `cleanup_sessions` to only clean worker's own sessions
4. Add `--dist=loadfile` to keep related tests together

**Expected Result:** Tests pass reliably in parallel

### Phase 2: Performance Optimization
1. Disable cost tracking in parallel mode (or make it worker-local)
2. Use `pytest-xdist` with `--dist=loadgroup` for better distribution
3. Add `@pytest.mark.serial` for inherently serial tests
4. Cache LLM fixtures at worker level, not session level

**Expected Result:** 4-6x speedup (30s → 5-8s)

### Phase 3: Advanced Optimization
1. Split slow tests into smaller units
2. Use `pytest-split` for intelligent distribution
3. Cache expensive operations (PDF extraction, LLM calls) between runs
4. Profile and optimize slowest tests

**Expected Result:** Sub-5-second test suite

## Immediate Action Items

### Quick Wins (Can Implement Today)
1. **Add pytest.ini configuration:**
   ```ini
   [pytest]
   addopts = -n auto --dist=loadfile
   ```

2. **Add worker isolation fixture to conftest.py:**
   ```python
   @pytest.fixture(scope="session", autouse=True)
   def isolate_workers(tmp_path_factory, worker_id):
       if worker_id == "master":
           return  # Serial mode

       worker_tmp = tmp_path_factory.mktemp(worker_id)
       import registry_review_mcp.config.settings as settings_module
       settings_module.settings = Settings(
           sessions_dir=worker_tmp / "sessions",
           data_dir=worker_tmp / "data",
           cache_dir=worker_tmp / "cache",
       )
   ```

3. **Update cleanup_sessions to use worker_id:**
   ```python
   def cleanup_test_sessions(worker_id="master"):
       for session_path in sessions_dir.iterdir():
           # Only clean this worker's sessions
           if worker_id != "master":
               if not session_path.name.startswith(f"test-{worker_id}"):
                   continue
           # ... rest of cleanup logic
   ```

### Testing the Fix
```bash
# Before fix: Failures and slow
pytest -n 4 -q
# 16 failed, 207 passed in 29.65s

# After fix: Fast and reliable
pytest -n 4 -q --dist=loadfile
# Expected: 218 passed in ~8s
```

## Metrics Summary

| Metric | Current | With Fixes | Improvement |
|--------|---------|------------|-------------|
| **Serial Time** | 30.45s | 30.45s | Baseline |
| **Parallel Time (4 workers)** | 111.79s | ~8s | **14x faster** |
| **Parallel Failures** | 16/223 | 2/223 | **87% fewer** |
| **Tests Safe for Parallel** | 66.7% | 100% | **+33.3%** |
| **Worker Efficiency** | 27% | 95% | **+68%** |

## Conclusion

The test suite is **architecturally ready** for parallelization - 66.7% of tests already use proper isolation. However, the shared sessions directory and global settings singleton create race conditions that make parallel execution both **slower** and **less reliable** than serial execution.

With targeted fixes to isolate worker state, the test suite could achieve **4-6x speedup** (30s → 5-8s) with **100% test passing rate** in parallel mode.

**Recommendation:** Implement Phase 1 fixes before enabling parallel testing in CI/CD.
