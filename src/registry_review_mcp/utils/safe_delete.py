"""Safe deletion utilities to prevent accidental data loss.

This module provides deletion functions that refuse to delete production paths,
serving as a defense-in-depth layer against test-induced data loss.

The data loss incident of 2025-12-03 taught us: behavioral defenses (fixtures that
modify settings) can fail silently. Structural defenses (refusing to delete certain
paths) cannot be bypassed by import path errors.
"""

import shutil
from pathlib import Path


class UnsafeDeleteError(Exception):
    """Raised when attempting to delete a protected path."""

    pass


# Paths that ARE safe to delete (allowlist approach)
# Note: /private/tmp/ and /private/var are included for macOS where /tmp is a symlink
# and pytest creates temp dirs in /var/folders/
SAFE_PATH_PREFIXES = (
    "/tmp/",
    "/var/tmp/",
    "/var/folders/",
    "/private/tmp/",
    "/private/var/",
)


def is_safe_to_delete(path: Path) -> bool:
    """Check if a path is safe to delete.

    Uses an allowlist approach: only explicitly safe paths can be deleted.
    Everything else is considered production data.

    Args:
        path: Path to check

    Returns:
        True if path is in a safe location (/tmp/, /var/tmp/)
    """
    path = path.resolve()
    path_str = str(path)

    # Only /tmp paths are safe to delete
    for prefix in SAFE_PATH_PREFIXES:
        if path_str.startswith(prefix):
            return True

    return False


def safe_rmtree(path: Path, force: bool = False) -> None:
    """Delete a directory tree, refusing if it's a production path.

    This function provides defense-in-depth: even if test isolation fails
    and code attempts to delete production data, this guard will prevent it.

    Args:
        path: Directory to delete
        force: If True, skip safety checks (DANGEROUS - only for explicit cleanup scripts)

    Raises:
        UnsafeDeleteError: If path is not in /tmp/ and force=False
    """
    path = Path(path).resolve()

    if not force and not is_safe_to_delete(path):
        raise UnsafeDeleteError(
            f"REFUSED: Cannot delete '{path}' - not in safe location (/tmp/). "
            f"This path appears to be production data. "
            f"If this is intentional, use force=True or delete manually."
        )

    if path.exists():
        shutil.rmtree(path)


def safe_unlink(path: Path, force: bool = False) -> None:
    """Delete a file, refusing if it's in a production path.

    Args:
        path: File to delete
        force: If True, skip safety checks

    Raises:
        UnsafeDeleteError: If path is not in /tmp/ and force=False
    """
    path = Path(path).resolve()

    if not force and not is_safe_to_delete(path):
        raise UnsafeDeleteError(
            f"REFUSED: Cannot delete '{path}' - not in safe location (/tmp/). "
            f"This file appears to be production data."
        )

    if path.exists():
        path.unlink()
