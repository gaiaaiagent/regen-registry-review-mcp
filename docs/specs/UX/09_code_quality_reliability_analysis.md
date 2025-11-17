# Code Quality and Reliability Analysis

**Registry Review MCP System v2.0.0**

**Date:** November 14, 2025
**Status:** Phase 5 (Integration & Polish) - 70% Complete
**Analyst:** Claude Code Quality Review Agent

---

## Executive Summary

The Registry Review MCP system demonstrates strong architectural foundations and production-ready patterns in several areas, while revealing opportunities for improvement in reliability, testing comprehensiveness, and operational observability. This analysis evaluates the codebase against industry best practices for production Python systems, MCP server patterns, and AI system reliability.

**Overall Assessment: B+ (Good, with clear path to A)**

**Strengths:**
- Excellent separation of concerns with clear architectural layers
- Robust state management with atomic operations and file locking
- Comprehensive LLM integration with retry logic, caching, and cost tracking
- Strong test coverage (120 tests passing, 100%)
- Well-documented codebase with clear roadmap and specifications

**Critical Improvements Needed:**
- Integration test coverage for end-to-end workflows
- Circuit breaker patterns for LLM API resilience
- Structured logging with correlation IDs for distributed tracing
- Performance monitoring and bottleneck identification
- Production-grade error recovery and graceful degradation

---

## 1. Code Architecture Assessment

### 1.1 Separation of Concerns

**Rating: A** - Excellent modular design

The codebase demonstrates exceptional separation of concerns across multiple architectural layers:

```
src/registry_review_mcp/
├── server.py              # MCP interface layer (842 lines)
├── config/settings.py     # Configuration management (101 lines)
├── models/                # Data models and validation
│   ├── errors.py          # Error hierarchy (104 lines)
│   ├── schemas.py         # Pydantic models
│   ├── evidence.py        # Evidence structures
│   ├── validation.py      # Validation models
│   └── report.py          # Report structures
├── tools/                 # Business logic layer
│   ├── session_tools.py   # Session management
│   ├── document_tools.py  # Document processing
│   ├── evidence_tools.py  # Evidence extraction
│   ├── validation_tools.py # Cross-validation
│   └── report_tools.py    # Report generation
├── extractors/            # LLM integration layer
│   └── llm_extractors.py  # AI-powered extraction (1202 lines)
├── utils/                 # Infrastructure layer
│   ├── state.py           # Atomic state management (175 lines)
│   ├── cache.py           # Caching utilities (148 lines)
│   ├── cost_tracker.py    # API cost tracking
│   └── patterns.py        # Regex patterns
└── prompts/               # Workflow orchestration
    ├── initialize.py
    ├── document_discovery.py
    ├── evidence_extraction.py
    ├── cross_validation.py
    ├── report_generation.py
    ├── human_review.py
    └── complete.py
```

**Strengths:**
- Clear layering prevents tight coupling between MCP protocol, business logic, and infrastructure
- Each module has a single, well-defined responsibility
- Models use Pydantic for runtime validation, preventing data corruption
- Error hierarchy provides fine-grained exception handling

**Concerns:**
- `llm_extractors.py` is 1202 lines - consider splitting into separate extractor classes
- Some circular dependency risk between tools and extractors (mitigated by lazy imports)

**Recommendation:** Extract `DateExtractor`, `LandTenureExtractor`, and `ProjectIDExtractor` into separate files (`extractors/date.py`, `extractors/tenure.py`, `extractors/project_id.py`) to improve maintainability.

---

### 1.2 Dependency Management

**Rating: A-** - Well-managed with room for improvement

**Current Dependencies:**
```toml
dependencies = [
    "mcp[cli]>=1.21.0",          # MCP protocol
    "pdfplumber>=0.11.0",         # PDF extraction
    "pydantic>=2.11.0",           # Data validation
    "python-dateutil>=2.8.0",     # Date parsing
    "fiona>=1.9.0",               # GIS files
    "structlog>=24.0.0",          # Structured logging (not yet used!)
    "pydantic-settings>=2.12.0",  # Config management
    "anthropic>=0.40.0",          # LLM API
    "rapidfuzz>=3.14.3",          # Fuzzy matching
]
```

**Strengths:**
- Minimal dependency footprint (9 core dependencies)
- Uses `uv` for deterministic dependency resolution
- Version pinning with `>=` allows security patches while preventing breaking changes
- `exclude-newer` in `pyproject.toml` ensures reproducible builds

**Concerns:**
- `structlog` is imported but standard `logging` is used throughout codebase
- No explicit dependency on async runtime (relies on Python 3.10+ asyncio)
- Missing observability dependencies (metrics, tracing)

**Recommendations:**
1. **Migrate to structured logging:** Replace `logging` with `structlog` for better production observability
2. **Add observability stack:**
   ```toml
   "opentelemetry-api>=1.20.0",     # Distributed tracing
   "prometheus-client>=0.18.0",     # Metrics collection
   "sentry-sdk>=1.35.0",            # Error tracking (optional)
   ```
3. **Pin major versions:** Consider `anthropic>=0.40.0,<1.0.0` to prevent breaking API changes

---

### 1.3 Modularity and Cohesion

**Rating: A** - High cohesion, low coupling

**Evidence of Strong Modularity:**

1. **Tool Independence:** Each tool file is self-contained and testable:
   - `session_tools.py` - Session CRUD operations
   - `document_tools.py` - PDF/GIS processing
   - `evidence_tools.py` - Requirement mapping
   - `validation_tools.py` - Cross-document checks

2. **Interface Consistency:** All tools follow consistent async patterns:
   ```python
   async def tool_function(session_id: str, ...) -> dict[str, Any]:
       """Docstring with args and returns."""
       # Validation
       # Business logic
       # State update
       # Return structured result
   ```

3. **Data Flow Separation:** Clear data flow through layers:
   ```
   MCP Server (server.py)
       ↓
   Tools (business logic)
       ↓
   Extractors (LLM calls) ← Utils (state, cache)
       ↓
   Models (validation)
   ```

**Concerns:**
- Some cross-cutting concerns (logging, cost tracking) scattered across modules
- State management tightly coupled to file system (limits future cloud deployment)

**Recommendations:**
1. **Extract cross-cutting concerns:** Create `observability/` module for logging, metrics, tracing
2. **Abstract state persistence:** Define `StateBackend` interface to support multiple storage backends

---

### 1.4 Extensibility

**Rating: B+** - Good foundation, needs interfaces

**Current Extensibility:**
- New document types can be added to `utils/patterns.py`
- New extractors follow `BaseExtractor` pattern
- New validation rules added to `validation_tools.py`

**Missing Extensibility Patterns:**
- No plugin system for custom extractors
- No registry pattern for document classifiers
- Hard-coded methodology checklist loading

**Recommendations:**

1. **Extractor Registry Pattern:**
   ```python
   class ExtractorRegistry:
       _extractors: dict[str, Type[BaseExtractor]] = {}

       @classmethod
       def register(cls, name: str, extractor_class: Type[BaseExtractor]):
           cls._extractors[name] = extractor_class

       @classmethod
       def get(cls, name: str) -> BaseExtractor:
           return cls._extractors[name]()

   # Usage
   @ExtractorRegistry.register("date")
   class DateExtractor(BaseExtractor):
       ...
   ```

2. **Strategy Pattern for Document Classification:**
   ```python
   class DocumentClassifier(Protocol):
       def classify(self, filepath: Path, content: str) -> str:
           ...

   class FilenameClassifier(DocumentClassifier):
       ...

   class ContentClassifier(DocumentClassifier):
       ...
   ```

3. **Methodology Plugin System:**
   ```python
   class MethodologyPlugin:
       def load_checklist(self) -> dict:
           ...

       def get_validators(self) -> list[Validator]:
           ...
   ```

---

### 1.5 Technical Debt

**Rating: B** - Moderate debt, well-documented

**Current Technical Debt Items:**

1. **TODO Comments in Code:**
   - No scattered TODO comments found (good!)
   - Roadmap clearly tracks future work

2. **Known Limitations (from ROADMAP.md):**
   - Single methodology support (Soil Carbon v1.2.2 only)
   - No batch processing for multi-farm projects
   - Local file system only (no cloud storage)
   - No multi-user concurrency support

3. **Deferred Features (Phase 3+):**
   - Advanced GIS spatial analysis
   - ML-based document classification
   - Multi-methodology support
   - Cloud storage connectors (Google Drive, SharePoint)
   - KOI Commons integration
   - Regen Ledger integration

**Recommendations:**
- Create `TECHNICAL_DEBT.md` to track architectural decisions and tradeoffs
- Add ADR (Architecture Decision Records) for major design choices
- Prioritize technical debt in each sprint (15-20% capacity)

---

## 2. Reliability Patterns Evaluation

### 2.1 Error Handling Strategies

**Rating: B+** - Good hierarchy, missing resilience patterns

**Current Error Handling:**

**Strengths:**
1. **Comprehensive Error Hierarchy:**
   ```python
   RegistryReviewError (base)
   ├── SessionError
   │   ├── SessionNotFoundError
   │   └── SessionLockError
   ├── DocumentError
   │   ├── DocumentNotFoundError
   │   ├── DocumentExtractionError
   │   └── DocumentClassificationError
   ├── RequirementError
   │   ├── RequirementNotFoundError
   │   └── EvidenceExtractionError
   ├── ValidationError
   │   ├── DateAlignmentError
   │   └── LandTenureValidationError
   └── ConfigurationError
       └── ChecklistLoadError
   ```

2. **Consistent Error Context:**
   ```python
   class RegistryReviewError(Exception):
       def __init__(self, message: str, details: dict | None = None):
           super().__init__(message)
           self.message = message
           self.details = details or {}
   ```

3. **User-Friendly Error Messages:**
   ```python
   except mcp_errors.SessionNotFoundError:
       return f"✗ Session not found: {session_id}\n\nUse list_sessions to see available sessions."
   ```

**Critical Gaps:**

1. **Missing Circuit Breaker for LLM API:**
   ```python
   # NEEDED: Prevent cascading failures when API is down
   from circuitbreaker import circuit

   @circuit(failure_threshold=5, recovery_timeout=60)
   async def call_llm_api(...):
       ...
   ```

2. **No Fallback Mechanisms:**
   - LLM extraction fails → Should fall back to regex/heuristic extraction
   - PDF extraction fails → Should flag for manual review, not crash

3. **Incomplete Exception Handling in Extractors:**
   ```python
   # Current (llm_extractors.py, line 566):
   except ValueError as e:
       logger.error(f"Invalid response from LLM for {chunk_name}: {e}")
       return []  # Silently returns empty, loses error context

   # SHOULD:
   except ValueError as e:
       logger.error(f"Invalid response from LLM for {chunk_name}: {e}")
       raise EvidenceExtractionError(
           f"Failed to parse LLM response for {chunk_name}",
           details={"chunk": chunk_name, "error": str(e)}
       )
   ```

**Recommendations:**

1. **Implement Circuit Breaker Pattern:**
   ```python
   # extractors/circuit_breaker.py
   class APICircuitBreaker:
       def __init__(self, failure_threshold=5, recovery_timeout=60):
           self.failure_count = 0
           self.last_failure_time = None
           self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

       async def call(self, func, *args, **kwargs):
           if self.state == "OPEN":
               if time.time() - self.last_failure_time > self.recovery_timeout:
                   self.state = "HALF_OPEN"
               else:
                   raise CircuitOpenError("Too many failures, circuit is open")

           try:
               result = await func(*args, **kwargs)
               if self.state == "HALF_OPEN":
                   self.state = "CLOSED"
                   self.failure_count = 0
               return result
           except Exception as e:
               self.failure_count += 1
               self.last_failure_time = time.time()
               if self.failure_count >= self.failure_threshold:
                   self.state = "OPEN"
               raise
   ```

2. **Add Fallback Strategy:**
   ```python
   async def extract_dates_with_fallback(markdown: str, images: list) -> list:
       try:
           return await llm_extractor.extract(markdown, images)
       except (APIError, CircuitOpenError):
           logger.warning("LLM extraction failed, falling back to regex")
           return regex_date_extractor.extract(markdown)
   ```

3. **Comprehensive Error Recovery:**
   ```python
   # Add to all tool functions
   try:
       result = await business_logic()
       return format_success(result)
   except RegistryReviewError as e:
       logger.error(f"Business logic error: {e}", extra=e.details)
       return format_error(e.message, e.details)
   except Exception as e:
       logger.exception(f"Unexpected error: {e}")
       return format_error("An unexpected error occurred. Please contact support.",
                          {"error_type": type(e).__name__})
   ```

---

### 2.2 Retry Mechanisms

**Rating: A-** - Excellent LLM retry logic, missing in other areas

**Current Implementation:**

**LLM API Retry (Excellent):**
```python
# extractors/llm_extractors.py, line 109
async def _call_api_with_retry(
    self,
    api_call: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 32.0,
    **kwargs,
) -> Any:
    """Exponential backoff with jitter for transient errors."""
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return await api_call(**kwargs)
        except (RateLimitError, InternalServerError, APIConnectionError, APITimeoutError) as e:
            if attempt < max_retries:
                jitter = delay * 0.25 * (2 * random.random() - 1)
                sleep_time = min(delay + jitter, max_delay)
                await asyncio.sleep(sleep_time)
                delay = min(delay * 2, max_delay)
            else:
                raise
```

**Strengths:**
- Exponential backoff prevents thundering herd
- Jitter (±25%) reduces synchronized retries
- Distinguishes retryable vs non-retryable errors
- Configurable timeouts and max retries

**Missing Retry Logic:**

1. **PDF Extraction:** No retry for transient file I/O errors
   ```python
   # NEEDED in document_tools.py
   @retry(max_attempts=3, backoff=ExponentialBackoff(),
          retry_on=(IOError, OSError))
   async def extract_pdf_text(filepath: Path):
       ...
   ```

2. **File Lock Acquisition:** Polling without backoff
   ```python
   # Current (state.py, line 50):
   while True:
       try:
           self.lock_file.touch(exist_ok=False)
           break
       except FileExistsError:
           time.sleep(0.1)  # Fixed delay, no backoff

   # SHOULD use exponential backoff:
   delay = 0.1
   while time.time() - start_time < timeout:
       try:
           self.lock_file.touch(exist_ok=False)
           break
       except FileExistsError:
           time.sleep(delay)
           delay = min(delay * 1.5, 5.0)  # Cap at 5 seconds
   ```

3. **Network Operations:** GIS file loading from network paths

**Recommendations:**

1. **Create Reusable Retry Decorator:**
   ```python
   # utils/retry.py
   def retry_with_backoff(
       max_attempts: int = 3,
       initial_delay: float = 0.5,
       max_delay: float = 30.0,
       retry_on: tuple[Type[Exception], ...] = (Exception,)
   ):
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               delay = initial_delay
               for attempt in range(max_attempts):
                   try:
                       return await func(*args, **kwargs)
                   except retry_on as e:
                       if attempt == max_attempts - 1:
                           raise
                       jitter = delay * 0.25 * (2 * random.random() - 1)
                       sleep_time = min(delay + jitter, max_delay)
                       logger.warning(f"Retry {attempt+1}/{max_attempts} after {sleep_time:.2f}s: {e}")
                       await asyncio.sleep(sleep_time)
                       delay = min(delay * 2, max_delay)
           return wrapper
       return decorator
   ```

2. **Apply to All External Operations:**
   - PDF extraction (pdfplumber)
   - GIS file reading (fiona)
   - File system operations (state management)

---

### 2.3 Graceful Degradation

**Rating: C** - Limited graceful degradation

**Current Behavior:**
- LLM extraction failure → Returns empty list, workflow continues
- PDF extraction failure → Entire document marked as failed
- Session lock timeout → Hard error, no fallback

**Needed Improvements:**

1. **Partial Success Support:**
   ```python
   # NEEDED: Return partial results instead of all-or-nothing
   {
       "status": "partial_success",
       "documents_processed": 5,
       "documents_failed": 2,
       "failed_documents": [
           {"path": "doc.pdf", "error": "Corrupted PDF", "fallback": "manual_review"}
       ],
       "evidence_extracted": [...],
       "warnings": [...]
   }
   ```

2. **Feature Flags for Degraded Mode:**
   ```python
   # settings.py additions
   enable_llm_extraction: bool = True
   enable_gis_processing: bool = True
   enable_image_analysis: bool = True

   # Automatic degradation
   if api_circuit_open:
       settings.enable_llm_extraction = False
       logger.warning("LLM extraction disabled due to API errors, using fallback")
   ```

3. **Read-Only Mode for Maintenance:**
   ```python
   class MaintenanceMode:
       @staticmethod
       def is_enabled() -> bool:
           return Path("/var/run/maintenance").exists()

       @staticmethod
       def check_and_reject_writes():
           if MaintenanceMode.is_enabled():
               raise MaintenanceError("System is in read-only maintenance mode")
   ```

**Recommendations:**
1. Implement partial success tracking throughout workflow
2. Add feature flags for optional capabilities
3. Create degraded mode that skips non-critical processing
4. Add health check endpoint that reports degraded status

---

### 2.4 Idempotency Guarantees

**Rating: B** - Partial idempotency, needs improvement

**Current Idempotency:**

**Strengths:**
1. **Session Creation:** Uses timestamp-based IDs, not random
   ```python
   session_id = f"session-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
   ```

2. **Caching Prevents Redundant API Calls:**
   ```python
   if cached := self.cache.get(cache_key):
       return cached  # Idempotent read
   ```

3. **Atomic File Updates:**
   ```python
   temp_path.replace(file_path)  # Atomic rename
   ```

**Idempotency Gaps:**

1. **No Request IDs:** Cannot detect duplicate requests
   ```python
   # NEEDED
   @mcp.tool()
   async def extract_evidence(
       session_id: str,
       request_id: str | None = None  # Client-provided idempotency key
   ) -> str:
       if request_id and operation_already_completed(request_id):
           return get_cached_result(request_id)
       ...
   ```

2. **Non-Idempotent State Updates:**
   ```python
   # Current: Running twice creates duplicate entries
   evidence_snippets.append(new_snippet)  # Not idempotent

   # Should: Use sets or check for existence
   if snippet not in evidence_snippets:
       evidence_snippets.append(snippet)
   ```

3. **No Operation Tracking:**
   - Cannot tell if operation is in-progress vs completed vs failed
   - Re-running workflow may duplicate work or corrupt state

**Recommendations:**

1. **Add Request ID Support:**
   ```python
   # utils/idempotency.py
   class IdempotencyTracker:
       def __init__(self, session_id: str):
           self.session_id = session_id
           self.state = StateManager(session_id)

       async def track_operation(self, request_id: str, operation: str, result: Any):
           operations = self.state.read_json("operations.json")
           operations[request_id] = {
               "operation": operation,
               "result": result,
               "timestamp": datetime.now(UTC).isoformat(),
               "status": "completed"
           }
           self.state.write_json("operations.json", operations)

       async def get_cached_result(self, request_id: str) -> Any | None:
           operations = self.state.read_json("operations.json")
           return operations.get(request_id, {}).get("result")
   ```

2. **Operation State Machine:**
   ```python
   {
       "operation_id": "extract_evidence_20251114",
       "status": "in_progress",  # pending, in_progress, completed, failed
       "started_at": "2025-11-14T10:00:00Z",
       "completed_at": null,
       "result": null
   }
   ```

3. **Deterministic IDs:** Use content hashing instead of timestamps
   ```python
   session_id = f"session-{hash_project_metadata()}"  # Same inputs = same ID
   ```

---

## 3. Testing Strategy Analysis

### 3.1 Test Coverage Assessment

**Rating: A-** - Excellent unit test coverage, missing integration tests

**Current Test Statistics:**
- Total Tests: 120
- Test Files: 13
- Test Code: 4,111 lines
- Source Code: 7,400 lines
- Test-to-Code Ratio: 55.5% (Good)
- Pass Rate: 100%

**Test Distribution:**

| Test Category | File | Lines | Focus |
|--------------|------|-------|-------|
| Infrastructure | test_infrastructure.py | ~300 | State management, config, errors |
| Document Processing | test_document_processing.py | ~400 | PDF extraction, GIS, classification |
| Evidence Extraction | test_evidence_extraction.py | ~350 | Requirement mapping, snippets |
| Validation | test_validation.py | ~400 | Date alignment, tenure, project IDs |
| LLM Extraction | test_llm_extraction.py | ~500 | Date/tenure/ID extraction |
| LLM Integration | test_llm_extraction_integration.py | ~350 | End-to-end LLM flows |
| Report Generation | test_report_generation.py | ~300 | Markdown/JSON reports |
| User Experience | test_user_experience.py | ~250 | Auto-selection, error messages |
| Cost Tracking | test_cost_tracking.py | ~200 | API cost monitoring |
| Locking | test_locking.py | ~150 | Concurrent access, deadlocks |
| **TOTAL** | | **4,111** | |

**Test Quality Indicators:**

**Strengths:**
1. **Shared Fixtures for Cost Optimization:**
   ```python
   @pytest.fixture(scope="session")
   async def botany_farm_dates(botany_farm_markdown):
       """Extract dates once, share across tests."""
       # Saves ~$0.02 per test run
   ```

2. **Comprehensive Cost Tracking in CI:**
   ```python
   def pytest_sessionfinish(session, exitstatus):
       """Print API cost summary after test run."""
       # Tracks: total_cost, cache_hit_rate, test_duration
   ```

3. **Real Data Testing:** Uses actual Botany Farm project files
   ```python
   @pytest.fixture
   def example_documents_path():
       return Path("examples/22-23").absolute()
   ```

4. **Async Test Support:**
   ```python
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   ```

**Critical Gaps:**

1. **NO Integration Tests:**
   - No end-to-end workflow tests (initialize → complete)
   - No multi-document validation scenarios
   - No error recovery testing across workflow stages

2. **Limited Error Case Coverage:**
   - Happy path: ~80% of tests
   - Error cases: ~15% of tests
   - Edge cases: ~5% of tests

3. **No Performance Tests:**
   - No load testing (100+ documents)
   - No concurrency testing (10+ simultaneous sessions)
   - No memory leak detection

4. **No Contract Tests for LLM:**
   - LLM response format changes could break system
   - No schema validation for extraction results

**Testing Gaps by Priority:**

| Priority | Gap | Impact | Effort |
|----------|-----|--------|--------|
| P0 | Integration test suite | High | 3 days |
| P0 | Error recovery tests | High | 2 days |
| P1 | Performance benchmarks | Medium | 2 days |
| P1 | LLM contract tests | Medium | 1 day |
| P2 | Chaos engineering | Low | 3 days |

---

### 3.2 Test Types and Quality

**Rating: B+** - Strong unit tests, weak integration testing

**Current Test Types:**

**1. Unit Tests (Excellent):**
```python
# test_infrastructure.py
async def test_state_manager_atomic_updates():
    """Test atomic file operations with locking."""
    state = StateManager("test-session")

    # Concurrent updates should not corrupt state
    async def update_counter(n):
        for _ in range(n):
            data = state.read_json("session.json")
            data["counter"] = data.get("counter", 0) + 1
            state.write_json("session.json", data)

    await asyncio.gather(update_counter(10), update_counter(10))

    result = state.read_json("session.json")
    assert result["counter"] == 20  # No lost updates
```

**2. Integration Tests (Missing):**
```python
# NEEDED: test_integration.py
async def test_full_workflow_end_to_end():
    """Test complete registry review workflow."""
    # Initialize
    session = await create_session("Test Project", "/path/to/docs")

    # Discovery
    docs = await discover_documents(session["session_id"])
    assert docs["documents_found"] >= 1

    # Extraction
    evidence = await extract_evidence(session["session_id"])
    assert evidence["requirements_covered"] >= 10

    # Validation
    validation = await cross_validate(session["session_id"])
    assert validation["validations_passed"] >= 3

    # Report
    report = await generate_report(session["session_id"])
    assert Path(report["report_path"]).exists()

    # Verify report content
    content = Path(report["report_path"]).read_text()
    assert "Test Project" in content
    assert all(f"REQ-{i:03d}" in content for i in range(1, 11))
```

**3. E2E Tests (Missing):**
```python
# NEEDED: test_e2e.py
async def test_real_world_scenario_botany_farm():
    """Test against real Botany Farm data with timing."""
    import time

    start = time.time()

    # Complete workflow
    session_id = await run_full_workflow(
        "Botany Farm 2022-2023",
        "examples/22-23"
    )

    duration = time.time() - start

    # Verify performance SLA
    assert duration < 120, f"Workflow took {duration}s, expected <120s"

    # Verify accuracy SLA
    report = load_report(session_id)
    assert report["coverage"] >= 0.85, "Expected 85%+ coverage"
```

**4. Property-Based Tests (Missing):**
```python
# NEEDED: test_properties.py
from hypothesis import given, strategies as st

@given(
    owner_name=st.text(min_size=1, max_size=100),
    area=st.floats(min_value=0.1, max_value=10000.0)
)
async def test_tenure_validation_properties(owner_name, area):
    """Property: Tenure validation should never crash."""
    fields = [
        {"owner_name": owner_name, "area_hectares": area, ...}
    ]
    result = await validate_land_tenure("test-session", fields)
    assert "status" in result
    assert result["status"] in ["pass", "warning", "fail"]
```

**Recommendations:**

1. **Integration Test Suite (P0):**
   - Create `tests/integration/` directory
   - Test each workflow stage combination
   - Test error recovery between stages
   - Target: 20 integration tests

2. **E2E Test Suite (P1):**
   - Real-world scenarios with timing assertions
   - Multi-project test corpus
   - Regression test suite for bug fixes
   - Target: 10 E2E tests

3. **Performance Test Suite (P1):**
   - Load tests (100+ documents)
   - Concurrency tests (10+ sessions)
   - Memory profiling tests
   - Target: 5 performance tests

4. **Contract Tests for LLM (P1):**
   - Schema validation for extraction responses
   - Fixture-based tests with example responses
   - Version compatibility tests
   - Target: 15 contract tests

---

### 3.3 Test Maintainability

**Rating: B** - Good fixtures, needs better organization

**Current Maintainability Features:**

**Strengths:**
1. **Shared Fixtures (conftest.py):**
   ```python
   @pytest.fixture(scope="session")
   async def botany_farm_dates(botany_farm_markdown):
       """Shared extraction reduces API costs."""
   ```

2. **Cleanup Automation:**
   ```python
   @pytest.fixture(autouse=True)
   def cleanup_sessions():
       """Clean up before and after each test."""
   ```

3. **Cost Tracking Infrastructure:**
   ```python
   def pytest_sessionfinish(session, exitstatus):
       """Aggregate and report API costs."""
   ```

**Maintainability Concerns:**

1. **Test Data Management:**
   - Real data in `examples/22-23/` (good for E2E, bad for unit tests)
   - No synthetic test data for edge cases
   - No test data versioning

2. **Test Organization:**
   ```
   tests/
   ├── test_*.py          # Flat structure, 13 files
   └── conftest.py

   # SHOULD BE:
   tests/
   ├── unit/              # Fast, isolated tests
   ├── integration/       # Multi-component tests
   ├── e2e/              # Full workflow tests
   ├── performance/       # Load and stress tests
   ├── fixtures/         # Shared test data
   └── conftest.py
   ```

3. **Test Parametrization Underused:**
   ```python
   # Current: Many similar tests
   def test_date_extraction_project_plan():
       ...

   def test_date_extraction_baseline_report():
       ...

   # Should use parametrization:
   @pytest.mark.parametrize("document_type,expected_dates", [
       ("project_plan", 5),
       ("baseline_report", 3),
       ("monitoring_report", 2),
   ])
   def test_date_extraction(document_type, expected_dates):
       ...
   ```

**Recommendations:**

1. **Reorganize Test Structure:**
   ```bash
   mkdir -p tests/{unit,integration,e2e,performance,fixtures}
   mv tests/test_infrastructure.py tests/unit/
   mv tests/test_document_processing.py tests/unit/
   # etc.
   ```

2. **Create Synthetic Test Data:**
   ```python
   # tests/fixtures/synthetic_documents.py
   def create_test_project(
       num_documents: int = 5,
       include_errors: bool = False
   ) -> Path:
       """Generate synthetic project for testing."""
       ...
   ```

3. **Add Test Markers:**
   ```python
   # conftest.py
   pytest.mark.unit = pytest.mark.unit
   pytest.mark.integration = pytest.mark.integration
   pytest.mark.slow = pytest.mark.slow
   pytest.mark.expensive = pytest.mark.expensive

   # Usage:
   @pytest.mark.unit
   def test_fast_unit_test():
       ...

   @pytest.mark.slow
   @pytest.mark.expensive
   async def test_llm_extraction():
       ...
   ```

4. **CI Test Stages:**
   ```yaml
   # .github/workflows/test.yml
   - name: Unit Tests (always)
     run: pytest tests/unit -v

   - name: Integration Tests (PR only)
     run: pytest tests/integration -v

   - name: E2E Tests (main only)
     run: pytest tests/e2e -v
   ```

---

## 4. State Management Analysis

### 4.1 Consistency Guarantees

**Rating: A-** - Strong file-based consistency, limited scalability

**Current State Management:**

**Strengths:**

1. **Atomic Updates with File Locking:**
   ```python
   # state.py
   @contextmanager
   def lock(self, timeout: int | None = None):
       """Acquire exclusive lock for modifications."""
       while True:
           try:
               self.lock_file.touch(exist_ok=False)  # Atomic creation
               break
           except FileExistsError:
               if time.time() - start_time > timeout:
                   raise SessionLockError(...)
               time.sleep(0.1)

       try:
           yield
       finally:
           self.lock_file.unlink()  # Always release
   ```

2. **Atomic File Writes:**
   ```python
   def write_json(self, filename: str, data: dict):
       temp_path = self.session_dir / f".{filename}.tmp"
       with open(temp_path, "w") as f:
           json.dump(data, f, indent=2)
       temp_path.replace(file_path)  # Atomic rename
   ```

3. **Nested Update Support:**
   ```python
   updates = {"workflow_progress.document_discovery": "completed"}
   state.update_json("session.json", updates)
   ```

**Consistency Concerns:**

1. **No Multi-Node Support:**
   - File locking only works on single machine
   - Cannot scale horizontally
   - NFS locking is unreliable

2. **No Transaction Log:**
   - Cannot replay state changes
   - No audit trail for debugging
   - Cannot recover from partial writes

3. **No State Versioning:**
   - Cannot rollback to previous state
   - No conflict resolution for concurrent updates
   - No optimistic locking

4. **State Corruption Risk:**
   ```python
   # If process crashes between read and write:
   data = state.read_json("session.json")  # Crash here
   data["counter"] += 1                     # Or here
   state.write_json("session.json", data)   # Or here

   # State could be corrupted or stale
   ```

**Recommendations:**

1. **Add Transaction Log:**
   ```python
   # utils/transaction_log.py
   class TransactionLog:
       def __init__(self, session_id: str):
           self.log_file = settings.get_session_path(session_id) / "transactions.log"

       def append(self, operation: str, data: dict):
           """Append-only log for audit and recovery."""
           entry = {
               "timestamp": datetime.now(UTC).isoformat(),
               "operation": operation,
               "data": data
           }
           with open(self.log_file, "a") as f:
               f.write(json.dumps(entry) + "\n")

       def replay_from(self, timestamp: datetime) -> dict:
           """Reconstruct state from log."""
           state = {}
           for line in open(self.log_file):
               entry = json.loads(line)
               if entry["timestamp"] >= timestamp.isoformat():
                   apply_operation(state, entry)
           return state
   ```

2. **Add State Versioning:**
   ```python
   {
       "version": 5,
       "previous_version": 4,
       "updated_at": "2025-11-14T10:30:00Z",
       "updated_by": "evidence_extraction",
       "changes": {"requirements_covered": 18},
       ...
   }
   ```

3. **Abstract State Backend:**
   ```python
   # utils/state_backend.py
   class StateBackend(Protocol):
       def read(self, key: str) -> dict:
           ...

       def write(self, key: str, data: dict) -> None:
           ...

       def update(self, key: str, updates: dict) -> dict:
           ...

   class FileStateBackend(StateBackend):
       """Current implementation."""
       ...

   class RedisStateBackend(StateBackend):
       """Future: Distributed state with Redis."""
       ...

   class PostgresStateBackend(StateBackend):
       """Future: ACID transactions with PostgreSQL."""
       ...
   ```

---

### 4.2 Concurrency Handling

**Rating: B** - Good single-machine, poor distributed

**Current Concurrency Support:**

**Strengths:**

1. **File-Based Locking:**
   ```python
   with state.lock(timeout=30):
       data = state.read_json("session.json")
       data["counter"] += 1
       state.write_json("session.json", data)
   ```

2. **Lock Timeout Prevention:**
   ```python
   if time.time() - start_time > timeout:
       raise SessionLockError("Could not acquire lock within 30s")
   ```

3. **Deadlock Prevention:**
   - Fixed locking order (always acquire session lock first)
   - Timeout-based deadlock breaking
   - Lock cleanup in `finally` block

**Concurrency Limitations:**

1. **No Read-Write Lock Separation:**
   ```python
   # All operations require exclusive lock, even reads
   with state.lock():  # Blocks other readers
       data = state.read_json("session.json")

   # SHOULD: Allow concurrent reads, exclusive writes
   with state.read_lock():  # Multiple readers allowed
       data = state.read_json("session.json")

   with state.write_lock():  # Exclusive access
       state.write_json("session.json", data)
   ```

2. **Lock Granularity Too Coarse:**
   ```python
   # Current: Lock entire session for small updates
   with state.lock():  # Blocks ALL session operations
       state.update_json("session.json", {"status": "in_progress"})

   # Better: Lock only specific resources
   with state.lock_resource("session.json"):
       ...
   ```

3. **No Distributed Coordination:**
   - Cannot coordinate across multiple MCP server instances
   - No leader election for distributed processing
   - No distributed transaction support

**Recommendations:**

1. **Implement Read-Write Locks:**
   ```python
   # utils/rwlock.py
   class ReadWriteLock:
       def __init__(self):
           self.readers = 0
           self.writer = False
           self.read_ready = asyncio.Condition()
           self.write_ready = asyncio.Condition()

       async def acquire_read(self):
           async with self.read_ready:
               while self.writer:
                   await self.read_ready.wait()
               self.readers += 1

       async def release_read(self):
           async with self.read_ready:
               self.readers -= 1
               if self.readers == 0:
                   self.write_ready.notify()

       async def acquire_write(self):
           async with self.write_ready:
               while self.writer or self.readers > 0:
                   await self.write_ready.wait()
               self.writer = True
   ```

2. **Add Resource-Level Locking:**
   ```python
   class StateManager:
       def __init__(self, session_id: str):
           self.locks = {}  # resource_name -> Lock

       def lock_resource(self, resource: str):
           if resource not in self.locks:
               self.locks[resource] = asyncio.Lock()
           return self.locks[resource]
   ```

3. **Future: Distributed Locking with Redis:**
   ```python
   # For multi-instance deployments
   from redis.lock import Lock as RedisLock

   class DistributedStateManager:
       def __init__(self, session_id: str, redis_client):
           self.redis = redis_client
           self.session_id = session_id

       def lock(self):
           return RedisLock(
               self.redis,
               f"session:{self.session_id}:lock",
               timeout=30
           )
   ```

---

### 4.3 Corruption Recovery

**Rating: C** - Limited recovery mechanisms

**Current Recovery Capabilities:**

**Strengths:**
1. **Cache Corruption Handling:**
   ```python
   # cache.py
   try:
       with open(cache_path) as f:
           cache_data = json.load(f)
   except (json.JSONDecodeError, KeyError, OSError):
       cache_path.unlink(missing_ok=True)  # Delete corrupted cache
       return default
   ```

2. **Lock File Cleanup:**
   ```python
   finally:
       if self.lock_file.exists():
           self.lock_file.unlink()
   ```

**Critical Gaps:**

1. **No Session Data Recovery:**
   ```python
   # If session.json is corrupted:
   state.read_json("session.json")  # Raises JSONDecodeError
   # → Entire session is lost, no recovery

   # NEEDED:
   def read_json_with_recovery(self, filename: str) -> dict:
       try:
           return self._read_json(filename)
       except json.JSONDecodeError:
           logger.error(f"Corrupted {filename}, attempting recovery")
           backup_path = self.session_dir / f"{filename}.backup"
           if backup_path.exists():
               return self._read_json_from_path(backup_path)
           raise SessionCorruptedError(...)
   ```

2. **No Backup Strategy:**
   - No automatic backups before writes
   - No point-in-time recovery
   - No export/import functionality

3. **No Health Checks:**
   - Cannot detect corruption before it causes failures
   - No validation of state integrity
   - No automatic repair

**Recommendations:**

1. **Automatic Backup Before Write:**
   ```python
   def write_json(self, filename: str, data: dict):
       file_path = self.session_dir / filename

       # Backup existing file
       if file_path.exists():
           backup_path = self.session_dir / f"{filename}.backup"
           shutil.copy2(file_path, backup_path)

       # Write new file atomically
       temp_path = self.session_dir / f".{filename}.tmp"
       with open(temp_path, "w") as f:
           json.dump(data, f, indent=2)
       temp_path.replace(file_path)
   ```

2. **State Validation:**
   ```python
   def validate_session_state(session_id: str) -> list[str]:
       """Validate session state integrity.

       Returns:
           List of validation errors (empty if valid)
       """
       errors = []
       state = StateManager(session_id)

       # Check required files exist
       required_files = ["session.json", "documents.json"]
       for file in required_files:
           if not state.exists(file):
               errors.append(f"Missing required file: {file}")

       # Validate JSON structure
       try:
           session_data = state.read_json("session.json")
           SessionSchema.model_validate(session_data)
       except ValidationError as e:
           errors.append(f"Invalid session.json: {e}")

       return errors
   ```

3. **Recovery Tool:**
   ```python
   # scripts/recover_session.py
   async def recover_session(session_id: str):
       """Attempt to recover corrupted session."""
       state = StateManager(session_id)

       # Try backup files
       for file in state.list_files():
           if file.endswith(".backup"):
               logger.info(f"Found backup: {file}")
               # Restore from backup

       # Reconstruct from transaction log
       if state.exists("transactions.log"):
           logger.info("Reconstructing from transaction log")
           # Replay log

       # Validate recovered state
       errors = validate_session_state(session_id)
       if errors:
           logger.error(f"Recovery failed: {errors}")
       else:
           logger.info("Session recovered successfully")
   ```

---

### 4.4 Migration Strategies

**Rating: D** - No migration support

**Current State:**
- No schema versioning
- No migration scripts
- No backward compatibility

**Critical for Production:**

1. **Schema Evolution:**
   ```python
   # session.json
   {
       "schema_version": "2.0.0",
       "created_at": "2025-11-14T10:00:00Z",
       "project_metadata": {...},
       ...
   }

   # Migration on load:
   def load_session_with_migration(session_id: str) -> dict:
       state = StateManager(session_id)
       data = state.read_json("session.json")

       current_version = data.get("schema_version", "1.0.0")
       if current_version != "2.0.0":
           data = migrate_session(data, current_version, "2.0.0")
           state.write_json("session.json", data)

       return data
   ```

2. **Migration Framework:**
   ```python
   # migrations/migration_manager.py
   class Migration:
       from_version: str
       to_version: str

       def migrate(self, data: dict) -> dict:
           raise NotImplementedError

   class Migration_1_0_to_2_0(Migration):
       from_version = "1.0.0"
       to_version = "2.0.0"

       def migrate(self, data: dict) -> dict:
           # Add new field
           if "workflow_progress" not in data:
               data["workflow_progress"] = {}

           # Rename field
           if "doc_discovery_status" in data:
               data["workflow_progress"]["document_discovery"] = \
                   data.pop("doc_discovery_status")

           data["schema_version"] = "2.0.0"
           return data

   MIGRATIONS = [Migration_1_0_to_2_0()]

   def migrate_session(data: dict, from_ver: str, to_ver: str) -> dict:
       for migration in MIGRATIONS:
           if migration.from_version == from_ver:
               data = migration.migrate(data)
               if migration.to_version == to_ver:
                   return data
       raise ValueError(f"No migration path from {from_ver} to {to_ver}")
   ```

3. **Backward Compatibility Testing:**
   ```python
   # tests/test_migrations.py
   @pytest.mark.parametrize("version,test_data", [
       ("1.0.0", load_fixture("session_v1.json")),
       ("1.5.0", load_fixture("session_v1_5.json")),
   ])
   def test_migration_from_old_version(version, test_data):
       migrated = migrate_session(test_data, version, "2.0.0")
       assert migrated["schema_version"] == "2.0.0"
       SessionSchema.model_validate(migrated)  # Must be valid
   ```

**Recommendations:**
1. Add schema versioning to all state files (P0)
2. Create migration framework (P0)
3. Build migration tests for each schema change (P0)
4. Document migration strategy in ARCHITECTURE.md (P1)

---

## 5. Performance Analysis

### 5.1 Bottleneck Identification

**Rating: C** - No systematic profiling, known bottlenecks

**Known Performance Characteristics:**

From ROADMAP.md:
- Complete workflow: <2 minutes (warm cache)
- Document discovery: <10 seconds
- Evidence extraction: <90 seconds
- 95%+ accuracy on document classification
- 90%+ accuracy on evidence location

**Identified Bottlenecks:**

1. **Sequential PDF Processing:**
   ```python
   # Current: Processes PDFs one at a time
   for doc in documents:
       text = await extract_pdf_text(doc.filepath)  # Blocking I/O
       classify_document(doc, text)

   # SHOULD: Parallel processing
   tasks = [extract_pdf_text(doc.filepath) for doc in documents]
   results = await asyncio.gather(*tasks)
   ```

2. **LLM API Latency:**
   - Average API call: 2-5 seconds
   - 20 requirements × 2 API calls = 40-100 seconds
   - No batching or parallelization

3. **Inefficient Evidence Snippet Extraction:**
   ```python
   # Current: Linear search through entire document
   for req in requirements:
       for doc in documents:
           full_text = load_full_text(doc)  # Loads entire PDF
           snippets = search_keywords(full_text, req.keywords)

   # SHOULD: Indexed search with lazy loading
   index = build_search_index(documents)  # One-time cost
   snippets = index.search(req.keywords, limit=5)  # O(log n)
   ```

4. **Cache Miss Penalty:**
   - Cold cache: 2 minutes
   - Warm cache: <1 minute
   - No cache pre-warming strategy

**Performance Measurement Gaps:**

1. **No Built-in Profiling:**
   - Cannot identify slow functions
   - No memory profiling
   - No database (file I/O) query analysis

2. **No Performance Regression Tests:**
   - Changes could silently degrade performance
   - No baseline benchmarks
   - No CI performance checks

**Recommendations:**

1. **Add Performance Profiling:**
   ```python
   # utils/profiling.py
   import cProfile
   import pstats
   from functools import wraps

   def profile_async(func):
       @wraps(func)
       async def wrapper(*args, **kwargs):
           profiler = cProfile.Profile()
           profiler.enable()

           result = await func(*args, **kwargs)

           profiler.disable()
           stats = pstats.Stats(profiler)
           stats.sort_stats('cumulative')
           stats.print_stats(20)  # Top 20 slowest functions

           return result
       return wrapper

   # Usage:
   @profile_async
   async def extract_evidence(session_id: str):
       ...
   ```

2. **Add Performance Metrics:**
   ```python
   # utils/metrics.py
   from prometheus_client import Summary, Histogram

   EVIDENCE_EXTRACTION_TIME = Summary(
       'evidence_extraction_seconds',
       'Time spent extracting evidence'
   )

   DOCUMENT_PROCESSING_TIME = Histogram(
       'document_processing_seconds',
       'Time to process single document',
       buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
   )

   # Usage:
   @EVIDENCE_EXTRACTION_TIME.time()
   async def extract_evidence(...):
       ...
   ```

3. **Performance Benchmarks:**
   ```python
   # tests/performance/test_benchmarks.py
   @pytest.mark.benchmark
   async def test_document_discovery_benchmark(benchmark):
       result = await benchmark(discover_documents, session_id)
       assert result["duration"] < 10.0  # SLA: <10 seconds

   @pytest.mark.benchmark
   async def test_full_workflow_benchmark(benchmark):
       result = await benchmark(run_full_workflow, "test-project")
       assert result["duration"] < 120.0  # SLA: <2 minutes
   ```

---

### 5.2 Optimization Opportunities

**Rating: B** - Good caching, needs parallelization

**Current Optimizations:**

**Strengths:**

1. **LLM Prompt Caching:**
   ```python
   system=[
       {
           "type": "text",
           "text": DATE_EXTRACTION_PROMPT,
           "cache_control": {"type": "ephemeral"}  # 90% cost savings
       }
   ]
   ```

2. **PDF Text Caching:**
   ```python
   cache_key = hashlib.sha256(filepath.encode()).hexdigest()
   if cached := pdf_cache.get(cache_key):
       return cached
   ```

3. **Shared Test Fixtures:**
   ```python
   @pytest.fixture(scope="session")
   async def botany_farm_dates(botany_farm_markdown):
       """Extract once, reuse across tests."""
   ```

**Optimization Opportunities:**

1. **Parallel Document Processing:**
   ```python
   # Current: Sequential
   for doc in documents:
       result = await process_document(doc)

   # Optimized: Parallel with concurrency limit
   semaphore = asyncio.Semaphore(settings.max_concurrent_extractions)

   async def process_with_limit(doc):
       async with semaphore:
           return await process_document(doc)

   results = await asyncio.gather(*[
       process_with_limit(doc) for doc in documents
   ])
   ```

2. **Batch LLM API Calls:**
   ```python
   # Current: One requirement per API call
   for req in requirements:
       result = await extract_evidence_for_requirement(req)

   # Optimized: Batch multiple requirements
   batch_size = 5
   for i in range(0, len(requirements), batch_size):
       batch = requirements[i:i+batch_size]
       prompt = build_batch_prompt(batch)
       results = await llm_api.call(prompt)
       parse_batch_results(results, batch)
   ```

3. **Lazy Loading:**
   ```python
   # Current: Loads all PDF text upfront
   documents = [
       {"filepath": path, "text": extract_pdf_text(path)}
       for path in document_paths
   ]

   # Optimized: Load on demand
   class LazyDocument:
       def __init__(self, filepath):
           self.filepath = filepath
           self._text = None

       @property
       def text(self):
           if self._text is None:
               self._text = extract_pdf_text(self.filepath)
           return self._text
   ```

4. **Search Indexing:**
   ```python
   # utils/search_index.py
   from whoosh.index import create_in
   from whoosh.fields import Schema, TEXT, ID

   class DocumentIndex:
       def __init__(self, session_id: str):
           schema = Schema(
               doc_id=ID(stored=True),
               content=TEXT(stored=True),
               page=ID(stored=True)
           )
           self.index = create_in(index_dir, schema)

       def add_document(self, doc_id: str, content: str, page: int):
           writer = self.index.writer()
           writer.add_document(doc_id=doc_id, content=content, page=str(page))
           writer.commit()

       def search(self, query: str, limit: int = 10):
           with self.index.searcher() as searcher:
               results = searcher.search(query, limit=limit)
               return [
                   {"doc_id": r["doc_id"], "content": r["content"], "page": r["page"]}
                   for r in results
               ]
   ```

**Estimated Performance Gains:**

| Optimization | Current Time | Optimized Time | Savings |
|--------------|--------------|----------------|---------|
| Parallel PDF processing | 30s (10 docs × 3s) | 6s (max 3s × 2 batches) | 80% |
| Batch LLM calls | 60s (20 reqs × 3s) | 15s (4 batches × 3.75s) | 75% |
| Search indexing | 10s per search | 0.1s per search | 99% |
| **Total** | **120s** | **30s** | **75%** |

---

### 5.3 Scalability Limits

**Rating: C** - Limited by architecture

**Current Limits:**

1. **Single Instance Only:**
   - File-based locking prevents multi-instance deployment
   - Cannot scale horizontally
   - All processing on single machine

2. **Memory Constraints:**
   ```python
   # Loads entire PDF into memory
   full_text = extract_pdf_text(filepath)  # Could be 10+ MB

   # All evidence kept in memory
   evidence_data = {
       "evidence": [...]  # Could be thousands of snippets
   }
   ```

3. **File System I/O:**
   - Sequential file operations
   - No distributed file system support
   - Local disk only

4. **No Queue System:**
   - Cannot defer expensive operations
   - No background job processing
   - Cannot prioritize urgent reviews

**Scalability Recommendations:**

1. **Introduce Queue System:**
   ```python
   # Use Celery or similar
   from celery import Celery

   app = Celery('registry_review')

   @app.task
   async def process_document_async(session_id: str, doc_path: str):
       """Background document processing."""
       result = await document_tools.extract_pdf_text(doc_path)
       update_session_state(session_id, {"documents_processed": +1})
       return result

   # Submit to queue
   for doc in documents:
       process_document_async.delay(session_id, doc.filepath)
   ```

2. **Streaming Processing:**
   ```python
   async def extract_evidence_streaming(session_id: str):
       """Process evidence in chunks to limit memory."""
       async for requirement in iter_requirements(session_id):
           evidence = await extract_evidence_for_requirement(requirement)
           yield evidence  # Stream results instead of accumulating
   ```

3. **Distributed State Backend:**
   ```python
   # Replace file-based state with Redis/PostgreSQL
   class RedisStateManager:
       def __init__(self, session_id: str, redis_client):
           self.redis = redis_client
           self.session_key = f"session:{session_id}"

       async def read_json(self, filename: str) -> dict:
           data = await self.redis.hget(self.session_key, filename)
           return json.loads(data)

       async def write_json(self, filename: str, data: dict):
           await self.redis.hset(self.session_key, filename, json.dumps(data))
   ```

**Target Scalability:**
- Support 10+ concurrent sessions
- Process 100+ document projects
- Handle 1000+ requirements efficiently

---

### 5.4 Resource Usage

**Rating: B** - Reasonable usage, needs monitoring

**Current Resource Profile:**

**CPU Usage:**
- PDF extraction: High (pdfplumber CPU-intensive)
- LLM API calls: Low (I/O bound)
- Evidence extraction: Medium (text processing)

**Memory Usage:**
- Session state: ~1-5 MB per session
- PDF cache: ~10-50 MB per document
- Evidence data: ~5-10 MB per session
- **Total estimate:** 50-100 MB per active session

**Disk Usage:**
- Sessions: ~10-20 MB per session
- Cache: ~100-500 MB (depends on TTL)
- Logs: ~1-10 MB per day

**Network Usage:**
- LLM API: ~50-500 KB per request
- Image uploads: ~100-500 KB per image
- **Total estimate:** 5-20 MB per workflow

**Resource Monitoring Needs:**

1. **Add Resource Tracking:**
   ```python
   # utils/resource_monitor.py
   import psutil
   import os

   class ResourceMonitor:
       @staticmethod
       def get_process_stats():
           process = psutil.Process(os.getpid())
           return {
               "cpu_percent": process.cpu_percent(),
               "memory_mb": process.memory_info().rss / 1024 / 1024,
               "num_threads": process.num_threads(),
               "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None
           }

       @staticmethod
       def get_system_stats():
           return {
               "cpu_percent": psutil.cpu_percent(),
               "memory_percent": psutil.virtual_memory().percent,
               "disk_percent": psutil.disk_usage('/').percent
           }
   ```

2. **Resource Limits:**
   ```python
   # config/settings.py additions
   max_memory_mb: int = 1024  # 1 GB limit
   max_cache_size_mb: int = 500
   max_concurrent_sessions: int = 10

   # Enforce limits
   if get_memory_usage() > settings.max_memory_mb:
       cache.clear()  # Emergency cache eviction
       logger.warning("Memory limit exceeded, cache cleared")
   ```

3. **Metrics Export:**
   ```python
   from prometheus_client import Gauge

   MEMORY_USAGE = Gauge('process_memory_bytes', 'Process memory usage')
   ACTIVE_SESSIONS = Gauge('active_sessions', 'Number of active sessions')
   CACHE_SIZE = Gauge('cache_size_bytes', 'Cache size in bytes')

   # Update periodically
   async def update_metrics():
       while True:
           stats = ResourceMonitor.get_process_stats()
           MEMORY_USAGE.set(stats["memory_mb"] * 1024 * 1024)
           ACTIVE_SESSIONS.set(count_active_sessions())
           await asyncio.sleep(10)
   ```

---

## 6. Observability Improvements

### 6.1 Logging Strategy

**Rating: C** - Basic logging, needs structure

**Current Logging:**

**Implementation:**
```python
# server.py
logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format,
    stream=sys.stderr,  # Correct for MCP protocol
)
logger = logging.getLogger(__name__)

# Usage throughout codebase
logger.info(f"Creating session for project: {project_name}")
logger.error(f"Failed to create session: {e}", exc_info=True)
```

**Strengths:**
- Logs to stderr (MCP requirement)
- Configurable log level
- Exception tracing with `exc_info=True`
- Module-level loggers

**Critical Gaps:**

1. **No Structured Logging:**
   ```python
   # Current: String formatting, hard to parse
   logger.info(f"Session created: {session_id}")

   # NEEDED: Structured logging with context
   logger.info("session_created",
       session_id=session_id,
       project_name=project_name,
       duration_ms=duration * 1000,
       user_id=user_id
   )

   # Output (JSON):
   # {"timestamp": "2025-11-14T10:00:00Z", "level": "info",
   #  "event": "session_created", "session_id": "session-20251114-100000",
   #  "project_name": "Botany Farm", "duration_ms": 234}
   ```

2. **No Correlation IDs:**
   ```python
   # Cannot trace request across multiple operations
   logger.info("Starting document discovery")
   logger.info("Processing PDF")
   logger.info("Document discovery complete")

   # Which documents? Which session? Which user?
   ```

3. **Inconsistent Log Messages:**
   - Some messages have context, some don't
   - No standard format for errors
   - No log levels standardization

4. **No Log Aggregation:**
   - Logs go to stderr only
   - No centralized log collection
   - No log analysis tools

**Recommendations:**

1. **Migrate to Structured Logging:**
   ```python
   # config/logging_config.py
   import structlog

   def configure_logging():
       structlog.configure(
           processors=[
               structlog.stdlib.filter_by_level,
               structlog.stdlib.add_logger_name,
               structlog.stdlib.add_log_level,
               structlog.stdlib.PositionalArgumentsFormatter(),
               structlog.processors.TimeStamper(fmt="iso"),
               structlog.processors.StackInfoRenderer(),
               structlog.processors.format_exc_info,
               structlog.processors.UnicodeDecoder(),
               structlog.processors.JSONRenderer()
           ],
           context_class=dict,
           logger_factory=structlog.stdlib.LoggerFactory(),
           cache_logger_on_first_use=True,
       )

   # Usage:
   logger = structlog.get_logger()
   logger.info("session_created",
       session_id=session_id,
       project_name=project_name,
       documents_found=7
   )
   ```

2. **Add Correlation IDs:**
   ```python
   # utils/context.py
   from contextvars import ContextVar

   correlation_id: ContextVar[str] = ContextVar('correlation_id', default=None)

   def set_correlation_id(cid: str):
       correlation_id.set(cid)

   def get_correlation_id() -> str:
       return correlation_id.get() or str(uuid.uuid4())

   # Middleware to inject into all logs
   class CorrelationIDProcessor:
       def __call__(self, logger, method_name, event_dict):
           event_dict['correlation_id'] = get_correlation_id()
           return event_dict

   # Server entry point
   @mcp.tool()
   async def discover_documents(session_id: str) -> str:
       correlation_id = str(uuid.uuid4())
       set_correlation_id(correlation_id)
       logger.info("document_discovery_started", session_id=session_id)
       ...
   ```

3. **Standardize Log Events:**
   ```python
   # utils/log_events.py
   class LogEvent:
       # Session events
       SESSION_CREATED = "session.created"
       SESSION_LOADED = "session.loaded"
       SESSION_UPDATED = "session.updated"

       # Document events
       DOCUMENT_DISCOVERED = "document.discovered"
       DOCUMENT_CLASSIFIED = "document.classified"
       PDF_EXTRACTED = "pdf.extracted"

       # Evidence events
       EVIDENCE_EXTRACTION_STARTED = "evidence.extraction.started"
       EVIDENCE_EXTRACTION_COMPLETED = "evidence.extraction.completed"

       # LLM events
       LLM_API_CALLED = "llm.api.called"
       LLM_API_FAILED = "llm.api.failed"
       LLM_CACHE_HIT = "llm.cache.hit"

   # Usage:
   logger.info(LogEvent.DOCUMENT_DISCOVERED,
       session_id=session_id,
       document_path=str(filepath),
       document_type=doc_type
   )
   ```

4. **Log Aggregation (Future):**
   ```python
   # Send logs to ELK/Loki/Datadog
   import logging_loki

   handler = logging_loki.LokiHandler(
       url="https://loki.example.com:3100/loki/api/v1/push",
       tags={"application": "registry-review-mcp"},
       version="1",
   )
   logging.root.addHandler(handler)
   ```

---

### 6.2 Metrics Collection

**Rating: D** - Minimal metrics

**Current Metrics:**

**Cost Tracking (Good):**
```python
# utils/cost_tracker.py
{
    "total_cost_usd": 0.0234,
    "total_api_calls": 15,
    "total_input_tokens": 45000,
    "total_output_tokens": 3000,
    "cache_hit_rate": 0.67
}
```

**Missing Critical Metrics:**

1. **Performance Metrics:**
   - Request latency (p50, p95, p99)
   - Operation duration
   - Throughput (requests/minute)

2. **Business Metrics:**
   - Sessions created per day
   - Success rate (completed vs failed workflows)
   - Average documents per session
   - Average requirements coverage

3. **System Metrics:**
   - CPU/memory usage
   - Cache hit rate (PDF, LLM)
   - Error rate by type
   - Queue depth (if implemented)

**Recommendations:**

1. **Add Prometheus Metrics:**
   ```python
   # utils/metrics.py
   from prometheus_client import Counter, Histogram, Gauge, Summary

   # Request metrics
   REQUEST_COUNT = Counter(
       'mcp_requests_total',
       'Total MCP requests',
       ['tool', 'status']
   )

   REQUEST_DURATION = Histogram(
       'mcp_request_duration_seconds',
       'Request duration',
       ['tool'],
       buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
   )

   # Business metrics
   SESSIONS_CREATED = Counter('sessions_created_total', 'Total sessions created')
   DOCUMENTS_PROCESSED = Counter('documents_processed_total', 'Total documents')
   REQUIREMENTS_COVERED = Histogram(
       'requirements_coverage_ratio',
       'Requirements coverage',
       buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0]
   )

   # System metrics
   ACTIVE_SESSIONS = Gauge('active_sessions', 'Currently active sessions')
   CACHE_SIZE = Gauge('cache_size_bytes', 'Cache size')
   CACHE_HIT_RATE = Gauge('cache_hit_rate', 'Cache hit rate')

   # LLM metrics
   LLM_API_CALLS = Counter(
       'llm_api_calls_total',
       'LLM API calls',
       ['extractor', 'status']
   )
   LLM_API_DURATION = Summary(
       'llm_api_duration_seconds',
       'LLM API call duration'
   )
   LLM_COST = Counter('llm_cost_usd_total', 'Total LLM cost')
   ```

2. **Instrument Code:**
   ```python
   # Decorator for automatic instrumentation
   def instrument_tool(tool_name: str):
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               with REQUEST_DURATION.labels(tool=tool_name).time():
                   try:
                       result = await func(*args, **kwargs)
                       REQUEST_COUNT.labels(tool=tool_name, status='success').inc()
                       return result
                   except Exception as e:
                       REQUEST_COUNT.labels(tool=tool_name, status='error').inc()
                       raise
           return wrapper
       return decorator

   # Usage:
   @instrument_tool('discover_documents')
   @mcp.tool()
   async def discover_documents(session_id: str) -> str:
       ...
   ```

3. **Metrics Endpoint:**
   ```python
   # server.py
   from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

   @mcp.resource("metrics")
   def metrics():
       """Expose Prometheus metrics."""
       return {
           "uri": "metrics://registry-review/prometheus",
           "mime_type": CONTENT_TYPE_LATEST,
           "text": generate_latest().decode('utf-8')
       }
   ```

---

### 6.3 Error Tracking

**Rating: C** - Basic exception logging, no aggregation

**Current Error Tracking:**

```python
# Logging exceptions
logger.error(f"Failed to extract PDF text: {e}", exc_info=True)

# Returning error messages to user
return f"✗ Error: {str(e)}"
```

**Missing Error Tracking:**

1. **No Error Aggregation:**
   - Cannot see error trends
   - No error rate monitoring
   - No error grouping by type

2. **No Error Context:**
   - Missing user context
   - No breadcrumb trail
   - No environment info

3. **No Alerting:**
   - No notifications for critical errors
   - No error budget tracking
   - No SLO monitoring

**Recommendations:**

1. **Integrate Sentry (Optional):**
   ```python
   # config/error_tracking.py
   import sentry_sdk
   from sentry_sdk.integrations.asyncio import AsyncioIntegration

   def configure_sentry():
       if settings.sentry_dsn:
           sentry_sdk.init(
               dsn=settings.sentry_dsn,
               environment=settings.environment,
               release=settings.version,
               traces_sample_rate=0.1,
               integrations=[AsyncioIntegration()]
           )

   # Add context
   def set_error_context(session_id: str, user_id: str | None = None):
       with sentry_sdk.configure_scope() as scope:
           scope.set_tag("session_id", session_id)
           if user_id:
               scope.set_user({"id": user_id})

   # Capture exceptions
   try:
       result = await extract_evidence(session_id)
   except Exception as e:
       sentry_sdk.capture_exception(e)
       raise
   ```

2. **Error Budget Tracking:**
   ```python
   # utils/error_budget.py
   class ErrorBudget:
       def __init__(self, target_slo: float = 0.99):
           self.target_slo = target_slo  # 99% success rate
           self.total_requests = 0
           self.failed_requests = 0

       def record_request(self, success: bool):
           self.total_requests += 1
           if not success:
               self.failed_requests += 1

       @property
       def success_rate(self) -> float:
           if self.total_requests == 0:
               return 1.0
           return 1.0 - (self.failed_requests / self.total_requests)

       @property
       def budget_remaining(self) -> float:
           """Percentage of error budget remaining."""
           if self.success_rate >= self.target_slo:
               return 1.0
           return (self.success_rate - self.target_slo) / (1.0 - self.target_slo)

       def should_alert(self) -> bool:
           return self.budget_remaining < 0.2  # 20% budget remaining
   ```

3. **Error Dashboard:**
   - Visualize error rates over time
   - Group errors by type, session, user
   - Alert on error budget exhaustion

---

### 6.4 Debugging Support

**Rating: B** - Good logging, needs tooling

**Current Debugging Capabilities:**

**Strengths:**
1. Detailed exception tracing
2. Module-level loggers
3. Configurable log levels
4. Session state persistence (can inspect after failure)

**Debugging Gaps:**

1. **No Debug Mode:**
   ```python
   # NEEDED:
   if settings.debug_mode:
       # Log all API requests/responses
       # Save intermediate results
       # Enable verbose logging
   ```

2. **No Interactive Debugging:**
   - Cannot attach debugger to running server
   - No REPL for inspecting state
   - No breakpoint support

3. **No Debug Tools:**
   - No session inspector tool
   - No state diff tool
   - No log analyzer

**Recommendations:**

1. **Debug Mode:**
   ```python
   # config/settings.py
   debug_mode: bool = Field(default=False)
   save_intermediate_results: bool = Field(default=False)
   log_api_requests: bool = Field(default=False)

   # Enable debug mode
   if settings.debug_mode:
       logger.setLevel(logging.DEBUG)

       # Log all LLM API calls
       if settings.log_api_requests:
           async def log_api_call(request, response):
               debug_logger.debug("llm_api_call",
                   request=request,
                   response=response,
                   duration=response.headers.get("x-request-duration")
               )
   ```

2. **Session Inspector Tool:**
   ```python
   # scripts/inspect_session.py
   import json
   from pathlib import Path

   def inspect_session(session_id: str):
       """Interactive session inspection tool."""
       session_dir = settings.get_session_path(session_id)

       print(f"Session: {session_id}")
       print(f"Path: {session_dir}")
       print("\nFiles:")
       for file in session_dir.glob("*.json"):
           size = file.stat().st_size
           print(f"  - {file.name} ({size} bytes)")

       # Load and display session data
       session_data = json.loads((session_dir / "session.json").read_text())
       print(f"\nStatus: {session_data['status']}")
       print(f"Created: {session_data['created_at']}")
       print(f"Documents: {session_data['statistics']['documents_found']}")
       print(f"Coverage: {session_data['statistics']['requirements_covered']}")

       # Interactive prompt
       while True:
           cmd = input("\nCommand (show/diff/validate/quit): ")
           if cmd == "quit":
               break
           elif cmd == "show":
               file = input("File: ")
               print(json.dumps(json.loads((session_dir / file).read_text()), indent=2))
           # ... more commands
   ```

3. **Log Analyzer:**
   ```python
   # scripts/analyze_logs.py
   def analyze_logs(log_file: Path):
       """Analyze structured logs for patterns."""
       events = []
       for line in log_file.read_text().splitlines():
           try:
               events.append(json.loads(line))
           except json.JSONDecodeError:
               continue

       # Analyze
       print(f"Total events: {len(events)}")
       print(f"Error rate: {sum(1 for e in events if e['level'] == 'error') / len(events) * 100:.2f}%")

       # Group by session
       by_session = {}
       for event in events:
           session_id = event.get('session_id')
           if session_id:
               by_session.setdefault(session_id, []).append(event)

       print(f"\nSessions: {len(by_session)}")
       for session_id, session_events in by_session.items():
           duration = (
               datetime.fromisoformat(session_events[-1]['timestamp']) -
               datetime.fromisoformat(session_events[0]['timestamp'])
           ).total_seconds()
           print(f"  {session_id}: {len(session_events)} events, {duration:.1f}s")
   ```

---

## 7. Prioritized Technical Debt Items

### P0 (Critical - Must Address Before Production)

1. **Integration Test Suite** (3 days)
   - End-to-end workflow tests
   - Error recovery scenarios
   - Multi-document validation
   - Target: 20 integration tests

2. **Circuit Breaker for LLM API** (1 day)
   - Prevent cascading failures
   - Graceful degradation
   - Fallback to regex extraction

3. **State Corruption Recovery** (2 days)
   - Automatic backups
   - State validation
   - Recovery tools

4. **Schema Versioning and Migration** (2 days)
   - Version all state files
   - Migration framework
   - Backward compatibility

### P1 (High - Production Ready)

5. **Structured Logging Migration** (2 days)
   - Replace `logging` with `structlog`
   - Add correlation IDs
   - Standardize log events

6. **Metrics Collection** (2 days)
   - Prometheus instrumentation
   - Performance metrics
   - Business metrics
   - Metrics endpoint

7. **Performance Optimization** (3 days)
   - Parallel document processing
   - Batch LLM calls
   - Search indexing

8. **Error Tracking Integration** (1 day)
   - Sentry integration (optional)
   - Error budget tracking
   - Alerting rules

### P2 (Medium - Enhanced Production)

9. **Retry Logic for All I/O** (1 day)
   - PDF extraction retry
   - GIS file loading retry
   - File lock backoff improvement

10. **Resource Monitoring** (2 days)
    - Memory/CPU tracking
    - Resource limits enforcement
    - Metrics export

11. **Debug Tooling** (2 days)
    - Session inspector
    - Log analyzer
    - Debug mode

12. **Extractor Modularity** (2 days)
    - Split `llm_extractors.py`
    - Extractor registry pattern
    - Plugin system

### P3 (Low - Nice to Have)

13. **Distributed State Backend** (5 days)
    - Redis/PostgreSQL backend
    - Multi-instance support
    - Distributed locking

14. **Queue System** (3 days)
    - Background job processing
    - Celery integration
    - Priority queues

15. **Advanced Testing** (3 days)
    - Property-based tests
    - Chaos engineering
    - Load testing

---

## 8. Summary and Recommendations

### 8.1 Overall Code Quality Assessment

**Grade: B+** (Good, with clear improvement path)

The Registry Review MCP system demonstrates strong engineering fundamentals:
- Clean architecture with excellent separation of concerns
- Comprehensive error hierarchy and handling
- Strong test coverage (120 tests, 100% passing)
- Production-ready LLM integration with retry logic and caching
- Well-documented codebase with clear roadmap

However, critical gaps prevent immediate production deployment:
- Missing integration and E2E tests
- No circuit breaker for LLM API resilience
- Limited observability (logging, metrics, tracing)
- No state corruption recovery mechanisms
- Single-instance architecture limits scalability

### 8.2 Production Readiness Checklist

**Current Status: 70% Production Ready**

✅ **Completed:**
- [x] Error hierarchy and handling
- [x] Unit test coverage
- [x] State management with locking
- [x] LLM retry logic with exponential backoff
- [x] Cost tracking and optimization
- [x] PDF/GIS extraction
- [x] Evidence mapping and validation
- [x] Report generation

⚠️ **In Progress (Phase 5):**
- [~] Integration tests (0% complete)
- [~] Example workflow documentation (0% complete)

❌ **Missing (P0 Requirements):**
- [ ] Circuit breaker for LLM API
- [ ] State corruption recovery
- [ ] Schema versioning and migration
- [ ] Structured logging with correlation IDs
- [ ] Metrics collection (Prometheus)
- [ ] Error aggregation and alerting

### 8.3 Recommended Implementation Plan

**Phase 1: Production Hardening (2 weeks)**

Week 1:
- Day 1-2: Add circuit breaker for LLM API
- Day 3-4: Implement state corruption recovery
- Day 5: Add schema versioning

Week 2:
- Day 1-2: Migrate to structured logging
- Day 3-4: Add metrics collection
- Day 5: Integration test suite setup

**Phase 2: Testing & Observability (1 week)**

Week 3:
- Day 1-3: Write integration tests (target: 20 tests)
- Day 4-5: Add error tracking and alerting

**Phase 3: Performance & Scalability (1 week)**

Week 4:
- Day 1-2: Parallel document processing
- Day 3-4: Batch LLM calls
- Day 5: Performance benchmarks

**Total Effort: 4 weeks to production-grade system**

### 8.4 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM API downtime | High | High | Circuit breaker + fallback extraction |
| State corruption | Medium | High | Automatic backups + validation |
| Performance degradation | Medium | Medium | Metrics + benchmarks + optimization |
| Schema evolution breakage | High | High | Versioning + migration framework |
| Memory leaks | Low | Medium | Resource monitoring + limits |
| Concurrency bugs | Low | High | Integration tests + locking tests |

### 8.5 Next Steps

**Immediate Actions (This Week):**
1. Create `TECHNICAL_DEBT.md` with prioritized items
2. Set up integration test framework
3. Implement circuit breaker for LLM API
4. Add basic metrics collection

**Short Term (Next Month):**
1. Complete Phase 1 production hardening
2. Achieve 100% integration test coverage
3. Deploy to staging environment
4. Conduct load testing

**Long Term (Next Quarter):**
1. Migrate to distributed state backend
2. Add queue system for background processing
3. Multi-methodology support
4. Cloud storage connectors

---

## Appendix A: Code Metrics

### A.1 Codebase Statistics

**Source Code:**
- Total lines: 7,400
- Python files: 28
- Average file size: 264 lines
- Largest file: `llm_extractors.py` (1,202 lines)

**Test Code:**
- Total lines: 4,111
- Test files: 13
- Test-to-code ratio: 55.5%
- Total tests: 120 (100% passing)

**Documentation:**
- README.md: Comprehensive
- ROADMAP.md: Detailed
- Inline docs: Good
- API docs: Good (docstrings)

### A.2 Dependency Analysis

**Core Dependencies:** 9
- mcp: MCP protocol
- pdfplumber: PDF extraction
- pydantic: Data validation
- anthropic: LLM API
- fiona: GIS processing

**Development Dependencies:** 4
- pytest: Testing framework
- black: Code formatting
- ruff: Linting

**Security:**
- No known vulnerabilities
- Regular dependency updates via `uv`
- Version pinning strategy

### A.3 Performance Benchmarks

**Current Performance (from ROADMAP.md):**
- Full workflow: <2 minutes (warm cache)
- Document discovery: <10 seconds
- Evidence extraction: <90 seconds
- Classification accuracy: 95%+
- Evidence location accuracy: 90%+

**Target Performance (Post-Optimization):**
- Full workflow: <30 seconds (warm cache)
- Document discovery: <5 seconds
- Evidence extraction: <20 seconds
- Classification accuracy: 95%+
- Evidence location accuracy: 90%+

---

## Appendix B: Industry Best Practices Alignment

### B.1 Python Production Best Practices

| Practice | Status | Notes |
|----------|--------|-------|
| Type hints | ✅ Partial | Good coverage, could be expanded |
| Docstrings | ✅ Good | Comprehensive function docs |
| Error handling | ✅ Good | Custom error hierarchy |
| Logging | ⚠️ Basic | Needs structured logging |
| Testing | ✅ Good | 100% pass rate, needs integration tests |
| Code formatting | ✅ Good | Black + Ruff configured |
| Dependency management | ✅ Excellent | UV with version pinning |
| Security | ✅ Good | API key management, no hardcoded secrets |

### B.2 MCP Server Best Practices

| Practice | Status | Notes |
|----------|--------|-------|
| Tool design | ✅ Excellent | Well-scoped, task-oriented tools |
| Idempotency | ⚠️ Partial | Needs request ID support |
| Error messages | ✅ Good | User-friendly, actionable |
| Logging to stderr | ✅ Correct | MCP protocol compliant |
| Schema validation | ✅ Good | Pydantic models throughout |
| Documentation | ✅ Good | Comprehensive docstrings |
| Containerization | ❌ Missing | Not yet containerized |
| Health checks | ❌ Missing | No health endpoint |

### B.3 AI System Testing Best Practices

| Practice | Status | Notes |
|----------|--------|-------|
| Unit testing | ✅ Good | 120 tests passing |
| Integration testing | ❌ Missing | Critical gap |
| E2E testing | ❌ Missing | Needed for real-world validation |
| LLM contract testing | ❌ Missing | Response schema validation |
| Ground truth validation | ✅ Good | Botany Farm accuracy tests |
| Cost tracking | ✅ Excellent | Comprehensive cost monitoring |
| Caching | ✅ Excellent | Prompt caching, PDF caching |
| Fallback strategies | ⚠️ Partial | Needs non-LLM fallbacks |

---

**Document Version:** 1.0
**Last Updated:** November 14, 2025
**Next Review:** End of Phase 5 (Integration & Polish)
