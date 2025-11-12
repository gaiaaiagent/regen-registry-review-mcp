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


@pytest.fixture
def example_documents_path():
    """Get path to example documents.

    Returns:
        Absolute path to examples/22-23 directory
    """
    return (Path(__file__).parent.parent / "examples" / "22-23").absolute()
