# MCP Server Quickstart: 5 Minutes to Running

Get your first MCP server running in Claude Desktop in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- UV installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Claude Desktop installed

## Step 1: Create Project (30 seconds)

```bash
# Create project
uv init my-weather-server --package
cd my-weather-server

# Add dependencies
uv add "mcp[cli]" httpx
```

## Step 2: Write Server (2 minutes)

Create `src/my_weather_server/server.py`:

```python
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("weather")

@mcp.tool()
async def get_weather(city: str) -> str:
    """Get weather for a city (uses wttr.in)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://wttr.in/{city}?format=%C+%t")
        return f"Weather in {city}: {response.text}"

if __name__ == "__main__":
    mcp.run()
```

Create `src/my_weather_server/__main__.py`:

```python
from .server import mcp

def main():
    mcp.run()

if __name__ == "__main__":
    main()
```

Create entry point in `pyproject.toml` (add to existing file):

```toml
[project.scripts]
my-weather-server = "my_weather_server.__main__:main"
```

## Step 3: Test (30 seconds)

```bash
# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run my-weather-server

# Open browser to http://localhost:6274
# Click "Tools" tab → should see "get_weather"
# Test it with city: "London"
```

## Step 4: Configure Claude Desktop (1 minute)

**macOS:** Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** Edit `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/my-weather-server",
        "run",
        "my-weather-server"
      ]
    }
  }
}
```

**Important:** Replace `/absolute/path/to/my-weather-server` with the actual path.

Get absolute path:
```bash
pwd  # Copy this output
```

## Step 5: Restart Claude Desktop (30 seconds)

1. Quit Claude Desktop (⌘+Q on Mac, Alt+F4 on Windows)
2. Restart Claude Desktop
3. Look for hammer icon 🔨 in bottom-right corner
4. Click it → should see "get_weather" tool

## Step 6: Test in Claude (30 seconds)

Ask Claude: **"What's the weather in Tokyo?"**

Claude should use your tool and return the result!

---

## 🎉 Success!

You've created your first MCP server. Now what?

### Next Steps

**Add more tools:**
```python
@mcp.tool()
def calculate(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

**Add a resource:**
```python
@mcp.resource("config://settings")
def get_settings() -> dict:
    """Get server settings."""
    return {"version": "1.0.0"}
```

**Add a prompt:**
```python
@mcp.prompt()
def analyze(topic: str) -> str:
    """Generate analysis prompt."""
    return f"Analyze {topic} and provide insights."
```

### Common Issues

**Server not appearing?**
- Check absolute path is correct
- Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log` (macOS)
- Verify UV installed: `which uv`
- Restart Claude Desktop

**Tool not being called?**
- Improve description: Make it clear when to use it
- Check tool appears in hammer icon menu
- Try asking Claude directly: "Use the get_weather tool"

**Import errors?**
- Run `uv sync` to install dependencies
- Verify mcp installed: `uv run python -c "import mcp; print(mcp.__version__)"`

### What You Built

```
my-weather-server/
├── pyproject.toml        # Project config
├── uv.lock              # Dependency lock
└── src/
    └── my_weather_server/
        ├── __init__.py
        ├── __main__.py   # Entry point
        └── server.py     # Your MCP server
```

### Architecture

```
You Ask Claude
    ↓
Claude Desktop (Host)
    ↓
MCP Client
    ↓
Your Server (via stdio)
    ↓
Weather API
```

## Going Further

### Production Features

**Add lifecycle management:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan(server):
    # Setup
    client = httpx.AsyncClient()
    try:
        yield {"client": client}
    finally:
        # Cleanup
        await client.aclose()

mcp = FastMCP("weather", lifespan=app_lifespan)
```

**Add error handling:**
```python
from mcp.types import ToolError

@mcp.tool()
async def safe_operation(param: str) -> str:
    """Tool with proper error handling."""
    try:
        result = process(param)
        return result
    except ValueError as e:
        raise ToolError(f"Invalid input: {e}")
    except Exception as e:
        raise ToolError(f"Operation failed: {e}")
```

**Add logging:**
```python
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,  # CRITICAL: stderr, not stdout
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@mcp.tool()
def logged_tool(param: str) -> str:
    """Tool with logging."""
    logger.info(f"Tool called with: {param}")
    return process(param)
```

### Explore Examples

- `templates/minimal-server.py` - Clean template
- `templates/advanced-server.py` - Production patterns
- `examples/database-server.py` - Database integration
- `examples/readonly-api.py` - API with caching
- `examples/cli-alternative.py` - CLI vs MCP comparison

### Read More

- `README.md` - Complete overview
- `checklists/mcp-vs-alternatives.md` - When to use MCP vs CLI
- `checklists/deployment.md` - Production deployment
- `checklists/common-errors.md` - Troubleshooting

### Get Help

- **This Skill:** Ask the MCP architect skill for guidance
- **MCP Discord:** https://discord.com/invite/model-context-protocol-1312302100125843476
- **GitHub:** https://github.com/modelcontextprotocol/python-sdk

---

## Summary: What You Learned

✅ **Created** MCP server with UV
✅ **Implemented** tool with async/await
✅ **Tested** with MCP Inspector
✅ **Configured** Claude Desktop
✅ **Used** tool in conversation

**Time:** 5 minutes
**Lines of code:** ~20
**Result:** Working MCP server in Claude Desktop

Now build something amazing! 🚀
