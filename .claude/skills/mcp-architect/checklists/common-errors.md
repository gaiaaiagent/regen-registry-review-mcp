# Common MCP Errors: Troubleshooting Guide

Quick reference for diagnosing and fixing the most common MCP server issues.

## Error Categories

1. [Connection Errors](#connection-errors)
2. [Protocol Errors](#protocol-errors)
3. [Configuration Errors](#configuration-errors)
4. [Runtime Errors](#runtime-errors)
5. [Performance Issues](#performance-issues)

---

## Connection Errors

### Error: Server Not Found / Connection Refused

**Symptoms:**
- Claude Desktop shows "Server failed to start"
- No hammer icon appears
- Logs show "connection refused" or "ENOENT"

**Causes & Solutions:**

#### 1. Relative Path in Configuration
```json
// ❌ WRONG
{"command": "python", "args": ["./server.py"]}

// ✅ CORRECT
{"command": "python", "args": ["/absolute/path/to/server.py"]}
```

#### 2. Command Not in PATH
```json
// ❌ If 'uv' not in PATH
{"command": "uv"}

// ✅ Use full path
{"command": "/usr/local/bin/uv"}

// ✅ Or ensure in PATH
export PATH="$HOME/.local/bin:$PATH"
```

#### 3. Wrong Working Directory
```json
// ❌ Missing directory flag
{
  "command": "uv",
  "args": ["run", "server.py"]
}

// ✅ Specify directory
{
  "command": "uv",
  "args": ["--directory", "/absolute/path", "run", "server.py"]
}
```

**Debugging Steps:**
```bash
# Test command manually
/absolute/path/to/command /absolute/path/to/server.py

# Check if command exists
which uv
which python

# Verify file exists
ls -la /absolute/path/to/server.py

# Check permissions
ls -l /absolute/path/to/server.py
chmod +x /absolute/path/to/server.py  # If needed
```

---

## Protocol Errors

### Error: Invalid JSON / Protocol Error

**Symptoms:**
- "Invalid JSON-RPC message"
- "Protocol version mismatch"
- Server starts but tools don't work
- Claude Desktop shows communication error

**Cause 1: stdout Contamination (MOST COMMON)**

```python
# ❌ WRONG - Breaks JSON-RPC protocol
print("Debug info")
print("Starting server")
console.log("Info")

# ✅ CORRECT - Use stderr
import sys
print("Debug info", file=sys.stderr)

# ✅ CORRECT - Configure logging
import logging
logging.basicConfig(stream=sys.stderr)
logger = logging.getLogger(__name__)
logger.info("Debug info")
```

**Rule:** ONLY JSON-RPC messages go to stdout. ALL debug output goes to stderr.

**Debugging:**
```bash
# Check what's being written to stdout
python server.py | head -20

# Should only see JSON-RPC messages like:
# {"jsonrpc":"2.0","method":"initialize",...}

# NOT human-readable text like:
# "Starting server..."
# "Debug: Loading config"
```

**Cause 2: Protocol Version Mismatch**

```python
# Check SDK version
pip show mcp

# Update if needed
uv add --upgrade "mcp>=1.0.0"
```

---

## Configuration Errors

### Error: Environment Variables Not Working

**Problem:** Environment variables not recognized

```json
// ❌ WRONG - Numbers/booleans as values
{
  "env": {
    "PORT": 8000,
    "DEBUG": true,
    "API_KEY": "value"
  }
}

// ✅ CORRECT - All values as strings
{
  "env": {
    "PORT": "8000",
    "DEBUG": "true",
    "API_KEY": "value"
  }
}
```

**Access in Python:**
```python
import os

# Convert string to appropriate type
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
API_KEY = os.getenv("API_KEY")

# Validate required variables
if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

### Error: Module Not Found

**Symptoms:**
```
ModuleNotFoundError: No module named 'mcp'
ModuleNotFoundError: No module named 'httpx'
```

**Solutions:**

```bash
# Verify dependencies installed
uv sync

# Check installation
uv run python -c "import mcp; print(mcp.__version__)"

# Reinstall if needed
uv add "mcp[cli]"

# Use correct command in config
{
  "command": "uv",
  "args": ["--directory", "/path", "run", "server.py"]
}
```

### Error: Wrong Python Version

**Symptoms:**
```
python: Python 3.9 is not supported (requires >=3.10)
SyntaxError: invalid syntax (match/case statements)
```

**Solution:**
```bash
# Check Python version
python --version

# MCP requires Python 3.10+
uv python install 3.11

# Create .python-version
echo "3.11" > .python-version

# Update pyproject.toml
requires-python = ">=3.10"

# Specify in config
{
  "command": "uv",
  "args": ["run", "--python", "3.11", "server.py"]
}
```

---

## Runtime Errors

### Error: TypeError: FastMCP() got unexpected keyword 'dependencies'

**Problem:** Using wrong parameter name

```python
# ❌ WRONG - No 'dependencies' parameter
mcp = FastMCP("Server", dependencies=["db", "cache"])

# ✅ CORRECT - Use 'lifespan' with context manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    db = await Database.connect()
    cache = {}
    try:
        yield AppContext(db=db, cache=cache)
    finally:
        await db.disconnect()

mcp = FastMCP("Server", lifespan=app_lifespan)
```

**Note:** The `dependencies` parameter exists in FastMCP 2.0 (separate project), not in the official SDK's FastMCP at `mcp.server.fastmcp`.

### Error: Tool Not Being Called

**Symptoms:**
- Agent doesn't use your tool
- Agent says "I don't have a tool for that"

**Debugging:**

1. **Check tool is registered:**
```bash
npx @modelcontextprotocol/inspector python server.py
# Click "Tools" tab - your tool should appear
```

2. **Improve tool description:**
```python
# ❌ POOR - Vague description
@mcp.tool()
def process(data: str) -> str:
    """Processes data."""
    pass

# ✅ GOOD - Clear, actionable description
@mcp.tool()
def process_customer_data(data: str) -> str:
    """Process customer data to extract email, phone, and address.

    Use this when you need to parse customer information from
    unstructured text. Handles common formats and validates output.
    """
    pass
```

3. **Check parameter types:**
```python
# ❌ WRONG - Missing type hints
@mcp.tool()
def add(a, b):  # No types!
    return a + b

# ✅ CORRECT - Clear types
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
```

4. **Verify tool isn't failing silently:**
```python
# Add logging
@mcp.tool()
async def my_tool(param: str, ctx: Context) -> str:
    await ctx.info(f"Tool called with: {param}")
    try:
        result = process(param)
        await ctx.info("Tool succeeded")
        return result
    except Exception as e:
        await ctx.error(f"Tool failed: {e}")
        raise
```

### Error: Context Access Fails

**Problem:** Can't access lifespan context

```python
# ❌ WRONG - Context not typed
@mcp.tool()
async def query(sql: str, ctx: Context) -> dict:
    db = ctx.request_context.lifespan_context.db  # Error!

# ✅ CORRECT - Properly typed context
from mcp.server.session import ServerSession

@dataclass
class AppContext:
    db: Database

@mcp.tool()
async def query(
    sql: str,
    ctx: Context[ServerSession, AppContext]  # Type the context!
) -> dict:
    db = ctx.request_context.lifespan_context.db  # Works!
    return await db.query(sql)
```

### Error: Timeout / Long Running Operations

**Problem:** Operation takes too long, no feedback

```python
# ❌ WRONG - No timeout or progress
@mcp.tool()
async def long_operation(items: list) -> dict:
    for item in items:
        process(item)  # Takes long time
    return {"done": True}

# ✅ CORRECT - Timeout and progress
import asyncio

@mcp.tool()
async def long_operation(items: list, ctx: Context) -> dict:
    """Long operation with timeout and progress."""
    try:
        async with asyncio.timeout(30):  # 30 second timeout
            total = len(items)
            for i, item in enumerate(items):
                await ctx.report_progress(
                    progress=(i + 1) / total,
                    total=1.0,
                    message=f"Processing {i+1}/{total}"
                )
                await process(item)
        return {"done": True}
    except asyncio.TimeoutError:
        raise ToolError("Operation timed out after 30 seconds")
```

---

## Performance Issues

### Issue: High Context Window Usage

**Symptoms:**
- Multiple MCP servers consuming >20% of context
- Agent performance degraded
- Token limits hit quickly

**Solutions:**

1. **Reduce tool count:**
```python
# ❌ TOO MANY - 30+ tools
@mcp.tool()
def tool1(): pass
@mcp.tool()
def tool2(): pass
# ... 30 more ...

# ✅ BETTER - Group related tools, use prompts
@mcp.tool()
def database_operation(operation: str, table: str) -> dict:
    """Unified database tool supporting: query, insert, update, delete."""
    if operation == "query":
        return query_table(table)
    elif operation == "insert":
        return insert_record(table)
    # etc.

@mcp.prompt()
def database_workflow(task: str) -> str:
    """Compose database operations for common workflows."""
    # Guide agent through multi-step process
    pass
```

2. **Optimize descriptions:**
```python
# ❌ TOO VERBOSE
@mcp.tool()
def calculate_sum(a: int, b: int) -> int:
    """This tool performs addition of two integer values.
    It takes two parameters, both of which must be integers.
    The first parameter (a) is the first number to add.
    The second parameter (b) is the second number to add.
    It returns an integer representing the sum of a and b.
    This is useful when you need to add numbers together.
    Example usage: calculate_sum(5, 3) returns 8.
    """
    return a + b

# ✅ CONCISE
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

3. **Consider alternatives:**
- Read `checklists/mcp-vs-alternatives.md`
- Convert internal tools to CLI (80% case)
- Use scripts for progressive disclosure (5% case)

### Issue: Slow Tool Responses

**Symptoms:**
- Tools take >5 seconds to respond
- User experience degraded
- Timeouts occurring

**Optimizations:**

1. **Connection pooling:**
```python
# ❌ WRONG - New connection each time
@mcp.tool()
async def query(sql: str) -> dict:
    db = await connect_database()  # Slow!
    result = await db.query(sql)
    await db.close()
    return result

# ✅ CORRECT - Connection pool
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("postgresql://...", pool_size=20)

@mcp.tool()
async def query(sql: str) -> dict:
    async with engine.begin() as conn:  # Fast!
        result = await conn.execute(sql)
        return result.mappings().all()
```

2. **Caching:**
```python
from datetime import datetime, timedelta

cache = {}
CACHE_TTL = timedelta(minutes=5)

@mcp.tool()
async def fetch(url: str) -> dict:
    """Fetch with TTL cache."""
    now = datetime.now()

    # Check cache
    if url in cache:
        data, cached_time = cache[url]
        if now - cached_time < CACHE_TTL:
            return data

    # Fetch fresh
    data = await http_client.get(url).json()
    cache[url] = (data, now)
    return data
```

3. **Async operations:**
```python
# ❌ SLOW - Sequential
@mcp.tool()
async def fetch_all(urls: list) -> list:
    results = []
    for url in urls:
        result = await fetch(url)  # One at a time
        results.append(result)
    return results

# ✅ FAST - Concurrent
import asyncio

@mcp.tool()
async def fetch_all(urls: list) -> list:
    """Fetch all URLs concurrently."""
    tasks = [fetch(url) for url in urls]
    return await asyncio.gather(*tasks)  # All at once!
```

---

## Debugging Tools

### MCP Inspector

```bash
# Interactive testing
npx @modelcontextprotocol/inspector python server.py

# With environment variables
npx @modelcontextprotocol/inspector \
  -e API_KEY=value \
  -e LOG_LEVEL=debug \
  python server.py

# CLI mode for automation
npx @modelcontextprotocol/inspector --cli python server.py \
  --method tools/call \
  --tool-name my-tool \
  --tool-arg param=value
```

### Log Analysis

```bash
# macOS logs
tail -f ~/Library/Logs/Claude/mcp*.log

# Filter for errors
tail -f ~/Library/Logs/Claude/mcp*.log | grep ERROR

# Watch in real-time
watch -n 1 'tail -20 ~/Library/Logs/Claude/mcp-server.log'
```

### Manual Testing

```bash
# Test Python environment
uv run python -c "import mcp; print(mcp.__version__)"

# Test server starts
uv run python server.py
# Should see JSON-RPC handshake, no Python errors

# Test with frozen lockfile
uv run --frozen python server.py

# Check UV environment
uv run python -c "import sys; print(sys.executable)"
```

---

## Quick Reference: Error → Solution

| Error | Quick Fix |
|-------|-----------|
| Connection refused | Use absolute paths |
| Invalid JSON | Check stdout is clean (no print statements) |
| Module not found | Run `uv sync` |
| Wrong Python version | Use Python 3.10+, check `.python-version` |
| Tool not called | Improve tool description |
| High context usage | Reduce tools, use prompts for workflows |
| Slow responses | Add connection pooling and caching |
| Timeout | Implement timeout handling and progress reporting |
| Dependencies error | Use `lifespan`, not `dependencies` parameter |
| Env vars not working | Ensure all values are strings in JSON config |

---

## When to Ask for Help

If you've tried the solutions above and still have issues:

1. **Check logs first:** Most errors are logged with details
2. **Test with Inspector:** Isolate whether it's server or client issue
3. **Minimal reproduction:** Create smallest possible failing example
4. **Community resources:**
   - MCP Discord: https://discord.com/invite/model-context-protocol-1312302100125843476
   - GitHub Discussions: https://github.com/modelcontextprotocol/modelcontextprotocol/discussions
   - Python SDK Issues: https://github.com/modelcontextprotocol/python-sdk/issues

**When reporting issues, include:**
- MCP SDK version (`pip show mcp`)
- Python version (`python --version`)
- Operating system
- Complete error message
- Minimal code to reproduce
- What you've already tried

---

## Prevention Checklist

Avoid common errors by following these practices:

- [ ] Always use absolute paths in configurations
- [ ] Configure logging to stderr only
- [ ] Use Python 3.10 or higher
- [ ] Type hint all tool parameters
- [ ] Write clear, actionable tool descriptions
- [ ] Implement proper error handling
- [ ] Test with MCP Inspector before deploying
- [ ] Use `uv sync --frozen` in production
- [ ] Validate environment variables on startup
- [ ] Monitor context window usage
- [ ] Implement timeouts for long operations
- [ ] Use connection pooling for databases/APIs

Following these guidelines prevents 90%+ of common MCP errors.
