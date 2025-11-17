# Quick Reference: Top 10 Improvements

**Last Updated:** 2025-11-15
**For Full Details:** See `REFACTORING_ACTION_PLAN.md` and `CODE_QUALITY_REVIEW.md`

---

## 🔥 Critical (Do First)

### 1. Methodology Registry
**Problem:** "soil-carbon-v1.2.2" hardcoded in 6+ files
**Impact:** Cannot support multiple methodologies
**Effort:** 4-6 hours
**File:** Create `src/registry_review_mcp/config/methodologies.py`

### 2. Document Classifier Registry
**Problem:** 80-line if/elif chain for classification
**Impact:** Cannot add document types without code changes
**Effort:** 6-8 hours
**File:** Create `src/registry_review_mcp/classifiers/`

---

## 🔶 High Priority (Next)

### 3. Extractor Factory
**Problem:** Each extractor creates own Anthropic client
**Impact:** Poor resource management, hard to test
**Effort:** 3-4 hours
**File:** Create `src/registry_review_mcp/extractors/factory.py`

### 4. Refactor discover_documents (195 lines)
**Problem:** Monolithic function with multiple responsibilities
**Impact:** Hard to test, understand, modify
**Effort:** 3-4 hours
**File:** `src/registry_review_mcp/tools/document_tools.py:67-261`

### 5. Refactor cross_validate (216 lines)
**Problem:** Longest function in codebase
**Impact:** Complex, fragile, untestable
**Effort:** 3-4 hours
**File:** `src/registry_review_mcp/tools/validation_tools.py:486-701`

### 6. Refactor generate_review_report (208 lines)
**Problem:** Report generation mixed with formatting
**Impact:** Hard to customize or extend
**Effort:** 2-3 hours
**File:** `src/registry_review_mcp/tools/report_tools.py:18-225`

---

## 🟡 Medium Priority (Quality)

### 7. Error Handling
**Problem:** Silent failures, no logging
**Impact:** Hard to debug, poor UX
**Effort:** 4-6 hours
**Files:** Multiple (A_initialize.py:86, document_tools.py:172, etc.)

### 8. Move Magic Numbers to Config
**Problem:** Hardcoded thresholds (0.7, 5%, 9000, etc.)
**Impact:** Cannot configure per environment
**Effort:** 2-3 hours
**File:** `src/registry_review_mcp/config/settings.py`

### 9. Citation Parser
**Problem:** String matching for citations
**Impact:** Brittle, error-prone
**Effort:** 3-4 hours
**File:** Create `src/registry_review_mcp/utils/citations.py`

### 10. Validation Registry
**Problem:** Validation rules hardcoded
**Impact:** Cannot customize per methodology
**Effort:** 4-5 hours
**File:** Create `src/registry_review_mcp/validators/registry.py`

---

## Quick Stats

- **Total Issues Found:** 47
- **Total Effort:** 8-10 days
- **Code Reduction:** ~40% duplication removed
- **Extensibility Gain:** Infinite (methodology/classifier/validator plugins)

---

## Before & After Examples

### Methodology Usage

```python
# Before (HARDCODED)
methodology: str = "soil-carbon-v1.2.2"

# After (DYNAMIC)
from ..config.methodologies import get_methodology_registry
registry = get_methodology_registry()
methodology: str = registry.get_default()
```

### Document Classification

```python
# Before (IF/ELIF CHAIN)
if match_any(filename, PROJECT_PLAN_PATTERNS):
    return ("project_plan", 0.95, "filename")
elif match_any(filename, BASELINE_PATTERNS):
    return ("baseline_report", 0.90, "filename")
# ... 10+ more branches

# After (STRATEGY PATTERN)
registry = ClassifierRegistry()
registry.register(PatternClassifier("project_plan", patterns, 0.95))
doc_type, confidence, method = registry.classify(filepath)
```

### Long Function

```python
# Before (195 LINES)
async def discover_documents(session_id: str) -> dict:
    # validation
    # file scanning
    # processing loop
    # duplicate checking
    # classification
    # error handling
    # saving
    # formatting

# After (5 FOCUSED FUNCTIONS)
async def discover_documents(session_id: str) -> dict:
    session_data = await _validate_session(session_id)
    files = await _scan_directory(Path(session_data["..."]))
    results = await _process_files(files, session_id)
    await _save_results(session_id, results)
    return _format_response(session_id, results)
```

---

## Implementation Checklist

### Week 1
- [ ] Methodology Registry (#1)
- [ ] Document Classifier Registry (#2)
- [ ] Integration tests

### Week 2
- [ ] Extractor Factory (#3)
- [ ] Refactor discover_documents (#4)
- [ ] Refactor cross_validate (#5)
- [ ] Refactor generate_review_report (#6)

### Week 3 (Optional)
- [ ] Error handling (#7)
- [ ] Config for magic numbers (#8)
- [ ] Citation parser (#9)
- [ ] Validation registry (#10)

---

## Testing Strategy

**For each refactoring:**
1. ✅ Write tests capturing current behavior
2. ✅ Refactor code
3. ✅ Ensure all tests pass
4. ✅ Add tests for new functionality
5. ✅ Run full test suite (184+ tests)

---

## Success Criteria

After completing all 10 improvements:

✅ Zero hardcoded "soil-carbon-v1.2.2" strings
✅ No functions >100 lines
✅ 40% reduction in code duplication
✅ All magic numbers in configuration
✅ Can add methodologies without code changes
✅ Can add classifiers without code changes
✅ Comprehensive error logging
✅ All 184+ tests passing

---

## Questions?

**Full Details:** See `docs/REFACTORING_ACTION_PLAN.md` (915 lines)
**Complete Analysis:** See `docs/CODE_QUALITY_REVIEW.md` (2,252 lines)
**Bug Fixes:** See `docs/BUG_FIXES_2025-11-14.md` (337 lines)
**Architecture:** See `docs/CODE_REVIEW_INITIALIZATION.md` (884 lines)
