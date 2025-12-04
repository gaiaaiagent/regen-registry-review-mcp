---
id: task-22
title: Audit and minimize Claude API costs
status: Done
assignee: []
created_date: '2025-12-04 03:10'
labels:
  - bug
  - critical
  - cost
  - api
dependencies: []
priority: critical
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Claude API credits are being consumed unexpectedly. This task audits all API usage points and implements cost controls.

## Immediate Issue Found

**Tests making real API calls without `@pytest.mark.expensive` marker:**

1. `tests/test_evidence_extraction.py:14` - `test_extract_all_evidence()` - ✅ FIXED
2. `tests/test_report_generation.py:71` - `test_markdown_report_includes_citations()` - ✅ FIXED
3. `tests/test_report_generation.py:252` - `test_full_report_workflow()` - ✅ FIXED

These tests now have `@pytest.mark.expensive` and are excluded from default `pytest` runs.

## API Call Sites in Codebase

| File | Line | Function | When Called |
|------|------|----------|-------------|
| `evidence_tools.py` | 400 | `messages.create` | Evidence extraction (23 calls per session) |
| `unified_analysis.py` | 504 | `messages.create` | Requirement analysis |
| `llm_extractors.py` | 528 | `messages.create` | Date extraction |
| `llm_extractors.py` | 732 | `messages.create` | Land tenure extraction |
| `llm_extractors.py` | 922 | `messages.create` | Project ID extraction |

## Cost Estimates

Per evidence extraction run (23 requirements, ~50K tokens per doc, 7 docs):
- Input: ~350K tokens × $3/MTok = ~$1.05
- Output: ~20K tokens × $15/MTok = ~$0.30
- **Total per run: ~$1.35**

If tests ran this 2-3 times: ~$4-5 consumed

## Mitigation Strategies

### Immediate (task-22a)
1. Add `@pytest.mark.expensive` to all tests calling `extract_all_evidence`
2. Verify pytest.ini excludes expensive tests by default

### Short-term (task-22b)
1. Add API call logging with cost estimates
2. Add environment check to refuse API calls in test environment without explicit flag
3. Add spending cap/alert system

### Long-term (task-22c)
1. Mock LLM responses for non-expensive tests
2. Use Haiku instead of Sonnet for development (5x cheaper)
3. Implement request batching where possible
4. Add cost dashboard/reporting

## Configuration Review

Current settings.py defaults:
```python
llm_extraction_enabled: bool = Field(default=False)  # Good - conservative
environment: str = Field(default="development")       # Uses Haiku in dev
llm_model_dev: str = "claude-haiku-4-5-20251001"     # $1/$5 per MTok
llm_model_prod: str = "claude-sonnet-4-5-20250929"   # $3/$15 per MTok
llm_cache_enabled: bool = Field(default=True)        # Good - reduces repeat calls
```

**Verified:** `evidence_tools.py` correctly uses `settings.get_active_llm_model()` which respects environment settings.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All tests making API calls have @pytest.mark.expensive marker
- [x] #2 Normal pytest run (no marker override) makes ZERO API calls
- [x] #4 Development environment uses Haiku (cheaper model) - verified in evidence_tools.py
- [ ] #3 API calls log estimated cost (future improvement)
- [ ] #5 Add CI check to prevent expensive tests from running without approval (future improvement)
<!-- AC:END -->
