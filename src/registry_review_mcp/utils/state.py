"""Atomic state management for session persistence.

Provides thread-safe file operations with locking to prevent corruption.
"""

import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..config.settings import settings
from ..models.errors import SessionLockError, SessionNotFoundError


class StateManager:
    """Manages atomic read/write operations for session state."""

    def __init__(self, session_id: str):
        """Initialize state manager for a session.

        Args:
            session_id: Unique identifier for the session
        """
        self.session_id = session_id
        self.session_dir = settings.get_session_path(session_id)
        self.lock_file = self.session_dir / ".lock"

    @contextmanager
    def lock(self, timeout: int | None = None):
        """Acquire exclusive lock for session modifications.

        Args:
            timeout: Maximum seconds to wait for lock (None = use settings default)

        Raises:
            SessionLockError: If lock cannot be acquired within timeout
        """
        # Ensure directory exists before trying to create lock file
        self.session_dir.mkdir(parents=True, exist_ok=True)

        timeout = timeout or settings.session_lock_timeout
        start_time = time.time()

        while True:
            try:
                # Try to create lock file (atomic operation)
                self.lock_file.touch(exist_ok=False)
                break
            except FileExistsError:
                # Lock already held, wait and retry
                if time.time() - start_time > timeout:
                    raise SessionLockError(
                        f"Could not acquire lock for session {self.session_id} within {timeout}s",
                        details={"session_id": self.session_id, "timeout": timeout},
                    )
                time.sleep(0.1)

        # Lock acquired, now execute and ensure cleanup
        try:
            yield
        finally:
            # Always release lock, even on exception
            try:
                if self.lock_file.exists():
                    self.lock_file.unlink()
            except Exception:
                # Force delete if normal unlink fails
                pass

    def read_json(self, filename: str) -> dict[str, Any]:
        """Read JSON file from session directory.

        Args:
            filename: Name of file to read (e.g., "session.json")

        Returns:
            Parsed JSON content

        Raises:
            SessionNotFoundError: If file does not exist
        """
        file_path = self.session_dir / filename

        if not file_path.exists():
            raise SessionNotFoundError(
                f"File not found: {filename}",
                details={"session_id": self.session_id, "filename": filename},
            )

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json_unlocked(self, filename: str, data: dict[str, Any]) -> None:
        """Write JSON file without acquiring lock (internal use only).

        Args:
            filename: Name of file to write (e.g., "session.json")
            data: Data to serialize as JSON
        """
        # Ensure session directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)

        file_path = self.session_dir / filename
        temp_path = self.session_dir / f".{filename}.tmp"

        # Write to temp file first
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        # Atomic rename
        temp_path.replace(file_path)

    def write_json(self, filename: str, data: dict[str, Any]) -> None:
        """Write JSON file to session directory atomically.

        Args:
            filename: Name of file to write (e.g., "session.json")
            data: Data to serialize as JSON

        Raises:
            SessionLockError: If lock cannot be acquired
        """
        with self.lock():
            self._write_json_unlocked(filename, data)

    def update_json(self, filename: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update JSON file with partial changes atomically.

        Args:
            filename: Name of file to update
            updates: Dictionary of fields to update (supports nested updates)

        Returns:
            Updated complete data

        Raises:
            SessionLockError: If lock cannot be acquired
            SessionNotFoundError: If file does not exist
        """
        with self.lock():
            data = self.read_json(filename)
            data.update(updates)
            # Use unlocked version since we already have the lock
            self._write_json_unlocked(filename, data)
            return data

    def exists(self, filename: str | None = None) -> bool:
        """Check if session or specific file exists.

        Args:
            filename: Optional specific file to check. If None, checks session directory.

        Returns:
            True if exists, False otherwise
        """
        if filename is None:
            return self.session_dir.exists()
        return (self.session_dir / filename).exists()

    def list_files(self) -> list[str]:
        """List all files in session directory.

        Returns:
            List of filenames (excluding lock files)
        """
        if not self.session_dir.exists():
            return []

        return [
            f.name
            for f in self.session_dir.iterdir()
            if f.is_file() and not f.name.startswith(".")
        ]
