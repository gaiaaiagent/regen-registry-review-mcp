# MCP vs Alternatives: Decision Matrix

When should you use MCP servers vs CLI tools vs scripts vs skills? This checklist helps you make the right architectural decision.

## Quick Decision Tree

```
┌─────────────────────────────────────┐
│ Who owns/controls the tool/system? │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┐
     │           │
  External    Internal
     │           │
     ▼           ▼
   ┌───┐      ┌───┐
   │MCP│      │CLI│
   │80%│      │80%│
   └───┘      └───┘
     │           │
     │           ▼
     │      ┌─────────────────────┐
     │      │ Context critical?    │
     │      └─────────┬───────────┘
     │                │
     │          ┌─────┴─────┐
     │          │           │
     │         Yes          No
     │          │           │
     │          ▼           ▼
     │    ┌─────────┐  ┌────────┐
     │    │Scripts/ │  │CLI/MCP │
     │    │Skills   │  │Wrapper │
     │    │5%       │  │15%     │
     │    └─────────┘  └────────┘
     │
     ▼
┌──────────────────────┐
│ Need agent-triggered │
│ in Claude Code?      │
└──────┬───────────────┘
       │
  ┌────┴────┐
  │         │
 Yes       No
  │         │
  ▼         ▼
┌─────┐  ┌───┐
│Skill│  │MCP│
│OK   │  │OK │
└─────┘  └───┘
```

## Comparison Matrix

| Criterion | MCP | CLI | Scripts | Skills |
|-----------|-----|-----|---------|--------|
| **Ownership** | External tools (80%) | Internal tools (80%) | Internal (5%) | Internal (varies) |
| **Context Usage** | High (5-10% per server) | Low (2-5%) | Very Low (<1%) | Very Low (<1%) |
| **Agent Invoked** | ✅ Yes | ❌ Manual prime | ❌ Manual prime | ✅ Yes |
| **Setup Complexity** | Low (install & config) | Medium (write CLI) | Medium (write scripts) | Medium (write skill) |
| **Customizability** | Low (unless you own it) | ✅ High | ✅ High | ✅ High |
| **Portability** | Low (MCP ecosystem) | ✅ High | ✅ Very High | Low (Claude only) |
| **Composability** | ✅ Good | ✅ Good | ✅ Good | ✅ Excellent |
| **Progressive Disclosure** | ❌ No (loads all tools) | ⚠️ Partial | ✅ Yes | ✅ Yes |
| **Multi-agent Scale** | ✅ Excellent | ❌ Poor | ❌ Poor | ⚠️ Depends |
| **Team Usability** | ✅ Anyone | ✅ Devs + Agents | ⚠️ Agents mainly | ⚠️ Agents mainly |

## When to Use Each Approach

### Use MCP (80% for external, 10% for internal)

**External Tools:**
- Integrating with third-party services (GitHub, Slack, Google Drive, PostgreSQL)
- Using community-maintained servers
- Want standard, widely-supported interface
- Simplicity more important than context optimization
- Need multi-agent access at scale
- Don't mind 5-10% context usage per server

**Internal Tools (10% case):**
- Already have CLI built, want MCP wrapper for agent scaling
- Using multiple agents simultaneously
- Don't want to manage priming prompts
- Context usage not critical (<3 MCP servers total)

**Example Use Cases:**
- ✅ Connect to GitHub API
- ✅ Query PostgreSQL database
- ✅ Integrate Slack notifications
- ✅ Access Google Drive files
- ✅ Use community filesystem server

### Use CLI (80% for new internal tools)

**When Building New Internal Tools:**
- You control the codebase
- Want it usable by: you + your team + agents (trifecta)
- Context usage moderate concern
- Want portability (not locked to one agent system)
- Comfortable with priming prompts
- Can easily wrap with MCP later if needed

**Pattern:**
```bash
# Prime agent with simple slash command
/prime-tool-name

# Agent reads:
# 1. README with high-level overview
# 2. CLI help output to understand usage

# Agent uses CLI directly via bash
uv run python cli.py command --options
```

**Example Use Cases:**
- ✅ Internal data processing pipeline
- ✅ Custom deployment tooling
- ✅ Project-specific utilities
- ✅ Code generation tools
- ✅ Build/test automation

**Upgrade Path:**
```
CLI → Wrap with MCP when:
  - Need 3+ agents using it simultaneously
  - Want to share with non-technical users
  - Context usage becomes acceptable (<20% total)
```

### Use Scripts (5% for context-critical cases)

**When Context Window is Critical:**
- Already using 3+ MCP servers (>15% context gone)
- Need progressive disclosure (lazy loading)
- Tools are rarely all used together
- Comfortable with more upfront engineering
- Single-file portability important

**Pattern:**
```bash
# Prime agent
/prime-scripts

# Agent reads only README with conditionals
# Then uses --help to understand each script as needed
uv run script1.py --help
uv run script1.py --actual-args
```

**Example Use Cases:**
- ⚠️ Rare: When MCP + CLI both consume too much context
- ⚠️ Rare: 10+ related tools that are rarely all needed
- ⚠️ Rare: Extreme context preservation requirements

**Tradeoff:**
- ✅ Minimal context usage
- ❌ Code duplication across scripts
- ❌ More maintenance burden
- ❌ Requires good README with conditionals

### Use Skills (Varies by ecosystem)

**Claude Code Ecosystem:**
- Building for Claude Code specifically
- Want agent-triggered automation
- Need modular, composable units
- Combining multiple capabilities (tools + prompts + MCP)
- Repeat workflow across contexts
- OK with Claude ecosystem lock-in

**Pattern:**
```
skill.md → Metadata (context efficient)
       ↓
   Instructions (loaded when triggered)
       ↓
   Resources (loaded as needed)
```

**Example Use Cases:**
- ✅ Git worktree management (create, list, remove, switch)
- ✅ Video processing workflows
- ✅ Code review automation
- ✅ Multi-step deployment
- ✅ Meta-skill (skill that builds skills)

**Considerations:**
- ✅ Agent-invoked (automatic)
- ✅ Context efficient (progressive disclosure)
- ✅ Composable (can use MCP, CLI, other skills)
- ❌ Claude Code lock-in
- ❌ Can't nest sub-agents
- ❌ Can't embed slash commands directly

## Real-World Examples

### Example 1: Kalshi Markets Integration

**Scenario:** Access prediction market data from Kalshi API

**Options Analysis:**

| Approach | Context | Complexity | Portability | Verdict |
|----------|---------|------------|-------------|---------|
| MCP | 10,000 tokens | Low | Low | ❌ High context cost |
| CLI | 5,000 tokens | Medium | High | ✅✅ Best balance |
| Scripts | 2,000 tokens | Medium | Very High | ⚠️ Overkill unless context critical |
| Skill | 2,000 tokens | Medium | Low | ⚠️ If Claude Code only |

**Recommendation:** Build CLI first (works for you + team + agents), consider scripts only if context becomes critical.

### Example 2: GitHub Issue Management

**Scenario:** Create, list, update GitHub issues

**External Service:** Yes (GitHub)

**Recommendation:** Use MCP
- Official GitHub MCP server exists
- Standard interface
- Don't reinvent the wheel
- Context cost acceptable for external integration

### Example 3: Internal Code Generator

**Scenario:** Generate boilerplate code for your project

**Options:**

1. **First iteration:** Slash command
   - Simplest to build
   - Test if it's actually useful
   - Easy to iterate

2. **If proven useful:** CLI
   - Make it usable by team AND agents
   - Still portable

3. **If context becomes issue:** Skill (if Claude Code) or Scripts (if universal)

### Example 4: Database Operations

**Scenario:** Query PostgreSQL database

**Exists:** Official PostgreSQL MCP server

**Recommendation:** Use MCP
- Don't rebuild what exists
- Standard interface
- Connection pooling handled
- Security best practices included

## Context Budget Management

### Scenario: Using Multiple Tools

If you're using multiple tools, monitor context budget:

```
MCP Server 1:    10,000 tokens (5%)
MCP Server 2:     8,000 tokens (4%)
MCP Server 3:    12,000 tokens (6%)
────────────────────────────────
Total:           30,000 tokens (15%)
Remaining:      170,000 tokens (85%)
```

**Decision Points:**

- **<10% total:** Don't worry, use MCP
- **10-20% total:** Consider if all servers always needed
  - Keep external MCP servers (can't avoid)
  - Convert internal MCP to CLI
- **>20% total:** Aggressive optimization
  - Keep critical external MCP only
  - Convert rest to CLI/scripts
  - Use skills for Claude Code workflows

## Decision Checklist

Use this checklist when choosing an approach:

### 1. Ownership Question
- [ ] Is this an external service/tool? → **MCP (80%)**
- [ ] Do I control the code? → **Continue to #2**

### 2. Context Budget
- [ ] Am I using <3 MCP servers? → **MCP wrapper OK (10%)**
- [ ] Am I using 3+ MCP servers? → **Continue to #3**

### 3. Tool Type
- [ ] Is this a new tool I'm building? → **CLI (80%)**
- [ ] Is context preservation critical? → **Scripts/Skills (5%)**
- [ ] Do I want agent-triggered in Claude Code? → **Skills**

### 4. Usage Pattern
- [ ] Need it for me + team + agents? → **CLI**
- [ ] Need it only for agents? → **Scripts or Skills**
- [ ] Need automatic agent triggering? → **Skills (if Claude) or MCP (universal)**

### 5. Portability
- [ ] Need it across multiple agent systems? → **CLI or Scripts**
- [ ] Claude Code only is fine? → **Skills OK**
- [ ] Want universal MCP compatibility? → **MCP**

## Key Principles

1. **Start simple:** Slash command → CLI → MCP/Skills
2. **Default to CLI for internal tools:** Works for you + team + agents
3. **Default to MCP for external tools:** Don't reinvent the wheel
4. **Optimize context only when needed:** Don't prematurely optimize
5. **Consider portability:** Avoid lock-in unless there's clear value
6. **Measure don't guess:** Monitor actual context usage

## Recommended Strategy

### For External Tools (You Don't Own)
```
80%: Just use MCP
15%: CLI if you need customization
 5%: Scripts/Skills if context critical
```

### For Internal Tools (You Build)
```
80%: Build CLI first
10%: Wrap with MCP if scaling agents
 5%: Use Scripts if context critical
 5%: Use Skills if Claude Code + agent-triggered
```

## Summary

The decision isn't binary. You can mix approaches:

- **MCP** for external integrations (GitHub, Slack, etc.)
- **CLI** for internal tools (your team + agents)
- **Scripts** when context is critical (rare)
- **Skills** when agent-triggered automation needed (Claude Code)

**Most common pattern:**
- 3-5 external MCP servers
- 5-10 internal CLI tools
- 0-2 scripts (only if context critical)
- 2-5 skills (Claude Code workflows)

This gives you the best of all worlds: standard interfaces for external systems, full control of internal tools, context efficiency when needed, and agent automation where valuable.
