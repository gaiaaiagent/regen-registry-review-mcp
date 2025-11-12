#!/usr/bin/env python3
"""
Advanced MCP Server Template

Production-ready MCP server demonstrating:
- Lifecycle management with async context managers
- Type-safe context access
- Error handling and retry logic
- Progress reporting
- Connection pooling patterns
- Structured logging

Usage:
    uv run python advanced-server.py
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional
import asyncio
import logging
import sys
import httpx

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from mcp.types import ToolError
from pydantic import BaseModel, Field

# Configure structured logging to stderr
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class QueryParams(BaseModel):
    """Type-safe query parameters with validation."""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    timeout: int = Field(default=30, ge=1, le=300)


@dataclass
class AppContext:
    """Application-wide context available to all tools."""
    http_client: httpx.AsyncClient
    cache: dict
    config: dict


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Manage application lifecycle with proper startup/shutdown.

    This context manager:
    - Initializes resources on startup
    - Provides them to tools via context
    - Ensures cleanup on shutdown
    """
    logger.info("Starting application lifecycle")

    # Startup: Initialize resources
    http_client = httpx.AsyncClient(timeout=30.0)
    cache = {}
    config = {
        "max_retries": 3,
        "cache_ttl": 300,
        "api_base_url": "https://api.example.com"
    }

    context = AppContext(
        http_client=http_client,
        cache=cache,
        config=config
    )

    try:
        yield context
    finally:
        # Shutdown: Cleanup resources
        logger.info("Shutting down application")
        await http_client.aclose()


# Initialize server with lifespan
mcp = FastMCP("advanced-server", lifespan=app_lifespan, mask_error_details=True)


# ============================================================================
# TOOLS WITH CONTEXT ACCESS
# ============================================================================

@mcp.tool()
async def fetch_data(
    url: str,
    ctx: Context[ServerSession, AppContext]
) -> dict:
    """Fetch data from external API with retry logic.

    Args:
        url: URL to fetch
        ctx: Server context with HTTP client access

    Returns:
        Fetched data as dictionary
    """
    # Access lifespan context
    http_client = ctx.request_context.lifespan_context.http_client
    config = ctx.request_context.lifespan_context.config

    await ctx.info(f"Fetching: {url}")

    # Retry with exponential backoff
    max_retries = config["max_retries"]

    for attempt in range(max_retries):
        try:
            response = await http_client.get(url)
            response.raise_for_status()

            await ctx.info("Fetch successful")
            return response.json()

        except httpx.HTTPError as e:
            if attempt == max_retries - 1:
                await ctx.error(f"All retries failed: {e}")
                logger.error(f"HTTP error for {url}", exc_info=True)
                raise ToolError(f"Failed to fetch {url}: {str(e)}")

            delay = 2 ** attempt
            await ctx.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
            await asyncio.sleep(delay)


@mcp.tool()
async def process_batch(
    items: list[str],
    ctx: Context[ServerSession, AppContext]
) -> dict:
    """Process multiple items with progress reporting.

    Args:
        items: List of items to process
        ctx: Server context for progress reporting

    Returns:
        Processing results summary
    """
    await ctx.info(f"Processing {len(items)} items")

    total = len(items)
    results = []

    for i, item in enumerate(items):
        # Report progress
        await ctx.report_progress(
            progress=(i + 1) / total,
            total=1.0,
            message=f"Processing item {i + 1}/{total}"
        )

        # Simulate processing
        await asyncio.sleep(0.1)
        results.append({"item": item, "status": "processed"})

    await ctx.info("Batch processing complete")

    return {
        "total": total,
        "processed": len(results),
        "results": results
    }


@mcp.tool()
async def cached_query(
    params: QueryParams,
    ctx: Context[ServerSession, AppContext]
) -> dict:
    """Query with caching support.

    Args:
        params: Query parameters (validated by Pydantic)
        ctx: Server context with cache access

    Returns:
        Query results (cached or fresh)
    """
    cache = ctx.request_context.lifespan_context.cache
    config = ctx.request_context.lifespan_context.config

    # Check cache
    cache_key = f"query:{params.query}:{params.limit}"

    if cache_key in cache:
        await ctx.info("Cache hit")
        return cache[cache_key]

    # Cache miss - fetch fresh data
    await ctx.info("Cache miss - fetching fresh data")

    # Simulate query
    await asyncio.sleep(0.5)
    result = {
        "query": params.query,
        "results": [f"result_{i}" for i in range(params.limit)],
        "cached": False
    }

    # Store in cache
    cache[cache_key] = result

    # Implement simple cache size limit
    if len(cache) > 100:
        oldest_key = next(iter(cache))
        del cache[oldest_key]

    return result


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("cache://stats")
def cache_statistics(ctx: Context[ServerSession, AppContext]) -> dict:
    """Get cache statistics.

    Returns:
        Cache metrics
    """
    cache = ctx.request_context.lifespan_context.cache

    return {
        "entries": len(cache),
        "max_size": 100,
        "keys": list(cache.keys())[:10]  # First 10 keys
    }


@mcp.resource("config://current")
def current_config(ctx: Context[ServerSession, AppContext]) -> dict:
    """Get current server configuration.

    Returns:
        Configuration dictionary
    """
    return ctx.request_context.lifespan_context.config


# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt()
def analyze_prompt(dataset: str) -> str:
    """Generate analysis prompt template.

    Args:
        dataset: Dataset to analyze

    Returns:
        Analysis prompt
    """
    return f"""Analyze the following dataset: {dataset}

Please provide:
1. Data quality assessment
2. Statistical summary
3. Key insights
4. Recommendations

Use the available tools to fetch and process the data."""


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting advanced MCP server with lifecycle management")
    mcp.run()
