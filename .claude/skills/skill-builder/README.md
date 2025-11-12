# Skill Builder

A meta-skill for creating new Claude Code skills with proper structure and best practices.

## What is This?

The skill-builder embodies the principle of **"build the thing that builds the thing"** - a powerful agentic abstraction. It helps you create well-structured, discoverable, and composable Claude Code skills.

This skill follows the insight from the agentic coding essays: skills are powerful compositional units, but **prompts are the primitive**. Everything in agent coding comes down to four elements: **context, model, prompt, and tools**. Every feature builds on these fundamentals.

## When to Use

Use this skill when you want to:
- Create a new Claude Code skill
- Package reusable functionality for agents
- Structure agent capabilities properly
- Get guidance on skill vs slash command vs sub-agent decisions

**But first:** Read `QUICKSTART.md` to ensure a skill is the right approach. Don't prematurely optimize into a skill when a slash command would suffice.

## Quick Start

Simply ask Claude:
```
"Create a skill for [functionality]"
"Help me build a skill that [does something]"
"I need a skill for [use case]"
```

The skill-builder will guide you through:
1. Clarifying requirements
2. Determining if a skill is the right approach
3. Creating proper structure
4. Generating SKILL.md with correct format
5. Adding supporting resources as needed

## Structure

```
skill-builder/
├── SKILL.md              # Main skill definition (Claude reads this)
├── README.md             # This file (for humans)
├── templates/            # Templates for new skills
│   ├── SKILL_TEMPLATE.md
│   └── SKILL_TEMPLATE_MINIMAL.md
├── scripts/              # Helper scripts
│   └── create_skill.py   # Automated skill generation
└── examples/             # Example skill patterns
    ├── simple-skill/
    ├── cli-wrapper-skill/
    ├── compositional-skill/
    └── workflow-skill/
```

## Manual Skill Creation

You can also use the helper script directly:

```bash
# Interactive mode (recommended)
python scripts/create_skill.py --interactive

# Command-line mode
python scripts/create_skill.py \
  --name my-skill \
  --scope personal \
  --description "Does something useful. Use when user needs this functionality."
```

## Philosophy

The skill-builder follows these principles:

1. **Prompts are primitives** - Always start with slash commands, escalate to skills only when needed
2. **Skills are compositional** - Skills can contain prompts, other skills, MCP servers, and sub-agents
3. **Progressive disclosure** - Only load context when needed
4. **Focused scope** - One skill, one capability domain
5. **Automatic invocation** - Skills trigger based on description matching, not manual invocation

## The Hierarchy

```
Skills (top level - composes everything)
  ├── Slash Commands (primitives - THE most important)
  ├── Other Skills (compose multiple skills)
  ├── MCP Servers (external integrations)
  └── Sub-agents (parallel, isolated workflows)
```

**Start with prompts.** Only create a skill when you have a proven, reusable solution that benefits from automatic invocation.

## Deep Philosophy: Why This Matters

### The Core Four

Everything in agentic coding reduces to four elements:
1. **Context** - What information is available
2. **Model** - The LLM processing the request
3. **Prompt** - Instructions guiding the model
4. **Tools** - Capabilities the agent can invoke

Every feature Claude Code adds—skills, sub-agents, MCP servers, hooks, plugins—is just a different way of managing these four elements. If you master the fundamentals, you'll master all compositional features built on top.

### Why Prompts are Primitives

The prompt is the fundamental unit of knowledge work. Everything is ultimately "tokens in, tokens out." Skills, sub-agents, and MCP servers are abstractions that make prompts more:
- **Discoverable** (skills trigger automatically)
- **Composable** (combine multiple capabilities)
- **Reusable** (package for repeated use)
- **Scalable** (sub-agents parallelize)
- **Integrated** (MCP connects external tools)

But they all execute prompts at the core. Don't give away your understanding of prompts. Master prompt engineering first.

### Progressive Disclosure is Key

Skills implement progressive disclosure in three layers:
1. **Metadata** (name/description) - Loaded for all skills
2. **Instructions** (SKILL.md content) - Loaded when skill invoked
3. **Resources** (templates/scripts/examples) - Loaded only when referenced

This is why SKILL.md should be concise. It only loads when the skill is invoked, but keeping it focused reduces context consumption and improves agent performance.

### Context Efficiency

MCP servers can consume 10,000+ tokens before your agent even starts working. With multiple MCP servers, you can lose 20%+ of context immediately.

Skills with progressive disclosure solve this:
- Only description loads initially (~50-200 tokens)
- Instructions load when skill invokes (~1,000-3,000 tokens)
- Resources load only when explicitly read

This is why the essays emphasize: **skills over MCP for context preservation**.

### Composition Over Everything

The power of skills isn't in what they do—it's in what they **compose**. A well-designed skill:
- Calls existing slash commands (don't rewrite prompts)
- Uses existing MCP servers (don't duplicate integrations)
- Invokes other skills (don't duplicate domain logic)
- Launches sub-agents (don't pollute context with parallel work)

**Don't rebuild what exists.** Compose it.

### The Reliability Question

One concern raised in the essays: when you chain multiple skills, will agents reliably call them in the right order?

This is valid. Skills are agent-invoked, meaning the agent decides. For critical workflows where order matters:
- **Option 1:** Use a single skill that orchestrates the workflow
- **Option 2:** Use a slash command with explicit steps
- **Option 3:** Use a sub-agent with a detailed prompt

Reliability increases when you're explicit. Skills trade some control for convenience.

## Examples

See the `examples/` directory for complete implementations:

- **simple-skill** - Code formatter (minimal structure, focused task)
- **cli-wrapper-skill** - Git analyzer (wraps existing CLI tool)
- **compositional-skill** - Code reviewer (combines multiple tools)
- **workflow-skill** - Feature scaffolder (multi-step orchestration)

## Best Practices for Skill Design

### Description Excellence

Your skill description is its discoverability mechanism. Make it work hard:

❌ **Bad:** "Handles PDF files"
✅ **Good:** "Convert PDF files to clean markdown using marker. Use when working with PDFs, document conversion, extracting content from PDFs, or when user asks to convert documents to markdown. Supports tables, equations, images, and multi-language OCR."

**Include:**
- What it does (functionality)
- When to use it (trigger words)
- What it supports (capabilities)
- Key constraints or features

**Use words users actually say:** "convert", "extract", "parse", "analyze", "generate", "create", "build"

### Focused Scope

One skill = one capability domain.

❌ Don't create "document-processor" that handles PDFs, Word, Excel
✅ Create separate focused skills:
- `pdf-converter` - PDF to markdown
- `spreadsheet-analyzer` - Excel analysis
- `presentation-builder` - PowerPoint creation

Focused skills are more:
- Discoverable (clearer triggers)
- Maintainable (easier to update)
- Reliable (less complexity)
- Composable (combine as needed)

### Composition Over Duplication

If functionality exists, compose it. Don't rebuild.

```markdown
## Instructions

1. Use SlashCommand tool to invoke: `/analyze-data`
2. Process the results with scripts/transform.py
3. Use `report-generator` skill for output
4. Use `mcp__github` MCP server to create issue if problems found
```

This skill composes:
- Existing slash command
- Local script
- Another skill
- MCP server

**Zero duplication. Maximum leverage.**

### Tool Restrictions for Safety

Restrict tools when appropriate:

```yaml
allowed-tools: Read, Grep, Glob  # Read-only analysis
```

```yaml
allowed-tools: Read, Write, Bash  # Full workflow capability
```

Omit `allowed-tools` for standard permissions (asks user).

### Progressive Disclosure in Practice

Structure content by loading frequency:

**SKILL.md** (loads on invocation):
- Core workflow steps
- Essential commands
- Key decision points

**Separate files** (loads only when read):
- Detailed reference material
- Large templates
- Extensive examples
- Bulk configuration

Reference them: "Read `templates/config.yaml` for configuration options"

## Skill Creation Checklist

- [ ] Verified a skill is appropriate (not slash command/sub-agent/MCP)
- [ ] Defined clear purpose and automatic trigger conditions
- [ ] Chose appropriate scope (personal vs project)
- [ ] Wrote trigger-rich description (what + when + capabilities)
- [ ] Provided step-by-step actionable instructions
- [ ] Included concrete examples with expected outputs
- [ ] Added supporting resources if needed (kept SKILL.md concise)
- [ ] Validated YAML frontmatter syntax
- [ ] Tested discovery: "What skills are available?"
- [ ] Tested invocation with natural language
- [ ] Verified it composes existing capabilities (not duplicating)
- [ ] Documented in project README if team skill

## Remember

**Skills are powerful, but prompts are fundamental.**

If you can solve it with a slash command, do that first. Only escalate to skills when:
1. You've proven the solution works
2. You need automatic invocation
3. You want reusable, portable packaging
4. You need to compose multiple capabilities

The prompt is the fundamental unit of knowledge work. Everything else builds on prompts.

## Resources

- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Skills Blog Post](https://claude.com/blog/skills)
- [Agent Skills Guide](../../docs/claude_docs/2025-10-27-claude-agent-skills.md)
- [Beyond MCP](../../docs/claude_docs/2025-11-10-beyond-mcp.md)
