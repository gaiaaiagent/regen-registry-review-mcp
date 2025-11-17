---
description: Show status of code review improvements and what's been completed
---

# Code Review Implementation Status

Please check the status of code review improvements and show what's been completed.

**Steps:**

1. **Read status from documentation:**
   - Check `docs/QUICK_REFERENCE_IMPROVEMENTS.md` checklist section
   - Check `docs/REFACTORING_ACTION_PLAN.md` implementation sections
   - Check git log for recent commits related to improvements

2. **Verify completed items:**
   - Check if files mentioned in improvements exist
   - Run tests to see if new tests were added
   - Search for hardcoded values that should be removed

3. **Show progress report:**

   ```
   📊 CODE REVIEW IMPLEMENTATION STATUS

   ✅ Completed:
   - [List completed improvements with dates]
   - [Show test counts before/after]

   🚧 In Progress:
   - [List any partially implemented improvements]

   ⏳ Not Started:
   - [List remaining improvements from top 10]

   📈 Metrics:
   - Tests: X/184 passing
   - Hardcoded methodologies removed: X/6
   - Functions >100 lines: X/3 refactored
   - Code duplication reduction: X%
   ```

4. **Recommended next action:**
   - What should be implemented next
   - Estimated effort
   - Link to documentation section

5. **Show any issues:**
   - Tests failing after improvements
   - Regressions introduced
   - Incomplete implementations

**Quick checks to run:**

```bash
# Count hardcoded "soil-carbon-v1.2.2" strings
grep -r "soil-carbon-v1.2.2" src/ --include="*.py" | wc -l

# Count long functions (>100 lines)
# (Manual check of document_tools.py, validation_tools.py, report_tools.py)

# Test status
pytest tests/ -v --tb=short | tail -20
```

Format the report to be clear and actionable, showing exactly what's been done and what's next.
