#!/usr/bin/env python3
"""
CLI Alternative to MCP Server

Demonstrates building a CLI tool instead of MCP server for:
- Internal tools you control
- Context efficiency (progressive disclosure)
- Portability across agent systems
- Team + agent + personal usage (the trifecta)

This is the SAME functionality as readonly-api.py but as a CLI.
Compare the two approaches to understand the tradeoffs.

Requirements:
    uv add click httpx

Usage:
    # By you (human)
    uv run python cli-alternative.py forecast --lat 40.7 --lon -74.0

    # By your team (humans)
    uv run python cli-alternative.py --help

    # By agents (with prime prompt)
    # Agent reads this file + README, then calls CLI directly
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta

import click
import httpx


# ============================================================================
# CLI CONFIGURATION
# ============================================================================

# Cache for API responses
CACHE = {}
CACHE_TTL = timedelta(minutes=30)
API_BASE = "https://api.weather.gov"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log(message: str, level: str = "INFO"):
    """Log to stderr (never stdout - keeps output clean for agents)."""
    print(f"[{level}] {message}", file=sys.stderr)


async def fetch_with_cache(url: str, http_client: httpx.AsyncClient) -> dict:
    """Fetch URL with caching."""
    now = datetime.now()

    # Check cache
    if url in CACHE:
        data, cached_time = CACHE[url]
        if now - cached_time < CACHE_TTL:
            log(f"Cache hit: {url}", "DEBUG")
            return data

    # Fetch fresh
    log(f"Fetching: {url}", "DEBUG")
    response = await http_client.get(url)
    response.raise_for_status()
    data = response.json()

    # Cache result
    CACHE[url] = (data, now)

    return data


# ============================================================================
# CLI COMMANDS
# ============================================================================

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """Weather data CLI tool.

    Example usage:
        python cli-alternative.py forecast --lat 40.7 --lon -74.0
        python cli-alternative.py current --lat 40.7 --lon -74.0
        python cli-alternative.py --help
    """
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug


@cli.command()
@click.option('--lat', type=float, required=True, help='Latitude (-90 to 90)')
@click.option('--lon', type=float, required=True, help='Longitude (-180 to 180)')
@click.option('--format', type=click.Choice(['json', 'text']), default='json', help='Output format')
@click.pass_context
def forecast(ctx, lat: float, lon: float, format: str):
    """Get 7-day weather forecast for location.

    Returns forecast with periods, temperatures, and conditions.
    Results cached for 30 minutes.
    """
    if ctx.obj.get('DEBUG'):
        log(f"Getting forecast for ({lat}, {lon})", "DEBUG")

    async def _fetch_forecast():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Get grid point
            points_url = f"{API_BASE}/points/{lat},{lon}"
            points_data = await fetch_with_cache(points_url, client)

            # Step 2: Get forecast
            forecast_url = points_data["properties"]["forecast"]
            forecast_data = await fetch_with_cache(forecast_url, client)

            return forecast_data

    try:
        result = asyncio.run(_fetch_forecast())

        if format == 'json':
            # Output JSON to stdout (agents parse this)
            print(json.dumps(result, indent=2))
        else:
            # Human-readable text format
            print(f"Forecast for ({lat}, {lon}):")
            for period in result["properties"]["periods"][:3]:
                print(f"\n{period['name']}:")
                print(f"  Temperature: {period['temperature']}°{period['temperatureUnit']}")
                print(f"  Conditions: {period['shortForecast']}")

    except Exception as e:
        log(f"Error: {e}", "ERROR")
        sys.exit(1)


@cli.command()
@click.option('--lat', type=float, required=True, help='Latitude (-90 to 90)')
@click.option('--lon', type=float, required=True, help='Longitude (-180 to 180)')
@click.option('--format', type=click.Choice(['json', 'text']), default='json', help='Output format')
@click.pass_context
def current(ctx, lat: float, lon: float, format: str):
    """Get current weather conditions for location.

    Returns current temperature, humidity, wind speed, and conditions.
    """
    if ctx.obj.get('DEBUG'):
        log(f"Getting current conditions for ({lat}, {lon})", "DEBUG")

    async def _fetch_current():
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get grid point
            points_url = f"{API_BASE}/points/{lat},{lon}"
            points_data = await fetch_with_cache(points_url, client)

            # Get observation stations
            stations_url = points_data["properties"]["observationStations"]
            stations_data = await fetch_with_cache(stations_url, client)

            # Get latest observation
            if not stations_data["features"]:
                raise Exception("No observation stations found")

            station_id = stations_data["features"][0]["id"]
            obs_url = f"{station_id}/observations/latest"
            obs_data = await fetch_with_cache(obs_url, client)

            return obs_data

    try:
        result = asyncio.run(_fetch_current())

        if format == 'json':
            print(json.dumps(result, indent=2))
        else:
            props = result["properties"]
            print(f"Current conditions for ({lat}, {lon}):")
            print(f"  Temperature: {props['temperature']['value']}°C")
            print(f"  Humidity: {props['relativeHumidity']['value']}%")
            print(f"  Wind Speed: {props['windSpeed']['value']} m/s")
            print(f"  Conditions: {props['textDescription']}")

    except Exception as e:
        log(f"Error: {e}", "ERROR")
        sys.exit(1)


@cli.command()
def cache_stats():
    """Show cache statistics."""
    print(json.dumps({
        "entries": len(CACHE),
        "keys": list(CACHE.keys())[:10]
    }, indent=2))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    cli(obj={})


# ============================================================================
# COMPARISON: CLI vs MCP
# ============================================================================

"""
CONTEXT USAGE:
- MCP Server: 10,000 tokens (5-10%) - Loads all tools on startup
- CLI Approach: 2,000 tokens (1-2%) - Agent reads this file + README as needed

INVOCATION:
- MCP Server: Agent-triggered automatically
- CLI Approach: Agent calls via bash after reading docs

PORTABILITY:
- MCP Server: MCP ecosystem only
- CLI Approach: Any agent system with bash access

TEAM USAGE:
- MCP Server: Agents only (humans need MCP client)
- CLI Approach: You + team + agents (the trifecta)

WHEN TO USE CLI:
1. Building internal tools (you control the code)
2. Want it usable by humans AND agents
3. Context efficiency matters (>3 MCP servers)
4. Want portability across agent systems
5. Comfortable with prime prompts

WHEN TO USE MCP:
1. External services (GitHub, Slack, PostgreSQL)
2. Using community servers (don't reinvent wheel)
3. Simplicity > context efficiency (<3 servers)
4. Want automatic agent triggering
5. Multi-agent scale (3+ agents using it)

UPGRADE PATH:
- Start with CLI (80% case for internal tools)
- Wrap with MCP if you need multi-agent scale (10% case)
- Keep both: CLI for you/team, MCP for agents

RECOMMENDED WORKFLOW:
1. Build CLI first (this file is the template)
2. Create prime prompt (see prime-weather-cli.md example)
3. Test with agents via prime prompt
4. Wrap with MCP only if needed (rarely needed)

See checklists/mcp-vs-alternatives.md for complete decision tree.
"""
