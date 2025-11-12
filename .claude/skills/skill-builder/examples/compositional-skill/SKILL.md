---
name: comprehensive-code-review
description: Perform comprehensive code review combining linting, testing, security scanning, and documentation checks. Use when user requests thorough code review, pre-commit checks, or comprehensive quality analysis.
---

# Comprehensive Code Review

Orchestrates multiple code quality tools to provide thorough code review.

## Instructions

This skill composes multiple existing capabilities for comprehensive analysis.

1. **Initialize Review** - Identify scope (files, directory, or entire project)

2. **Run Linting** - Use language-specific linters:
   ```bash
   # Python
   ruff check .

   # JavaScript/TypeScript
   eslint .
   ```

3. **Execute Tests** - Invoke test runner:
   ```bash
   pytest  # Python
   npm test  # JavaScript
   ```

4. **Security Scan** - Check for vulnerabilities:
   ```bash
   bandit -r .  # Python security
   npm audit  # JavaScript dependencies
   ```

5. **Check Documentation** - Verify docs exist and are current:
   - Use Read tool to check for README.md
   - Verify docstrings/comments in code files
   - Check for outdated documentation

6. **Code Complexity Analysis**:
   ```bash
   radon cc . -a  # Python complexity
   ```

7. **Combine Results** - Synthesize all findings into comprehensive report:
   - High priority issues (security, failing tests)
   - Medium priority (linting errors, missing docs)
   - Low priority (style issues, complexity warnings)

8. **Generate Action Items** - Provide prioritized list of improvements

## Examples

### Example: Full Project Review

```
Input: "Review the codebase before we merge to main"

Process:
1. Run ruff check on Python files
2. Execute pytest suite
3. Run bandit security scanner
4. Check documentation completeness
5. Analyze code complexity

Output:
- 3 security issues found (HIGH PRIORITY)
- 12 linting errors (MEDIUM PRIORITY)
- Test suite passing (✓)
- Missing docstrings in 5 files (LOW PRIORITY)
- Average complexity: B (acceptable)
```

## Compositional Elements

This skill leverages:
- Existing linting tools (external CLIs)
- Test frameworks (bash commands)
- Security scanners (external tools)
- Read tool (for documentation checks)
- Bash tool (for all CLI invocations)

## Best Practices

- Run quick checks first (linting) before expensive checks (full test suite)
- Allow user to skip certain checks if they want faster review
- Provide summary first, details on request
- Suggest fixes for common issues
- Respect existing tool configurations (.eslintrc, pyproject.toml, etc.)
