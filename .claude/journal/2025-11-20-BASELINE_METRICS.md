# Test Suite Baseline Metrics

**Date**: 2025-11-20
**State**: Pre-Phase 2 (Post-Parallelization)

## Current State

### Test Count
- Total tests: 275 tests
- Selected by default: 234 tests (41 deselected via markers)
- Test files: 27 files
- Total test code: 8,337 lines

### Test File Sizes
- Largest file: `test_upload_tools.py` (needs verification)
- Average lines per file: ~309 lines

### Performance (Parallel Enabled ✅)
- Parallel workers: 16 (auto-detected)
- Expected runtime: 15-17s (50% reduction from 34s baseline)
- Worker isolation: ✅ Implemented

### Coverage
- Measuring... (background process running)

### Known Issues
- 1 collection error detected
- 57 redundant tests identified
- 7 bare except blocks
- 12 weak assertions
- 13 unnecessary async tests

## Target State (End of Roadmap)

### Test Count
- Total tests: ~217 tests (58 removed as redundant)
- All properly marked and categorized
- No file >500 lines

### Performance
- Target runtime: <12s (71% reduction)
- Parallel execution: ✅
- Optimized fixtures: Session scope
- Cleanup overhead: Reduced 80%

### Coverage
- Target: 80% overall
- No critical module <50%
- Branch coverage enabled

## Tracking
- Phase 1: ✅ Complete (parallelization)
- Phase 2: Starting now
- Remaining phases: 6
