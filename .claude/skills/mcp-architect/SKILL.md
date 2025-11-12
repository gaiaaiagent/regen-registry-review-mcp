---
name: mcp-architect
description: Expert guidance for building, designing, testing, and deploying production-ready Python MCP servers. Use when building MCP servers, implementing tools/resources/prompts, configuring UV, troubleshooting MCP issues, optimizing performance, or deciding between MCP and alternatives (CLI/scripts/skills). Covers FastMCP patterns, testing strategies, deployment, and best practices.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
---

# MCP Architect

Expert system for designing and building production-ready Model Context Protocol (MCP) servers in Python.

## Core Expertise

This skill provides comprehensive guidance on:

- **MCP Architecture**: Understanding tools, resources, prompts, and sampling primitives
- **FastMCP Development**: Modern Python patterns with the official SDK
- **UV Package Management**: Fast, reliable dependency management for MCP projects
- **Testing Strategies**: Unit tests, integration tests, and behavioral testing
- **Production Deployment**: Docker, CI/CD, and scaling patterns
- **Performance Optimization**: Context efficiency, caching, connection pooling
- **Security Best Practices**: Input validation, error masking, authentication
- **Alternative Approaches**: When to use CLI, scripts, or skills instead of MCP

## Instructions

### 1. Assess Requirements

When user asks about MCP, first determine the task:

**For new MCP servers:**
1. Read `templates/minimal-server.py` for simple use cases
2. Read `templates/advanced-server.py` for complex scenarios with lifecycle management
3. Read `templates/pyproject.toml` for UV configuration
4. Ask: What external system/data source will this integrate with?
5. Ask: What operations (tools), data (resources), or templates (prompts) are needed?

**For existing MCP servers:**
1. Use Grep to find MCP server files: `@mcp.tool\|@mcp.resource\|@mcp.prompt\|FastMCP`
2. Read the main server file to understand current architecture
3. Identify the specific issue (performance, errors, testing, deployment)

**For architecture decisions:**
1. Read `checklists/mcp-vs-alternatives.md` to evaluate if MCP is the right choice
2. Consider context window impact, complexity, and control requirements

### 2. Development Workflow

**Project Setup:**
```bash
# Initialize with UV (recommended)
uv init mcp-{name}-server --package
cd mcp-{name}-server
uv add "mcp[cli]>=1.0.0"
uv add httpx pydantic  # Add domain-specific deps
uv add --dev pytest pytest-asyncio ruff mypy
```

**Implementation Pattern:**
1. Start with minimal server template
2. Add tools for executable functions (user approval required)
3. Add resources for data/context (read-only access)
4. Add prompts for reusable conversation templates (user-initiated)
5. Implement lifespan management for database/connection pooling
6. Add proper error handling and logging (to stderr, not stdout)
7. Add type hints and Pydantic validation

**Key Rules:**
- All logs MUST go to stderr (`logging.basicConfig(stream=sys.stderr)`)
- Never write debug output to stdout (breaks JSON-RPC protocol)
- Use absolute paths in configurations
- Python 3.10+ required (not 3.7-3.9)
- FastMCP uses `lifespan` parameter, NOT `dependencies` parameter

### 3. Testing Strategy

**Unit Testing:**
```python
import pytest
from fastmcp import Client

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
# Use MCP Inspector (primary testing tool)
npx @modelcontextprotocol/inspector python server.py

# Or use MCP CLI
mcp dev server.py
```

**Behavioral Testing:**
- Test with real AI models, not just unit tests
- Verify tool hit rate (does AI call correct tool?)
- Check parameter extraction accuracy
- Test tool chaining and complex workflows

### 4. Production Deployment

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/project",
        "run",
        "server-name"
      ],
      "env": {
        "API_KEY": "value",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

**Docker Deployment:**
1. Read `templates/Dockerfile` for multi-stage build pattern
2. Use official UV base images: `ghcr.io/astral-sh/uv:python3.11-alpine`
3. Set environment variables: `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`
4. Use `--frozen` flag in production to enforce lockfile

**Critical Deployment Checklist:**
- Commit `uv.lock` to version control
- Use absolute paths in all configurations
- All environment variable values must be strings (not numbers/booleans)
- Test with `--frozen` flag locally before deploying
- Configure health check endpoints
- Implement graceful shutdown handling

### 5. Common Pitfalls and Solutions

**stdout Contamination (Most Common):**
```python
# ❌ WRONG - Breaks protocol
print("Debug info")

# ✅ CORRECT
import sys
print("Debug info", file=sys.stderr)
logging.basicConfig(stream=sys.stderr)
```

**Wrong Python Version:**
- Requirement: Python 3.10+ (not 3.7-3.9)
- Specify in pyproject.toml: `requires-python = ">=3.10"`

**Relative Paths:**
```json
// ❌ WRONG
{"command": "python", "args": ["./server.py"]}

// ✅ CORRECT
{"command": "python", "args": ["/absolute/path/server.py"]}
```

**Missing Lifespan:**
```python
# ❌ WRONG - No dependencies parameter exists
mcp = FastMCP("Server", dependencies=["db"])

# ✅ CORRECT - Use lifespan context manager
@asynccontextmanager
async def app_lifespan(server: FastMCP):
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        await db.disconnect()

mcp = FastMCP("Server", lifespan=app_lifespan)
```

### 6. Performance Optimization

**Context Window Efficiency:**
- MCP servers consume 5-10% of context on initialization
- For 3+ MCP servers, consider alternatives (CLI, scripts, skills)
- Read `checklists/mcp-vs-alternatives.md` for decision matrix

**Progressive Disclosure:**
- Use prompts to compose tools (tools are individual, prompts are workflows)
- Implement resource subscriptions for dynamic data
- Limit tool count to 10-15 per server

**Caching and Connection Pooling:**
```python
# Connection pool for databases
engine = create_async_engine("postgresql://...", pool_size=20)

# TTL cache for API responses
cache = {}
CACHE_TTL = timedelta(minutes=5)
```

### 7. Architecture Decisions

**When to use MCP (vs CLI/scripts/skills):**

Use MCP when:
- Integrating with external tools/data sources
- Need standard, shareable interface
- Want automatic tool discovery
- Simplicity more important than context efficiency

Use CLI/scripts instead when:
- Building internal tools you control
- Context window preservation critical
- Need progressive disclosure (lazy loading)
- Want portability across agent systems

Use skills instead when:
- Claude Code specific
- Need agent-triggered automation
- Combining multiple capabilities
- Want modular file system pattern

**Decision Matrix:**
1. Read `checklists/mcp-vs-alternatives.md` for comprehensive comparison
2. Consider: Who owns it? External → MCP. Internal → CLI/scripts first
3. Consider: Context usage? <10% → OK. >20% → Alternatives
4. Consider: Lock-in? Universal → MCP/CLI. Claude-specific → Skills OK

### 8. Security Best Practices

**Input Validation:**
```python
from pydantic import BaseModel, Field, validator

class SafeInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)

    @validator('query')
    def validate_query(cls, v):
        forbidden = ['DROP', 'DELETE', 'INSERT', '--']
        if any(word in v.upper() for word in forbidden):
            raise ValueError("Query contains forbidden keywords")
        return v
```

**Error Masking:**
```python
mcp = FastMCP("Server", mask_error_details=True)
```

**Environment-Based Secrets:**
- Never hardcode API keys or credentials
- Use environment variables (as strings)
- Document required environment variables

### 9. Reporting Results

After completing MCP tasks, provide:

1. **Summary**: What was accomplished
2. **Files Created/Modified**: List with line numbers for key sections
3. **Next Steps**: Testing commands, configuration needed, deployment steps
4. **Gotchas**: Potential issues to watch for (context usage, dependencies, etc.)

## Examples

### Example 1: Build New Weather MCP Server

User: "Build an MCP server for weather data"

Response:
1. Read `templates/minimal-server.py`
2. Initialize project: `uv init mcp-weather-server --package`
3. Add dependencies: `uv add "mcp[cli]" httpx`
4. Implement weather tool with async/await
5. Add resource for server status
6. Test with Inspector: `npx @modelcontextprotocol/inspector python server.py`
7. Provide Claude Desktop configuration

### Example 2: Debug Existing MCP Server

User: "My MCP server isn't working in Claude Desktop"

Response:
1. Use Grep to find MCP server: `@mcp.tool\|FastMCP`
2. Read server file to analyze
3. Check common issues:
   - stdout contamination?
   - Relative paths in config?
   - Environment variables as strings?
   - Python version >=3.10?
4. Review configuration file for absolute paths
5. Test with Inspector to isolate issue
6. Provide fix with explanation

### Example 3: Optimize Context Usage

User: "My MCP servers are using too much context"

Response:
1. Read `checklists/mcp-vs-alternatives.md`
2. Count current MCP servers and estimate context usage
3. Evaluate alternatives:
   - Keep external MCP servers (80% case)
   - Convert internal tools to CLI (15% case)
   - Use scripts/skills for progressive disclosure (5% case)
4. Show concrete implementation for chosen approach
5. Measure context savings

## Resources

**Quick Start:**
- `QUICKSTART.md` - Get your first MCP server running in 5 minutes

**Templates:**
- `templates/minimal-server.py` - Basic MCP server structure
- `templates/advanced-server.py` - Production server with lifecycle
- `templates/pyproject.toml` - UV configuration
- `templates/Dockerfile` - Docker deployment
- `templates/test-template.py` - Testing patterns

**Checklists:**
- `checklists/mcp-vs-alternatives.md` - Decision matrix for MCP vs CLI/scripts/skills
- `checklists/deployment.md` - Production deployment checklist
- `checklists/common-errors.md` - Troubleshooting guide
- `checklists/uv-cheatsheet.md` - Complete UV commands reference

**Examples:**
- `examples/readonly-api.py` - Simple API integration with caching
- `examples/database-server.py` - Database with connection pooling and security
- `examples/cli-alternative.py` - CLI approach for comparison with MCP
- `examples/validate-templates.py` - Validation script for templates

## Key Principles

1. **Prompts are primitives** - MCP prompts compose tools for workflows
2. **Stderr for logs** - Never pollute stdout with debug output
3. **Absolute paths** - Always in configurations
4. **UV for management** - Fast, reliable, production-ready
5. **Test with Inspector** - Primary manual testing tool
6. **Progressive disclosure** - Prompts > Tools for common workflows
7. **Context awareness** - Monitor token usage, use alternatives when needed
8. **Security first** - Validate inputs, mask errors, use environment variables

## Latest Updates

- Protocol version: 2025-06-18 (latest)
- SDK version: 1.21.0+ recommended
- Python requirement: 3.10+ minimum
- FastMCP integrated into official SDK at `mcp.server.fastmcp`
- UV 0.9.x production-ready for MCP development
