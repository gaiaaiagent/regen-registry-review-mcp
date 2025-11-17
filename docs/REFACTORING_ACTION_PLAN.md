# Refactoring Action Plan: Priority Improvements

**Date:** 2025-11-15
**Status:** Ready for Implementation
**Based On:** Comprehensive Code Quality Review (2,252 lines, 47 issues identified)

---

## Executive Summary

This action plan prioritizes the **top 10 improvements** from the comprehensive code quality review that will deliver the most value with manageable effort. Focus is on **extensibility**, **maintainability**, and **removing hardcoded values**.

**Estimated Timeline:** 8-10 days total
**Expected Outcome:** 40% reduction in code duplication, support for multiple methodologies, improved testability

---

## Phase 1: Critical Issues (Days 1-3)

### 1. Implement Methodology Registry ⚡ CRITICAL

**Current Problem:**
- "soil-carbon-v1.2.2" hardcoded in 6+ files
- Cannot add new methodologies without code changes
- Risk of typos and inconsistencies

**Files Affected:**
- `src/registry_review_mcp/models/schemas.py:25`
- `src/registry_review_mcp/server.py:47,307`
- `src/registry_review_mcp/tools/session_tools.py:30`
- `src/registry_review_mcp/tools/evidence_tools.py:276,361`
- `src/registry_review_mcp/prompts/A_initialize.py:159`

**Solution:**

Create new file: `src/registry_review_mcp/config/methodologies.py`

```python
"""Methodology registry with auto-discovery."""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional
import json
from pydantic import BaseModel


class MethodologyMetadata(BaseModel):
    """Metadata for a methodology."""
    id: str
    name: str
    version: str
    protocol: str
    checklist_filename: str
    description: str
    active: bool = True


class MethodologyRegistry:
    """Registry of available methodologies with auto-discovery."""

    def __init__(self, checklists_dir: Path):
        self.checklists_dir = checklists_dir
        self._methodologies: Dict[str, MethodologyMetadata] = {}
        self._default_id: Optional[str] = None
        self._load_methodologies()

    def _load_methodologies(self):
        """Auto-discover methodologies from checklist files."""
        for checklist_file in self.checklists_dir.glob("*.json"):
            try:
                with open(checklist_file, 'r') as f:
                    data = json.load(f)

                metadata = MethodologyMetadata(
                    id=data.get("methodology_id"),
                    name=data.get("methodology_name"),
                    version=data.get("version"),
                    protocol=data.get("protocol"),
                    checklist_filename=checklist_file.name,
                    description=f"{data.get('methodology_name')} {data.get('version')}"
                )

                self._methodologies[metadata.id] = metadata

                # Set first as default
                if not self._default_id:
                    self._default_id = metadata.id

            except Exception:
                # Skip invalid checklists
                pass

    def get_default(self) -> str:
        """Get default methodology ID."""
        return self._default_id or "soil-carbon-v1.2.2"

    def list_available(self) -> list[MethodologyMetadata]:
        """List all active methodologies."""
        return [m for m in self._methodologies.values() if m.active]


# Global registry instance
_registry: Optional[MethodologyRegistry] = None


def get_methodology_registry() -> MethodologyRegistry:
    """Get or create the global methodology registry."""
    global _registry
    if _registry is None:
        from .settings import settings
        _registry = MethodologyRegistry(settings.checklists_dir)
    return _registry
```

**Usage After Refactoring:**

```python
# Before (HARDCODED):
methodology: str = "soil-carbon-v1.2.2"

# After (DYNAMIC):
from ..config.methodologies import get_methodology_registry

registry = get_methodology_registry()
methodology: str = registry.get_default()
```

**Testing:**
```python
def test_methodology_registry_auto_discovery():
    """Test that registry discovers all checklist files."""
    registry = MethodologyRegistry(settings.checklists_dir)
    methodologies = registry.list_available()
    assert len(methodologies) > 0
    assert "soil-carbon-v1.2.2" in [m.id for m in methodologies]
```

**Effort:** 4-6 hours
**Impact:** 🔥 High - Enables multi-methodology support

---

### 2. Create Document Classifier Registry

**Current Problem:**
- Hardcoded if/elif chain for document classification (80+ lines)
- Cannot add new document types without modifying core code
- Difficult to test individual classification rules

**File:** `src/registry_review_mcp/tools/document_tools.py:293-373`

**Solution:**

Create new file: `src/registry_review_mcp/classifiers/base.py`

```python
"""Document classifier base classes and registry."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from pathlib import Path


class DocumentClassifier(ABC):
    """Abstract base class for document classifiers."""

    @property
    @abstractmethod
    def document_type(self) -> str:
        """Type of document this classifier identifies."""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Priority (higher = checked first)."""
        pass

    @abstractmethod
    def matches(self, filepath: Path, content: Optional[str] = None) -> Tuple[bool, float]:
        """
        Check if document matches this type.

        Returns:
            (matches, confidence) tuple
        """
        pass


class PatternClassifier(DocumentClassifier):
    """Classifier based on filename patterns."""

    def __init__(self, document_type: str, patterns: list, confidence: float = 0.9, priority: int = 100):
        self._document_type = document_type
        self._patterns = patterns
        self._confidence = confidence
        self._priority = priority

    @property
    def document_type(self) -> str:
        return self._document_type

    @property
    def priority(self) -> int:
        return self._priority

    def matches(self, filepath: Path, content: Optional[str] = None) -> Tuple[bool, float]:
        from ..utils.patterns import match_any

        filename = filepath.name.lower()
        if match_any(filename, self._patterns):
            return (True, self._confidence)
        return (False, 0.0)


class ClassifierRegistry:
    """Registry for document classifiers."""

    def __init__(self):
        self._classifiers: List[DocumentClassifier] = []

    def register(self, classifier: DocumentClassifier):
        """Register a classifier."""
        self._classifiers.append(classifier)
        # Sort by priority (descending)
        self._classifiers.sort(key=lambda c: c.priority, reverse=True)

    def classify(self, filepath: Path, content: Optional[str] = None) -> Tuple[str, float, str]:
        """
        Classify a document using registered classifiers.

        Returns:
            (document_type, confidence, method) tuple
        """
        for classifier in self._classifiers:
            matches, confidence = classifier.matches(filepath, content)
            if matches:
                method = classifier.__class__.__name__.replace("Classifier", "").lower()
                return (classifier.document_type, confidence, method)

        # No match
        return ("unknown", 0.50, "default")
```

Create: `src/registry_review_mcp/classifiers/soil_carbon.py`

```python
"""Classifiers for soil carbon methodology documents."""

from .base import PatternClassifier, ClassifierRegistry


def register_soil_carbon_classifiers(registry: ClassifierRegistry):
    """Register all soil carbon document classifiers."""

    # Project Plan
    registry.register(PatternClassifier(
        document_type="project_plan",
        patterns=["project_plan", "project_description", "pd_"],
        confidence=0.95,
        priority=100
    ))

    # Baseline Report
    registry.register(PatternClassifier(
        document_type="baseline_report",
        patterns=["baseline", "base_line", "br_"],
        confidence=0.90,
        priority=90
    ))

    # Monitoring Report
    registry.register(PatternClassifier(
        document_type="monitoring_report",
        patterns=["monitoring", "mr_", "annual_report"],
        confidence=0.90,
        priority=90
    ))

    # ... register all other classifiers
```

**Effort:** 6-8 hours
**Impact:** 🔥 High - Extensible classification system

---

### 3. Fix StateManager Nested Update (Already Fixed!)

✅ **Status:** COMPLETED in previous session

See: `src/registry_review_mcp/utils/state.py:127-163`

---

## Phase 2: High Impact Improvements (Days 4-6)

### 4. Create LLM Extractor Factory

**Current Problem:**
- Each extractor instantiates its own Anthropic client
- No shared caching or configuration
- Difficult to mock for testing

**Files:**
- `src/registry_review_mcp/extractors/llm_extractors.py:24,154,269`

**Solution:**

Create: `src/registry_review_mcp/extractors/factory.py`

```python
"""Factory for creating LLM extractors with shared resources."""

from typing import Dict, Type, Optional
from anthropic import Anthropic
from .llm_extractors import DateExtractor, LandTenureExtractor, ProjectIDExtractor
from ..config.settings import settings


class ExtractorFactory:
    """Factory for creating LLM extractors with shared client."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.anthropic_api_key
        self._client: Optional[Anthropic] = None
        self._extractors: Dict[str, object] = {}

    @property
    def client(self) -> Anthropic:
        """Get or create shared Anthropic client."""
        if self._client is None:
            self._client = Anthropic(api_key=self._api_key)
        return self._client

    def get_date_extractor(self) -> DateExtractor:
        """Get or create DateExtractor instance."""
        if 'date' not in self._extractors:
            self._extractors['date'] = DateExtractor(client=self.client)
        return self._extractors['date']

    def get_land_tenure_extractor(self) -> LandTenureExtractor:
        """Get or create LandTenureExtractor instance."""
        if 'land_tenure' not in self._extractors:
            self._extractors['land_tenure'] = LandTenureExtractor(client=self.client)
        return self._extractors['land_tenure']

    def get_project_id_extractor(self) -> ProjectIDExtractor:
        """Get or create ProjectIDExtractor instance."""
        if 'project_id' not in self._extractors:
            self._extractors['project_id'] = ProjectIDExtractor(client=self.client)
        return self._extractors['project_id']


# Global factory instance
_factory: Optional[ExtractorFactory] = None


def get_extractor_factory() -> ExtractorFactory:
    """Get or create global extractor factory."""
    global _factory
    if _factory is None:
        _factory = ExtractorFactory()
    return _factory
```

**Effort:** 3-4 hours
**Impact:** 🔥 Medium-High - Better resource management, easier testing

---

### 5. Refactor Long Functions

**Current Problem:**
- `discover_documents`: 195 lines
- `cross_validate`: 216 lines
- `generate_review_report`: 208 lines

**Solution:** Extract Method refactoring

**Example - discover_documents:**

```python
# Before: 195 lines in one function

# After: Split into focused functions
async def discover_documents(session_id: str) -> dict[str, Any]:
    """Discover and index all documents."""
    session_data = await _validate_session(session_id)
    documents_path = Path(session_data["project_metadata"]["documents_path"])

    discovered_files = await _scan_directory(documents_path)
    results = await _process_discovered_files(discovered_files, session_id)
    await _save_discovery_results(session_id, results, session_data)

    return _format_discovery_response(session_id, results)


async def _validate_session(session_id: str) -> dict[str, Any]:
    """Validate session exists and return data."""
    # 10 lines


async def _scan_directory(documents_path: Path) -> list[Path]:
    """Scan directory for supported files."""
    # 20 lines


async def _process_discovered_files(files: list[Path], session_id: str) -> ProcessingResults:
    """Process discovered files and classify them."""
    # 40 lines


async def _save_discovery_results(session_id: str, results: ProcessingResults, session_data: dict):
    """Save discovery results to session."""
    # 20 lines


def _format_discovery_response(session_id: str, results: ProcessingResults) -> dict:
    """Format final response."""
    # 10 lines
```

**Files to Refactor:**
1. `src/registry_review_mcp/tools/document_tools.py:67-261` (discover_documents)
2. `src/registry_review_mcp/tools/validation_tools.py:486-701` (cross_validate)
3. `src/registry_review_mcp/tools/report_tools.py:18-225` (generate_review_report)

**Effort:** 8-10 hours (all three functions)
**Impact:** 🔥 High - Much more testable and maintainable

---

### 6. Improve Error Handling

**Current Problem:**
- Exceptions caught and silently ignored
- No logging of failures
- User doesn't know what went wrong

**Example Issues:**
- `A_initialize.py:86-89` - Swallows all exceptions from session iteration
- `document_tools.py:172-218` - 46 lines of nested try/except

**Solution:**

```python
# Before:
try:
    # Load session
    state_manager = StateManager(session_dir.name)
    session_data = state_manager.read_json("session.json")
    # ...
except Exception:
    # Skip corrupted sessions
    continue

# After:
try:
    # Load session
    state_manager = StateManager(session_dir.name)
    session_data = state_manager.read_json("session.json")
    # ...
except json.JSONDecodeError as e:
    logger.warning(f"Skipping corrupted session {session_dir.name}: Invalid JSON - {e}")
    continue
except KeyError as e:
    logger.warning(f"Skipping session {session_dir.name}: Missing required field {e}")
    continue
except Exception as e:
    logger.error(f"Unexpected error loading session {session_dir.name}: {e}", exc_info=True)
    continue
```

**Effort:** 4-6 hours
**Impact:** 🔥 Medium - Better debugging and user experience

---

## Phase 3: Quality Improvements (Days 7-8)

### 7. Move Magic Numbers to Configuration

**Current Problem:**
- Validation thresholds hardcoded in logic
- Cannot configure per methodology or environment

**Examples:**
- `llm_extractors.py:259` - `if confidence < 0.7`
- `validation_tools.py:123` - `if area_diff_pct > 5.0`
- `validation_tools.py:271` - `if count >= 9000`

**Solution:**

Add to `settings.py`:

```python
class ValidationThresholds(BaseModel):
    """Validation threshold configuration."""
    min_llm_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    area_difference_tolerance_pct: float = Field(default=5.0, ge=0.0, le=100.0)
    project_id_suspicious_count: int = Field(default=9000, ge=0)
    date_alignment_max_delta_days: int = Field(default=120, ge=0)


class Settings(BaseSettings):
    # ... existing fields ...

    # Validation thresholds
    validation: ValidationThresholds = Field(default_factory=ValidationThresholds)
```

Usage:

```python
# Before:
if confidence < 0.7:
    logger.warning("Low confidence")

# After:
if confidence < settings.validation.min_llm_confidence:
    logger.warning(f"Low confidence (threshold: {settings.validation.min_llm_confidence})")
```

**Effort:** 2-3 hours
**Impact:** 🟡 Medium - More flexible configuration

---

### 8-10. Additional Quality Improvements

**8. Citation Parser** (3-4 hours)
- Structured citation handling instead of string matching
- File: `src/registry_review_mcp/utils/citations.py`

**9. Validation Registry** (4-5 hours)
- Strategy pattern for pluggable validators
- File: `src/registry_review_mcp/validators/registry.py`

**10. Template Method for Extractors** (3-4 hours)
- Base class with shared evidence traversal
- Reduce duplication in LLM extractors

---

## Testing Strategy

For each refactoring:

1. **Before Refactoring:**
   - Write tests capturing current behavior
   - Run full test suite to establish baseline

2. **During Refactoring:**
   - Refactor one component at a time
   - Run tests after each change
   - Add tests for new functionality

3. **After Refactoring:**
   - Ensure all existing tests pass
   - Add integration tests
   - Verify no performance regression

**New Test Files to Create:**
- `tests/test_methodology_registry.py`
- `tests/test_classifier_registry.py`
- `tests/test_extractor_factory.py`

---

## Success Metrics

**Code Quality:**
- ✅ Zero hardcoded "soil-carbon-v1.2.2" strings
- ✅ No functions >100 lines
- ✅ 40% reduction in code duplication
- ✅ All magic numbers in configuration

**Extensibility:**
- ✅ Can add new methodology by dropping checklist file
- ✅ Can add new document classifier without modifying core code
- ✅ Can configure validation thresholds via environment variables

**Maintainability:**
- ✅ Each component independently testable
- ✅ Clear separation of concerns
- ✅ Comprehensive error logging

**Test Coverage:**
- ✅ Maintain 100% test pass rate (184+ tests)
- ✅ Add 20+ new tests for refactored components

---

## Risk Mitigation

**Risk 1: Breaking Existing Functionality**
- **Mitigation:** Test-driven refactoring - write tests first
- **Fallback:** Git branches for each phase

**Risk 2: Introducing Performance Regressions**
- **Mitigation:** Benchmark before/after for key operations
- **Threshold:** <10% performance change acceptable

**Risk 3: Integration Issues**
- **Mitigation:** Integration tests run after each phase
- **Strategy:** Deploy incrementally, not all at once

---

## Implementation Order

**Week 1:**
- Day 1: Methodology Registry (#1)
- Day 2: Document Classifier Registry (#2)
- Day 3: Testing and integration

**Week 2:**
- Day 4: Extractor Factory (#4)
- Day 5-6: Refactor long functions (#5)
- Day 7: Error handling improvements (#6)

**Optional (Week 3):**
- Day 8: Configuration improvements (#7)
- Day 9-10: Citation parser, validation registry, template method (#8-10)

---

## Next Steps

1. ✅ Review this action plan
2. ⏳ Create GitHub issues for each item
3. ⏳ Start with Phase 1, Item #1 (Methodology Registry)
4. ⏳ Daily standup to track progress
5. ⏳ Code review after each phase

---

**Document Status:** Ready for Implementation
**Last Updated:** 2025-11-15
**Owner:** Development Team
