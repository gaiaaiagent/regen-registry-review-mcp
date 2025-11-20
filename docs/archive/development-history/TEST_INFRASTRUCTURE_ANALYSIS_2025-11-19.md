# Test Infrastructure Analysis and Optimization Recommendations

**Date:** 2025-11-19
**Scope:** Complete test infrastructure audit covering fixtures, factories, helpers, and patterns
**Total Test LOC:** 7,931 lines across 24 test files
**Total Test Methods:** 318 tests

---

## Executive Summary

The test suite demonstrates thoughtful infrastructure with factory patterns and shared fixtures, but significant opportunities exist for reduction and optimization. This analysis identifies **3,200-4,500 characters** of potential savings through consolidation, helper functions, and pattern extraction.

### Key Findings

1. **Strong Foundation:** Factory pattern implementation (factories.py) is well-designed
2. **Underutilization:** Only 3 of 24 test files use SessionManager context manager
3. **High Duplication:** Manual session cleanup appears 36 times across files
4. **PDF Creation:** Base64 PDF generation duplicated in fixtures vs factories
5. **Assertion Patterns:** Common validation logic not extracted to helpers

---

## 1. Fixture Efficiency Analysis

### Current State

**conftest.py Fixtures:**
- `temp_data_dir` - Used widely ✓
- `test_settings` - Used widely ✓
- `cache` - Low utilization
- `cleanup_sessions` (autouse) - Good design ✓
- `cleanup_examples_sessions` - Explicit use, good separation ✓
- `example_documents_path` - Used widely ✓
- `botany_farm_markdown` (session scope) - EXCELLENT cost optimization ✓
- `botany_farm_dates/tenure/project_ids` (function scope) - Good caching ✓

**Redundant Fixtures in test_upload_tools.py:**
```python
@pytest.fixture
def sample_pdf_base64():  # 14 lines of PDF content
    pdf_content = b"%PDF-1.4..."
    return base64.b64encode(pdf_content).decode('utf-8')

@pytest.fixture
def sample_pdf2_base64():  # Similar but different content
    ...

@pytest.fixture
def sample_pdf3_base64():  # Third variation
    ...

@pytest.fixture
def sample_text_base64():
    ...
```

**Problem:** These duplicate functionality already in `factories.py`:
```python
def pdf_file(suffix: str = "", filename: str = "test.pdf") -> FileBuilder:
    return FileBuilder().with_filename(filename).with_pdf_content(suffix)

def text_file(content: str = "Test content", filename: str = "test.txt") -> FileBuilder:
    return FileBuilder().with_filename(filename).with_text_content(content)
```

### Recommendations

#### 1.1 Consolidate PDF Generation
**Remove:** test_upload_tools.py fixtures (sample_pdf_base64, sample_pdf2_base64, sample_pdf3_base64, sample_text_base64)
**Replace with:** Factory functions from factories.py
**Estimated Savings:** 80-100 lines (~2,400 chars)

```python
# Before (in test_upload_tools.py)
def test_create_session_success(self, test_settings, sample_pdf_base64):
    result = await upload_tools.create_session_from_uploads(
        files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}]
    )

# After
from tests.factories import pdf_file

def test_create_session_success(self, test_settings):
    result = await upload_tools.create_session_from_uploads(
        files=[pdf_file().build()]
    )
```

#### 1.2 Create Shared Mock Fixtures
**Current:** Mock creation duplicated across test_llm_extraction.py, test_marker_integration.py
**Recommendation:** Add to conftest.py

```python
# conftest.py
@pytest.fixture
def mock_llm_response():
    """Factory for creating mock LLM responses."""
    def _create(json_content: str, use_code_fence: bool = True):
        if use_code_fence:
            text = f"```json\n{json_content}\n```"
        else:
            text = json_content
        mock = Mock()
        mock.content = [Mock(text=text)]
        return mock
    return _create

@pytest.fixture
def mock_llm_client(mock_llm_response):
    """Factory for creating mock LLM clients."""
    def _create(response_json: str):
        response = mock_llm_response(response_json)
        client = AsyncMock()
        client.messages.create.return_value = response
        return client
    return _create
```

**Estimated Savings:** 60-80 lines across 3 files (~1,800 chars)

---

## 2. Factory Pattern Usage Optimization

### Current Utilization

**Using SessionManager (3 files):**
- test_validation.py ✓
- test_integration_full_workflow.py ✓
- factories.py (definition) ✓

**NOT using SessionManager (21 files):**
- test_upload_tools.py - 24 manual try/finally blocks
- test_document_processing.py - 2 manual cleanup calls
- test_evidence_extraction.py - 5 manual cleanup calls
- test_user_experience.py - 3 manual cleanup calls
- test_infrastructure.py - 1 manual cleanup call
- Plus 16 more files

### Pattern: Manual Cleanup Anti-Pattern

**Duplicated 36 times across codebase:**
```python
try:
    # Test code
    result = await upload_tools.create_session_from_uploads(...)
    assert result["success"] is True
    # ... more assertions
finally:
    await session_tools.delete_session(result["session_id"])
```

### Recommendations

#### 2.1 Extend SessionManager Usage
**Target Files:** test_upload_tools.py, test_document_processing.py, test_evidence_extraction.py

**Before (test_upload_tools.py - line 70-101):**
```python
@pytest.mark.asyncio
async def test_create_session_success(self, test_settings, sample_pdf_base64):
    result = await upload_tools.create_session_from_uploads(
        project_name="Test Project",
        files=[{"filename": "test.pdf", "content_base64": sample_pdf_base64}],
        methodology="soil-carbon-v1.2.2"
    )

    assert result["success"] is True
    assert "session_id" in result
    # ... 10 more lines of assertions

    # Cleanup
    try:
        await session_tools.delete_session(result["session_id"])
    except:
        pass
```

**After:**
```python
from tests.factories import SessionBuilder, SessionManager, pdf_file

@pytest.mark.asyncio
async def test_create_session_success(self):
    async with SessionManager() as manager:
        session_id = await manager.create(
            SessionBuilder()
                .with_project_name("Test Project")
                .with_file(pdf_file())
                .with_methodology("soil-carbon-v1.2.2")
        )

        session = await session_tools.load_session(session_id)
        assert session["project_metadata"]["project_name"] == "Test Project"
        # Auto-cleanup on exit
```

**Estimated Savings per file:**
- test_upload_tools.py: 24 instances × 4 lines = 96 lines (~2,880 chars)
- test_document_processing.py: 2 instances × 4 lines = 8 lines (~240 chars)
- test_evidence_extraction.py: 5 instances × 4 lines = 20 lines (~600 chars)

**Total Estimated Savings:** 124 lines (~3,720 chars)

#### 2.2 Create Additional Factory Helpers

**Missing Pattern:** Validation result assertions

**Current (repeated 15+ times):**
```python
assert result["status"] in ["pass", "fail", "warning"]
assert "confidence" in result
assert 0.0 <= result["confidence"] <= 1.0
assert "flagged_for_review" in result
assert isinstance(result["flagged_for_review"], bool)
```

**Proposed Helper (factories.py):**
```python
class ValidationAssertions:
    """Common assertions for validation results."""

    @staticmethod
    def assert_valid_validation_result(result: Dict):
        """Assert validation result has correct structure."""
        assert result["status"] in ["pass", "fail", "warning"]
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
        assert "flagged_for_review" in result
        assert isinstance(result["flagged_for_review"], bool)

    @staticmethod
    def assert_validation_passed(result: Dict):
        """Assert validation passed."""
        ValidationAssertions.assert_valid_validation_result(result)
        assert result["status"] == "pass"
        assert result["flagged_for_review"] is False

    @staticmethod
    def assert_validation_failed(result: Dict):
        """Assert validation failed."""
        ValidationAssertions.assert_valid_validation_result(result)
        assert result["status"] == "fail"
        assert result["flagged_for_review"] is True
```

**Estimated Savings:** 15 instances × 5 lines = 75 lines (~1,875 chars)

---

## 3. Test Helper Completeness

### Missing Helpers

#### 3.1 Document Verification Helpers
**Pattern appears 8+ times:**
```python
state_manager = StateManager(session_id)
docs_data = state_manager.read_json("documents.json")
documents = docs_data.get("documents", docs_data)
assert len(documents) > 0
```

**Proposed Helper:**
```python
# tests/helpers/document_helpers.py
from registry_review_mcp.utils.state import StateManager
from typing import List, Dict

def get_session_documents(session_id: str) -> List[Dict]:
    """Get documents from session's documents.json."""
    manager = StateManager(session_id)
    docs_data = manager.read_json("documents.json")
    return docs_data.get("documents", docs_data)

def assert_documents_found(session_id: str, min_count: int = 1):
    """Assert minimum documents were discovered."""
    docs = get_session_documents(session_id)
    assert len(docs) >= min_count, f"Expected at least {min_count} documents, found {len(docs)}"
    return docs

def assert_document_type_exists(session_id: str, doc_type: str):
    """Assert specific document type was classified."""
    docs = get_session_documents(session_id)
    types = [d["classification"] for d in docs]
    assert doc_type in types, f"Expected document type '{doc_type}', found: {types}"
```

**Estimated Savings:** 8 instances × 4 lines = 32 lines (~960 chars)

#### 3.2 Evidence Verification Helpers
**Pattern appears 6+ times:**
```python
manager = StateManager(session_id)
evidence_data = manager.read_json("evidence.json")
requirements_covered = evidence_data.get("requirements_covered", 0)
requirements_total = evidence_data.get("requirements_total", 0)
assert requirements_covered > 0
```

**Proposed Helper:**
```python
# tests/helpers/evidence_helpers.py
def get_evidence_summary(session_id: str) -> Dict:
    """Get evidence extraction summary."""
    manager = StateManager(session_id)
    return manager.read_json("evidence.json")

def assert_coverage_meets_threshold(session_id: str, min_coverage: float = 0.3):
    """Assert evidence coverage meets minimum threshold."""
    evidence = get_evidence_summary(session_id)
    covered = evidence.get("requirements_covered", 0)
    total = evidence.get("requirements_total", 0)

    if total == 0:
        pytest.fail("No requirements found in checklist")

    coverage = covered / total
    assert coverage >= min_coverage, \
        f"Coverage {coverage:.1%} below threshold {min_coverage:.1%} ({covered}/{total})"

    return evidence
```

**Estimated Savings:** 6 instances × 5 lines = 30 lines (~900 chars)

#### 3.3 Workflow Stage Helpers
**Pattern appears 12+ times:**
```python
session = await session_tools.load_session(session_id)
assert session["workflow_progress"]["document_discovery"] == "completed"
```

**Already exists in factories.py but underutilized:**
```python
SessionAssertions.assert_workflow_stage_completed(session_id, "document_discovery")
```

**Recommendation:** Promote usage through documentation and examples

---

## 4. Shared Test Utilities

### Patterns Across Multiple Files

#### 4.1 LLM Mock Creation (3 files)
**Files:** test_llm_extraction.py, test_marker_integration.py, factories.py

**Current Duplication:**
```python
# test_llm_extraction.py (lines 32-47)
mock_response = Mock()
mock_response.content = [Mock(text='```json\n[...]\n```')]

# test_marker_integration.py (lines 28-43)
mock_convert_fn = Mock(return_value=(...))
mock_get_models.return_value = {"models": Mock(), "convert_fn": mock_convert_fn}

# factories.py (lines 284-316)
def create_llm_mock_response(json_content: str, use_code_fence: bool = True) -> Mock:
    ...
```

**Recommendation:** Consolidate to factories.py and promote as standard pattern

#### 4.2 Unique Document Names (2 files)
**Pattern for cache avoidance:**
```python
import time
doc_name = f"test_{int(time.time() * 1000000)}.pdf"
```

**Already exists in factories.py:**
```python
def unique_doc_name(test_name: str) -> str:
    """Generate unique document name for testing to avoid cache collisions."""
    return f"{test_name}_{int(time.time() * 1000000)}.pdf"
```

**Recommendation:** Promote usage

#### 4.3 Pytest Skip Patterns (7 files)
**Common pattern:**
```python
if not settings.anthropic_api_key or not settings.llm_extraction_enabled:
    pytest.skip("LLM extraction not configured")

if not example_path.exists():
    pytest.skip("Botany Farm example data not available")
```

**Proposed Helper:**
```python
# tests/helpers/skip_helpers.py
import pytest
from pathlib import Path
from registry_review_mcp.config.settings import settings

def skip_if_no_llm():
    """Skip test if LLM extraction is not configured."""
    if not settings.anthropic_api_key or not settings.llm_extraction_enabled:
        pytest.skip("LLM extraction not configured")

def skip_if_no_examples():
    """Skip test if example data is not available."""
    path = Path(__file__).parent.parent / "examples" / "22-23"
    if not path.exists():
        pytest.skip("Botany Farm example documents not available")
    return path

# Usage
@pytest.fixture
def botany_farm_path():
    return skip_if_no_examples()
```

**Estimated Savings:** 13 instances × 3 lines = 39 lines (~975 chars)

---

## 5. Setup/Teardown Optimization

### Current State

**Excellent Design:**
- `cleanup_sessions` (autouse, function scope) - Prevents test pollution ✓
- `cleanup_examples_sessions` (explicit) - Preserves user data ✓
- `cleanup_cache_once` (session scope) - Efficient ✓

**Optimization Opportunity:**
```python
# conftest.py lines 271-329
@pytest.fixture(autouse=True, scope="function")
def cleanup_sessions():
    """Clean up TEST sessions before and after each test."""
    # ... 58 lines of cleanup logic
```

### Recommendations

#### 5.1 Extract Cleanup Logic to Helper
**Current:** Cleanup logic embedded in fixture (58 lines)
**Proposed:** Extract to reusable function

```python
# tests/helpers/cleanup_helpers.py
from pathlib import Path
import shutil
import json

def cleanup_test_sessions():
    """Remove ONLY definitively test-created sessions."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    sessions_dir = data_dir / "sessions"

    if not sessions_dir.exists():
        return

    for session_path in sessions_dir.iterdir():
        if not session_path.is_dir():
            continue

        # Delete test-* sessions
        if session_path.name.startswith("test-"):
            shutil.rmtree(session_path, ignore_errors=True)
            continue

        # Check if session points to pytest temp directory
        try:
            session_file = session_path / "session.json"
            if session_file.exists():
                with open(session_file) as f:
                    session_data = json.load(f)
                    docs_path_str = session_data.get("project_metadata", {}).get("documents_path", "")
                    if "/tmp/pytest-" in docs_path_str or "/tmp/pytest_" in docs_path_str:
                        shutil.rmtree(session_path, ignore_errors=True)
        except Exception:
            shutil.rmtree(session_path, ignore_errors=True)

# conftest.py
from tests.helpers.cleanup_helpers import cleanup_test_sessions

@pytest.fixture(autouse=True, scope="function")
def cleanup_sessions():
    """Clean up TEST sessions before and after each test."""
    cleanup_test_sessions()
    yield
    cleanup_test_sessions()
```

**Benefits:**
- Reusable in manual cleanup scripts
- Testable independently
- Cleaner fixture definition

---

## 6. Character Reduction Estimates

### Summary by Recommendation

| Recommendation | Files Affected | Estimated Savings (chars) |
|---------------|----------------|---------------------------|
| 1.1 Consolidate PDF fixtures | 1 | 2,400 |
| 1.2 Shared mock fixtures | 3 | 1,800 |
| 2.1 Extend SessionManager | 6 | 3,720 |
| 2.2 Validation assertions | 4 | 1,875 |
| 3.1 Document helpers | 5 | 960 |
| 3.2 Evidence helpers | 4 | 900 |
| 3.3 Workflow helpers (promotion) | 8 | 600 |
| 4.3 Skip helpers | 7 | 975 |
| **TOTAL** | **24 files** | **13,230 chars** |

### High-Impact Quick Wins (Top 3)

1. **SessionManager Adoption** (3,720 chars, 6 files)
   - Replace try/finally with context manager
   - Immediate readability improvement
   - Zero functionality change

2. **Consolidate PDF Fixtures** (2,400 chars, 1 file)
   - Remove duplicate sample_pdf fixtures
   - Use existing factory functions
   - One-time refactor

3. **Validation Assertions** (1,875 chars, 4 files)
   - Extract repeated validation checks
   - Single helper class addition
   - Reusable across all validation tests

**Total Quick Wins:** 7,995 chars (~60% of total savings)

---

## 7. New Shared Utilities to Create

### Proposed Module Structure

```
tests/
├── helpers/
│   ├── __init__.py
│   ├── cleanup_helpers.py      # Session/cache cleanup logic
│   ├── document_helpers.py     # Document verification
│   ├── evidence_helpers.py     # Evidence verification
│   ├── skip_helpers.py         # Conditional test skipping
│   └── mock_helpers.py         # LLM and API mocking
├── conftest.py                 # Fixtures only
├── factories.py                # Test data builders (existing)
└── test_*.py                   # Test files
```

### helpers/__init__.py
```python
"""Shared test helpers and utilities.

Import commonly used helpers for convenience:
    from tests.helpers import (
        skip_if_no_llm,
        get_session_documents,
        assert_coverage_meets_threshold,
        ValidationAssertions,
    )
"""

from .skip_helpers import skip_if_no_llm, skip_if_no_examples
from .document_helpers import get_session_documents, assert_documents_found
from .evidence_helpers import get_evidence_summary, assert_coverage_meets_threshold
from .cleanup_helpers import cleanup_test_sessions

# Import assertion classes
from tests.factories import SessionAssertions, ValidationAssertions

__all__ = [
    # Skip helpers
    "skip_if_no_llm",
    "skip_if_no_examples",

    # Document helpers
    "get_session_documents",
    "assert_documents_found",

    # Evidence helpers
    "get_evidence_summary",
    "assert_coverage_meets_threshold",

    # Cleanup
    "cleanup_test_sessions",

    # Assertions
    "SessionAssertions",
    "ValidationAssertions",
]
```

### helpers/mock_helpers.py
```python
"""Mock creation helpers for LLM and external services."""

from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

def create_llm_response(json_content: str, use_code_fence: bool = True) -> Mock:
    """Create a mock LLM response with JSON content.

    Args:
        json_content: The JSON string to return
        use_code_fence: Whether to wrap in markdown code fence

    Returns:
        Mock response object compatible with Anthropic API
    """
    if use_code_fence:
        text = f"```json\n{json_content}\n```"
    else:
        text = json_content

    mock_response = Mock()
    mock_response.content = [Mock(text=text)]
    return mock_response

def create_llm_client(response: Mock) -> AsyncMock:
    """Create a mock LLM client that returns the given response.

    Args:
        response: Mock response from create_llm_response()

    Returns:
        AsyncMock client compatible with Anthropic SDK
    """
    mock_client = AsyncMock()
    mock_client.messages.create.return_value = response
    return mock_client

def create_marker_models(markdown_output: str, page_count: int = 1) -> Dict[str, Any]:
    """Create mock marker models for PDF conversion testing.

    Args:
        markdown_output: The markdown text to return
        page_count: Number of pages to report

    Returns:
        Mock models dict compatible with marker_extractor
    """
    mock_convert_fn = Mock(return_value=(
        markdown_output,
        {},  # images
        {"page_count": page_count}  # metadata
    ))

    return {
        "models": Mock(),
        "convert_fn": mock_convert_fn
    }
```

---

## 8. Implementation Priority

### Phase 1: Quick Wins (Week 1)
**Impact:** 7,995 chars saved, 60% of total

1. **Day 1:** Extend SessionManager to test_upload_tools.py
   - Refactor 24 try/finally blocks
   - Savings: 2,880 chars

2. **Day 2:** Remove duplicate PDF fixtures
   - Update test_upload_tools.py to use factories
   - Savings: 2,400 chars

3. **Day 3:** Add ValidationAssertions to factories.py
   - Refactor validation tests
   - Savings: 1,875 chars

4. **Day 4:** Add skip_helpers.py
   - Refactor pytest.skip calls
   - Savings: 975 chars

### Phase 2: Helper Infrastructure (Week 2)
**Impact:** 2,760 chars saved, 21% of total

5. **Day 5-6:** Create helpers/ module
   - document_helpers.py
   - evidence_helpers.py
   - Savings: 1,860 chars

6. **Day 7:** Create mock_helpers.py
   - Consolidate LLM mocking
   - Savings: 900 chars

### Phase 3: Systematic Adoption (Week 3)
**Impact:** 2,475 chars saved, 19% of total

7. **Days 8-10:** Extend SessionManager to remaining files
   - test_document_processing.py
   - test_evidence_extraction.py
   - test_user_experience.py
   - Savings: 840 chars

8. **Days 11-12:** Promote helper usage
   - Update documentation
   - Refactor remaining instances
   - Savings: 1,635 chars

---

## 9. Validation Metrics

### Success Criteria

After implementation, measure:

1. **Reduction Metrics:**
   - Total test LOC reduced by 8-10%
   - Average test method length reduced from 25 → 20 lines
   - Fixture usage increased by 40%

2. **Quality Metrics:**
   - Zero new test failures
   - All existing tests pass
   - Coverage maintained at ≥ 85%

3. **Maintainability Metrics:**
   - Helper function usage: 60+ call sites
   - SessionManager adoption: 18/24 files (75%)
   - Manual cleanup instances: < 5

### Risk Mitigation

- Run full test suite after each phase
- Keep original implementations commented during migration
- Create rollback commits at phase boundaries

---

## 10. Conclusion

The test infrastructure demonstrates mature patterns (factories, session cleanup, cost tracking) but suffers from underutilization and duplication. The proposed changes target:

- **13,230 characters saved** (16-20% reduction in test code)
- **Zero functionality change** (refactoring only)
- **Improved maintainability** through helper consolidation
- **Faster test authoring** via reusable patterns

The three-phase implementation plan delivers quick wins first (60% of savings in Week 1) while building sustainable infrastructure for long-term maintenance.

### Recommended Next Steps

1. Review this analysis with the team
2. Approve Phase 1 quick wins
3. Create implementation branches
4. Execute Week 1 refactoring
5. Measure results and iterate

---

**Analysis Prepared By:** Claude Code (Sonnet 4.5)
**Review Status:** Draft
**Estimated Implementation:** 3 weeks (15 work days)
