"""Test locking mechanism in isolation."""

import pytest
import time
from pathlib import Path

from registry_review_mcp.utils.state import StateManager


class TestLockingMechanism:
    """Focused tests for the lock mechanism."""

    def test_basic_lock_acquisition_and_release(self, test_settings):
        """Test that a lock can be acquired and released."""
        manager = StateManager("session-bb0000000001")

        # Should be able to acquire lock
        with manager.lock():
            assert manager.lock_file.exists(), "Lock file should exist while locked"

        # Lock should be released after context
        assert not manager.lock_file.exists(), "Lock file should be deleted after release"

    def test_lock_prevents_concurrent_access(self, test_settings):
        """Test that lock actually prevents concurrent access."""
        manager = StateManager("session-bb0000000002")

        # Acquire lock
        with manager.lock():
            # Try to acquire again - should fail quickly
            manager2 = StateManager("session-bb0000000002")
            with pytest.raises(Exception) as exc_info:
                with manager2.lock(timeout=1):  # Short timeout
                    pass

            assert "lock" in str(exc_info.value).lower()

    def test_write_json_alone(self, test_settings):
        """Test that write_json works and releases lock."""
        manager = StateManager("session-bb0000000003")

        data = {"test": "value"}
        manager.write_json("test.json", data)

        # Lock should be released
        assert not manager.lock_file.exists(), "Lock should be released after write"

        # Should be able to write again immediately
        data2 = {"test": "value2"}
        manager.write_json("test.json", data2)

        assert not manager.lock_file.exists()

    def test_update_json_critical_bug(self, test_settings):
        """Test the critical bug: update_json calling write_json while holding lock."""
        manager = StateManager("session-bb0000000004")

        # Create initial data
        initial = {"count": 0, "status": "pending"}
        manager.write_json("test.json", initial)

        # This is where the bug happens: update_json locks, then calls write_json which tries to lock again
        start = time.time()
        try:
            updated = manager.update_json("test.json", {"count": 1})
            duration = time.time() - start

            # Should complete quickly (< 1 second)
            assert duration < 1.0, f"update_json took {duration}s - likely deadlocked"
            assert updated["count"] == 1
            assert not manager.lock_file.exists(), "Lock should be released"

        except Exception as e:
            duration = time.time() - start
            pytest.fail(f"update_json failed after {duration}s: {e}")
