#!/usr/bin/env python3
"""
Database MCP Server Example

Production-ready database integration demonstrating:
- SQLAlchemy with async engine
- Connection pooling
- Transaction management
- Parameterized queries (SQL injection prevention)
- Error handling

This server provides tools for database operations with PostgreSQL.

Requirements:
    uv add "mcp[cli]" sqlalchemy asyncpg psycopg2-binary
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional
import logging
import sys

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text
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

class QueryParams(BaseModel):
    """Safe query parameters with validation."""
    sql: str = Field(..., min_length=1, max_length=5000)
    params: Optional[dict] = None
    limit: int = Field(default=100, ge=1, le=1000)


@dataclass
class AppContext:
    """Application context with database engine."""
    engine: AsyncEngine
    connection_pool_size: int


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Manage database connection pool lifecycle."""
    logger.info("Initializing database connection pool")

    # NOTE: Replace with your actual database URL
    # Format: postgresql+asyncpg://user:password@host:port/database
    DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/mydb"

    # Create async engine with connection pooling
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=20,          # Max connections in pool
        max_overflow=10,       # Additional connections if pool exhausted
        pool_pre_ping=True,    # Verify connections before use
        echo=False,            # Set to True for SQL query logging
        pool_recycle=3600,     # Recycle connections after 1 hour
    )

    context = AppContext(
        engine=engine,
        connection_pool_size=20
    )

    try:
        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection pool ready")

        yield context

    finally:
        logger.info("Closing database connection pool")
        await engine.dispose()


# Initialize server
mcp = FastMCP("database-server", lifespan=app_lifespan)


# ============================================================================
# TOOLS
# ============================================================================

@mcp.tool()
async def query_database(
    params: QueryParams,
    ctx: Context[ServerSession, AppContext]
) -> dict:
    """Execute a SELECT query against the database.

    SECURITY: Only SELECT queries allowed. Uses parameterized queries
    to prevent SQL injection. Results are limited to protect memory.

    Args:
        params: Query parameters with SQL and optional bind params

    Returns:
        Query results as list of dictionaries
    """
    engine = ctx.request_context.lifespan_context.engine

    await ctx.info(f"Executing query (limit: {params.limit})")

    # Security: Validate query is SELECT only
    sql_upper = params.sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        raise ToolError("Only SELECT queries are allowed")

    # Security: Block dangerous keywords
    dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
    if any(keyword in sql_upper for keyword in dangerous):
        raise ToolError(f"Query contains forbidden keywords: {dangerous}")

    try:
        async with engine.begin() as conn:
            # Add LIMIT clause for safety
            query = text(f"{params.sql} LIMIT :limit")

            # Execute with parameters (prevents SQL injection)
            result = await conn.execute(
                query,
                {**(params.params or {}), "limit": params.limit}
            )

            # Fetch results
            rows = result.mappings().all()

            await ctx.info(f"Query returned {len(rows)} rows")

            return {
                "rows": [dict(row) for row in rows],
                "count": len(rows),
                "limited": len(rows) == params.limit
            }

    except Exception as e:
        await ctx.error(f"Query failed: {e}")
        logger.error("Database query error", exc_info=True)
        raise ToolError(f"Database query failed: {str(e)}")


@mcp.tool()
async def get_table_schema(
    table_name: str,
    ctx: Context[ServerSession, AppContext]
) -> dict:
    """Get schema information for a database table.

    Args:
        table_name: Name of the table to describe

    Returns:
        Table schema with column names, types, and constraints
    """
    engine = ctx.request_context.lifespan_context.engine

    await ctx.info(f"Getting schema for table: {table_name}")

    # Security: Validate table name (prevent SQL injection)
    if not table_name.replace("_", "").isalnum():
        raise ToolError("Invalid table name: only alphanumeric and underscore allowed")

    try:
        async with engine.begin() as conn:
            # Query information schema
            query = text("""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """)

            result = await conn.execute(query, {"table_name": table_name})
            columns = result.mappings().all()

            if not columns:
                raise ToolError(f"Table '{table_name}' not found")

            await ctx.info(f"Found {len(columns)} columns")

            return {
                "table_name": table_name,
                "columns": [dict(col) for col in columns],
                "column_count": len(columns)
            }

    except ToolError:
        raise
    except Exception as e:
        await ctx.error(f"Schema query failed: {e}")
        logger.error("Schema query error", exc_info=True)
        raise ToolError(f"Failed to get table schema: {str(e)}")


@mcp.tool()
async def list_tables(
    ctx: Context[ServerSession, AppContext]
) -> dict:
    """List all tables in the database.

    Returns:
        List of table names
    """
    engine = ctx.request_context.lifespan_context.engine

    await ctx.info("Listing all tables")

    try:
        async with engine.begin() as conn:
            query = text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            result = await conn.execute(query)
            tables = result.scalars().all()

            await ctx.info(f"Found {len(tables)} tables")

            return {
                "tables": list(tables),
                "count": len(tables)
            }

    except Exception as e:
        await ctx.error(f"Failed to list tables: {e}")
        logger.error("List tables error", exc_info=True)
        raise ToolError(f"Failed to list tables: {str(e)}")


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("pool://stats")
def connection_pool_stats(ctx: Context[ServerSession, AppContext]) -> dict:
    """Get connection pool statistics.

    Returns:
        Pool size, checked out connections, and overflow
    """
    engine = ctx.request_context.lifespan_context.engine
    pool = engine.pool

    return {
        "pool_size": ctx.request_context.lifespan_context.connection_pool_size,
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "size": pool.size(),
        "status": "healthy" if pool.checkedout() < pool.size() else "high_load"
    }


@mcp.resource("status://health")
async def health_check(ctx: Context[ServerSession, AppContext]) -> dict:
    """Database health check.

    Returns:
        Health status and connectivity
    """
    engine = ctx.request_context.lifespan_context.engine

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()

        return {
            "status": "healthy",
            "database": "connected",
            "pool": "operational"
        }
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt()
def data_analysis(table_name: str) -> str:
    """Generate prompt for database data analysis.

    Args:
        table_name: Table to analyze

    Returns:
        Analysis workflow prompt
    """
    return f"""Analyze data in table: {table_name}

Steps:
1. Use get_table_schema to understand table structure
2. Use query_database to get sample data (LIMIT 10)
3. Use query_database to get summary statistics:
   - Row count: SELECT COUNT(*) FROM {table_name}
   - Distinct values for key columns
   - Min/max for numeric columns
4. Identify data quality issues
5. Provide insights and recommendations

Present findings in a structured format."""


@mcp.prompt()
def explore_database() -> str:
    """Generate prompt for database exploration.

    Returns:
        Database exploration workflow
    """
    return """Explore this database systematically:

1. Use list_tables to see all available tables
2. For each table:
   - Use get_table_schema to understand structure
   - Use query_database to preview data (LIMIT 5)
3. Identify relationships between tables
4. Summarize database purpose and structure

Present as organized overview with key findings."""


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting database MCP server")
    logger.info("NOTE: Update DATABASE_URL in app_lifespan before use")
    mcp.run()
