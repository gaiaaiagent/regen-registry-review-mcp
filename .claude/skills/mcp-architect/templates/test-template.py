"""
MCP Server Testing Template

Comprehensive testing patterns for MCP servers including:
- Unit tests for individual tools
- Integration tests with FastMCP client
- Parametrized testing
- Mock external dependencies
- Error handling verification
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastmcp import FastMCP, Client
from fastmcp.client.transports import FastMCPTransport

# Import your server instance
# from mcp_server.server import mcp


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def mcp_server():
    """Create a test MCP server instance."""
    mcp = FastMCP("test-server")

    @mcp.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @mcp.tool()
    def divide(a: int, b: int) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

    @mcp.resource("config://test")
    def test_config() -> dict:
        """Test configuration resource."""
        return {"setting": "value"}

    @mcp.prompt()
    def test_prompt(topic: str) -> str:
        """Test prompt template."""
        return f"Analyze: {topic}"

    return mcp


@pytest.fixture
async def mcp_client(mcp_server):
    """Create test client connected to server."""
    async with Client(mcp_server) as client:
        yield client


# ============================================================================
# BASIC TOOL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_add_tool(mcp_client: Client[FastMCPTransport]):
    """Test basic tool functionality."""
    result = await mcp_client.call_tool(
        name="add",
        arguments={"a": 5, "b": 3}
    )

    assert result.data is not None
    assert isinstance(result.data, int)
    assert result.data == 8


@pytest.mark.asyncio
async def test_divide_tool(mcp_client: Client[FastMCPTransport]):
    """Test division tool."""
    result = await mcp_client.call_tool(
        name="divide",
        arguments={"a": 10, "b": 2}
    )

    assert result.data == 5.0


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1, 2, 3),
        (2, 3, 5),
        (0, 0, 0),
        (-1, 1, 0),
        (100, 200, 300),
        (-10, -5, -15),
    ]
)
@pytest.mark.asyncio
async def test_add_parametrized(
    a: int,
    b: int,
    expected: int,
    mcp_client: Client
):
    """Test add tool with multiple input combinations."""
    result = await mcp_client.call_tool(
        name="add",
        arguments={"a": a, "b": b}
    )
    assert result.data == expected


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_division_by_zero(mcp_client: Client):
    """Test error handling for invalid input."""
    with pytest.raises(Exception) as exc_info:
        await mcp_client.call_tool(
            name="divide",
            arguments={"a": 10, "b": 0}
        )

    assert "Division by zero" in str(exc_info.value)


@pytest.mark.asyncio
async def test_missing_arguments(mcp_client: Client):
    """Test error when required arguments are missing."""
    with pytest.raises(Exception):
        await mcp_client.call_tool(
            name="add",
            arguments={"a": 5}  # Missing 'b'
        )


@pytest.mark.asyncio
async def test_invalid_argument_types(mcp_client: Client):
    """Test error when argument types are wrong."""
    with pytest.raises(Exception):
        await mcp_client.call_tool(
            name="add",
            arguments={"a": "not a number", "b": 5}
        )


# ============================================================================
# RESOURCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_read_resource(mcp_client: Client):
    """Test reading a resource."""
    resources = await mcp_client.list_resources()

    # Find our test config resource
    config_resource = next(
        (r for r in resources if r.uri == "config://test"),
        None
    )

    assert config_resource is not None

    # Read the resource
    result = await mcp_client.read_resource(config_resource.uri)

    assert result is not None
    # Parse the result and verify content
    # (implementation depends on your resource format)


# ============================================================================
# PROMPT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_prompts(mcp_client: Client):
    """Test listing available prompts."""
    prompts = await mcp_client.list_prompts()

    assert len(prompts) > 0

    # Find our test prompt
    test_prompt = next(
        (p for p in prompts if "test_prompt" in p.name),
        None
    )

    assert test_prompt is not None


@pytest.mark.asyncio
async def test_get_prompt(mcp_client: Client):
    """Test retrieving a prompt with arguments."""
    result = await mcp_client.get_prompt(
        name="test_prompt",
        arguments={"topic": "data analysis"}
    )

    assert result is not None
    # Verify prompt content
    # (implementation depends on your prompt structure)


# ============================================================================
# MOCK EXTERNAL DEPENDENCIES
# ============================================================================

@pytest.fixture
def mock_http_client():
    """Mock httpx.AsyncClient for testing API calls."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": "mocked"}
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        yield mock_client


@pytest.mark.asyncio
async def test_external_api_call(mcp_client: Client, mock_http_client):
    """Test tool that calls external API with mocked response."""
    # This assumes you have a tool called 'fetch_data'
    # Adjust according to your actual tools
    result = await mcp_client.call_tool(
        name="fetch_data",
        arguments={"url": "https://api.example.com/data"}
    )

    # Verify mocked response
    assert result.data["data"] == "mocked"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_tool_chaining(mcp_client: Client):
    """Test chaining multiple tool calls together."""
    # Call first tool
    result1 = await mcp_client.call_tool(
        name="add",
        arguments={"a": 5, "b": 3}
    )

    # Use result in second tool call
    result2 = await mcp_client.call_tool(
        name="divide",
        arguments={"a": result1.data, "b": 2}
    )

    assert result2.data == 4.0


@pytest.mark.asyncio
async def test_concurrent_tool_calls(mcp_client: Client):
    """Test multiple concurrent tool calls."""
    import asyncio

    # Create multiple concurrent tasks
    tasks = [
        mcp_client.call_tool(name="add", arguments={"a": i, "b": i + 1})
        for i in range(10)
    ]

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    # Verify all completed successfully
    assert len(results) == 10
    assert all(r.data is not None for r in results)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_tool_performance(mcp_client: Client):
    """Test tool call performance."""
    import time

    start = time.time()

    for _ in range(100):
        await mcp_client.call_tool(
            name="add",
            arguments={"a": 1, "b": 2}
        )

    duration = time.time() - start

    # Assert reasonable performance (adjust threshold as needed)
    assert duration < 10.0, f"100 tool calls took {duration:.2f}s (expected <10s)"


# ============================================================================
# SERVER LIFECYCLE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_server_initialization(mcp_server):
    """Test server initializes correctly."""
    assert mcp_server.name == "test-server"


@pytest.mark.asyncio
async def test_list_tools(mcp_client: Client):
    """Test listing all available tools."""
    tools = await mcp_client.list_tools()

    assert len(tools) > 0

    # Verify expected tools exist
    tool_names = [t.name for t in tools]
    assert "add" in tool_names
    assert "divide" in tool_names


# ============================================================================
# BEHAVIORAL TESTS (AI Model Testing)
# ============================================================================

# Note: These tests require actual AI model integration
# They verify that the AI correctly uses your tools

@pytest.mark.skip(reason="Requires AI model integration")
@pytest.mark.asyncio
async def test_ai_tool_selection():
    """Test that AI selects correct tool for task.

    This would require integration with an actual AI model
    to verify behavioral correctness, not just functional correctness.
    """
    pass


@pytest.mark.skip(reason="Requires AI model integration")
@pytest.mark.asyncio
async def test_ai_parameter_extraction():
    """Test that AI correctly extracts parameters from natural language."""
    pass


# ============================================================================
# TEST UTILITIES
# ============================================================================

def assert_tool_result_valid(result, expected_type=None):
    """Helper to validate tool result structure."""
    assert result is not None
    assert hasattr(result, 'data')

    if expected_type:
        assert isinstance(result.data, expected_type)


# ============================================================================
# RUNNING TESTS
# ============================================================================

# Run with pytest:
#   uv run pytest tests/ -v
#
# Run with coverage:
#   uv run pytest tests/ --cov=mcp_server --cov-report=html
#
# Run specific test:
#   uv run pytest tests/test_server.py::test_add_tool -v
#
# Run with markers:
#   uv run pytest tests/ -m "not skip" -v
