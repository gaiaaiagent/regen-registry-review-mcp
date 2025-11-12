#!/usr/bin/env python3
"""
Read-Only API MCP Server Example

Demonstrates connecting to external APIs with:
- HTTP client in lifespan context
- Async tool implementation
- Error handling and retries
- Caching for performance
- Input validation with Pydantic

This server provides read-only access to a weather API.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import logging
import sys

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from mcp.types import ToolError
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class LocationInput(BaseModel):
    """Validated location input."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")


@dataclass
class AppContext:
    """Application context with HTTP client and cache."""
    http_client: httpx.AsyncClient
    cache: dict
    api_base_url: str


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Manage HTTP client lifecycle."""
    logger.info("Initializing HTTP client")

    http_client = httpx.AsyncClient(
        timeout=30.0,
        headers={"User-Agent": "MCP-Weather-Server/1.0"}
    )

    context = AppContext(
        http_client=http_client,
        cache={},
        api_base_url="https://api.weather.gov"
    )

    try:
        yield context
    finally:
        logger.info("Closing HTTP client")
        await http_client.aclose()


# Initialize server
mcp = FastMCP("weather-api", lifespan=app_lifespan)


# ============================================================================
# TOOLS
# ============================================================================

@mcp.tool()
async def get_forecast(
    location: LocationInput,
    ctx: Context[ServerSession, AppContext]
) -> dict:
    """Get weather forecast for a location.

    Fetches 7-day forecast from National Weather Service API.
    Results are cached for 30 minutes to reduce API load.

    Args:
        location: Latitude and longitude coordinates

    Returns:
        Weather forecast with periods, temperatures, and conditions
    """
    http_client = ctx.request_context.lifespan_context.http_client
    cache = ctx.request_context.lifespan_context.cache
    api_base = ctx.request_context.lifespan_context.api_base_url

    await ctx.info(f"Getting forecast for ({location.latitude}, {location.longitude})")

    # Check cache
    cache_key = f"forecast:{location.latitude}:{location.longitude}"
    if cache_key in cache:
        cached_data, cached_time = cache[cache_key]
        if datetime.now() - cached_time < timedelta(minutes=30):
            await ctx.info("Returning cached forecast")
            return cached_data

    # Fetch with retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Step 1: Get grid point
            points_url = f"{api_base}/points/{location.latitude},{location.longitude}"
            points_response = await http_client.get(points_url)
            points_response.raise_for_status()
            points_data = points_response.json()

            # Step 2: Get forecast
            forecast_url = points_data["properties"]["forecast"]
            forecast_response = await http_client.get(forecast_url)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            # Cache result
            cache[cache_key] = (forecast_data, datetime.now())

            # Limit cache size
            if len(cache) > 100:
                oldest_key = min(cache.items(), key=lambda x: x[1][1])[0]
                del cache[oldest_key]

            await ctx.info("Forecast retrieved successfully")
            return forecast_data

        except httpx.HTTPError as e:
            if attempt == max_retries - 1:
                await ctx.error(f"Failed after {max_retries} attempts")
                logger.error(f"HTTP error for {points_url}", exc_info=True)
                raise ToolError(f"Unable to fetch forecast: {str(e)}")

            delay = 2 ** attempt
            await ctx.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s")
            await asyncio.sleep(delay)


@mcp.tool()
async def get_current_conditions(
    location: LocationInput,
    ctx: Context[ServerSession, AppContext]
) -> dict:
    """Get current weather conditions for a location.

    Args:
        location: Latitude and longitude coordinates

    Returns:
        Current temperature, humidity, wind speed, and conditions
    """
    http_client = ctx.request_context.lifespan_context.http_client
    api_base = ctx.request_context.lifespan_context.api_base_url

    await ctx.info("Fetching current conditions")

    try:
        # Get grid point
        points_url = f"{api_base}/points/{location.latitude},{location.longitude}"
        points_response = await http_client.get(points_url)
        points_response.raise_for_status()
        points_data = points_response.json()

        # Get observation stations
        stations_url = points_data["properties"]["observationStations"]
        stations_response = await http_client.get(stations_url)
        stations_response.raise_for_status()
        stations_data = stations_response.json()

        # Get latest observation from first station
        if stations_data["features"]:
            station_id = stations_data["features"][0]["id"]
            obs_url = f"{station_id}/observations/latest"
            obs_response = await http_client.get(obs_url)
            obs_response.raise_for_status()

            await ctx.info("Current conditions retrieved")
            return obs_response.json()
        else:
            raise ToolError("No observation stations found for this location")

    except httpx.HTTPError as e:
        await ctx.error(f"Error fetching conditions: {e}")
        logger.error("HTTP error in get_current_conditions", exc_info=True)
        raise ToolError(f"Unable to fetch current conditions: {str(e)}")


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("cache://stats")
def cache_stats(ctx: Context[ServerSession, AppContext]) -> dict:
    """Get cache statistics.

    Returns:
        Cache size and hit rate information
    """
    cache = ctx.request_context.lifespan_context.cache
    return {
        "entries": len(cache),
        "max_size": 100,
        "keys": list(cache.keys())[:10]
    }


@mcp.resource("status://health")
async def health_check(ctx: Context[ServerSession, AppContext]) -> dict:
    """Server health check.

    Returns:
        Health status and connectivity
    """
    http_client = ctx.request_context.lifespan_context.http_client
    api_base = ctx.request_context.lifespan_context.api_base_url

    try:
        # Quick connectivity test
        response = await http_client.get(f"{api_base}/", timeout=5.0)
        api_healthy = response.status_code == 200
    except:
        api_healthy = False

    return {
        "status": "healthy" if api_healthy else "degraded",
        "api_connectivity": api_healthy,
        "cache_enabled": True
    }


# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt()
def weather_analysis(location_name: str) -> str:
    """Generate prompt for weather analysis.

    Args:
        location_name: Name of the location to analyze

    Returns:
        Prompt template for comprehensive weather analysis
    """
    return f"""Analyze the weather for {location_name}:

1. Get current conditions using get_current_conditions tool
2. Get 7-day forecast using get_forecast tool
3. Summarize key weather patterns
4. Identify any concerning conditions
5. Provide recommendations for outdoor activities

Present the analysis in a clear, concise format."""


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting weather API MCP server")
    mcp.run()
