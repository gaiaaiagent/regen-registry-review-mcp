# Multi-stage Dockerfile for MCP Server
# Optimized for UV package manager with layer caching

# ============================================================================
# Builder Stage: Install dependencies
# ============================================================================
FROM ghcr.io/astral-sh/uv:python3.11-alpine AS builder

WORKDIR /app

# Copy dependency manifests first (for layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies with frozen lockfile
# --frozen ensures exact versions from lockfile
# --no-dev excludes development dependencies
RUN uv sync --frozen --no-dev

# Copy application source code
COPY src/ ./src/

# ============================================================================
# Runtime Stage: Minimal production image
# ============================================================================
FROM python:3.11-alpine

WORKDIR /app

# Create non-root user for security
RUN adduser -D -h /app mcpuser && \
    chown -R mcpuser:mcpuser /app

# Copy virtual environment from builder
COPY --from=builder --chown=mcpuser:mcpuser /app/.venv /app/.venv

# Copy application source
COPY --from=builder --chown=mcpuser:mcpuser /app/src /app/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Switch to non-root user
USER mcpuser

# Health check (adjust port/endpoint for your server)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"  # Replace with actual health check

# Expose port if using HTTP transport
# EXPOSE 8000

# Run the MCP server
CMD ["python", "-m", "mcp_server"]

# ============================================================================
# Build and Run Instructions
# ============================================================================
#
# Build image:
#   docker build -t mcp-server:latest .
#
# Run container:
#   docker run -d \
#     --name mcp-server \
#     -p 8000:8000 \
#     -e API_KEY=your-api-key \
#     -e LOG_LEVEL=info \
#     mcp-server:latest
#
# Run with docker-compose:
#   See docker-compose.yml example below
#
# Debug container:
#   docker run -it --rm mcp-server:latest sh
#
# View logs:
#   docker logs -f mcp-server
#
# ============================================================================
# docker-compose.yml Example
# ============================================================================
#
# version: '3.8'
#
# services:
#   mcp-server:
#     build: .
#     image: mcp-server:latest
#     container_name: mcp-server
#     restart: unless-stopped
#     ports:
#       - "8000:8000"
#     environment:
#       - API_KEY=${API_KEY}
#       - LOG_LEVEL=info
#       - DATABASE_URL=postgresql://user:pass@db:5432/dbname
#     depends_on:
#       - db
#     networks:
#       - mcp-network
#
#   db:
#     image: postgres:15-alpine
#     container_name: mcp-db
#     restart: unless-stopped
#     environment:
#       - POSTGRES_USER=user
#       - POSTGRES_PASSWORD=pass
#       - POSTGRES_DB=dbname
#     volumes:
#       - postgres-data:/var/lib/postgresql/data
#     networks:
#       - mcp-network
#
# volumes:
#   postgres-data:
#
# networks:
#   mcp-network:
#     driver: bridge
#
# ============================================================================
# Production Best Practices
# ============================================================================
#
# 1. Use multi-stage builds to reduce image size
# 2. Run as non-root user for security
# 3. Set UV environment variables for optimization
# 4. Use .dockerignore to exclude unnecessary files
# 5. Pin Python and base image versions
# 6. Implement proper health checks
# 7. Use environment variables for configuration
# 8. Enable bytecode compilation with UV_COMPILE_BYTECODE=1
# 9. Use --frozen flag to ensure reproducible builds
# 10. Layer caching: copy dependency files before source code
#
# ============================================================================
# .dockerignore Example
# ============================================================================
#
# __pycache__/
# *.py[cod]
# *$py.class
# .venv/
# .pytest_cache/
# .coverage
# .mypy_cache/
# .ruff_cache/
# tests/
# docs/
# *.md
# .git/
# .gitignore
# .env
# .DS_Store
