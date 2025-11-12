"""Pytest configuration and fixtures for Registry Review MCP tests."""

import pytest
import shutil
from pathlib import Path
import tempfile

from registry_review_mcp.config.settings import Settings


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

    This is needed because Cache uses the global settings object.

    TODO: Refactor Cache to accept Settings instance for proper test isolation.
    """
    data_dir = Path(__file__).parent.parent / "data"
    cache_dir = data_dir / "cache"

    # Clean up cache before test session starts
    if cache_dir.exists():
        for item in cache_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)

    yield

    # Clean up cache after all tests complete
    if cache_dir.exists():
        for item in cache_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def cleanup_sessions():
    """Clean up sessions before and after each test.

    This is needed because StateManager uses the global settings object,
    so test data gets written to the real data/ directory instead of tmp.

    TODO: Refactor StateManager to accept Settings instance for proper test isolation.
    """
    data_dir = Path(__file__).parent.parent / "data"
    sessions_dir = data_dir / "sessions"

    def cleanup():
        # Clean up ALL sessions (since we can't distinguish test vs real in current architecture)
        if sessions_dir.exists():
            for item in sessions_dir.iterdir():
                if item.is_dir() and item.name.startswith("session-"):
                    shutil.rmtree(item, ignore_errors=True)

    # Clean up before test
    cleanup()

    yield

    # Clean up after test
    cleanup()


@pytest.fixture
def example_documents_path():
    """Get path to example documents.

    Returns:
        Absolute path to examples/22-23 directory
    """
    return (Path(__file__).parent.parent / "examples" / "22-23").absolute()
