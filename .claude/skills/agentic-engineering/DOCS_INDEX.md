# Documentation Index

Quick reference for locating relevant documentation based on user questions.

## By Topic

### Architecture & Decisions

**"Should I use X or Y?"**
- `docs/claude_docs/2025-10-27-claude-agent-skills.md` - Skills vs MCP vs sub-agents vs slash commands
- `docs/claude_docs/2025-08-25-agentic-interaction-patterns.md` - Complete decision framework
- `docs/claude_docs/2025-11-10-beyond-mcp.md` - MCP alternatives (CLI, scripts, skills)

### Multi-Agent Systems

**"How do I manage multiple agents?"**
- `docs/claude_docs/2025-11-03-multi-agent-orchestration.md` - Orchestrator pattern, CRUD, observability
- `docs/claude_docs/2025-07-28-claude-subagents.md` - Sub-agent patterns and usage
- `docs/claude_docs/2025-09-29-multi-agent-compute-scaling.md` - Scaling compute with agents

### MCP Development

**"How do I build an MCP server?"**
- `docs/mcp_docs/2025-11-11-mcp_uv_cheat_sheet.md` - Comprehensive development guide
- `docs/mcp_docs/2025-11-11-mcp_breakdown.md` - Technical deep-dive and API reference
- `docs/mcp_docs/2025-06-02-mcp_server_primitives.md` - MCP primitives and patterns
- `docs/mcp_docs/2025-06-02-uv_running_python.md` - uv package manager guide

### Context Optimization

**"How do I optimize context windows?"**
- `docs/claude_docs/2025-09-08-context-engineering.md` - Context engineering principles
- `docs/claude_docs/2025-11-10-beyond-mcp.md` - Progressive disclosure with CLI/scripts/skills
- `docs/mcp_docs/2025-11-11-mcp_breakdown.md` - Context-efficient MCP patterns

### Prompts & Best Practices

**"How do I write better prompts?"**
- `docs/claude_docs/2025-09-15-agentic-prompts.md` - Agentic prompt engineering
- `docs/claude_docs/2025-10-06-agentic-coding.md` - Agentic coding practices
- `docs/claude_docs/2025-09-22-custom-agents.md` - Building custom agents

### Observability & Hooks

**"How do I monitor my agents?"**
- `docs/claude_docs/2025-07-14-hooks-multi-agent-observability.md` - Hooks and observability
- `docs/claude_docs/2025-11-03-multi-agent-orchestration.md` - Observability in orchestrator pattern

### Scaling & Performance

**"How do I scale my agentic system?"**
- `docs/claude_docs/2025-06-09-infinite-agents.md` - Infinite agents pattern
- `docs/claude_docs/2025-09-29-multi-agent-compute-scaling.md` - Compute scaling strategies
- `docs/claude_docs/2025-11-03-multi-agent-orchestration.md` - Managing agents at scale

## By File

### Claude Docs (docs/claude_docs/)

| File | Topics | Use When |
|------|--------|----------|
| 2025-06-09-infinite-agents.md | Infinite agents, scaling | Scaling questions |
| 2025-07-14-hooks-multi-agent-observability.md | Hooks, observability | Monitoring, lifecycle |
| 2025-07-28-claude-subagents.md | Sub-agents | Sub-agent patterns |
| 2025-08-25-agentic-interaction-patterns.md | Decision framework | "What should I use?" |
| 2025-09-08-context-engineering.md | Context optimization | Context questions |
| 2025-09-15-agentic-prompts.md | Prompt engineering | Prompt questions |
| 2025-09-22-custom-agents.md | Custom agents | Building agents |
| 2025-09-29-multi-agent-compute-scaling.md | Compute scaling | Scaling compute |
| 2025-10-06-agentic-coding.md | Coding practices | Best practices |
| 2025-10-27-claude-agent-skills.md | Skills vs others | Architecture decisions |
| 2025-11-03-multi-agent-orchestration.md | Orchestrator | Multi-agent management |
| 2025-11-10-beyond-mcp.md | MCP alternatives | CLI/scripts/skills |

### MCP Docs (docs/mcp_docs/)

| File | Topics | Use When |
|------|--------|----------|
| 2025-06-02-mcp_server_primitives.md | MCP primitives | Understanding MCP |
| 2025-06-02-uv_running_python.md | uv, Python | Package management |
| 2025-11-11-mcp_breakdown.md | MCP deep-dive | Technical details |
| 2025-11-11-mcp_uv_cheat_sheet.md | Complete guide | Building MCP servers |

## Reading Strategy

### For Quick Questions
Read only the most relevant 1-2 files

### For Complex Questions
Read 3-4 related files for comprehensive understanding

### For Implementation
Read implementation guides + best practices:
- MCP: `mcp_uv_cheat_sheet.md` + `mcp_breakdown.md`
- Multi-agent: `multi-agent-orchestration.md` + `claude-subagents.md`
- Architecture: `agentic-interaction-patterns.md` + `claude-agent-skills.md`

## Common Question Patterns

| Question Pattern | Primary Docs | Secondary Docs |
|-----------------|--------------|----------------|
| "Should I use X or Y?" | agentic-interaction-patterns.md | claude-agent-skills.md, beyond-mcp.md |
| "How do I build..." | Relevant guide (mcp_uv_cheat_sheet, etc.) | Best practices docs |
| "How do I scale..." | multi-agent-compute-scaling.md | infinite-agents.md, orchestration.md |
| "How do I optimize..." | context-engineering.md | beyond-mcp.md |
| "What's the best way..." | agentic-interaction-patterns.md | Relevant specific docs |

## Progressive Disclosure

Don't read entire files unless necessary. Use this strategy:

1. **Scan** - Check file headers/sections
2. **Select** - Read only relevant sections
3. **Synthesize** - Combine insights from multiple sources
4. **Reference** - Point to docs for deeper exploration

This keeps the skill context-efficient while providing comprehensive expertise.
