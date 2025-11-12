# MCP Server Development Cheat Sheet for Claude Code

A comprehensive quick-reference guide for developing Model Context Protocol (MCP) servers with Python, covering architecture, implementation patterns, testing, and deployment.

---

## 1. Fundamental Information about MCP Servers

### What is MCP?

**Model Context Protocol (MCP)** is an open standard protocol released by Anthropic in November 2024 that enables seamless integration between LLM applications and external data sources and tools. It acts as a "USB-C port for AI applications."

**Core Purpose:** Solves the N×M integration problem by transforming custom integrations (N applications × M data sources) into a standardized protocol (N+M connections).

**Key Benefits:**
- Breaks down data silos with universal data access
- Reduces LLM hallucinations through grounded context
- Enables scalable, connected AI systems
- Provides single standard replacing bespoke implementations

### Core Architecture

**Three-Layer Model:**

```
User → Host Application → MCP Client → MCP Server → External System
                              ↑                ↓
                              └────────────────┘
                              (JSON-RPC 2.0)
```

**Components:**

1. **Host** (Container/Coordinator): The main AI application (e.g., Claude Desktop, IDEs) that creates and manages MCP clients, controls permissions, and enforces security
2. **Client** (Protocol Interface): 1:1 connection with servers, handles protocol negotiation, routes messages, maintains security boundaries
3. **Server** (Capability Provider): Exposes resources, tools, and prompts; operates independently with focused responsibilities

### Server Types (Capabilities)

**1. Tools** (Model-Controlled Execution)
- **Purpose:** Executable functions that perform actions
- **Control:** AI decides when and how to call
- **Requires:** User approval for each execution
- **Examples:** Database queries, API calls, file operations, calculations

**2. Resources** (Application-Controlled Data)
- **Purpose:** Structured data/content providing context
- **Control:** Client application explicitly fetches
- **Types:** Text (UTF-8) or Binary (Base64)
- **Examples:** Configuration files, database schemas, documentation, logs

**3. Prompts** (User-Initiated Templates)
- **Purpose:** Pre-defined instruction templates
- **Control:** User explicitly selects (e.g., slash commands)
- **Features:** Variable arguments, autocomplete support
- **Examples:** Code review templates, report generation, meeting notes

**4. Sampling** (Server-Initiated LLM Requests)
- **Purpose:** Enables servers to request LLM completions
- **Direction:** Server→Client (reverse of tools)
- **Use Cases:** Data analysis, intelligent decisions, multi-step AI workflows

### Transport Mechanisms

**stdio (Standard Input/Output)** - Local Communication
- **Use When:** Desktop apps, CLI tools, local integrations
- **Pros:** Low latency (microseconds), simple setup, no auth needed
- **Cons:** Local only, single client
- **Configuration:**
```json
{
  "command": "python",
  "args": ["/absolute/path/to/server.py"]
}
```

**StreamableHTTP** - Remote Communication (Modern)
- **Use When:** Web apps, cloud servers, multiple clients, remote access
- **Pros:** Scalable, firewall-friendly, standard auth
- **Cons:** Network latency, requires HTTP server
- **Features:** Single endpoint, session management, SSE streaming

### Protocol Message Types (JSON-RPC 2.0)

**Request** (expects response):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {"name": "calculate", "arguments": {"a": 5, "b": 3}}
}
```

**Response** (reply to request):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {"content": [{"type": "text", "text": "Result: 8"}]}
}
```

**Notification** (one-way, no response):
```json
{
  "jsonrpc": "2.0",
  "method": "progress",
  "params": {"progressToken": "op-123", "progress": 75, "total": 100}
}
```

**Key Methods:**

| Client→Server | Server→Client | Notifications |
|--------------|--------------|---------------|
| initialize | sampling/createMessage | initialized |
| tools/list, tools/call | ping | cancelled, progress |
| resources/list, resources/read | | resources/updated |
| prompts/list, prompts/get | | tools/list_changed |

### Lifecycle Management

**1. Initialization Phase:**
```
1. Client sends initialize request with protocol version and capabilities
2. Server responds with its capabilities and protocol version
3. Client sends initialized notification
4. Normal operations begin
```

**2. Operation Phase:**
- Both parties respect negotiated capabilities
- Exchange requests, responses, and notifications
- Handle timeouts and cancellations

**3. Shutdown Phase:**
- Close transport-specific connections
- Graceful cleanup of resources
- Handle SIGTERM/SIGINT signals

**Critical Rules:**
- Always initialize before other operations
- Never assume capabilities without negotiation
- Only write JSON-RPC to stdout (logs go to stderr)
- Preserve request `id` in responses
- Implement timeouts for all requests

---

## 2. Python Development Best Practices

### Using uv for Package Management

**Why uv?**
- **10-100x faster** than pip
- **Automatic virtual environments** - no manual activation needed
- **Python version management** built-in
- **Universal lockfile** for reproducible builds
- **Official MCP recommendation**

**Installation:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip
pip install uv
```

**Create New MCP Server Project:**
```bash
# Option 1: Use official template
uvx create-mcp-server

# Option 2: Manual setup
uv init mcp-weather-server --package
cd mcp-weather-server
uv add "mcp[cli]"
uv add httpx pydantic
uv add --dev pytest pytest-asyncio ruff mypy
```

**Project Structure:**
```
mcp-server/
├── .venv/              # Auto-created by uv
├── .python-version     # Pin Python version (e.g., "3.11")
├── pyproject.toml      # Project configuration
├── uv.lock            # Dependency lockfile
├── README.md
├── tests/
│   └── test_server.py
└── src/
    └── mcp_server/
        ├── __init__.py
        ├── __main__.py   # Entry point
        └── server.py     # MCP server implementation
```

**Key pyproject.toml Configuration:**
```toml
[project]
name = "mcp-weather-server"
version = "0.1.0"
description = "MCP server providing weather data"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.scripts]
mcp-weather-server = "mcp_weather_server.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.5.0",
]
```

**Common uv Commands:**
```bash
# Add dependencies
uv add requests
uv add "fastapi>=0.115.0"
uv add --dev pytest

# Remove dependencies
uv remove requests

# Update dependencies
uv lock --upgrade
uv sync

# Run scripts (no activation needed!)
uv run python script.py
uv run pytest
uv run mcp dev server.py

# Manual venv (if needed)
uv venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate  # Windows
```

### Server Implementation Patterns

**Basic FastMCP Server:**
```python
from mcp.server.fastmcp import FastMCP

# Create server instance
mcp = FastMCP("Weather Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

@mcp.resource("config://settings")
def get_settings() -> str:
    """Get application settings"""
    return '{"theme": "dark", "language": "en"}'

@mcp.prompt()
def analyze_data(dataset: str) -> str:
    """Template for data analysis"""
    return f"Analyze the following dataset: {dataset}"

if __name__ == "__main__":
    mcp.run()  # Uses stdio transport by default
```

**Advanced Server with Lifecycle Management:**
```python
from contextlib import asynccontextmanager
from dataclasses import dataclass
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

@dataclass
class AppContext:
    db: Database
    cache: dict

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Manage application lifecycle with type-safe context"""
    db = await Database.connect()
    cache = {}
    try:
        yield AppContext(db=db, cache=cache)
    finally:
        await db.disconnect()

mcp = FastMCP("Advanced Server", lifespan=app_lifespan)

@mcp.tool()
async def query_data(
    query: str,
    ctx: Context[ServerSession, AppContext]
) -> dict:
    """Query with context access"""
    await ctx.info(f"Executing query: {query}")
    
    # Access lifespan context
    db = ctx.request_context.lifespan_context.db
    result = await db.query(query)
    
    return {"status": "success", "data": result}
```

### Error Handling and Logging

**Structured Error Handling:**
```python
from mcp.server.fastmcp import FastMCP, ToolError
import logging
import sys

# Configure logging (MUST use stderr)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

mcp = FastMCP("Secure Server", mask_error_details=True)

@mcp.tool()
async def fetch_data(url: str, ctx: Context) -> dict:
    """Fetch data with comprehensive error handling"""
    await ctx.info(f"Fetching: {url}")
    
    try:
        # Validate input
        if not url.startswith(('http://', 'https://')):
            raise ToolError("URL must start with http:// or https://")
        
        # Execute with timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
        await ctx.info("Fetch successful")
        return response.json()
        
    except httpx.HTTPError as e:
        await ctx.error(f"HTTP error: {e}")
        logger.error(f"HTTP error for {url}", exc_info=True)
        raise ToolError(f"Failed to fetch {url}: {str(e)}")
        
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        logger.exception("Unexpected error in fetch_data")
        raise ToolError("An unexpected error occurred")
```

**Logging Best Practices:**
```python
@mcp.tool()
async def complex_operation(data: dict, ctx: Context) -> dict:
    """Tool with comprehensive logging"""
    # Use context for MCP protocol logging
    await ctx.debug(f"Debug: Processing {data}")
    await ctx.info("Info: Starting operation")
    await ctx.warning("Warning: This is experimental")
    await ctx.error("Error: Something failed")
    
    # Use Python logging for internal tracking
    logger.info(f"Operation started: {data}")
    logger.error("Error occurred", exc_info=True)
    
    # CRITICAL: All print() must go to stderr
    print("Debug info", file=sys.stderr)
```

### Async/Await Patterns

**Async Tools:**
```python
import asyncio
import httpx

@mcp.tool()
async def fetch_url(url: str) -> dict:
    """Async HTTP request"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

@mcp.tool()
async def batch_process(items: list[str]) -> list:
    """Process multiple items concurrently"""
    async def process_item(item: str) -> dict:
        await asyncio.sleep(0.1)  # Simulate work
        return {"item": item, "processed": True}
    
    # Process concurrently
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results

@mcp.tool()
async def generate_poem(topic: str, ctx: Context) -> str:
    """Use LLM sampling from server"""
    from mcp.types import SamplingMessage, TextContent
    
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=f"Write a poem about {topic}")
            )
        ],
        max_tokens=100
    )
    
    return result.content.text if result.content.type == "text" else str(result.content)
```

### Type Hints and Validation

**Pydantic Models for Validation:**
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any

class SearchParams(BaseModel):
    """Strongly typed search parameters"""
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=10, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = None
    sort_by: str = Field(default="relevance")
    
    @validator('sort_by')
    def validate_sort(cls, v):
        allowed = ['relevance', 'date', 'popularity']
        if v not in allowed:
            raise ValueError(f'sort_by must be one of {allowed}')
        return v

@mcp.tool()
def search(
    query: str,
    max_results: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Type-safe search with validation"""
    params = SearchParams(
        query=query,
        max_results=max_results,
        filters=filters
    )
    # Implementation...
    return []

class WeatherData(BaseModel):
    """Structured output"""
    temperature: float = Field(description="Temperature in Celsius")
    humidity: float = Field(description="Humidity percentage")
    condition: str
    wind_speed: float

@mcp.tool()
def get_weather(city: str) -> WeatherData:
    """Return validated structured data"""
    return WeatherData(
        temperature=22.5,
        humidity=45.0,
        condition="sunny",
        wind_speed=5.2
    )
```

### Testing Strategies

**Unit Testing with FastMCP Client:**
```python
import pytest
from fastmcp import FastMCP, Client
from fastmcp.client.transports import FastMCPTransport

# Your server
mcp = FastMCP("Test Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

# Test fixture
@pytest.fixture
async def mcp_client():
    """Create test client connected directly to server"""
    async with Client(mcp) as client:
        yield client

# Basic test
@pytest.mark.asyncio
async def test_add_tool(mcp_client: Client[FastMCPTransport]):
    """Test add tool with various inputs"""
    result = await mcp_client.call_tool(
        name="add",
        arguments={"a": 5, "b": 3}
    )
    
    assert result.data is not None
    assert isinstance(result.data, int)
    assert result.data == 8

# Parametrized testing
@pytest.mark.parametrize(
    "a, b, expected",
    [(1, 2, 3), (2, 3, 5), (0, 0, 0), (-1, 1, 0), (100, 200, 300)]
)
@pytest.mark.asyncio
async def test_add_parametrized(a: int, b: int, expected: int, mcp_client: Client):
    """Test with multiple input combinations"""
    result = await mcp_client.call_tool(name="add", arguments={"a": a, "b": b})
    assert result.data == expected

# Error handling test
@pytest.mark.asyncio
async def test_division_by_zero(mcp_client: Client):
    """Test error handling for invalid input"""
    with pytest.raises(Exception) as exc_info:
        await mcp_client.call_tool(
            name="divide",
            arguments={"a": 10, "b": 0}
        )
    assert "Division by zero" in str(exc_info.value)

# Mock external dependencies
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_external_api_call(mcp_client: Client):
    """Test tool that calls external API"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": "mocked"}
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await mcp_client.call_tool(
            name="fetch_data",
            arguments={"url": "https://api.example.com"}
        )
        assert result.data["data"] == "mocked"
```

---

## 3. Development Workflow

### Setting Up a New MCP Server Project

**Step-by-Step Setup:**

```bash
# 1. Create project with uv
uvx create-mcp-server
# OR manually:
uv init mcp-weather-server --package
cd mcp-weather-server

# 2. Add MCP dependencies
uv add "mcp[cli]"
uv add httpx pydantic

# 3. Add dev dependencies
uv add --dev pytest pytest-asyncio ruff mypy

# 4. Create server structure
mkdir -p src/mcp_weather_server
touch src/mcp_weather_server/__init__.py
touch src/mcp_weather_server/server.py
touch src/mcp_weather_server/__main__.py
```

**Server Implementation (server.py):**
```python
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("weather-server")

NWS_API_BASE = "https://api.weather.gov"

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> dict:
    """Get weather forecast for coordinates"""
    async with httpx.AsyncClient() as client:
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_response = await client.get(points_url)
        points_data = points_response.json()
        
        forecast_url = points_data["properties"]["forecast"]
        forecast_response = await client.get(forecast_url)
        return forecast_response.json()

@mcp.resource("weather://status")
def server_status() -> str:
    """Server health status"""
    return "Weather server operational"

if __name__ == "__main__":
    mcp.run()
```

**Entry Point (__main__.py):**
```python
from .server import mcp

def main():
    """Entry point for MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()
```

### Configuration Files and Manifests

**pyproject.toml (Complete Example):**
```toml
[project]
name = "mcp-weather-server"
version = "0.1.0"
description = "MCP server providing weather data"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.scripts]
mcp-weather-server = "mcp_weather_server.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.5.0",
    "mypy>=1.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true
```

**.python-version:**
```
3.11
```

**.gitignore:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual environments
.venv/
venv/
ENV/

# Distribution
dist/
build/
*.egg-info/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDEs
.vscode/
.idea/
*.swp

# uv
uv.lock  # Include or exclude based on team preference
```

### Debugging Techniques

**Critical Rule: stdout vs stderr**

**ONLY JSON-RPC messages go to stdout. ALL logs/debug output MUST go to stderr.**

```python
import sys

# ✅ CORRECT
print("Debug info", file=sys.stderr)
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

# ❌ WRONG - Breaks protocol
print("Debug info")  # Goes to stdout!
```

**5-Step Debugging Workflow:**

1. **Reproduce Error** - Document exact input, environment, create minimal test case
2. **Check Logs:**
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log
   
   # Windows
   Get-Content "$env:APPDATA\Claude\logs\mcp*.log" -Wait
   
   # Linux
   tail -f ~/.local/share/Claude/logs/mcp*.log
   ```
3. **Isolate Problem** - Connection? Specific tool? Input-related? External dependencies?
4. **Test with MCP Inspector** - Controlled environment, view raw JSON-RPC messages
5. **Fix and Verify** - Test original case, check for new issues, verify edge cases

**Structured Logging:**
```python
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@mcp.tool()
async def debug_tool(param: str, ctx: Context) -> str:
    """Tool with comprehensive logging"""
    # MCP context logging
    await ctx.debug(f"Input: {param}")
    await ctx.info("Processing started")
    
    # Python logging
    logger.info(f"Tool called with: {param}")
    
    try:
        result = process(param)
        await ctx.info("Processing complete")
        return result
    except Exception as e:
        await ctx.error(f"Error: {e}")
        logger.exception("Processing failed")
        raise ToolError(f"Failed to process: {e}")
```

### Local Testing Methods

**MCP Inspector - Primary Testing Tool:**

```bash
# Run directly
npx @modelcontextprotocol/inspector

# Test built server
npx @modelcontextprotocol/inspector python src/mcp_server/server.py

# With environment variables
npx @modelcontextprotocol/inspector -e API_KEY=value python server.py

# With arguments
npx @modelcontextprotocol/inspector python server.py arg1 arg2

# Custom ports
CLIENT_PORT=8080 SERVER_PORT=9000 npx @modelcontextprotocol/inspector python server.py
```

**Default URLs:**
- Inspector UI: `http://localhost:6274`
- Proxy Server: Port `6277`

**Inspector Features:**
- **Resources Tab:** List, inspect metadata/content, test subscriptions
- **Prompts Tab:** View templates, test with custom inputs
- **Tools Tab:** List tools, view schemas, test with inputs, see results
- **Notifications Pane:** View server logs in real-time

**CLI Mode for Automation:**
```bash
# List tools
npx @modelcontextprotocol/inspector --cli python server.py --method tools/list

# Call a tool
npx @modelcontextprotocol/inspector --cli python server.py \
  --method tools/call \
  --tool-name mytool \
  --tool-arg key=value
```

**Python MCP CLI:**
```bash
# Install with CLI support
pip install "mcp[cli]"

# Development with Inspector
mcp dev server.py
# Opens http://localhost:5173

# Install to Claude Desktop
mcp install server.py

# Run standalone
mcp start server.py
```

### Integration with Claude Desktop

**Configuration File Locations:**
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Access Configuration:**
1. Open Claude Desktop
2. Click **Claude menu** in system menu bar
3. Select **Settings…**
4. Click **Developer** tab
5. Click **Edit Config**

**Configuration Examples:**

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-weather-server",
        "run",
        "mcp-weather-server"
      ],
      "env": {
        "API_KEY": "your-api-key",
        "LOG_LEVEL": "debug"
      }
    },
    "python-server": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"]
    },
    "remote-server": {
      "type": "sse",
      "url": "http://localhost:3000/sse"
    }
  }
}
```

**Important Notes:**
- **Always use absolute paths** (not relative)
- **Restart Claude Desktop** after config changes (⌘+R / Ctrl+R)
- Verify: Look for hammer icon 🔨 at bottom-right
- Check Settings → Developer for server status

**Configuration Workflow:**
1. Edit configuration file
2. Save file
3. Restart Claude Desktop
4. Click hammer icon to see available tools
5. Check logs if server doesn't appear

---

## 4. Implementation Patterns

### Tool Implementation Examples

**Basic Tool:**
```python
@mcp.tool()
def calculate(operation: str, a: int, b: int) -> str:
    """Perform basic math operations"""
    if operation == "add":
        return f"Result: {a + b}"
    elif operation == "multiply":
        return f"Result: {a * b}"
    raise ToolError(f"Unknown operation: {operation}")
```

**Async Tool with Progress Reporting:**
```python
@mcp.tool()
async def long_running_task(
    task_name: str,
    ctx: Context,
    steps: int = 5
) -> str:
    """Execute a task with progress updates"""
    await ctx.info(f"Starting: {task_name}")
    
    for i in range(steps):
        progress = (i + 1) / steps
        await ctx.report_progress(
            progress=progress,
            total=1.0,
            message=f"Step {i + 1}/{steps}"
        )
        await asyncio.sleep(0.5)  # Simulate work
    
    return f"Task '{task_name}' completed"
```

**Tool with Structured Output:**
```python
from pydantic import BaseModel

class WeatherData(BaseModel):
    temperature: float
    humidity: float
    condition: str
    wind_speed: float

@mcp.tool()
async def get_weather(city: str) -> WeatherData:
    """Get weather - returns validated structured data"""
    # Fetch from API...
    return WeatherData(
        temperature=22.5,
        humidity=45.0,
        condition="sunny",
        wind_speed=5.2
    )
```

**Tool with Error Handling and Retry:**
```python
import asyncio

async def retry_with_backoff(operation, max_attempts: int = 3):
    """Exponential backoff retry pattern"""
    for attempt in range(max_attempts):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            delay = 2 ** attempt
            await asyncio.sleep(delay)

@mcp.tool()
async def resilient_fetch(url: str, ctx: Context) -> dict:
    """Fetch with retry logic"""
    async def fetch():
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    try:
        return await retry_with_backoff(fetch, max_attempts=3)
    except Exception as e:
        await ctx.error(f"Failed after retries: {e}")
        raise ToolError(f"Unable to fetch {url}: {str(e)}")
```

### Resource Exposure Patterns

**Static Resource:**
```python
@mcp.resource("config://settings")
def get_settings() -> str:
    """Get application settings"""
    return json.dumps({
        "theme": "dark",
        "language": "en",
        "debug": False
    })
```

**Dynamic Resource with URI Templates:**
```python
@mcp.resource("file://documents/{name}")
def read_document(name: str) -> str:
    """Read a document by name - URI parameter extraction"""
    # Parameter extracted from URI pattern
    path = DOCUMENTS_DIR / name
    if not path.exists():
        raise ResourceError(f"Document not found: {name}")
    return path.read_text()

@mcp.resource("user://{user_id}/profile")
async def user_profile(user_id: str, ctx: Context) -> dict:
    """Get user profile by ID"""
    await ctx.info(f"Fetching profile for user {user_id}")
    # Fetch from database...
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "created": "2024-01-01"
    }
```

**Resource with Context:**
```python
@mcp.resource("database://query/{table}")
async def query_table(table: str, ctx: Context[ServerSession, AppContext]) -> str:
    """Query database table with context access"""
    await ctx.info(f"Querying table: {table}")
    
    # Access lifespan context resources
    db = ctx.request_context.lifespan_context.db
    result = await db.query(f"SELECT * FROM {table}")
    
    return json.dumps(result)
```

### Prompt Template Creation

**Basic Prompt:**
```python
@mcp.prompt()
def code_review_prompt(code: str) -> str:
    """Generate code review prompt"""
    return f"""Please review this code:

{code}

Focus on:
1. Code quality and readability
2. Potential bugs or security issues
3. Performance considerations
4. Best practices"""
```

**Prompt with Multiple Arguments:**
```python
@mcp.prompt()
def report_prompt(topic: str, format: str = "detailed", audience: str = "technical") -> str:
    """Generate report prompt with customization"""
    return f"""Create a {format} report about {topic} for a {audience} audience.

Include:
- Executive summary
- Key findings
- Recommendations
- Supporting data"""
```

### Request/Response Handling

**Tool Response Types:**
```python
from mcp.types import CallToolResult, TextContent

# Simple return (recommended)
@mcp.tool()
def simple_tool() -> str:
    """Return plain string"""
    return "Success"

# Structured return
@mcp.tool()
def structured_tool() -> dict:
    """Return structured data"""
    return {"status": "success", "data": [1, 2, 3]}

# Full control with CallToolResult
@mcp.tool()
def advanced_tool() -> CallToolResult:
    """Return CallToolResult for full control"""
    return CallToolResult(
        content=[TextContent(type="text", text="Success")],
        _meta={"hidden": "metadata for client"}
    )

# Error response
@mcp.tool()
def error_tool() -> CallToolResult:
    """Return error result"""
    return CallToolResult(
        isError=True,
        content=[TextContent(type="text", text="Operation failed")]
    )
```

### State Management

**Stateless Design (Preferred):**
```python
@mcp.tool()
async def process_data(params: dict) -> dict:
    """Each tool call is self-contained"""
    temp_file = await create_temp_file()
    try:
        await process_file(temp_file, params)
        return {"status": "success"}
    finally:
        await cleanup_temp_file(temp_file)
```

**Session-Based (When Required):**
```python
from uuid import uuid4

sessions = {}

@mcp.tool()
def start_session(user_id: str) -> str:
    """Create session with auto-cleanup"""
    session_id = str(uuid4())
    sessions[session_id] = {
        "user_id": user_id,
        "created_at": time.time(),
        "data": {}
    }
    
    # Auto-cleanup after 1 hour
    asyncio.create_task(cleanup_session(session_id, 3600))
    
    return f"Session {session_id} created"

@mcp.tool()
def use_session(session_id: str, operation: str) -> dict:
    """Use existing session"""
    session = sessions.get(session_id)
    if not session:
        raise ToolError(
            "Session expired. Please create a new session with start_session tool."
        )
    # Use session...
    return {"status": "success"}

async def cleanup_session(session_id: str, delay: int):
    """Auto-cleanup session after delay"""
    await asyncio.sleep(delay)
    sessions.pop(session_id, None)
```

### Authentication and Security

**Input Sanitization:**
```python
from pathlib import Path
import re

@mcp.tool()
def read_file(filepath: str) -> str:
    """Read file with path traversal protection"""
    # Validate path
    path = Path(filepath).resolve()
    allowed_dir = Path("/allowed/directory").resolve()
    
    if not str(path).startswith(str(allowed_dir)):
        raise ToolError("Access denied: path outside allowed directory")
    
    if not path.exists():
        raise ToolError(f"File not found: {filepath}")
    
    try:
        return path.read_text()
    except Exception as e:
        raise ToolError(f"Error reading file: {e}")

@mcp.tool()
def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\'&]', '', text)
    # Limit length
    return sanitized[:1000]
```

**Environment-Based Authentication:**
```python
import os

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable required")

@mcp.tool()
async def authenticated_request(endpoint: str) -> dict:
    """Make authenticated API request"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint, headers=headers)
        response.raise_for_status()
        return response.json()
```

**Error Masking:**
```python
# Mask internal errors from clients
mcp = FastMCP("Secure Server", mask_error_details=True)

@mcp.tool()
def secure_operation(param: str) -> str:
    """Internal errors are masked"""
    try:
        # Operation that might fail...
        result = internal_process(param)
        return result
    except ValueError as e:
        # Client-visible error - always passed through
        raise ToolError(f"Invalid input: {e}")
    except Exception as e:
        # Internal error - details masked from client
        # Client sees: "An error occurred"
        # Server logs full details to stderr
        logger.exception("Internal error")
        raise
```

---

## 5. Common Pitfalls and Solutions

### stdout Contamination (Most Common Error)

**Problem:** Writing anything to stdout breaks JSON-RPC protocol.

```python
# ❌ WRONG - Breaks protocol
print("Debug info")
console.log("Debug")

# ✅ CORRECT - Use stderr
import sys
print("Debug info", file=sys.stderr)
logging.basicConfig(stream=sys.stderr)
```

### Missing Server Connection

**Problem:** Server created but never connected to transport.

```python
# ❌ WRONG - Server not connected
server = McpServer(name="MyServer")
server.tool("myTool", schema, handler)
# Missing: await server.connect(transport)

# ✅ CORRECT
server = McpServer(name="MyServer")
server.tool("myTool", schema, handler)
transport = StdioServerTransport()
await server.connect(transport)  # Critical!
```

### Relative Paths in Configuration

**Problem:** Claude Desktop can't find server with relative paths.

```json
// ❌ WRONG
{"command": "python", "args": ["./server.py"]}

// ✅ CORRECT - Absolute path
{"command": "python", "args": ["/Users/username/project/server.py"]}
```

### Timeout Handling

**Problem:** Long operations without timeout or progress.

```python
# ❌ WRONG - No timeout
async def long_operation():
    result = await very_slow_api_call()
    return result

# ✅ CORRECT - With timeout and progress
@mcp.tool()
async def long_operation(ctx: Context) -> str:
    """Long operation with timeout and progress"""
    try:
        async with asyncio.timeout(30):  # 30s timeout
            for i in range(10):
                await ctx.report_progress(i / 10, 1.0, f"Step {i+1}/10")
                await process_step(i)
            return "Complete"
    except asyncio.TimeoutError:
        raise ToolError("Operation timed out after 30 seconds")
```

### Connection Pooling

**Problem:** Creating new connections for each request.

```python
# ❌ WRONG - New connection each time
@mcp.tool()
async def query_db(sql: str) -> dict:
    db = await connect_database()  # Slow!
    result = await db.query(sql)
    await db.close()
    return result

# ✅ CORRECT - Use connection pool
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("postgresql://...", pool_size=20)

@mcp.tool()
async def query_db(sql: str) -> dict:
    async with engine.begin() as conn:
        result = await conn.execute(sql)
        return result.mappings().all()
```

### Memory Management

**Problem:** Returning large responses without limits.

```python
# ❌ WRONG - Unlimited response size
@mcp.tool()
async def fetch_large(url: str) -> str:
    response = await httpx.get(url)
    return response.text  # Could be gigabytes!

# ✅ CORRECT - Limit response size
MAX_RESPONSE_SIZE = 1024 * 1024  # 1MB

@mcp.tool()
async def fetch_large(url: str) -> str:
    """Fetch with size limit"""
    response = await httpx.get(url)
    text = response.text
    
    if len(text) > MAX_RESPONSE_SIZE:
        return f"Response too large ({len(text)} bytes). First 1MB:\n{text[:MAX_RESPONSE_SIZE]}"
    
    return text
```

### Error Messages for Agents

**Problem:** Human-focused error messages that don't guide agents.

```python
# ❌ BAD - Not actionable for agent
raise Error("You don't have access")

# ✅ GOOD - Agent-focused, actionable
raise ToolError(
    "Access denied. The MCP server requires a valid API_TOKEN in environment "
    "variables. Current token is invalid or missing. Set API_TOKEN in server "
    "configuration and restart.",
    {"required_env_var": "API_TOKEN", "current_value": "not set"}
)
```

### Performance Considerations

**Best Practices:**
1. **Tool Budget:** Limit to 10-15 tools per server
2. **Optimize Descriptions:** Clear, concise descriptions help LLMs understand
3. **Timeouts:** Default 30s, adjust based on operation type
4. **Progress Notifications:** For operations >5 seconds
5. **Caching:** Cache frequently accessed data
6. **Database Optimization:** Use indexes, pagination, prepared statements
7. **Connection Pooling:** Reuse database/HTTP connections
8. **Lazy Initialization:** Connect only when needed

**Caching Pattern:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

cache = {}
CACHE_TTL = timedelta(minutes=5)

@mcp.tool()
async def fetch_cached(url: str) -> dict:
    """Fetch with TTL cache"""
    now = datetime.now()
    
    if url in cache:
        cached_data, cached_time = cache[url]
        if now - cached_time < CACHE_TTL:
            return cached_data
    
    # Fetch fresh data
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
    
    # Cache result
    cache[url] = (data, now)
    
    # Cleanup old entries
    if len(cache) > 100:
        oldest = min(cache.items(), key=lambda x: x[1][1])
        del cache[oldest[0]]
    
    return data
```

### Common Error Reference

| Error | Cause | Solution |
|-------|-------|----------|
| ENOENT | Invalid path | Use absolute paths |
| EADDRINUSE | Port conflict | Change port or kill process |
| MODULE_NOT_FOUND | Missing dependencies | Run `uv sync` |
| Server transport closed | Server crash | Check logs, ensure connect() |
| Invalid JSON | stdout pollution | Use stderr for all logs |
| Connection refused | Server not running | Verify process and port |
| Timeout | Long operation | Implement timeout handling |
| Protocol version mismatch | Outdated SDK | Update: `uv lock --upgrade-package mcp` |

---

## 6. Master List of External URLs

### Official Documentation

- **https://modelcontextprotocol.io/** - Official MCP documentation site with comprehensive guides on architecture, concepts, and implementation. Essential starting point for all MCP development.

- **https://spec.modelcontextprotocol.io/specification/** - Complete MCP specification document detailing protocol architecture, JSON-RPC 2.0 messaging, and technical requirements. Critical reference for MCP-compliant implementations.

- **https://modelcontextprotocol.io/docs/learn/architecture** - Architecture overview explaining client-host-server model, protocol layers, and MCP primitives. Foundational understanding of component interactions.

- **https://modelcontextprotocol.io/docs/sdk** - Official SDKs documentation hub with links to Python, TypeScript, C#, Kotlin implementations. Central resource for language-specific development.

- **https://modelcontextprotocol.io/docs/develop/build-server** - Step-by-step tutorial for building first MCP server with weather API examples in Python and TypeScript. Hands-on getting started guide.

- **https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop** - Claude Desktop-specific guide for installing and managing local MCP servers using desktop extensions. Essential for testing with Claude.

- **https://www.anthropic.com/news/model-context-protocol** - Anthropic's official announcement explaining MCP motivation, use cases, and ecosystem vision. Provides strategic context.

### Official GitHub Repositories

- **https://github.com/modelcontextprotocol/python-sdk** - Official Python SDK for building MCP servers and clients with FastMCP interface and all transport types. Primary tool for Python developers.

- **https://github.com/modelcontextprotocol/typescript-sdk** - Official TypeScript SDK for MCP servers and clients. Primary tool for JavaScript/TypeScript development.

- **https://github.com/modelcontextprotocol/csharp-sdk** - Official C# SDK maintained with Microsoft for .NET developers. Integrates with Visual Studio and GitHub Copilot.

- **https://github.com/modelcontextprotocol/kotlin-sdk** - Official Kotlin SDK maintained with JetBrains for JVM-based development. Supports Android and enterprise Java environments.

- **https://github.com/modelcontextprotocol/servers** - Official reference implementations including filesystem, GitHub, PostgreSQL, SQLite, Puppeteer, Redis, Slack, Google Drive servers. Production-ready templates.

- **https://github.com/modelcontextprotocol/modelcontextprotocol** - Main repository containing MCP specification and documentation source. Canonical source for protocol evolution.

- **https://github.com/anthropics/mcpb** - MCP Bundle (.mcpb) specification and tooling for single-click installable server packages. Essential for distribution.

- **https://github.com/modelcontextprotocol** - Main MCP GitHub organization hosting all official SDKs, tools, and specifications. Central hub for open-source development.

### Python SDK Resources

- **https://pypi.org/project/mcp/** - MCP Python SDK on PyPI with installation instructions and version history. Official package repository.

- **https://anish-natekar.github.io/mcp_docs/getting-started.html** - Comprehensive Python SDK documentation covering FastMCP, tools, resources, and deployment. Detailed Python-specific guide.

- **https://anish-natekar.github.io/mcp_docs/examples.html** - Python SDK examples including weather API, SQLite, HTTP requests. Practical code samples.

- **https://medium.com/@syed_hasan/step-by-step-guide-building-an-mcp-server-using-python-sdk-alphavantage-claude-ai-7a2bfb0c3096** - Tutorial building MCP server with AlphaVantage stock API integration. Real-world financial data example.

### TypeScript SDK Resources

- **https://www.npmjs.com/package/@modelcontextprotocol/sdk** - MCP TypeScript SDK on NPM with API documentation. Official package with type definitions.

- **https://dev.to/shadid12/how-to-build-mcp-servers-with-typescript-sdk-1c28** - Tutorial building MCP servers with TypeScript including CocktailDB API example. Practical implementation guide.

- **https://www.freecodecamp.org/news/how-to-build-a-custom-mcp-server-with-typescript-a-handbook-for-developers/** - Comprehensive handbook combining MCP theory with TypeScript practice. In-depth guide.

- **https://learn.microsoft.com/en-us/azure/developer/ai/build-mcp-server-ts** - Microsoft guide for deploying TypeScript MCP servers to Azure Container Apps. Enterprise deployment patterns.

### uv Package Manager

- **https://docs.astral.sh/uv/** - Complete uv documentation covering installation, project management, and Python version management. Critical tool for MCP Python development.

- **https://docs.astral.sh/uv/getting-started/installation/** - Installation guide for uv across platforms with multiple methods. Essential setup guide.

- **https://github.com/astral-sh/uv** - uv GitHub repository with source code and community discussions. Access to latest features.

- **https://www.datacamp.com/tutorial/python-uv** - DataCamp guide to uv features and usage. Tutorial-style introduction.

- **https://realpython.com/python-uv/** - Real Python in-depth guide to managing projects with uv. Detailed examples and best practices.

### Development Tools

- **https://modelcontextprotocol.io/docs/tools/inspector** - Official MCP Inspector documentation for interactive browser-based testing. Essential debugging tool.

- **https://github.com/modelcontextprotocol/inspector** - MCP Inspector GitHub repository with CLI mode and configuration options. Open-source debugging tool.

- **https://mcp.ziziyi.com/inspector** - Web-based MCP Inspector running directly in browser. Convenient online testing.

### Tutorials & Guides

- **https://medium.com/@nimritakoul01/the-model-context-protocol-mcp-a-complete-tutorial-a3abe8a7f4ef** - Complete MCP tutorial covering architecture and implementation. Comprehensive conceptual overview.

- **https://snyk.io/articles/a-beginners-guide-to-visually-understanding-mcp-architecture/** - Visual guide to MCP architecture with diagrams. Excellent for visual learners.

- **https://dev.to/pavanbelagatti/model-context-protocol-mcp-101-a-hands-on-beginners-guide-47ho** - Beginner's hands-on guide with weather server example. Step-by-step walkthrough.

- **https://composio.dev/blog/mcp-server-step-by-step-guide-to-building-from-scrtch** - Guide to building MCP servers from scratch. Detailed implementation patterns.

### Community Resources

- **https://discord.com/invite/model-context-protocol-1312302100125843476** - Official MCP Discord server with 10,417+ members. Primary community hub for discussions.

- **https://github.com/modelcontextprotocol/modelcontextprotocol/discussions** - GitHub Discussions for MCP specification topics. Structured forum for protocol evolution.

### Example Servers

- **https://github.com/appcypher/awesome-mcp-servers** - Curated list of 500+ community MCP servers. Comprehensive directory.

- **https://github.com/wong2/awesome-mcp-servers** - Another curated list with 600+ servers including crypto, blockchain, communication tools. Alternative directory.

- **https://www.pulsemcp.com/** - Searchable directory of MCP servers with download statistics. Web-based discovery tool.

- **https://www.claudemcp.com/** - Community-driven MCP server directory with search. Alternative discovery platform.

### Integration Guides

- **https://openai.github.io/openai-agents-python/mcp/** - OpenAI Agents SDK documentation for using MCP servers. Shows integration with OpenAI agents.

- **https://googleapis.github.io/genai-toolbox/getting-started/mcp_quickstart/** - Google GenAI Toolbox MCP quickstart. MCP in Google's AI ecosystem.

---

## Quick Reference Cards

### Development Commands Cheat Sheet

```bash
# Project Setup
uv init mcp-server --package
uv add "mcp[cli]" httpx pydantic
uv add --dev pytest pytest-asyncio ruff

# Development
uv run python -m mcp_server
uv run mcp dev server.py
uv run pytest

# Linting & Formatting
uv run ruff check .
uv run ruff format .
uv run mypy src/

# Dependency Management
uv add package-name
uv remove package-name
uv lock --upgrade
uv sync

# Testing with Inspector
npx @modelcontextprotocol/inspector python server.py
mcp dev server.py

# Installation
mcp install server.py
```

### pyproject.toml Template

```toml
[project]
name = "mcp-server"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["mcp>=1.0.0", "httpx>=0.27.0"]

[project.scripts]
mcp-server = "mcp_server.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = ["pytest>=8.0.0", "pytest-asyncio>=0.23.0", "ruff>=0.5.0"]
```

### Minimal Server Template

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ServerName")

@mcp.tool()
def example_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"

@mcp.resource("example://data")
def example_resource() -> str:
    """Resource description"""
    return "Resource content"

@mcp.prompt()
def example_prompt(input: str) -> str:
    """Prompt description"""
    return f"Process: {input}"

if __name__ == "__main__":
    mcp.run()
```

### Claude Desktop Config Template

```json
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": ["--directory", "/absolute/path", "run", "mcp-server"],
      "env": {"API_KEY": "value"}
    }
  }
}
```

### Testing Template

```python
import pytest
from fastmcp import Client

@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c

@pytest.mark.asyncio
async def test_tool(client):
    result = await client.call_tool("tool_name", {"param": "value"})
    assert result.data == expected
```

---

**Last Updated:** Based on MCP specification 2024-11-05 and Python SDK 1.0.0+

**Usage:** Keep this cheat sheet open while developing MCP servers. Reference specific sections as needed during implementation, debugging, and testing.
