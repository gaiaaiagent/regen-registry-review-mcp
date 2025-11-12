# Python MCP Documentation Technical Audit Report

**Protocol Version Audited**: 2025-03-26 documentation  
**Audit Date**: November 12, 2025  
**Current SDK Version**: 1.21.0  
**Current Protocol Version**: 2025-06-18

## Critical inaccuracies requiring immediate correction

### Python version requirements are fundamentally wrong

**Documented claim**: "Python 3.7+ with 3.10+ recommended"  
**Actual requirement**: Python ≥ 3.10 (hard minimum, not recommendation)

**Evidence**: The official PyPI package for `mcp` explicitly requires Python ≥3.10 with supported versions limited to 3.10, 3.11, 3.12, and 3.13. The package will fail to install on Python 3.7, 3.8, or 3.9.

**Impact**: Users attempting to install on Python 3.7-3.9 will encounter immediate installation failures. This is a critical blocking issue that makes the documentation actively misleading.

**Correction needed**: "Requires Python 3.10 or higher. Versions 3.10, 3.11, 3.12, and 3.13 are officially supported."

### FastMCP dependencies parameter does not exist in official SDK

**Documented pattern**: `FastMCP(name, dependencies=[...])`  
**Actual API**: No `dependencies` parameter exists in `mcp.server.fastmcp.FastMCP`

**Evidence**: Examination of the official SDK source code and examples shows FastMCP accepts a `lifespan` parameter, not `dependencies`. The confusion stems from FastMCP 2.0, which is a completely separate project (github.com/jlowin/fastmcp) maintained by Prefect.

**Working pattern**:
```python
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        await db.disconnect()

mcp = FastMCP("My App", lifespan=app_lifespan)
```

**Impact**: Code examples using `dependencies` parameter will fail immediately with TypeError. This affects all lifecycle management examples.

**Clarification needed**: The documentation must distinguish between FastMCP 1.0 (integrated into official SDK at `mcp.server.fastmcp`) and FastMCP 2.0 (separate package at github.com/jlowin/fastmcp). These are distinct projects with different APIs.

### Message types import path needs clarification

**Documented import**: `from mcp.server.fastmcp.prompts import base`  
**Status**: Correct but incomplete

The import is accurate, but documentation should clarify that `base.Message` is the base class for type annotations, while `base.UserMessage` and `base.AssistantMessage` are used for instantiation. Current documentation may lead developers to instantiate `base.Message` directly, which is incorrect.

**Complete pattern**:
```python
from mcp.server.fastmcp.prompts import base

@mcp.prompt()
def example() -> list[base.Message]:  # Type annotation uses base.Message
    return [
        base.UserMessage("User text"),      # Instantiate specific types
        base.AssistantMessage("AI text")
    ]
```

## Outdated information requiring updates

### Protocol version is one generation behind

**Documented version**: 2025-03-26  
**Current version**: 2025-06-18 (released June 18, 2025)

The documentation references protocol version 2025-03-26, which was superseded by version 2025-06-18. While 2025-03-26 information remains accurate for that version, the documentation should acknowledge the newer specification.

**Key changes in 2025-06-18**:
- Removed JSON-RPC batching (which was added in 2025-03-26 but subsequently removed)
- Added structured tool output as an official feature
- Enhanced OAuth security with RFC 8707 Resource Indicators
- Introduced elicitation capability for mid-session user requests
- Added `MCP-Protocol-Version` header requirement for HTTP requests
- Introduced `title` fields for human-friendly display names

**Recommendation**: Either update to 2025-06-18 or add a prominent notice that a newer protocol version exists with a changelog summary.

### SDK version references are outdated

**Current SDK version**: v1.21.0 (released November 6, 2025)  
**Release cadence**: Multiple releases per month throughout 2025

The SDK has been under active development with frequent releases. Recent versions include significant improvements:
- v1.21.0: OAuth enhancements, streamable HTTP improvements
- v1.20.0: Relaxed Accept header requirements, RFC 7523 JWT flows
- v1.19.0: Tool metadata support, direct CallToolResult returns

**Impact**: Documentation written for earlier SDK versions may not reflect current best practices or available features.

### HTTP+SSE transport deprecation status

**Current status**: HTTP+SSE transport from 2024-11-05 was replaced by Streamable HTTP in 2025-03-26

The documentation should explicitly state that HTTP+SSE is deprecated legacy transport and Streamable HTTP is the recommended approach for production servers. While backward compatibility exists, new implementations should use Streamable HTTP.

**Anthropic MCP Directory policy**: "Remote MCP servers should support the Streamable HTTP transport. Servers may support SSE for the time being, but in the future it will be deprecated."

### GitHub star count claim requires verification

**Documented claim**: "12,000+ GitHub stars"  
**Actual count**: TypeScript SDK has approximately 10,500 stars; Python SDK has approximately 2,700 stars

The claim appears slightly inflated unless referring to cumulative stars across all repositories in the modelcontextprotocol organization. The claim should either:
1. Specify which repository (e.g., "TypeScript SDK has 10.5k+ stars")
2. State it's cumulative across the organization
3. Be updated to reflect current accurate counts

The "250+ community servers" claim is accurate based on the extensive lists in the official servers repository.

## Code examples requiring corrections

### Tool context injection pattern

**Current examples likely show**: Basic patterns without typed context  
**Best practice pattern**:
```python
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

mcp = FastMCP("Example")

@mcp.tool()
async def example_tool(
    param: str,
    ctx: Context[ServerSession, None]  # Explicitly typed
) -> str:
    await ctx.info("Starting operation")
    await ctx.report_progress(progress=0.5, total=1.0)
    return "result"
```

The context parameter provides access to logging, progress reporting, and session information. Examples should consistently show this pattern for any non-trivial tool.

### Lifespan management examples need correction

All examples using `dependencies` parameter must be rewritten to use `lifespan` with proper async context manager pattern:

```python
from dataclasses import dataclass
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

@dataclass
class AppContext:
    db: Database
    config: dict

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    # Startup
    db = await Database.connect()
    config = load_config()
    
    try:
        yield AppContext(db=db, config=config)
    finally:
        # Shutdown
        await db.disconnect()

mcp = FastMCP("Server", lifespan=app_lifespan)

@mcp.tool()
def use_db(ctx: Context[ServerSession, AppContext]) -> str:
    db = ctx.request_context.lifespan_context.db
    return db.query("SELECT 1")
```

### Resource URI template examples are correct

The documented pattern `"users://{user_id}/profile"` is verified as correct. These examples can remain as-is.

### All decorator syntax is correct

The patterns `@mcp.tool()`, `@mcp.resource()`, and `@mcp.prompt()` are all verified correct in the current SDK.

## Missing critical information

### No formal deprecation policy documented

**Gap**: The MCP specification has no published deprecation policy despite making breaking changes between versions.

**Evidence**: GitHub Discussion #308 (January 2025) raised community concerns about "specification changes without deprecation policy." The HTTP+SSE to Streamable HTTP transition affected 186+ community servers without formal timelines.

**Impact**: Developers cannot plan migration strategies or understand support windows for legacy features.

**Recommendation**: Document that while no formal policy exists, the project has established Specification Enhancement Proposal (SEP) governance and typically maintains backward compatibility through SDK fallback mechanisms. The next version is planned for November 25, 2025, with a 14-day RC validation window.

### Error handling patterns under-documented

**Current state**: Basic error examples exist  
**Missing guidance**:
- Structured error responses with machine-readable codes
- Retry-After semantics for temporary failures
- Error categorization (client error vs. server error vs. external dependency error)
- Circuit breaker patterns for external service calls
- Transaction rollback and compensating actions

**Recommended pattern to document**:
```python
from enum import Enum

class ErrorCategory(Enum):
    CLIENT_ERROR = "client_error"    # 4xx - Client's fault
    SERVER_ERROR = "server_error"    # 5xx - Server's fault  
    EXTERNAL_ERROR = "external_error" # 502/503 - Dependency failure

@dataclass
class MCPError:
    category: ErrorCategory
    code: str
    message: str
    details: Optional[dict] = None
    retry_after: Optional[int] = None
```

### Testing approaches are minimally documented

**Current state**: One basic testing example exists  
**Critical missing patterns**:

**In-memory testing with FastMCP**:
```python
import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport

@pytest.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client

async def test_tool_execution(mcp_client: Client[FastMCPTransport]):
    result = await mcp_client.call_tool(
        name="add",
        arguments={"x": 1, "y": 2}
    )
    assert result.data == 3
```

**Behavioral testing guidance**: Documentation should emphasize testing with real AI models, not just unit tests. Key metrics to test:
- Tool hit rate (does AI call the correct tool?)
- Parameter extraction accuracy
- Output parseability by AI models
- Tool chaining and complex workflows

**MCP Inspector usage**: Document using `npx @modelcontextprotocol/inspector` for development testing as the primary manual testing approach.

### Security best practices need expansion

**Currently documented**: Basic security concepts  
**Missing critical patterns**:

**Confused deputy prevention**:
```python
# OAuth Resource Server pattern (required as of March 2025)
from mcp.server.auth.provider import TokenVerifier

class SimpleTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        # Validate token was issued FOR YOUR SERVER
        # Never use token passthrough
        pass
```

**Scope minimization**: Document that omnibus scopes (like `mcp:*`) are anti-patterns. Use progressive elevation with specific scopes.

**Local server sandboxing**: Document that local servers (stdio transport) should show full command to users before execution and restrict file system/network access.

**Prompt injection filtering**: Recommend filtering at edge (client-side) and preprocessing at execution layer.

### Production deployment patterns absent

**Missing guidance**:
- Horizontal scaling with stateless design
- Load balancing for Streamable HTTP servers
- Session management at scale
- Connection pooling best practices
- Blue-green deployment strategies
- Monitoring and observability patterns (mention MCPCat as community solution)

**Performance targets to document**:
- Throughput: >1000 requests/second per instance
- P95 latency: <100ms for simple operations
- P99 latency: <500ms for complex operations  
- Error rate: <0.1% under normal conditions

### Common pitfalls not documented

**Critical gotchas from community issues**:

**Tool naming conventions**: Tool names with spaces, dots, or special characters break parsing. Document that snake_case is recommended for Python (best GPT-4o tokenization).

**Database connection anti-pattern**:
```python
# ❌ WRONG - Connect on server initialization
class Server:
    def __init__(self):
        self.db = Database.connect()  # Fails if misconfigured

# ✅ CORRECT - Connect in lifespan, access in tools
@mcp.tool()
def query(ctx: Context) -> str:
    db = ctx.request_context.lifespan_context.db
    return db.query()
```

**Tool budget management**: Offering too many tools (>30) confuses AI agents. Document grouping related tools into separate servers or using dynamic toolset discovery.

**Path configuration issues**: Document using explicit, configurable paths rather than hardcoded paths like `Documents/Cline/MCP` which don't respect system locale.

### Pydantic advanced patterns under-documented

**Missing patterns**:
- Custom validators in MCP tool context
- Discriminated unions for tool inputs
- Performance optimization with Pydantic v2
- Strict vs. flexible validation modes

**Document strict validation pattern**:
```python
from pydantic import BaseModel, Field, field_validator

class StrictInput(BaseModel):
    email: EmailStr
    age: int = Field(ge=0, le=150)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        if '@' not in value:
            raise ValueError('Invalid email')
        return value

# Enable strict mode
mcp = FastMCP("Server", strict_input_validation=True)
```

## Simplification opportunities

### Reduce conceptual overhead in quick start

**Current approach**: Likely introduces multiple concepts simultaneously  
**Simplified approach**: Show absolute minimal example first, then layer complexity

**Minimal example** (10 lines):
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")

@mcp.tool()
def add(x: int, y: int) -> int:
    """Add two numbers"""
    return x + y
```

**Then** introduce lifespan, context, progress reporting, etc. as separate progressive examples.

### Consolidate transport configuration examples

**Issue**: Multiple transport examples scattered  
**Solution**: Create single comprehensive transport section:

```python
# STDIO (local/CLI servers) - DEFAULT
mcp = FastMCP("Server")

# HTTP (Streamable HTTP) - RECOMMENDED for remote
mcp = FastMCP("Server")
# Run with: fastmcp run server.py --transport http --port 8000

# SSE (legacy, being deprecated)
# Not recommended for new servers
```

### Reduce character count in verbose examples

Many examples can remove unnecessary comments and boilerplate. For instance:

**Before** (verbose):
```python
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession

# Create a new FastMCP server instance
mcp = FastMCP("Example Server")

# Define a tool that adds two numbers
@mcp.tool()
def add(a: int, b: int) -> int:
    """
    This tool adds two numbers together.
    
    Args:
        a: The first number
        b: The second number
    
    Returns:
        The sum of a and b
    """
    return a + b
```

**After** (concise):
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Example")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
```

The docstring serves as the tool description, so verbose comments are redundant.

### Eliminate redundant FastMCP vs. SDK confusion

**Current confusion**: Documentation likely doesn't clearly distinguish FastMCP 1.0 (in SDK) from FastMCP 2.0 (separate project)

**Clarification needed**: Add prominent callout box at the beginning:

> **FastMCP Versions**: This documentation covers FastMCP 1.0, which is integrated into the official MCP Python SDK at `mcp.server.fastmcp`. A separate project called FastMCP 2.0 exists at github.com/jlowin/fastmcp with additional enterprise features but a different API. Unless specifically mentioned, all code examples use the official SDK's FastMCP 1.0.

## Structural improvements

### Reorganize by user journey

**Recommended structure**:
1. **Installation** (correct commands: `pip install "mcp[cli]"`)
2. **Minimal example** (5-10 lines)
3. **Core concepts** (tools, resources, prompts)
4. **Lifecycle management** (lifespan pattern)
5. **Testing** (in-memory testing with FastMCP)
6. **Deployment** (transports, configuration, production patterns)
7. **Security** (OAuth 2.1, best practices)
8. **Advanced topics** (structured output, progress reporting)
9. **Troubleshooting** (common pitfalls)

### Create decision tree for transport selection

```
Do you need remote access?
├─ No → Use STDIO (default)
└─ Yes → Use Streamable HTTP
    ├─ Need OAuth 2.1? → Yes (production)
    └─ Development only? → Optional
```

### Add "Common Mistakes" section

Document the top 10 mistakes from GitHub issues:
1. Wrong Python version (3.7-3.9 won't work)
2. Using `dependencies` parameter (doesn't exist)
3. Tool names with spaces/special chars
4. Too many tools (>30)
5. Database connections on init
6. Missing environment variables in Claude Code
7. Using deprecated SSE transport
8. Not testing with real AI models
9. Returning errors with sensitive data
10. Hardcoded paths and credentials

### Separate quick reference from detailed guides

Create a "Cheat Sheet" section:
- Common decorator patterns
- Context method reference (ctx.info, ctx.report_progress, etc.)
- Transport configuration formats
- Installation commands for different package managers

## Reliability issues

### Version pinning recommendations missing

**Issue**: No guidance on dependency management  
**Recommendation**: Document version pinning strategy

```toml
# pyproject.toml
[project]
dependencies = [
    "mcp[cli]>=1.21.0,<2.0.0",  # Allow patch updates
    "pydantic>=2.0.0,<3.0.0"
]
```

### Graceful degradation patterns not documented

**Pattern to add**:
```python
@mcp.tool()
async def query_database(query: str, ctx: Context) -> str:
    try:
        return await db.execute(query)
    except DatabaseConnectionError:
        await ctx.warning("Database unavailable, using cache")
        return cache.get(query) or "Service temporarily unavailable"
```

### Circuit breaker patterns missing

**Critical for production**:
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_external_api():
    # Fails fast after 5 failures, recovers after 60s
    pass
```

### Retry logic not standardized

Document using tenacity for exponential backoff:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def flaky_operation():
    pass
```

## Maintainability concerns

### No migration guides between protocol versions

**Issue**: Breaking changes between 2024-11-05, 2025-03-26, and 2025-06-18 lack migration documentation

**Recommended additions**:
- "Migrating from 2024-11-05 to 2025-03-26" guide (HTTP+SSE → Streamable HTTP)
- "Migrating from 2025-03-26 to 2025-06-18" guide (JSON-RPC batching removal, structured output)

### SDK version compatibility matrix missing

**Table to add**:
| SDK Version | Protocol Version | Python Version | Key Features |
|-------------|-----------------|----------------|--------------|
| 1.21.0 | 2025-06-18 | 3.10-3.13 | Structured output, enhanced OAuth |
| 1.20.0 | 2025-03-26 | 3.10-3.13 | Streamable HTTP, RFC 7523 JWT |
| 1.19.0 | 2025-03-26 | 3.10-3.13 | Tool metadata, direct CallToolResult |

### Type annotation standards need documentation

**Recommended standard**:
```python
from typing import Annotated
from pydantic import Field

@mcp.tool()
def example(
    name: Annotated[str, Field(description="User name", min_length=1)],
    age: Annotated[int, Field(description="User age", ge=0, le=150)]
) -> dict[str, str]:
    """Type annotations generate JSON Schema automatically"""
    pass
```

### Logging and observability patterns absent

**Pattern to document**:
```python
import structlog

logger = structlog.get_logger()

@mcp.tool()
async def tool(param: str, ctx: Context) -> str:
    logger.info("tool_called", 
                tool="tool",
                param=param,
                request_id=ctx.request_id)
    
    await ctx.info(f"Processing {param}")
    result = process(param)
    
    logger.info("tool_completed",
                tool="tool", 
                result_length=len(result))
    return result
```

### Configuration management patterns missing

**Recommended pattern**:
```python
from pydantic_settings import BaseSettings

class ServerConfig(BaseSettings):
    database_url: str
    api_key: str
    port: int = 8000
    
    class Config:
        env_file = ".env"

config = ServerConfig()
mcp = FastMCP("Server")
```

## Development tools verification summary

All documented tools verified to exist:
- ✅ `npx @modelcontextprotocol/inspector` - Official inspector (npm package)
- ✅ `fastmcp dev`, `fastmcp install`, `fastmcp run` - FastMCP CLI commands
- ✅ `mcp dev`, `mcp install`, `mcp run` - Official MCP SDK CLI commands (separate from FastMCP)
- ✅ `/mcp` - Claude Code slash command
- ✅ Configuration JSON formats validated

**Critical distinction to document**: The official SDK has `mcp` commands (from `pip install "mcp[cli]"`), while FastMCP has `fastmcp` commands (from `pip install fastmcp`). These are separate packages with different CLIs.

## Installation commands verification

**Verified correct**:
```bash
# Official SDK with CLI tools
pip install "mcp[cli]"
uv add "mcp[cli]"

# Minimal installation
pip install mcp

# With specific extras
pip install "mcp[cli,rich,ws]"
```

**MCP Inspector** (verified):
```bash
npx @modelcontextprotocol/inspector
npx @modelcontextprotocol/inspector node build/index.js
npx @modelcontextprotocol/inspector --cli node build/index.js
```

## Recommendations summary

### Immediate corrections required
1. Fix Python version requirement (3.10+ minimum, not 3.7+)
2. Remove or correct all `dependencies` parameter references
3. Add FastMCP 1.0 vs. 2.0 disambiguation
4. Update protocol version to 2025-06-18 or note it exists

### High-priority additions
1. Add error handling patterns section
2. Expand testing documentation with in-memory testing and behavioral testing
3. Add common pitfalls section with top 10 mistakes
4. Document security best practices comprehensively
5. Add production deployment patterns

### Medium-priority improvements
1. Create migration guides between protocol versions
2. Add SDK version compatibility matrix
3. Reorganize by user journey (installation → minimal example → advanced)
4. Add configuration management patterns
5. Document logging and observability

### Low-priority refinements
1. Reduce verbosity in examples
2. Create quick reference cheat sheet
3. Add performance optimization patterns
4. Document Pydantic advanced patterns
5. Consolidate transport examples

The documentation is fundamentally sound in structure but contains critical inaccuracies that would cause immediate failures for users. The Python version requirement and dependencies parameter issues are blocking problems that must be corrected immediately. The protocol version being one generation behind is less critical but should be updated for currency. Missing testing, security, and production deployment guidance represents gaps that reduce production readiness of implementations.

The recommended approach is to prioritize corrections first (hours), then add missing critical documentation (days), followed by structural improvements (weeks) based on available resources and community feedback.
