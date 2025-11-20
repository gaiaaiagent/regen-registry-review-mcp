# Registry Review MCP - Testing Makefile
# Provides convenient shortcuts for different test tiers

.PHONY: help test smoke fast full parallel watch changed coverage clean

# Default target
help:
	@echo "Registry Review MCP - Test Targets"
	@echo "===================================="
	@echo ""
	@echo "Quick Testing:"
	@echo "  make smoke      - Run smoke tests (< 1s target)"
	@echo "  make fast       - Run fast unit tests (< 5s target)"
	@echo "  make full       - Run full test suite (< 40s)"
	@echo "  make parallel   - Run full suite in parallel (< 15s)"
	@echo ""
	@echo "Development:"
	@echo "  make watch      - Watch mode: auto-run smoke tests on changes"
	@echo "  make changed    - Run tests for changed files only"
	@echo ""
	@echo "Quality:"
	@echo "  make coverage   - Run tests with coverage report"
	@echo "  make clean      - Clean test artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  make smoke      # Quick validation"
	@echo "  make watch      # Continuous testing"
	@echo "  make changed    # Before commit"
	@echo "  make parallel   # Full validation"

# Smoke tests: Critical path validation (< 1s)
smoke:
	@echo "🚀 Running smoke tests..."
	pytest -m smoke -v

# Fast tests: Unit tests without I/O (< 5s)
fast:
	@echo "⚡ Running fast tests..."
	pytest -m "not slow and not integration and not expensive and not marker" -v

# Full test suite (default filters applied)
full:
	@echo "🔍 Running full test suite..."
	pytest tests/ -v

# Parallel execution for faster full runs
parallel:
	@echo "⚡ Running tests in parallel..."
	pytest tests/ -n auto -v

# Watch mode: continuous testing (requires pytest-watch)
watch:
	@echo "👀 Starting watch mode (Ctrl+C to stop)..."
	@command -v ptw >/dev/null 2>&1 || { echo "Installing pytest-watch..."; pip install pytest-watch; }
	ptw -- -m smoke -v

# Run tests for changed files only (requires pytest-picked)
changed:
	@echo "📝 Running tests for changed files..."
	@command -v pytest >/dev/null 2>&1 || { echo "Error: pytest not installed"; exit 1; }
	pytest --picked -n auto -v 2>/dev/null || pytest --picked -v

# Coverage report
coverage:
	@echo "📊 Running tests with coverage..."
	pytest tests/ -n auto --cov=src/registry_review_mcp --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated: htmlcov/index.html"
	@command -v open >/dev/null 2>&1 && open htmlcov/index.html || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open htmlcov/index.html || \
	echo "Open htmlcov/index.html in your browser"

# Clean test artifacts
clean:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -f test_costs_report.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Clean complete"

# Aliases for common typos
test: full
tests: full
unit: fast
quick: smoke
ci: parallel
