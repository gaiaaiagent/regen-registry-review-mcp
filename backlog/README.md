# Registry Review MCP Backlog

This directory tracks bugs, improvements, and feature requests for the Registry Review MCP server using the [Backlog.md](https://github.com/MrLesk/Backlog.md) format.

## Quick Commands

```bash
# List all tasks
backlog task list

# View a specific task
backlog task view task-1

# Create a new task
backlog task create "Task title" --priority high --labels "feature,workflow"

# Edit task status
backlog task edit task-1 --status "In Progress"
```

## Current Tasks

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| task-1 | Implement Human Review stage (Stage 7) | High | To Do |
| task-2 | Implement Completion stage (Stage 8) | Medium | To Do |
| task-3 | Cross-validation end-to-end testing | Medium | To Do |
| task-4 | Add PDF export to report generation | Low | To Do |

## Project Status

**Stages 1-6:** Complete (Initialize, Discovery, Mapping, Extraction, Cross-Validation, Report)
**Stages 7-8:** Not implemented (Human Review, Completion)

See `docs/ROADMAP.md` for full assessment.

## Labels

- `feature` - New functionality
- `workflow` - Workflow stage implementation
- `stage-5` through `stage-8` - Stage-specific work
- `testing` - Test coverage
- `enhancement` - Optional improvements

## Adding New Tasks

Use the CLI:
```bash
backlog task create "Title" --priority medium --labels "label1,label2" --desc "Description"
```

Or create a file in `tasks/` with this frontmatter:
```yaml
---
id: task-N
title: Task title
status: To Do
assignee: []
created_date: 'YYYY-MM-DD HH:MM'
labels: []
dependencies: []
priority: medium
---
```
