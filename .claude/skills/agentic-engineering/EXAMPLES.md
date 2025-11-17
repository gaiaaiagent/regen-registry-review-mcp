# Agentic Engineering Examples

Real-world examples demonstrating how to use the agentic engineering skill for architecture decisions, implementation guidance, and best practices.

## Table of Contents

1. [Architecture Decisions](#architecture-decisions)
2. [Multi-Agent Systems](#multi-agent-systems)
3. [MCP Server Development](#mcp-server-development)
4. [Context Optimization](#context-optimization)
5. [Migration & Refactoring](#migration--refactoring)
6. [Decision Trees](#decision-trees)

---

## Architecture Decisions

### Example 1: Internal API Access

**Question:** "We have an internal API for customer data. Should I build a skill or MCP server?"

**Skill Response:**

**Direct Answer:** Build an **MCP server** first, then optionally wrap in a skill if needed.

**Reasoning:**

This is a classic external integration use case - exactly what MCP servers were designed for. Here's the decision path:

```
Internal API = External data source
    ↓
MCP server is the right primitive
    ↓
Consider upgrading to skill only if:
- Context window becomes constrained (multiple MCP servers)
- Want automatic invocation based on context
- Need bundled resources (templates, scripts)
```

**Implementation:**

```bash
# 1. Create MCP server
uv init mcp-customer-api --package
cd mcp-customer-api
uv add "mcp[cli]" httpx pydantic

# 2. Implement
# src/mcp_customer_api/server.py
from mcp.server.fastmcp import FastMCP
import httpx
import os

mcp = FastMCP("customer-api")
API_BASE = os.getenv("CUSTOMER_API_BASE")
API_KEY = os.getenv("CUSTOMER_API_KEY")

@mcp.tool()
async def get_customer(customer_id: str) -> dict:
    """Get customer details by ID"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/customers/{customer_id}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def search_customers(query: str, limit: int = 10) -> list:
    """Search customers by name or email"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/customers/search",
            params={"q": query, "limit": limit},
            headers=headers
        )
        return response.json()

if __name__ == "__main__":
    mcp.run()
```

**When to Upgrade to Skill:**

Only upgrade if you experience:
- **Context pressure** - 3+ MCP servers consuming >20% context
- **Workflow bundling** - Need to package templates, scripts alongside
- **Auto-invocation** - Want skill triggered automatically by context

**Tradeoffs:**
- MCP: Standard, portable, simple - manual invocation
- Skill: Auto-invoked, context-efficient - Claude-specific

---

### Example 2: Git Worktree Management

**Question:** "I need to manage multiple git worktrees. Slash command, sub-agent, or skill?"

**Skill Response:**

**Direct Answer:** Start with a **slash command**, upgrade to **skill** when you need full worktree lifecycle management.

**Decision Path:**

```
Creating one worktree = One-off task
    ↓
Use slash command
    ↓
Managing worktrees (create, list, stop, remove) = Repeat workflow
    ↓
Upgrade to skill
```

**Level 1: Slash Command (Start Here)**

```markdown
# .claude/commands/create-worktree.md
Create a new git worktree with the following:

1. Create worktree for branch: {{BRANCH_NAME}}
2. Set up environment variables for unique ports
3. Install dependencies
4. Start dev servers

Use port offset {{PORT_OFFSET}} (e.g., 4010, 5013)
```

**Level 2: Skill (When You Need Management)**

When you're creating/managing multiple worktrees frequently:

```
.claude/skills/worktree-manager/
├── SKILL.md
├── scripts/
│   ├── create.sh
│   ├── list.sh
│   ├── stop.sh
│   └── remove.sh
└── templates/
    └── env.template
```

**Why This Progression:**

1. **Slash command proves the workflow** - You understand the steps
2. **Skill adds automation** - Manages complete lifecycle
3. **Resources stay organized** - Scripts, templates in dedicated directory

---

## Multi-Agent Systems

### Example 3: Codebase QA Across Frontend/Backend

**Question:** "I need to QA both frontend and backend code. How should I structure this?"

**Skill Response:**

**Direct Answer:** Use the **Orchestrator Agent** pattern with specialized sub-agents.

**Architecture:**

```
You (User)
    ↓
Orchestrator Agent (coordinates)
    ├─→ Frontend QA Agent (specialized, isolated context)
    ├─→ Backend QA Agent (specialized, isolated context)
    └─→ Integration QA Agent (specialized, isolated context)
```

**Implementation Pattern:**

```python
# Orchestrator creates specialized agents
agents = {
    "frontend": create_agent(
        name="frontend-qa",
        focus="frontend code review",
        context=["src/frontend/**/*.tsx", "src/components/**/*"]
    ),
    "backend": create_agent(
        name="backend-qa",
        focus="backend code review",
        context=["src/api/**/*.py", "src/services/**/*"]
    ),
    "integration": create_agent(
        name="integration-qa",
        focus="integration testing",
        context=["tests/integration/**/*"]
    )
}

# Orchestrator commands agents with detailed prompts
for agent_type, agent in agents.items():
    prompt = f"""
    Review {agent_type} code for:
    1. Code quality and readability
    2. Security vulnerabilities
    3. Performance issues
    4. Best practices

    Create summary in docs/{agent_type}-qa-summary.md
    Include Mermaid diagrams for architecture
    """
    command_agent(agent.id, prompt)

# Monitor progress
observe_agents(agents.values())

# Cleanup when done
for agent in agents.values():
    delete_agent(agent.id)
```

**Key Principles:**

1. **Context Protection** - Each agent sees only what it needs
2. **Focused Purpose** - One agent, one responsibility
3. **Aggressive Deletion** - Delete agents when work completes
4. **Orchestrator Coordination** - Orchestrator delegates, doesn't process

**When to Use:**

- ✅ Multiple independent tasks that can run in parallel
- ✅ Need to isolate different contexts (frontend vs backend)
- ✅ Want to scale compute beyond single agent
- ❌ Simple sequential tasks (use regular prompts instead)

---

### Example 4: Parallel Image Generation

**Question:** "I need to generate 100 images for a presentation. What's the best approach?"

**Skill Response:**

**Direct Answer:** **Prompt → Sub-agents** pattern with parallelization.

**Progression:**

```
1. Ad hoc (test the workflow)
    ↓
2. Reusable prompt (standardize)
    ↓
3. Sub-agents (parallelize at scale)
```

**Level 1: Test the Workflow**

```
"Generate an image using Replicate MCP:
- Prompt: 'futuristic data center'
- Model: stability-ai/sdxl
- Aspect ratio: 16:9"
```

**Level 2: Reusable Prompt**

```markdown
# .claude/commands/generate-images.md
Generate {{COUNT}} images with the following:

1. Use Replicate MCP server
2. Model: stability-ai/sdxl
3. Base prompt: {{BASE_PROMPT}}
4. Variations: Add different styles, lighting, perspectives
5. Aspect ratio: 16:9
6. Save to: presentations/images/

Create variations like:
- "{{BASE_PROMPT}}, professional photography"
- "{{BASE_PROMPT}}, studio lighting"
- "{{BASE_PROMPT}}, aerial view"
```

**Level 3: Sub-agents for Scale (100+ images)**

```
Create 5 sub-agents, each generates 20 images

Agent 1: Professional photography style (20 images)
Agent 2: Studio lighting style (20 images)
Agent 3: Aerial views (20 images)
Agent 4: Close-up details (20 images)
Agent 5: Wide angle scenes (20 images)

All run in parallel → 100 images generated concurrently
```

**Why Sub-agents Here:**

- **Parallelization** - 5x faster than sequential
- **Specialization** - Each agent focuses on one style
- **Isolation** - Failures don't affect other agents

**Don't Upgrade to MCP Unless:**

You need to integrate multiple services (Replicate + your company's brand assets + customer data)

---

## MCP Server Development

### Example 5: Building a Weather MCP Server

**Question:** "How do I build an MCP server that provides weather data?"

**Skill Response:**

**Complete Implementation:**

```bash
# 1. Setup
uvx create-mcp-server
# Enter: weather-server

cd weather-server
uv add "mcp[cli]" httpx pydantic

# 2. Create server
# src/weather_server/server.py
```

```python
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
import httpx
from pydantic import BaseModel
from typing import Optional

mcp = FastMCP("weather-server")

# Structured output model
class WeatherData(BaseModel):
    temperature: float
    humidity: float
    condition: str
    wind_speed: float
    location: str

@mcp.tool()
async def get_weather(
    latitude: float,
    longitude: float,
    ctx: Context[ServerSession, None]
) -> WeatherData:
    """Get current weather for coordinates using NWS API"""
    await ctx.info(f"Fetching weather for {latitude}, {longitude}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get grid point
            points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
            await ctx.report_progress(0.3, 1.0, "Getting grid point")

            points_response = await client.get(points_url)
            points_response.raise_for_status()
            points_data = points_response.json()

            # Get forecast
            forecast_url = points_data["properties"]["forecast"]
            await ctx.report_progress(0.6, 1.0, "Getting forecast")

            forecast_response = await client.get(forecast_url)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Extract current period
            current = forecast_data["properties"]["periods"][0]

            await ctx.report_progress(1.0, 1.0, "Complete")

            return WeatherData(
                temperature=current["temperature"],
                humidity=current.get("relativeHumidity", {}).get("value", 0),
                condition=current["shortForecast"],
                wind_speed=float(current["windSpeed"].split()[0]),
                location=points_data["properties"]["relativeLocation"]["properties"]["city"]
            )

    except httpx.HTTPError as e:
        await ctx.error(f"HTTP error: {e}")
        raise ToolError(f"Failed to fetch weather: {e}")
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise ToolError("Weather service unavailable")

@mcp.resource("weather://status")
def server_status() -> str:
    """Get server status"""
    return "Weather server operational - using NWS API"

@mcp.prompt()
def weather_analysis(location: str) -> str:
    """Generate weather analysis prompt"""
    return f"""Analyze the weather for {location} and provide:

1. Current conditions summary
2. Forecast analysis
3. Recommendations for outdoor activities
4. Any weather alerts or concerns
"""

if __name__ == "__main__":
    mcp.run()
```

**Test with Inspector:**

```bash
npx @modelcontextprotocol/inspector python src/weather_server/server.py
```

**Configure for Claude:**

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/weather-server",
        "run",
        "weather-server"
      ]
    }
  }
}
```

**Critical Pitfalls Avoided:**

✅ **stderr for logging** - `await ctx.info()` goes to stderr
✅ **Progress reporting** - Shows status for long operations
✅ **Error handling** - Catches HTTP and unexpected errors
✅ **Timeout** - 30s timeout prevents hanging
✅ **Structured output** - Pydantic model ensures type safety
✅ **Absolute paths** - Configuration uses absolute path

---

## Context Optimization

### Example 6: Beyond MCP - Context-Efficient Alternatives

**Question:** "My MCP server is using 10% of my context window before I even start. What alternatives do I have?"

**Skill Response:**

**The Problem:**

```
MCP Server = 10,000 tokens on load
Stack 3 MCP servers = 30,000 tokens (15% of 200K context)
```

**Solution: Progressive Disclosure Alternatives**

### Option 1: CLI Approach (5.6% context)

```markdown
# .claude/commands/prime-kalshi.md
Read only these files to understand the Kalshi CLI:

1. docs/kalshi/README.md - Overview and setup
2. src/kalshi/cli.py - CLI interface

Workflow:
- Use `--help` flag to see available commands
- Run commands via bash
- Do NOT read other Python files unless needed

Example: `python cli.py search --query "AGI" --limit 5`
```

**Context Saved:** ~4.4% (10% → 5.6%)

### Option 2: Scripts Approach (2% context)

```markdown
# .claude/commands/prime-kalshi-scripts.md
File system scripts for Kalshi markets.

Read: scripts/README.md

Each script is self-contained. Use `--help` to understand usage.

Available scripts:
- search.py - Search markets
- get-market.py - Get market details
- get-orders.py - Get order book

Do NOT read scripts themselves unless --help doesn't provide needed info.

Use: `uv run scripts/search.py --query "AGI" --json`
```

**Context Saved:** ~8% (10% → 2%)

### Option 3: Skills Approach (1% context)

```
.claude/skills/kalshi-markets/
├── SKILL.md (only metadata loaded initially)
└── scripts/ (loaded on-demand)
```

**Context Saved:** ~9% (10% → 1%)

**Decision Matrix:**

| Approach | Context | Setup | Invocation | Portability |
|----------|---------|-------|------------|-------------|
| MCP | 10% | Low | Auto | High |
| CLI | 5.6% | Medium | Manual | Very High |
| Scripts | 2% | Medium | Manual | High |
| Skill | 1% | High | Auto | Medium (Claude-only) |

**Recommendation:**

Start with **MCP** (simplest). Only migrate if:
- Stacking 3+ MCP servers
- Context window >20% consumed at boot
- Need context efficiency more than simplicity

---

## Migration & Refactoring

### Example 7: Upgrading Slash Command to Skill

**Question:** "I have a slash command I use all the time. When should I convert it to a skill?"

**Skill Response:**

**Convert When You Need:**

1. **Automatic invocation** - Want agent to trigger without manual /command
2. **File system resources** - Need to bundle scripts, templates, configs
3. **Progressive disclosure** - Want context-efficient loading
4. **Repeat workflow** - Using this across multiple projects

**Migration Path:**

**Before (Slash Command):**

```markdown
# .claude/commands/analyze-code.md
Analyze the codebase and create a summary:

1. Read all Python files in src/
2. Create architecture diagram
3. List key components
4. Identify dependencies
5. Write summary to docs/architecture.md
```

**After (Skill):**

```
.claude/skills/code-analyzer/
├── SKILL.md
├── scripts/
│   ├── find-components.py
│   ├── analyze-deps.py
│   └── generate-diagram.py
└── templates/
    └── architecture-template.md
```

**SKILL.md:**

```markdown
---
name: code-analyzer
description: Automatically analyze codebase architecture when user asks about code structure, components, dependencies, or architecture. Creates diagrams and documentation.
---

# Code Analyzer

When user asks about codebase structure or architecture:

1. Run scripts/find-components.py to identify components
2. Run scripts/analyze-deps.py to map dependencies
3. Run scripts/generate-diagram.py to create Mermaid diagrams
4. Use templates/architecture-template.md for output format
5. Write to docs/architecture.md

Scripts are self-contained. Use --help for usage.
```

**Benefits of Migration:**

- ✅ Auto-triggers on architecture questions
- ✅ Scripts are reusable and testable
- ✅ Template ensures consistent output
- ✅ Portable across projects (copy skill directory)

**Keep as Slash Command If:**

- ❌ Only use it in one project
- ❌ Don't need automatic triggering
- ❌ No additional resources needed

---

## Decision Trees

### Decision Tree 1: What Pattern Should I Use?

```
START: I need to solve a problem with agents

├─ Have you done this task before?
│  ├─ No → Use ad hoc prompt (explore the problem)
│  └─ Yes ↓
│
├─ Do you do this task repeatedly (3+ times)?
│  ├─ No → Keep using ad hoc prompts
│  └─ Yes ↓
│
├─ Create reusable prompt (slash command)
│
├─ Do you need parallelization AND specialization?
│  ├─ Yes → Use sub-agents
│  └─ No ↓
│
├─ Do you need to integrate external services?
│  ├─ Yes ↓
│  │  ├─ External service? → Use MCP server
│  │  ├─ Multiple services? → Use wrapper MCP server
│  │  └─ Need context efficiency? → Consider CLI/scripts/skill
│  └─ No ↓
│
├─ Do you need automatic invocation + bundled resources?
│  ├─ Yes → Use skill
│  └─ No → Keep using slash command
│
└─ Do you need multiple interface layers (UI, API, CLI)?
   ├─ Yes → Build full application
   └─ No → You're done! Use what you have
```

### Decision Tree 2: MCP vs Alternatives

```
START: I need to give my agent access to functionality

├─ Who owns/controls this functionality?
│  ├─ External (3rd party API, service) ↓
│  │  ├─ Existing MCP server available?
│  │  │  ├─ Yes → Use MCP server (80% of cases)
│  │  │  └─ No ↓
│  │  │     ├─ Simple integration? → Use MCP server
│  │  │     └─ Context-constrained? → Consider CLI/scripts
│  │
│  └─ Internal (you're building it) ↓
│     ├─ Humans need to use it too?
│     │  ├─ Yes → Build CLI (works for humans + agents)
│     │  └─ No ↓
│     │
│     ├─ Need context efficiency?
│     │  ├─ Yes → Use scripts or skill
│     │  └─ No → Use CLI or MCP
│     │
│     └─ Need auto-invocation?
│        ├─ Yes → Wrap in skill
│        └─ No → CLI is sufficient
```

### Decision Tree 3: Single Agent vs Multi-Agent

```
START: I have a task to complete

├─ Can this be done in one focused task?
│  ├─ Yes → Use single agent (primary or sub-agent)
│  └─ No ↓
│
├─ Are the tasks independent (can run in parallel)?
│  ├─ No → Use single agent with sequential steps
│  └─ Yes ↓
│
├─ Would each task consume >50% of context if combined?
│  ├─ No → Use single agent
│  └─ Yes ↓
│
├─ Use orchestrator + multiple sub-agents
│
└─ For each sub-task:
   ├─ Create focused agent
   ├─ Provide only necessary context
   ├─ Monitor via observability
   └─ Delete when complete
```

---

## Quick Wins

### Pattern: Start Simple

```
Problem: "I need to do X"

✅ RIGHT:
1. Ad hoc prompt first
2. Understand the problem
3. Then choose the right pattern

❌ WRONG:
1. Build complex multi-agent MCP wrapper skill
2. Realize you didn't understand the problem
3. Wasted time on wrong solution
```

### Pattern: Three Times Rule

```
✅ Use this pattern:

First time: Ad hoc (learn)
Second time: Ad hoc (confirm pattern)
Third time: Automate (reusable prompt)
10th time: Optimize (skill/MCP)
```

### Pattern: Context Budget

```
✅ Monitor context usage:

< 5% consumed: No action needed
5-15% consumed: Monitor
15-25% consumed: Consider optimization
> 25% consumed: Use CLI/scripts/skills

Example:
- 1 MCP server (10%): OK
- 3 MCP servers (30%): Migrate to CLI/scripts
```

---

## Summary

The key to agentic engineering is **starting simple and scaling only when complexity is earned through actual need**. Use this examples guide to:

1. **See real patterns** before implementing
2. **Understand tradeoffs** before committing
3. **Avoid over-engineering** by following progressive paths
4. **Learn from mistakes** others have made

Remember: **Prompts are primitives. Master them first.**
