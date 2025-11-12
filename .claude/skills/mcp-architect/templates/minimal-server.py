#!/usr/bin/env python3
"""
Minimal MCP Server Template

A basic MCP server demonstrating essential patterns:
- Tool implementation (executable functions)
- Resource exposure (read-only data)
- Prompt templates (conversation starters)

Usage:
    uv run python minimal-server.py
"""

from mcp.server.fastmcp import FastMCP
import logging
import sys

# Configure logging to stderr (CRITICAL: never stdout)
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create server instance
mcp = FastMCP("minimal-server")


# ============================================================================
# TOOLS - Functions that can be called by LLMs
# ============================================================================

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    logger.info(f"Adding {a} + {b}")
    return a + b


@mcp.tool()
def greet(name: str) -> str:
    """Generate a friendly greeting.

    Args:
        name: Name to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}! Welcome to the MCP server."


# ============================================================================
# RESOURCES - Data that can be accessed by LLMs
# ============================================================================

@mcp.resource("config://settings")
def get_settings() -> dict:
    """Get server configuration settings.

    Returns:
        Configuration dictionary
    """
    return {
        "version": "1.0.0",
        "environment": "development",
        "features": ["tools", "resources", "prompts"]
    }


@mcp.resource("status://health")
def health_check() -> str:
    """Server health status.

    Returns:
        Health status message
    """
    return "Server is operational"


# ============================================================================
# PROMPTS - Reusable conversation templates
# ============================================================================

@mcp.prompt()
def welcome_prompt() -> str:
    """Generate a welcome prompt for new users.

    Returns:
        Welcome message with instructions
    """
    return """Welcome to this MCP server!

I can help you with:
1. Mathematical operations (use the 'add' tool)
2. Friendly greetings (use the 'greet' tool)
3. Server configuration (check the 'config://settings' resource)

What would you like to do?"""


@mcp.prompt()
def help_prompt(topic: str) -> str:
    """Generate a help prompt for specific topics.

    Args:
        topic: Topic to get help with

    Returns:
        Contextual help message
    """
    return f"""Help for: {topic}

Available tools:
- add(a, b): Add two numbers
- greet(name): Generate greeting

Available resources:
- config://settings: Server configuration
- status://health: Health check

For more information, ask specific questions!"""


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting minimal MCP server")
    mcp.run()  # Uses stdio transport by default
