# Skill Examples

These examples demonstrate common skill patterns and best practices.

## Available Examples

### 1. Simple Skill: Code Formatter

**Pattern:** Focused, single-purpose skill with straightforward workflow

**Location:** `simple-skill/`

**What it demonstrates:**
- Minimal structure
- Clear trigger conditions
- Language-specific tool selection
- Tool availability checking
- Basic error handling

**Use this pattern when:**
- You have a focused, well-defined task
- The workflow is straightforward (3-5 steps)
- No complex composition needed
- Limited supporting resources required

---

### 2. CLI Wrapper Skill: Git Analyzer

**Pattern:** Wraps existing CLI tool with agent-friendly instructions

**Location:** `cli-wrapper-skill/`

**What it demonstrates:**
- Wrapping existing command-line tools
- Multiple command variations based on user needs
- Output parsing and summarization
- Repository verification before operations
- Handling different analysis types

**Use this pattern when:**
- You have an existing CLI tool to wrap
- Multiple commands serve related purposes
- Output needs interpretation/summarization
- Tool installation verification is important

---

### 3. Compositional Skill: Comprehensive Code Review

**Pattern:** Combines multiple tools and capabilities for comprehensive analysis

**Location:** `compositional-skill/`

**What it demonstrates:**
- Orchestrating multiple tools
- Sequential workflow with dependencies
- Combining results from different sources
- Prioritizing findings
- Progressive complexity (quick checks first, expensive checks later)

**Use this pattern when:**
- You need to combine multiple tools/capabilities
- The task requires synthesizing information from various sources
- Results need prioritization or categorization
- Users may want to skip certain steps

---

### 4. Workflow Skill: Feature Scaffolder

**Pattern:** Multi-step orchestration with decision points and user interaction

**Location:** `workflow-skill/`

**What it demonstrates:**
- Complex multi-step workflows
- Analyzing existing patterns before creating new ones
- Generating multiple related files
- Integration with existing codebase
- Creating actionable next steps

**Use this pattern when:**
- The task has many sequential steps
- You need to analyze before generating
- Creating multiple related artifacts
- Integration with existing code is required
- Users need guidance on next steps

---

## Comparison Matrix

| Feature | Simple | CLI Wrapper | Compositional | Workflow |
|---------|--------|-------------|---------------|----------|
| Complexity | Low | Medium | Medium | High |
| Steps | 3-5 | 5-8 | 5-10 | 10+ |
| External Tools | Few | One main tool | Multiple | Multiple |
| File Generation | No | No | No | Yes |
| User Interaction | Minimal | Minimal | Optional | Required |
| Context Usage | Low | Low | Medium | Medium-High |
| Best For | Single task | Tool wrapping | Analysis | Code generation |

## Using These Examples

1. **Study the pattern** - Read through the SKILL.md to understand the structure
2. **Copy and modify** - Use as a starting point for your own skill
3. **Adapt to your needs** - Change the specifics while keeping the pattern
4. **Test thoroughly** - Ensure your skill triggers correctly and handles edge cases

## Best Practices from Examples

### From Simple Skill
- Keep scope focused
- Use clear step numbering
- Check tool availability first
- Provide concrete examples

### From CLI Wrapper
- Verify prerequisites before execution
- Offer multiple command variations
- Summarize output, don't dump raw data
- Handle both success and error cases

### From Compositional Skill
- Run quick checks before expensive operations
- Allow selective execution
- Prioritize findings by importance
- Synthesize results into actionable insights

### From Workflow Skill
- Gather requirements upfront
- Analyze existing patterns first
- Generate with meaningful boilerplate
- Provide clear next steps
- Document integration points

## Creating Your Own

When creating a new skill:

1. **Start with the simplest pattern** that fits your needs
2. **Add complexity only when necessary**
3. **Test discovery** - Can Claude find it with natural language?
4. **Test invocation** - Does it trigger at the right times?
5. **Iterate** - Refine based on actual usage

## Questions?

If you're unsure which pattern to use, ask yourself:

- **Single tool, single task?** → Simple Skill
- **Wrapping existing CLI?** → CLI Wrapper
- **Combining multiple tools?** → Compositional Skill
- **Multi-step with generation?** → Workflow Skill

When in doubt, start simple. You can always add complexity later.
