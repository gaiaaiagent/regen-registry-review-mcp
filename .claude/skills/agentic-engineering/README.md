# Agentic Engineering Expert Skill

A comprehensive Claude Code skill providing expert guidance on agentic engineering, multi-agent systems, MCP server development, and architectural decisions.

## What This Skill Does

This skill transforms Claude into an expert agentic engineering advisor with deep knowledge of:

- **Architecture Decisions** - When to use skills vs MCP servers vs sub-agents vs slash commands
- **Multi-Agent Orchestration** - Orchestrator patterns, scaling agents, managing agent fleets
- **MCP Server Development** - Python SDK, FastMCP, uv tooling, testing, deployment
- **Interaction Patterns** - Decision frameworks for choosing the right agentic approach
- **Context Engineering** - Optimizing context windows, progressive disclosure techniques
- **Best Practices** - Common pitfalls, security, performance, reliability patterns

## When to Use This Skill

The skill automatically triggers when you ask about:

- "Should I use a skill or MCP server for...?"
- "How do I build a multi-agent system?"
- "What's the right pattern for my use case?"
- "How do I implement an orchestrator agent?"
- "When should I use sub-agents vs prompts?"
- "How do I optimize context windows?"
- "Best practices for MCP server development"
- "How to scale my agents?"
- "CLI vs scripts vs skills vs MCP?"

## Knowledge Base

The skill has access to 12 comprehensive documentation files covering:

### Claude Agentic Documentation

1. **claude-agent-skills.md** - Skills vs MCP vs sub-agents vs slash commands
2. **multi-agent-orchestration.md** - Orchestrator agent pattern, scaling compute
3. **agentic-interaction-patterns.md** - Decision framework for choosing patterns
4. **beyond-mcp.md** - Alternatives to MCP (CLI, scripts, skills)
5. **infinite-agents.md** - Scaling with agents
6. **hooks-multi-agent-observability.md** - Hooks and observability
7. **claude-subagents.md** - Sub-agent patterns
8. **context-engineering.md** - Context optimization
9. **agentic-prompts.md** - Prompt engineering for agents
10. **custom-agents.md** - Building custom agents
11. **multi-agent-compute-scaling.md** - Compute scaling
12. **agentic-coding.md** - Agentic coding practices

### MCP Development Documentation

1. **mcp_breakdown.md** - MCP technical deep-dive and audit
2. **mcp_uv_cheat_sheet.md** - Comprehensive MCP development guide
3. **mcp_server_primitives.md** - MCP primitives and patterns
4. **uv_running_python.md** - Using uv for Python projects

## Core Principles

The skill emphasizes these foundational principles:

### 1. Prompts as Primitives

> Everything comes down to context, model, prompt, and tools. Prompts are the fundamental unit of knowledge work. Don't give away the prompt.

### 2. Start Simple, Scale When Needed

> Keep it simple. Don't over-engineer. Let complexity be earned, not assumed. Larger working systems are almost always built from simple working systems.

### 3. Progressive Disclosure

> Load context only when needed. Use progressive disclosure patterns to protect context windows and improve agent performance.

### 4. Composition Over Duplication

> Build modular, composable solutions. Skills can use MCP servers, prompts can call sub-agents, everything composes.

### 5. The Core Four

> Context, Model, Prompt, Tools - these are fundamental. Every feature builds on top of these. Master the fundamentals.

## Decision Frameworks

### When to Use What Pattern

```
Ad hoc prompt
    ↓ (recognized pattern - 3x rule)
Reusable prompt (slash command)
    ↓ (need specialization AND parallelization)
Sub-agent
    ↓ (multiple services OR context efficiency)
MCP server
    ↓ (automatic behavior + repeat workflows)
Skill
    ↓ (multiple interface layers + long-term vision)
Full application
```

### MCP vs Alternatives

**Use MCP server when:**
- Integrating external tools/data sources
- Need standard protocol across agents
- Want to share functionality
- 80% of external tool use cases

**Use CLI when:**
- Building new tools (works for humans + agents)
- Need full control and customization
- Want to avoid MCP overhead
- 80% of new tool development

**Use Scripts when:**
- Need progressive disclosure
- Want context preservation
- Single-file portability matters
- Context window is constrained

**Use Skills when:**
- Want automatic agent invocation
- Need bundled resources (templates, scripts)
- Context efficiency is critical
- Repeat workflows with file system resources

## Example Questions and Answers

### Architecture

**Q:** "Should I build a skill or an MCP server for my use case?"

**A:** The skill will analyze your use case and provide:
- Direct recommendation with reasoning
- Decision framework
- Implementation path
- Tradeoff analysis
- Best practices

### Implementation

**Q:** "How do I build my first MCP server?"

**A:** The skill provides:
- Quick setup guide with uv
- Minimal working example
- Testing with MCP Inspector
- Claude Desktop configuration
- Common pitfalls to avoid
- Next steps

### Orchestration

**Q:** "How do I manage multiple agents working in parallel?"

**A:** The skill explains:
- Orchestrator agent pattern
- CRUD operations for agents
- Context window protection
- Observability strategies
- Lifecycle management
- Best practices for scaling

## How It Works

The skill uses **progressive disclosure** - it doesn't load all documentation upfront. Instead:

1. **Analyzes your question** to determine the topic
2. **Selectively reads** only relevant documentation
3. **Synthesizes guidance** from multiple sources
4. **Provides actionable advice** with examples
5. **References docs** for deeper exploration

This approach keeps the skill context-efficient while providing comprehensive expertise.

## Usage Examples

### Basic Usage

Simply ask your question naturally:

```
"Should I use a skill or MCP server for accessing our company API?"

"How do I implement multi-agent orchestration?"

"What's the best way to optimize context windows?"
```

### Advisory Mode (Default)

The skill provides guidance, frameworks, and decisions:

```
"When should I upgrade from a slash command to a sub-agent?"
```

### Implementation Mode

Ask explicitly for implementation help:

```
"Show me how to build an MCP server with FastMCP and uv"

"Give me code for an orchestrator agent pattern"
```

### Hybrid Mode

Get both guidance and code:

```
"Explain when to use skills vs MCP and show me an example of each"
```

## What Makes This Skill Special

### 1. Comprehensive Knowledge

Synthesizes knowledge from 16 expert-level documentation files covering the full spectrum of agentic engineering.

### 2. Opinionated Guidance

Provides clear recommendations based on established best practices, not just options.

### 3. Decision Frameworks

Offers structured decision trees to help you choose the right approach.

### 4. Context Efficient

Uses progressive disclosure - reads only what's needed for your question.

### 5. Implementation Ready

Provides concrete code examples, setup instructions, and next steps.

### 6. Pitfall Aware

Warns about common mistakes before you make them (stdout contamination, relative paths, etc.).

## Integration with Your Workflow

This skill complements your development workflow:

1. **Planning Phase** - Use for architecture decisions
2. **Implementation Phase** - Use for code examples and patterns
3. **Debugging Phase** - Use for troubleshooting guidance
4. **Scaling Phase** - Use for optimization and scaling patterns

## Skill Structure

```
.claude/skills/agentic-engineering/
├── SKILL.md           # Main skill definition (this file)
├── README.md          # Documentation (you're reading it)
└── docs/              # Reference documentation
    ├── claude_docs/   # Claude agentic patterns
    └── mcp_docs/      # MCP development guides
```

## Allowed Tools

The skill can use these tools to provide comprehensive answers:

- **Read** - Access documentation files
- **Grep** - Search documentation for specific topics
- **Glob** - Find relevant files
- **Bash** - Run commands for examples
- **WebFetch** - Fetch additional resources if needed

## Success Criteria

You get maximum value from this skill when:

1. **You understand WHY** - Not just what to do, but why this approach is right
2. **You can decide** - Have a clear decision framework for your situation
3. **You can implement** - Have concrete next steps or working code
4. **You avoid pitfalls** - Know common mistakes before making them
5. **You can scale** - Understand how to grow from simple to complex solutions

## Philosophy

This skill embodies the core philosophy of agentic engineering:

> The goal is not just to solve your immediate problem, but to make you a better agentic engineer who understands the principles and can make informed decisions independently.

## Contributing

This skill is built from curated documentation. To improve it:

1. Add new documentation files to `docs/claude_docs/` or `docs/mcp_docs/`
2. Update SKILL.md to reference new patterns or frameworks
3. Test with real questions to ensure quality
4. Share learnings with the community

## Related Resources

- **Claude Code Documentation** - https://docs.claude.com/claude-code
- **MCP Official Docs** - https://modelcontextprotocol.io
- **uv Documentation** - https://docs.astral.sh/uv
- **FastMCP** - Python MCP server framework

## License

This skill and its documentation are provided as-is for educational and development purposes.

---

**Last Updated:** 2025-11-12
**Version:** 1.0.0
**Compatibility:** Claude Code with skills support
