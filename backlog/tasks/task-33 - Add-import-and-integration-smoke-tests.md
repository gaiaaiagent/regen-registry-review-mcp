---
id: task-33
title: Add import and integration smoke tests
status: Open
assignee: []
created_date: '2025-12-04'
updated_date: '2025-12-04'
labels:
  - testing
  - reliability
  - high
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A missing dependency (`pymupdf4llm`) caused production failures despite 243 passing tests. The root cause: our test suite exercises the wrong code paths.

### Root Cause Analysis

**pytest.ini line 28 excludes critical tests by default:**
```
-m "not expensive and not integration and not accuracy and not marker"
```

When developers run `pytest`, they see all tests pass but the following critical paths are NEVER exercised:

1. **fast_extractor.py** - Zero test imports. This is the module that failed.
2. **services/document_processor.py** - Zero test imports. Orchestrates all processing.
3. **services/background_jobs.py** - Zero test imports. Manages async tasks.
4. **8 tools/*.py files** - Minimal coverage. MCP tool implementations.
5. **9 prompts/*.py files** - Zero test imports. LLM templates.

### The Lazy Import Problem

Five locations use `try: import X except ImportError` patterns that defer failures to runtime:
- `fast_extractor.py:60` - pymupdf4llm (THE BUG)
- `marker_extractor.py:68,105,113,857` - torch (optional, but masks issues)

These pass at import time because the try/except defers the actual import until function execution.

### Solution: Two New Test Types

**1. Import Verification Test (Fast, Always Runs)**

A test that imports every module and verifies all required dependencies are installed:

```python
# tests/test_imports.py
"""Verify all modules import successfully and dependencies are installed."""

import pytest

def test_all_modules_import():
    """Import every module to catch missing dependencies."""
    # Core
    from registry_review_mcp import server
    from registry_review_mcp.config import settings

    # Services
    from registry_review_mcp.services import document_processor
    from registry_review_mcp.services import background_jobs

    # Extractors (including lazy dependencies)
    from registry_review_mcp.extractors import fast_extractor
    from registry_review_mcp.extractors import marker_extractor
    from registry_review_mcp.extractors import llm_extractors

    # All tools
    from registry_review_mcp.tools import upload_tools
    from registry_review_mcp.tools import session_tools
    from registry_review_mcp.tools import document_tools
    from registry_review_mcp.tools import evidence_tools
    from registry_review_mcp.tools import mapping_tools
    from registry_review_mcp.tools import report_tools
    from registry_review_mcp.tools import validation_tools
    from registry_review_mcp.tools import human_review_tools

def test_pymupdf4llm_available():
    """Verify pymupdf4llm is installed (the bug we caught)."""
    import pymupdf4llm
    assert hasattr(pymupdf4llm, 'to_markdown')

def test_marker_available():
    """Verify marker-pdf is installed."""
    from marker.models import create_model_dict
    from marker.converters.pdf import PdfConverter
```

**2. Integration Smoke Test (Fast, Runs on CI)**

A lightweight test that exercises critical paths without expensive API calls:

```python
# tests/test_smoke_integration.py
"""Smoke tests for critical integration paths."""

import pytest
from pathlib import Path

@pytest.mark.integration
class TestIntegrationSmoke:
    """Fast integration tests that verify critical paths work."""

    @pytest.mark.asyncio
    async def test_fast_extract_pdf(self, example_documents_path):
        """Verify fast_extract_pdf works with real PDF."""
        from registry_review_mcp.extractors.fast_extractor import fast_extract_pdf

        pdf = example_documents_path / "4997Botany22_Public_Project_Plan.pdf"
        result = await fast_extract_pdf(str(pdf))

        assert "markdown" in result
        assert len(result["markdown"]) > 100
        assert result["extraction_method"] == "pymupdf4llm"

    @pytest.mark.asyncio
    async def test_mcp_server_startup(self):
        """Verify MCP server can start without errors."""
        from registry_review_mcp.server import mcp, start_review

        # Verify tools are registered
        assert mcp is not None
        # Verify start_review exists and is callable
        assert callable(start_review)
```

### Why This Matters

Without these tests:
- A developer removes a dependency from pyproject.toml
- They run `pytest` - all 243 tests pass
- They commit and push
- Production breaks

With these tests:
- Import test fails immediately
- Developer knows something is wrong
- Bug never reaches production

### Acceptance Criteria

- [ ] `test_imports.py` imports all source modules
- [ ] `test_imports.py` verifies critical dependencies (pymupdf4llm, marker, pdfplumber)
- [ ] `test_smoke_integration.py` exercises fast_extract_pdf with real PDF
- [ ] `test_smoke_integration.py` verifies MCP server can start
- [ ] Integration smoke tests run in CI (not excluded by default)
- [ ] Import tests run on every pytest invocation
<!-- SECTION:DESCRIPTION:END -->
