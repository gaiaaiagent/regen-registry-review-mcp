"""Pytest configuration and shared fixtures."""

import pytest
import pytest_asyncio
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

from registry_review_mcp.config.settings import settings, Settings
from registry_review_mcp.extractors.llm_extractors import (
    DateExtractor,
    LandTenureExtractor,
    ProjectIDExtractor,
)


# Global cost tracker for aggregating all test costs
_test_suite_costs = {
    'total_cost': 0.0,
    'total_calls': 0,
    'total_input_tokens': 0,
    'total_output_tokens': 0,
    'cached_calls': 0,
    'by_test': {},
    'start_time': None,
    'end_time': None,
}


def pytest_configure(config):
    """Called before test session starts."""
    _test_suite_costs['start_time'] = datetime.now()

    # Register custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow (real API calls)")
    config.addinivalue_line("markers", "expensive: marks tests with high API costs")


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished."""
    _test_suite_costs['end_time'] = datetime.now()

    # Aggregate costs from all /tmp test tracking files
    cost_files = list(Path('/tmp').glob('test_*.json'))

    if not cost_files:
        return

    for file in cost_files:
        try:
            with open(file) as f:
                data = json.load(f)
                _test_suite_costs['total_cost'] += data.get('total_cost_usd', 0.0)
                _test_suite_costs['total_calls'] += data.get('total_api_calls', 0)
                _test_suite_costs['total_input_tokens'] += data.get('total_input_tokens', 0)
                _test_suite_costs['total_output_tokens'] += data.get('total_output_tokens', 0)

                # Count cached calls
                api_calls = data.get('api_calls', [])
                _test_suite_costs['cached_calls'] += sum(1 for call in api_calls if call.get('cached', False))

                # Track by test
                session_id = data.get('session_id', file.stem)
                _test_suite_costs['by_test'][session_id] = {
                    'cost': data.get('total_cost_usd', 0.0),
                    'calls': data.get('total_api_calls', 0),
                }
        except Exception:
            pass

    # Print summary if we have costs
    if _test_suite_costs['total_calls'] > 0:
        print("\n" + "=" * 80)
        print("API COST SUMMARY")
        print("=" * 80)
        print(f"Total API Calls: {_test_suite_costs['total_calls']:,}")
        print(f"  - Real API calls: {_test_suite_costs['total_calls'] - _test_suite_costs['cached_calls']:,}")
        print(f"  - Cached calls: {_test_suite_costs['cached_calls']:,}")
        print(f"Total Tokens: {_test_suite_costs['total_input_tokens'] + _test_suite_costs['total_output_tokens']:,}")
        print(f"  - Input: {_test_suite_costs['total_input_tokens']:,}")
        print(f"  - Output: {_test_suite_costs['total_output_tokens']:,}")
        print(f"Total Cost: ${_test_suite_costs['total_cost']:.4f}")

        if _test_suite_costs['total_calls'] > 0:
            cache_rate = _test_suite_costs['cached_calls'] / _test_suite_costs['total_calls'] * 100
            print(f"Cache Hit Rate: {cache_rate:.1f}%")

        duration = (_test_suite_costs['end_time'] - _test_suite_costs['start_time']).total_seconds()
        print(f"Test Duration: {duration:.1f}s")
        print("=" * 80)

        # Save to file for later analysis
        report_path = Path('test_costs_report.json')
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': _test_suite_costs['start_time'].isoformat(),
                'duration_seconds': duration,
                'total_cost_usd': _test_suite_costs['total_cost'],
                'total_api_calls': _test_suite_costs['total_calls'],
                'cached_calls': _test_suite_costs['cached_calls'],
                'total_input_tokens': _test_suite_costs['total_input_tokens'],
                'total_output_tokens': _test_suite_costs['total_output_tokens'],
                'by_test': _test_suite_costs['by_test'],
            }, f, indent=2, default=str)

        print(f"\nDetailed cost report saved to: test_costs_report.json")
        print(f"For analysis, run: python scripts/analyze_test_costs.py\n")


# =============================================================================
# Shared Test Fixtures (Cost Optimization)
# =============================================================================


@pytest.fixture(scope="session")
def botany_farm_markdown():
    """Load Botany Farm Project Plan markdown once for all tests.

    Returns the first 20K chars to match what individual tests use.
    """
    project_plan_path = Path("examples/22-23/4997Botany22_Public_Project_Plan/4997Botany22_Public_Project_Plan.md")

    if not project_plan_path.exists():
        pytest.skip("Botany Farm Project Plan not found")

    with open(project_plan_path) as f:
        markdown = f.read()

    # Return first 20K chars (matching what tests use)
    return markdown[:20000]


@pytest_asyncio.fixture(scope="function")
async def botany_farm_dates(botany_farm_markdown):
    """Extract dates from Botany Farm once and share across tests.

    Requires API key and LLM extraction to be enabled.
    """
    if not settings.anthropic_api_key or not settings.llm_extraction_enabled:
        pytest.skip("LLM extraction not configured")

    extractor = DateExtractor()
    results = await extractor.extract(
        botany_farm_markdown,
        [],
        "Botany_Farm_Project_Plan"
    )
    return results


@pytest_asyncio.fixture(scope="function")
async def botany_farm_tenure(botany_farm_markdown):
    """Extract land tenure from Botany Farm once and share across tests.

    Requires API key and LLM extraction to be enabled.
    """
    if not settings.anthropic_api_key or not settings.llm_extraction_enabled:
        pytest.skip("LLM extraction not configured")

    extractor = LandTenureExtractor()
    results = await extractor.extract(
        botany_farm_markdown,
        [],
        "Botany_Farm_Project_Plan"
    )
    return results


@pytest_asyncio.fixture(scope="function")
async def botany_farm_project_ids(botany_farm_markdown):
    """Extract project IDs from Botany Farm once and share across tests.

    Requires API key and LLM extraction to be enabled.
    """
    if not settings.anthropic_api_key or not settings.llm_extraction_enabled:
        pytest.skip("LLM extraction not configured")

    extractor = ProjectIDExtractor()
    results = await extractor.extract(
        botany_farm_markdown,
        [],
        "Botany_Farm_Project_Plan"
    )
    return results


# =============================================================================
# Original Test Fixtures (Required by existing tests)
# =============================================================================


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for tests.

    Args:
        tmp_path: Pytest temporary directory fixture

    Yields:
        Path to temporary data directory
    """
    data_dir = tmp_path / "test_data"
    data_dir.mkdir(parents=True)

    # Create subdirectories
    (data_dir / "checklists").mkdir()
    (data_dir / "sessions").mkdir()
    (data_dir / "cache").mkdir()

    yield data_dir

    # Cleanup
    shutil.rmtree(data_dir, ignore_errors=True)


@pytest.fixture
def test_settings(temp_data_dir):
    """Create test settings with temporary directories.

    Args:
        temp_data_dir: Temporary data directory fixture

    Returns:
        Settings instance for testing
    """
    return Settings(
        data_dir=temp_data_dir,
        checklists_dir=temp_data_dir / "checklists",
        sessions_dir=temp_data_dir / "sessions",
        cache_dir=temp_data_dir / "cache",
        enable_caching=True,
    )


@pytest.fixture(scope="session", autouse=True)
def cleanup_cache_once():
    """Clean cache once at the start of the test session.

    This prevents test pollution from previous runs while avoiding
    repeated cleanup operations.
    """
    from registry_review_mcp.utils.cache import Cache

    # Clean the default cache directory
    cache = Cache("test_cleanup")
    cache.clear()

    yield  # Run all tests

    # Optional: Clean up after tests (commented out to preserve for inspection)
    # cache.clear()


@pytest.fixture
def cache(test_settings):
    """Create a cache instance for testing.

    Args:
        test_settings: Test settings fixture

    Returns:
        Cache instance
    """
    from registry_review_mcp.utils.cache import Cache

    return Cache("test", cache_dir=test_settings.cache_dir)


@pytest.fixture(autouse=True, scope="function")
def cleanup_sessions():
    """Clean up TEST sessions before and after each test.

    CRITICAL: Only removes sessions that are DEFINITELY from tests:
    - Sessions with names starting with "test-"
    - Sessions pointing to /tmp/pytest directories (pytest temp dirs)
    - Corrupted session files (likely failed tests)

    PRESERVES:
    - Sessions pointing to examples/ (user might be manually testing)
    - Sessions pointing to real project directories outside the repo
    - Any session that might be from actual MCP server usage

    NOTE: Tests that use examples/ directory should use the separate
    `cleanup_examples_sessions` fixture to clean up after themselves.
    """
    data_dir = Path(__file__).parent.parent / "data"
    sessions_dir = data_dir / "sessions"

    def cleanup_test_sessions():
        """Remove ONLY definitively test-created sessions."""
        if not sessions_dir.exists():
            return

        for session_path in sessions_dir.iterdir():
            if not session_path.is_dir():
                continue

            # Delete test-* sessions (explicitly test-prefixed)
            if session_path.name.startswith("test-"):
                shutil.rmtree(session_path, ignore_errors=True)
                continue

            # Check if session points to pytest temp directory
            try:
                session_file = session_path / "session.json"
                if session_file.exists():
                    with open(session_file) as f:
                        session_data = json.load(f)
                        docs_path_str = session_data.get("project_metadata", {}).get("documents_path", "")
                        if docs_path_str:
                            # ONLY delete if pointing to /tmp/pytest-*
                            # (definitively a pytest temp directory)
                            if "/tmp/pytest-" in docs_path_str or "/tmp/pytest_" in docs_path_str:
                                shutil.rmtree(session_path, ignore_errors=True)
                                continue
            except Exception:
                # If we can't read the session or it's corrupted, delete it
                # (likely a failed test)
                shutil.rmtree(session_path, ignore_errors=True)

    # Cleanup before test
    cleanup_test_sessions()

    yield  # Run the test

    # Cleanup after test
    cleanup_test_sessions()


@pytest.fixture(scope="function")
def cleanup_examples_sessions():
    """Clean up sessions pointing to examples directory.

    Use this fixture explicitly in tests that use the examples/ directory
    to ensure they don't leave sessions behind.

    This is separate from the autouse cleanup_sessions to preserve user
    sessions that might be manually testing with examples.
    """
    data_dir = Path(__file__).parent.parent / "data"
    sessions_dir = data_dir / "sessions"
    examples_dir = (Path(__file__).parent.parent / "examples").resolve()

    def cleanup_examples():
        """Remove sessions pointing to examples directory."""
        if not sessions_dir.exists():
            return

        for session_path in sessions_dir.iterdir():
            if not session_path.is_dir():
                continue

            try:
                session_file = session_path / "session.json"
                if session_file.exists():
                    with open(session_file) as f:
                        session_data = json.load(f)
                        docs_path_str = session_data.get("project_metadata", {}).get("documents_path", "")
                        if docs_path_str:
                            try:
                                docs_path = Path(docs_path_str).resolve()
                                docs_path.relative_to(examples_dir)
                                # This session uses examples - delete it
                                shutil.rmtree(session_path, ignore_errors=True)
                            except (ValueError, OSError):
                                # Not under examples or path doesn't exist
                                pass
            except Exception:
                # Can't read session - skip it
                pass

    # Cleanup before test
    cleanup_examples()

    yield  # Run the test

    # Cleanup after test
    cleanup_examples()


@pytest.fixture
def example_documents_path():
    """Get path to example documents.

    Returns:
        Absolute path to examples/22-23 directory
    """
    return (Path(__file__).parent.parent / "examples" / "22-23").absolute()
