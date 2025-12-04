---
id: task-17
title: Evidence extraction prompts user for matrix view
status: Done
assignee: []
created_date: '2025-12-04 04:47'
updated_date: '2025-12-04 04:47'
labels:
  - enhancement
  - ux
  - stage-4
  - chatgpt
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
After evidence extraction completes, the response now includes prompts to guide the user to view the full requirements matrix rather than requiring them to explicitly request it.

### Problem

In the GPT workflow, after evidence extraction completed:
1. GPT showed a summary with key findings
2. User had to explicitly ask "Please provide the complete requirements matrix for me to review"
3. GPT then fetched the matrix

This required users to know they could ask for the matrix.

### Solution

Added `user_prompts` and `next_steps` fields to the evidence extraction response:

```python
response["user_prompts"] = {
    "show_matrix": "Would you like to see the complete requirements matrix with all evidence details?",
    "cross_validate": "Would you like to run cross-validation to check consistency across documents?",
}
response["next_steps"] = [
    "1. Review the evidence summary above",
    "2. Ask to see the complete requirements matrix for detailed review",
    "3. Run cross-validation to check for inconsistencies",
    "4. Generate the final report when ready",
]
```

### Implementation

Modified `evidence_tools.py:763-778`:
- Added `user_prompts` dict with natural language questions
- Added `next_steps` list with workflow guidance
- GPT will now include these prompts in its response

All 243 tests pass.
<!-- SECTION:DESCRIPTION:END -->
