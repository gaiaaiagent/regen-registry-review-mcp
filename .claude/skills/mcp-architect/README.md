# MCP Architect Skill

Expert system for designing, building, testing, and deploying production-ready Python MCP servers.

## Overview

This skill consolidates comprehensive MCP (Model Context Protocol) expertise covering:

- **MCP Architecture**: Understanding the three core primitives (tools, resources, prompts)
- **FastMCP Development**: Modern Python patterns with the official SDK
- **UV Package Management**: Fast, reliable dependency management
- **Testing Strategies**: Unit, integration, and behavioral testing
- **Production Deployment**: Docker, CI/CD, and scaling patterns
- **Performance Optimization**: Context efficiency, caching, connection pooling
- **Security Best Practices**: Input validation, error masking, authentication
- **Architecture Decisions**: When to use MCP vs CLI vs scripts vs skills

## When to Use This Skill

The skill automatically activates when you:

- Build new MCP servers
- Design MCP architecture
- Implement tools, resources, or prompts
- Configure UV for MCP projects
- Troubleshoot MCP issues
- Optimize MCP performance
- Test or deploy MCP servers
- Decide between MCP and alternatives

## Key Features

### Comprehensive Templates

**Server Templates:**
- `templates/minimal-server.py` - Basic MCP server with essential patterns
- `templates/advanced-server.py` - Production-ready with lifecycle management
- `templates/pyproject.toml` - Complete UV configuration
- `templates/Dockerfile` - Multi-stage Docker deployment
- `templates/test-template.py` - Testing patterns and examples

### Decision Support

**Checklists:**
- `checklists/mcp-vs-alternatives.md` - Comprehensive decision matrix for choosing between MCP, CLI, scripts, and skills
- `checklists/deployment.md` - Production deployment checklist
- `checklists/common-errors.md` - Troubleshooting guide with solutions

### Working Examples

**Examples:**
- `examples/readonly-api.py` - Read-only API integration with caching
- More examples available in the skill directory

## Quick Start

### Creating a New MCP Server

```python
# The skill will guide you through:
1. Project initialization with UV
2. Dependency setup
3. Server implementation
4. Testing with MCP Inspector
5. Claude Desktop configuration
6. Production deployment

# Just ask:
"Build an MCP server for [your use case]"
```

### Troubleshooting Existing Server

```python
# The skill will:
1. Find your MCP server files
2. Analyze the code
3. Identify common issues
4. Provide fixes with explanations

# Just ask:
"Debug my MCP server - it's not connecting"
```

### Architecture Decisions

```python
# The skill will:
1. Assess your requirements
2. Evaluate tradeoffs
3. Recommend approach (MCP vs alternatives)
4. Provide implementation guidance

# Just ask:
"Should I use MCP or CLI for my internal tool?"
```

## Core Expertise Areas

### 1. MCP Primitives

**Tools (Model-Controlled Execution):**
- Executable functions AI can call
- Require user approval
- Examples: database queries, API calls, calculations

**Resources (Application-Controlled Data):**
- Structured data/content for context
- Client explicitly fetches
- Examples: config files, documentation, logs

**Prompts (User-Initiated Templates):**
- Pre-defined conversation templates
- Compose multiple tools into workflows
- Examples: code review, report generation

### 2. Modern Python Development

**UV Package Manager:**
- 10-100x faster than pip
- Automatic virtual environment management
- Universal lockfiles for reproducible builds
- Python version management built-in

**FastMCP Framework:**
- Official MCP Python SDK
- Simple decorator-based API
- Built-in lifecycle management
- Type-safe context access

### 3. Testing Strategies

**Unit Testing:**
```python
@pytest.fixture
async def mcp_client():
    async with Client(mcp) as client:
        yield client

@pytest.mark.asyncio
async def test_tool(mcp_client):
    result = await mcp_client.call_tool("tool_name", {"param": "value"})
    assert result.data == expected
```

**Manual Testing:**
```bash
# MCP Inspector (primary tool)
npx @modelcontextprotocol/inspector python server.py

# MCP CLI
mcp dev server.py
```

### 4. Production Deployment

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": ["--directory", "/absolute/path", "run", "server-name"],
      "env": {"API_KEY": "value"}
    }
  }
}
```

**Docker Deployment:**
- Multi-stage builds for minimal images
- Official UV base images
- Non-root user for security
- Health checks and monitoring

### 5. Performance Optimization

**Context Window Management:**
- MCP servers consume 5-10% context each
- For 3+ servers, consider alternatives
- Use prompts to compose tools (workflows > individual actions)

**Caching and Connection Pooling:**
- HTTP client reuse in lifespan context
- Database connection pools
- TTL-based caching for API responses

### 6. Security Best Practices

**Input Validation:**
- Pydantic models for type safety
- Validators for business logic
- SQL injection prevention
- Path traversal protection

**Error Handling:**
- Mask internal errors: `mask_error_details=True`
- Log to stderr only (never stdout)
- Structured error messages for agents

## Architecture Decision Framework

### Decision Tree

```
External Tool? → Yes → MCP (80%)
              → No  → Consider:
                      - Context critical? → Scripts/Skills (5%)
                      - Agent-triggered? → Skills (varies)
                      - Default → CLI (80%)
```

### Comparison Matrix

| Criterion | MCP | CLI | Scripts | Skills |
|-----------|-----|-----|---------|--------|
| External tools | ✅ Best | ❌ | ❌ | ❌ |
| Internal tools | ⚠️ OK | ✅ Best | ⚠️ Rare | ⚠️ Claude only |
| Context usage | ❌ High | ✅ Low | ✅ Very Low | ✅ Very Low |
| Portability | ⚠️ MCP ecosystem | ✅ Universal | ✅ Universal | ❌ Claude only |
| Agent-triggered | ✅ Yes | ❌ Manual | ❌ Manual | ✅ Yes |
| Setup complexity | ✅ Low | ⚠️ Medium | ⚠️ Medium | ⚠️ Medium |

### Recommendations

**For External Tools (80% MCP):**
- GitHub, Slack, PostgreSQL, etc.
- Use existing MCP servers
- Don't reinvent the wheel

**For Internal Tools (80% CLI):**
- Build CLI first
- Works for you + team + agents
- Portable across agent systems
- Can wrap with MCP later if needed

**For Context-Critical (5% Scripts/Skills):**
- Only when using 3+ MCP servers
- Progressive disclosure needed
- Extreme context preservation required

## Common Patterns

### Pattern 1: Read-Only API Integration

```python
from mcp.server.fastmcp import FastMCP, Context
import httpx

@asynccontextmanager
async def app_lifespan(server):
    client = httpx.AsyncClient()
    try:
        yield {"client": client}
    finally:
        await client.aclose()

mcp = FastMCP("api-server", lifespan=app_lifespan)

@mcp.tool()
async def fetch_data(url: str, ctx: Context) -> dict:
    client = ctx.request_context.lifespan_context["client"]
    response = await client.get(url)
    return response.json()
```

### Pattern 2: Database Operations

```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("postgresql://...", pool_size=20)

@mcp.tool()
async def query(sql: str) -> list:
    async with engine.begin() as conn:
        result = await conn.execute(sql)
        return result.mappings().all()
```

### Pattern 3: Workflow Composition with Prompts

```python
@mcp.tool()
def individual_operation(param: str) -> str:
    """Individual action."""
    return process(param)

@mcp.prompt()
def workflow(goal: str) -> str:
    """Compose operations into workflow.

    Use individual_operation multiple times to achieve goal.
    """
    return f"Achieve {goal} by: 1. ... 2. ... 3. ..."
```

## Critical Rules

### 1. stdout vs stderr

```python
# ❌ WRONG - Breaks JSON-RPC protocol
print("Debug info")

# ✅ CORRECT
import sys
print("Debug info", file=sys.stderr)
logging.basicConfig(stream=sys.stderr)
```

### 2. Absolute Paths

```json
// ❌ WRONG
{"command": "python", "args": ["./server.py"]}

// ✅ CORRECT
{"command": "python", "args": ["/absolute/path/server.py"]}
```

### 3. Python Version

- **Required:** Python 3.10 or higher
- **Not supported:** Python 3.7, 3.8, 3.9

### 4. Lifespan (not dependencies)

```python
# ❌ WRONG - No dependencies parameter
mcp = FastMCP("Server", dependencies=["db"])

# ✅ CORRECT - Use lifespan
mcp = FastMCP("Server", lifespan=app_lifespan)
```

### 5. Environment Variables as Strings

```json
// ❌ WRONG
{"env": {"PORT": 8000, "DEBUG": true}}

// ✅ CORRECT
{"env": {"PORT": "8000", "DEBUG": "true"}}
```

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Server not connecting | Use absolute paths in config |
| Invalid JSON error | Check stdout is clean (no print statements) |
| Module not found | Run `uv sync` |
| Wrong Python version | Use Python 3.10+, check `.python-version` |
| Tool not called | Improve tool description |
| High context usage | Reduce tools, use prompts, consider CLI |
| Slow responses | Connection pooling, caching, async operations |

See `checklists/common-errors.md` for comprehensive troubleshooting.

## Development Workflow

### 1. Initialize Project

```bash
uv init mcp-{name}-server --package
cd mcp-{name}-server
uv add "mcp[cli]" httpx pydantic
uv add --dev pytest pytest-asyncio ruff mypy
```

### 2. Implement Server

- Start with `templates/minimal-server.py`
- Add tools, resources, prompts
- Implement lifespan if needed
- Add error handling and logging

### 3. Test Locally

```bash
# Unit tests
uv run pytest

# Manual testing with Inspector
npx @modelcontextprotocol/inspector python server.py

# Or with MCP CLI
mcp dev server.py
```

### 4. Configure Claude Desktop

- Edit `claude_desktop_config.json`
- Use absolute paths
- Set environment variables
- Restart Claude Desktop

### 5. Deploy to Production

- Commit `uv.lock` to version control
- Use `--frozen` flag
- Deploy with Docker or serverless
- Set up monitoring and logging

## Resources

**Official Documentation:**
- MCP: https://modelcontextprotocol.io/
- UV: https://docs.astral.sh/uv/
- FastMCP: https://pypi.org/project/mcp/

**Community:**
- MCP Discord: https://discord.com/invite/model-context-protocol-1312302100125843476
- GitHub: https://github.com/modelcontextprotocol/python-sdk

**This Skill:**
- `SKILL.md` - Main skill instructions
- `templates/` - Code templates
- `checklists/` - Decision guides
- `examples/` - Working examples

## Examples Usage

### Example 1: New Weather Server

**User:** "Build an MCP server for weather data"

**Skill provides:**
1. Project initialization commands
2. Server implementation with templates
3. Testing instructions
4. Claude Desktop configuration
5. Deployment guidance

### Example 2: Troubleshooting

**User:** "My MCP server isn't working"

**Skill provides:**
1. Diagnostic steps
2. Common issue identification
3. Fixes with explanations
4. Testing verification

### Example 3: Architecture Decision

**User:** "Should I use MCP or CLI for my tool?"

**Skill provides:**
1. Ownership assessment (external vs internal)
2. Context budget evaluation
3. Tradeoff analysis
4. Recommendation with rationale
5. Implementation guidance

## Key Principles

1. **Prompts are primitives** - Start with clear prompts, escalate to tools
2. **Stderr for logs** - Never pollute stdout
3. **Absolute paths** - Always in configurations
4. **UV for management** - Fast, reliable, production-ready
5. **Test with Inspector** - Primary manual testing tool
6. **Context awareness** - Monitor usage, use alternatives when needed
7. **Security first** - Validate inputs, mask errors
8. **Progressive disclosure** - Prompts compose tools into workflows

## Latest Updates

- **Protocol:** 2025-06-18 (latest spec)
- **SDK:** 1.21.0+ recommended
- **Python:** 3.10+ minimum required
- **UV:** 0.9.x production-ready
- **FastMCP:** Integrated into official SDK

## Contributing

This skill is designed to evolve with:
- New MCP protocol versions
- Python SDK updates
- Community best practices
- Real-world deployment patterns

Keep templates and checklists current with latest recommendations.

---

**Note:** This skill consolidates expertise from official MCP documentation, UV documentation, community best practices, and production deployment experience. Use it as your comprehensive guide for all MCP development needs.
