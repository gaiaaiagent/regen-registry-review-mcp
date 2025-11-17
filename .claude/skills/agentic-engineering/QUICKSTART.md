# Quick Start Guide

Get immediate value from the agentic engineering skill in under 2 minutes.

## The 3 Most Common Questions

### 1. "Should I use a skill, MCP server, sub-agent, or slash command?"

**Answer in 30 seconds:**

```
Ad hoc prompt → First time, exploring
    ↓
Slash command → You've done it 3+ times
    ↓
Sub-agent → Need parallelization + specialization
    ↓
MCP server → External integration or multi-service wrapper
    ↓
Skill → Automatic invocation + bundled resources
    ↓
Full app → Multiple interfaces + long-term product
```

**Quick Decision:**
- **External API?** → MCP server (80% of cases)
- **Building new tool?** → CLI first (works for humans + agents)
- **Repeat workflow?** → Slash command → Skill
- **Parallel tasks?** → Sub-agents
- **Context tight?** → Scripts or Skills instead of MCP

**See:** [EXAMPLES.md](EXAMPLES.md#architecture-decisions) for detailed examples

---

### 2. "How do I build my first MCP server?"

**Answer in 1 minute:**

```bash
# Setup (30 seconds)
uvx create-mcp-server
cd my-server
uv add "mcp[cli]" httpx pydantic

# Minimal server (30 seconds)
```

```python
# src/my_server/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run()
```

**Test:**
```bash
npx @modelcontextprotocol/inspector python src/my_server/server.py
```

**Critical Rules:**
- ✅ All logs to stderr: `print("debug", file=sys.stderr)`
- ✅ Use absolute paths in config
- ✅ Restart Claude after config changes

**See:** [EXAMPLES.md](EXAMPLES.md#mcp-server-development) for complete implementation

---

### 3. "How do I optimize context windows?"

**Answer in 30 seconds:**

**Context Consumption:**
- MCP server: ~10% context per server
- CLI approach: ~5.6% context
- Scripts approach: ~2% context
- Skills approach: ~1% context

**When to Optimize:**

| Context Used | Action |
|--------------|--------|
| < 15% | No action needed |
| 15-25% | Monitor, consider optimization |
| > 25% | Migrate to CLI/scripts/skills |

**Quick Wins:**

1. **Reduce MCP servers** - Combine related functionality
2. **Use progressive disclosure** - CLI + prime prompts
3. **Use scripts** - Single-file, load on-demand
4. **Use skills** - Auto progressive disclosure

**See:** [EXAMPLES.md](EXAMPLES.md#context-optimization) for detailed alternatives

---

## Core Principles (Remember These)

### 1. Start Simple, Scale When Needed
Don't build a multi-agent MCP wrapper skill when a slash command works. Let complexity be earned.

### 2. Prompts Are Primitives
Everything comes down to: Context + Model + Prompt + Tools. Master prompts first.

### 3. Three Times Rule
Do it once → Ad hoc
Do it twice → Confirm pattern
Do it three times → Automate (slash command)
Do it 10+ times → Optimize (skill/MCP)

### 4. Progressive Disclosure
Load only what you need, when you need it. Protect context windows.

### 5. Delete Agents When Done
Agents are temporary resources. Create → Use → Delete. Don't hoard agents.

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Over-Engineering
```
Bad: Build complex MCP wrapper with skill for a one-time task
Good: Use ad hoc prompt first, then decide
```

### ❌ Mistake 2: stdout Contamination
```python
# BAD - Breaks MCP protocol
print("Debug info")

# GOOD - Logs to stderr
import sys
print("Debug info", file=sys.stderr)
```

### ❌ Mistake 3: Relative Paths
```json
// BAD
{"command": "python", "args": ["./server.py"]}

// GOOD
{"command": "python", "args": ["/absolute/path/server.py"]}
```

### ❌ Mistake 4: Not Deleting Agents
```
Bad: Keep 5 agents running after work is done
Good: Delete agents immediately when task completes
```

### ❌ Mistake 5: Skipping the CLI
```
Bad: Build MCP server for new internal tool
Good: Build CLI first (works for humans + agents), wrap MCP if needed
```

---

## Decision Trees

### Quick Tree 1: Pattern Selection

```
Need to do task → Ad hoc prompt
    ↓
Done 3+ times? → Slash command
    ↓
Need parallelization? → Sub-agents
    ↓
External integration? → MCP server
    ↓
Auto-invocation? → Skill
```

### Quick Tree 2: MCP vs Alternatives

```
External 3rd party API? → MCP server (80%)
    ↓
Building new tool? → CLI (80%)
    ↓
Context constrained? → Scripts/Skills
    ↓
Auto-invocation? → Skill
```

---

## What to Ask the Skill

The skill automatically triggers on questions like:

**Architecture:**
- "Should I use X or Y?"
- "What's the right pattern for my use case?"
- "When do I need sub-agents?"

**Implementation:**
- "How do I build an MCP server?"
- "Show me how to implement multi-agent orchestration"
- "How do I set up progressive disclosure?"

**Optimization:**
- "How do I reduce context usage?"
- "My MCP server is using too much context"
- "How do I scale my agents?"

**Best Practices:**
- "What are common MCP pitfalls?"
- "How should I structure my agent system?"
- "What's the best way to manage agent lifecycle?"

---

## Next Steps

1. **Try it** - Ask the skill a question about your use case
2. **Read examples** - See [EXAMPLES.md](EXAMPLES.md) for real-world patterns
3. **Check docs** - Browse [DOCS_INDEX.md](DOCS_INDEX.md) for deeper topics
4. **Read full guide** - See [README.md](README.md) for comprehensive docs

---

## Emergency Reference

**MCP Server Won't Start?**
1. Check logs: `~/Library/Logs/Claude/mcp*.log`
2. Verify absolute paths in config
3. Check stderr for errors (not stdout!)
4. Test with Inspector first

**Context Window Exploding?**
1. Count MCP servers (3+ servers = problem)
2. Migrate to CLI/scripts approach
3. Use progressive disclosure patterns

**Agent Not Performing Well?**
1. Check context window usage
2. Is agent too generalized? (Make it focused)
3. Too much context? (Reduce scope)
4. Delete and recreate with cleaner context

---

**Time to Value: 2 minutes**
**Most Useful Section: The 3 Most Common Questions**
**When Stuck: Ask the skill directly - it has access to all documentation**
