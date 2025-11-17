---
description: Implement a specific improvement from the code review recommendations
---

# Implement Code Improvement

I want to implement one of the improvements from the code review.

**Improvement to implement:** {IMPROVEMENT_NAME or NUMBER}

Please:

1. **Locate the recommendation:**
   - Read `docs/REFACTORING_ACTION_PLAN.md`
   - Find the specific improvement (#1-10)
   - Extract full details and code examples

2. **Check current state:**
   - Verify the issue still exists
   - Check if it's already been fixed
   - Identify all affected files

3. **Create implementation plan:**
   - List files to create
   - List files to modify
   - Order of implementation
   - Testing strategy

4. **Implement the improvement:**
   - Create new files with complete implementation
   - Modify existing files as needed
   - Follow the examples from the documentation
   - Add comprehensive error handling

5. **Write tests:**
   - Create test file if needed
   - Add tests for new functionality
   - Ensure all existing tests still pass

6. **Verify:**
   - Run full test suite
   - Check for regressions
   - Verify the improvement works as expected

7. **Document:**
   - Update relevant documentation
   - Add comments explaining design decisions
   - Update this command with status

After implementation, provide:
- Summary of changes made
- Files created/modified
- Test results
- Any issues encountered
- Next recommended improvement

**Available Improvements:**

From `QUICK_REFERENCE_IMPROVEMENTS.md`:

🔥 **Critical:**
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
