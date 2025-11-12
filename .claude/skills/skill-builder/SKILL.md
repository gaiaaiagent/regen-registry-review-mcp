---
name: skill-builder
description: Creates new Claude Code skills with proper structure, YAML frontmatter, and best practices. Use when user wants to create a new skill, package reusable functionality, or needs help structuring agent capabilities. Guides on when skills are appropriate vs slash commands, sub-agents, or MCP servers.
allowed-tools: Read, Write, Glob, Bash
---

# Skill Builder

Creates new Claude Code skills following best practices and proper structure.

## Pre-Creation Decision

Before creating a skill, ask: Should this be a skill?

**Create a skill when:**
- Repeat workflow across multiple contexts
- Automatic invocation desired (agent triggers it)
- Combines multiple operations
- Needs reusable resources (scripts/templates)

**Use slash command instead when:**
- Simple, manual trigger needed
- Still prototyping the solution
- One-off or single-step task

**Use sub-agent instead when:**
- Need parallel execution
- Want isolated context

**Use MCP server instead when:**
- External tool/data source integration

If uncertain, read `QUICKSTART.md` in this skill's directory for decision tree.

## Skill Creation Workflow

### 1. Gather Requirements

Ask user these clarifying questions:

1. What problem does this skill solve?
2. When should it trigger? (specific words/contexts)
3. What tools needed? (Read, Write, Bash, Grep, Glob, etc.)
4. Scope: personal (`~/.claude/skills/`) or project (`.claude/skills/`)?
5. Need supporting resources? (scripts, templates, examples)
6. Can it compose existing capabilities? (slash commands, other skills, MCP servers)

### 2. Create Directory Structure

```bash
# For personal skills
mkdir -p ~/.claude/skills/skill-name

# For project skills
mkdir -p .claude/skills/skill-name

# Add subdirectories if needed
mkdir -p skill-name/{templates,scripts,examples}
```

### 3. Generate SKILL.md

Use template from `templates/SKILL_TEMPLATE_MINIMAL.md` for simple skills or `templates/SKILL_TEMPLATE.md` for complex skills.

**Required YAML frontmatter:**
```yaml
---
name: lowercase-with-hyphens (max 64 chars)
description: What it does AND when to use it (max 1024 chars, include trigger words)
allowed-tools: Read, Write, Bash (optional, comma-separated)
---
```

**Critical: Description must include both functionality AND trigger conditions.**

Good example:
```yaml
description: Convert PDF files to markdown using marker. Use when working with PDFs, document conversion, extracting content, or when user asks to parse documents. Supports tables, equations, OCR.
```

**Instructions section structure:**
1. Prerequisites/verification steps
2. Numbered workflow steps with specific commands
3. Error handling
4. Result reporting

**Examples section:**
- Concrete use cases with commands
- Expected outputs
- Common variations

### 4. Add Supporting Resources (if needed)

**Templates** (`templates/`): Files the skill generates or uses as base

**Scripts** (`scripts/`): Helper utilities, preferably single-file with inline dependencies

**Examples** (`examples/`): Reference implementations

### 5. Create README.md (optional but recommended)

Human-readable documentation explaining:
- Purpose and use cases
- How it works
- Dependencies
- Examples

### 6. Validate and Test

Run validation:
```bash
# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('SKILL.md').read().split('---')[1])"

# Verify structure
tree skill-name/
```

Test workflow:
1. Restart Claude Code
2. Ask: "What skills are available?"
3. Test invocation with natural language matching triggers
4. Verify tool restrictions work
5. Check supporting resources load correctly

### 7. Deploy

**For project skills:**
```bash
git add .claude/skills/skill-name/
git commit -m "Add skill-name skill"
git push
```

**For personal skills:** Already available after restart.

## Quick Reference Patterns

**CLI Wrapper:**
```markdown
## Instructions
1. Check tool installed: `tool --version`
2. Run command: `tool [args] input --output output`
3. Report results
```

**Multi-step Workflow:**
```markdown
## Instructions
1. **Analyze** - Read/Grep input
2. **Transform** - Process with scripts/processor.py
3. **Generate** - Use templates/output.md
4. **Report** - Summarize results
```

**Compositional:**
```markdown
## Instructions
1. Use `/existing-command` slash command
2. Invoke `other-skill` for processing
3. Use MCP server if needed
4. Combine results
```

## Automated Creation

For faster creation, use the helper script:

```bash
python scripts/create_skill.py --interactive
```

Or see examples:
- `examples/simple-skill/` - Basic pattern
- `examples/cli-wrapper-skill/` - Wrapping existing tools
- `examples/compositional-skill/` - Combining capabilities
- `examples/workflow-skill/` - Complex orchestration

## Common Issues

**Not discovered:** Check YAML syntax, add more trigger words to description, restart Claude Code

**Wrong triggers:** Make description more specific, avoid overlap with other skills

**Tools don't work:** Verify `allowed-tools` includes what you need, use absolute paths

**Resources won't load:** Use Read tool explicitly, verify paths relative to skill directory

## Key Principles

1. **Prompts are primitives** - Start with slash commands, escalate to skills only when proven
2. **Focused scope** - One skill, one capability domain
3. **Compose, don't duplicate** - Use existing slash commands, skills, MCP servers
4. **Progressive disclosure** - Keep SKILL.md concise, details in separate files
5. **Trigger-rich descriptions** - Include words users actually say

## Resources

For deeper understanding, read:
- `README.md` in this directory - Philosophy and detailed guidance
- `QUICKSTART.md` - Decision tree for choosing right approach
- `examples/README.md` - Pattern comparison and usage guide
- [Official Skills Docs](https://code.claude.com/docs/en/skills)
