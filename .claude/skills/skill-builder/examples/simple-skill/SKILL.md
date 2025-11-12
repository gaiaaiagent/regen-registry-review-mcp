---
name: code-formatter
description: Automatically format code files using standard formatters. Use when user mentions formatting, cleaning up code, applying code style, or fixing indentation. Supports Python, JavaScript, TypeScript, JSON, and Markdown.
allowed-tools: Read, Write, Bash
---

# Code Formatter

Automatically formats code files using appropriate formatters for each language.

## Instructions

1. **Identify files to format** - User specifies files or use Glob to find files matching patterns

2. **Determine language** - Based on file extension:
   - `.py` - Use `black` or `ruff format`
   - `.js`, `.ts`, `.jsx`, `.tsx` - Use `prettier`
   - `.json` - Use `jq` or `prettier`
   - `.md` - Use `prettier`

3. **Check formatter availability**:
   ```bash
   black --version  # For Python
   prettier --version  # For JS/TS/JSON/MD
   ```

4. **Format the file(s)**:
   ```bash
   black /path/to/file.py
   prettier --write /path/to/file.js
   ```

5. **Report results** - Tell user which files were formatted

## Examples

### Example 1: Format Python file

```bash
black /home/user/project/main.py
```

### Example 2: Format all JavaScript files in directory

```bash
prettier --write "/home/user/project/**/*.js"
```

## Best Practices

- Always confirm formatter is installed before attempting to format
- Show diff or summary of changes when possible
- Format entire directory when user doesn't specify files
- Respect any existing config files (.prettierrc, pyproject.toml, etc.)
