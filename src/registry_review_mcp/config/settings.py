"""Configuration management for Registry Review MCP.

Centralized settings with environment variable support and validation.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="REGISTRY_REVIEW_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    # Paths
    data_dir: Path = Field(default_factory=lambda: Path.cwd() / "data")
    checklists_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "checklists")
    sessions_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "sessions")
    cache_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "cache")

    # Session
    session_lock_timeout: int = 30  # seconds
    session_auto_save: bool = True

    # Document Processing
    max_pdf_pages: int = 500
    pdf_cache_ttl: int = 86400  # 24 hours in seconds
    max_concurrent_extractions: int = 5

    # Evidence Extraction
    evidence_snippet_context: int = 100  # words before/after match
    min_confidence_threshold: float = 0.5
    keyword_search_fuzzy: bool = True
    fuzzy_match_threshold: float = 0.8

    # Validation
    date_alignment_max_delta_days: int = 120  # 4 months
    land_tenure_fuzzy_match: bool = True
    project_id_min_occurrences: int = 3

    # Performance
    enable_caching: bool = True
    cache_compression: bool = True

    def __init__(self, **kwargs):
        """Initialize settings and create required directories."""
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        for dir_path in [self.data_dir, self.checklists_dir, self.sessions_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_checklist_path(self, methodology: str) -> Path:
        """Get the path to a checklist file."""
        return self.checklists_dir / f"{methodology}.json"

    def get_session_path(self, session_id: str) -> Path:
        """Get the path to a session directory."""
        return self.sessions_dir / session_id

    def get_cache_path(self, cache_key: str) -> Path:
        """Get the path to a cached file."""
        return self.cache_dir / f"{cache_key}.cache"


# Global settings instance
settings = Settings()
