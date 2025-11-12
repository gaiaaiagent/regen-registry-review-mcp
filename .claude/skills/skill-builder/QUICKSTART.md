# Quickstart: Choosing the Right Approach

Fast decision tree for selecting between Skills, Slash Commands, Sub-agents, and MCP Servers.

## The One-Minute Decision Tree

```
START: I need to give my agent a capability
│
├─→ Is this an external tool/API/data source?
│   └─→ YES → Use MCP Server
│   └─→ NO → Continue
│
├─→ Do I need parallel execution or isolated context?
│   └─→ YES → Use Sub-agent
│   └─→ NO → Continue
│
├─→ Is this proven, reusable, and needs automatic triggering?
│   └─→ YES → Use Skill
│   └─→ NO → Use Slash Command (start here!)
```

## Quick Reference Guide

### Use **Slash Commands** (Prompts) when:
- ✅ Simple, focused task
- ✅ Manual trigger is fine
- ✅ Still prototyping/testing the approach
- ✅ One-off or infrequent use
- ✅ 1-5 straightforward steps

**Examples:**
- Generate commit message
- Format code in current file
- Explain a function
- Run tests

**How to create:**
```bash
echo "Your prompt instructions here" > .claude/commands/my-command.md
```

### Use **Skills** when:
- ✅ Repeat workflow (used often)
- ✅ Automatic invocation desired
- ✅ Multiple operations to orchestrate
- ✅ Needs supporting resources (scripts/templates)
- ✅ Already proven with slash command

**Examples:**
- PDF to markdown conversion
- Feature scaffolding
- Code review orchestration
- Documentation generation

**How to create:** Use this skill-builder skill or run the script.

### Use **Sub-agents** when:
- ✅ Need parallel execution
- ✅ Want isolated context (work won't pollute main agent)
- ✅ Complex task can run independently
- ✅ Don't need the context afterward

**Examples:**
- Parallel test suite runs
- Independent code analysis
- Security audit (large output)
- Batch processing

**How to create:** Use Task tool with specific sub-agent type.

### Use **MCP Servers** when:
- ✅ External tool integration
- ✅ External data source
- ✅ Third-party API
- ✅ Existing MCP server available

**Examples:**
- GitHub integration
- Database queries
- Slack notifications
- Weather API

**How to create:** Build MCP server or install existing one from marketplace.

## The Progression Path

Most capabilities should follow this evolution:

```
1. Slash Command (prototype)
   ↓ (if used repeatedly)
2. Refined Slash Command
   ↓ (if needs automatic triggering + composition)
3. Skill
   ↓ (if needs external distribution)
4. Plugin (with bundled skill)
```

**Never skip the slash command stage.** Prompts are the primitive. Everything builds on prompts.

## Common Scenarios

### "I want to format code"
→ **Slash Command** (simple, manual trigger)

### "I want agents to automatically format code when they notice issues"
→ **Skill** (automatic trigger)

### "I want to format 50 files in parallel"
→ **Sub-agent** (parallel execution)

### "I want to integrate with Prettier API"
→ **MCP Server** (external tool)

---

### "I want to analyze git history"
→ **Slash Command** (simple git commands)

### "I want comprehensive repo analysis with multiple git tools"
→ **Skill** (orchestrates multiple git operations)

### "I want to analyze 10 branches in parallel"
→ **Sub-agent** (parallel isolated analysis)

### "I want to integrate with GitHub API"
→ **MCP Server** (external API)

---

### "I want to convert a PDF"
→ **Slash Command** (if one-time)
→ **Skill** (if frequent, with marker CLI)

### "I want to convert 100 PDFs"
→ **Sub-agent** (batch parallel processing)

### "I want to integrate with Adobe API"
→ **MCP Server** (external service)

## The Composition Hierarchy

```
┌─────────────────────────────────────┐
│           Skills (Top)              │  ← Composes everything
│  - Agent invoked                    │
│  - Automatic triggering             │
│  - Progressive disclosure           │
└──────────┬──────────────────────────┘
           │
           ├─→ Slash Commands (Primitives) ← Start here!
           │   - Manual invocation
           │   - Simple prompts
           │
           ├─→ Other Skills
           │   - Compose multiple skills
           │
           ├─→ MCP Servers
           │   - External integrations
           │
           └─→ Sub-agents
               - Parallel/isolated work
```

**Skills sit at the top**, but **slash commands are the foundation**.

## Red Flags: When NOT to Create a Skill

❌ "I just thought of this approach" → Prototype with slash command first

❌ "I'll only use this once" → Just use slash command

❌ "I need this to run in parallel" → Use sub-agent

❌ "I'm connecting to external API" → Use MCP server

❌ "I want manual control" → Use slash command

## Decision Questions

Ask yourself:

1. **Have I proven this works?** If no → Slash command
2. **Will I use this repeatedly?** If no → Slash command
3. **Should agent trigger automatically?** If no → Slash command
4. **Does it need composition?** If no → Slash command
5. **Is it external integration?** If yes → MCP server
6. **Need parallel execution?** If yes → Sub-agent

**If all answers point to skill, then create a skill.**

## Time Investment Guide

| Approach | Time to Create | Maintenance | Flexibility |
|----------|---------------|-------------|-------------|
| Slash Command | 5-10 min | Low | High |
| Skill | 30-60 min | Medium | Medium |
| Sub-agent | 15-30 min | Low | High |
| MCP Server | 2-4 hours | High | Low |

**Start with the quickest approach that solves your problem.**

## Still Unsure?

**Default to slash commands.** You can always escalate later.

The progression is natural:
1. Start with slash command
2. Use it repeatedly
3. Realize you want automatic triggering
4. Elevate to skill

**Don't prematurely optimize into a skill.**

## Next Steps

- **To create slash command:** Just make a markdown file in `.claude/commands/`
- **To create skill:** Continue reading main SKILL.md in this directory
- **To use sub-agent:** Use the Task tool in your workflow
- **To add MCP server:** Install from marketplace or build your own

---

**Remember:** Prompts are the primitive. Everything else is composition.
