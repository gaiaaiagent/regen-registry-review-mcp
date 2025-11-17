# Development Commands

This directory contains slash commands for development workflows.

## Code Review Commands (New!)

### `/review-docs`
Read and summarize all code review documentation.

**What it does:**
- Reads all 6 code review documents (141 KB)
- Provides executive summary
- Lists top 5 priority improvements
- Identifies quick wins
- Asks clarifying questions

**When to use:** First time seeing the code review, or need a refresher

---

### `/review-status`
Show implementation status of code review improvements.

**What it does:**
- Checks which improvements are completed
- Shows test metrics
- Counts remaining hardcoded values
- Recommends next action

**When to use:** Want to see progress, decide what to work on next

---

### `/implement-improvement {NUMBER}`
Implement a specific improvement from the code review.

**What it does:**
- Locates the recommendation in documentation
- Creates implementation plan
- Implements the changes
- Writes tests
- Verifies everything works

**When to use:** Ready to implement one of the 10 priority improvements

**Example:**
```
/implement-improvement 1
/implement-improvement Methodology Registry
```

---

## Existing Commands

### `/continue`
Continue working on the current task.

### `/improve`
Suggest improvements for the current code.

### `/initialize`
Initialize a new development session.

### `/initialize-full`
Full initialization with detailed setup.

---

## Code Review Documentation

All code review documentation is in `docs/`:

- **Start here:** `docs/QUICK_REFERENCE_IMPROVEMENTS.md` (Top 10 improvements)
- **Navigation:** `docs/README_REVIEWS.md` (Document index)
- **Summary:** `docs/SESSION_SUMMARY_2025-11-15.md` (Overview)
- **Action Plan:** `docs/REFACTORING_ACTION_PLAN.md` (Implementation timeline)
- **Full Analysis:** `docs/CODE_QUALITY_REVIEW.md` (47 issues, 2,252 lines)
- **Bug Fixes:** `docs/BUG_FIXES_2025-11-14.md` (Bugs fixed)

---

## Quick Reference: Top 10 Improvements

🔥 **Critical (Do First):**
1. Methodology Registry (4-6 hours)
2. Document Classifier Registry (6-8 hours)

🔶 **High Priority:**
3. Extractor Factory (3-4 hours)
4. Refactor discover_documents (3-4 hours)
5. Refactor cross_validate (3-4 hours)
6. Refactor generate_review_report (2-3 hours)

🟡 **Medium Priority:**
7. Error Handling (4-6 hours)
8. Move Magic Numbers to Config (2-3 hours)
9. Citation Parser (3-4 hours)
10. Validation Registry (4-5 hours)

**Total Effort:** 8-10 days for complete refactoring

---

## Workflow

**1. Understand the review:**
```bash
/review-docs
```

**2. Check status:**
```bash
/review-status
```

**3. Implement improvement:**
```bash
/implement-improvement 1
```

**4. Verify:**
```bash
pytest tests/ -v
/review-status
```

**5. Repeat for next improvement**

---

**Last Updated:** 2025-11-15
**Status:** Ready to use
