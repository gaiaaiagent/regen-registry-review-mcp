"""Caching utilities for PDF extraction and other expensive operations."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from ..config.settings import settings


class Cache:
    """Simple file-based cache with TTL support."""

    def __init__(self, namespace: str = "default"):
        """Initialize cache with namespace.

        Args:
            namespace: Logical grouping for cache entries
        """
        self.namespace = namespace
        self.cache_dir = settings.cache_dir / namespace
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, key: str) -> str:
        """Generate a cache key hash.

        Args:
            key: Original cache key

        Returns:
            SHA256 hash of the key
        """
        return hashlib.sha256(f"{self.namespace}:{key}".encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for a cache key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.json"

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache.

        Args:
            key: Cache key
            default: Value to return if not found or expired

        Returns:
            Cached value or default
        """
        if not settings.enable_caching:
            return default

        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return default

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check TTL
            if cache_data.get("ttl"):
                expires_at = cache_data["cached_at"] + cache_data["ttl"]
                if time.time() > expires_at:
                    # Expired, remove file
                    cache_path.unlink(missing_ok=True)
                    return default

            return cache_data["value"]

        except (json.JSONDecodeError, KeyError, OSError):
            # Corrupted cache file, remove it
            cache_path.unlink(missing_ok=True)
            return default

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (None = use default from settings)
        """
        if not settings.enable_caching:
            return

        ttl = ttl or settings.pdf_cache_ttl
        cache_path = self._get_cache_path(key)

        cache_data = {
            "key": key,
            "value": value,
            "cached_at": time.time(),
            "ttl": ttl,
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, default=str)

    def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key
        """
        cache_path = self._get_cache_path(key)
        cache_path.unlink(missing_ok=True)

    def clear(self) -> int:
        """Clear all cache entries in this namespace.

        Returns:
            Number of entries cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count

    def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists and not expired, False otherwise
        """
        return self.get(key) is not None


# Global cache instances
pdf_cache = Cache("pdf_extraction")
gis_cache = Cache("gis_metadata")
