---
name: git-analyzer
description: Analyze git repository history, contributions, and statistics. Use when user asks about git history, code contributions, commit statistics, repository insights, or wants to analyze git logs.
allowed-tools: Bash, Read
---

# Git Analyzer

Provides comprehensive git repository analysis and insights.

## Instructions

1. **Verify git repository**:
   ```bash
   git rev-parse --is-inside-work-tree
   ```

2. **Determine analysis type** based on user request:
   - Commit history
   - Contribution statistics
   - File change analysis
   - Author statistics
   - Branch analysis

3. **Run appropriate git commands**:

   **For commit history**:
   ```bash
   git log --oneline --graph --decorate --all -n 20
   ```

   **For contribution statistics**:
   ```bash
   git shortlog -sn --all
   ```

   **For file changes**:
   ```bash
   git log --stat --pretty=format:'' --numstat
   ```

   **For recent activity**:
   ```bash
   git log --since="1 month ago" --pretty=format:"%h - %an, %ar : %s"
   ```

4. **Parse and summarize results** - Present insights in readable format

## Examples

### Example 1: Top contributors

```bash
git shortlog -sn --all | head -n 10
```

Output:
```
   150  John Doe
    89  Jane Smith
    45  Bob Johnson
```

### Example 2: Recent commits

```bash
git log --oneline --since="1 week ago"
```

### Example 3: File change frequency

```bash
git log --pretty=format: --name-only | sort | uniq -c | sort -rg | head -n 10
```

## Best Practices

- Always verify you're in a git repository first
- Provide context about date ranges when showing history
- Summarize large outputs rather than dumping raw data
- Offer to drill deeper if user wants more details
- Handle both regular and bare repositories
