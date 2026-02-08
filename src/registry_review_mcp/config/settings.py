"""Configuration management for Registry Review MCP.

Centralized settings with environment variable support and validation.
Uses XDG Base Directory Specification for production data isolation.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_xdg_data_home() -> Path:
    """Get XDG data directory for persistent application data.

    Returns $XDG_DATA_HOME if set, otherwise ~/.local/share (XDG default).
    Production sessions and checklists are stored here.
    """
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))


def _get_xdg_cache_home() -> Path:
    """Get XDG cache directory for non-essential cached data.

    Returns $XDG_CACHE_HOME if set, otherwise ~/.cache (XDG default).
    PDF extraction cache and LLM response cache are stored here.
    """
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))


def _get_project_root() -> Path:
    """Get the project root directory based on this file's location.

    Used for accessing bundled resources like default checklists.
    Path: config/settings.py → registry_review_mcp → src → project_root
    """
    return Path(__file__).resolve().parent.parent.parent.parent


# Application identifier for XDG directories
APP_NAME = "registry-review-mcp"


class Settings(BaseSettings):
    """Application settings with environment variable support.

    IMMUTABLE AFTER INITIALIZATION: Settings are frozen after __init__ completes.
    Any attempt to modify settings at runtime will raise TypeError. This prevents
    the class of bugs where test code accidentally modifies the global settings
    singleton, which caused production data loss on 2025-12-03.

    Data Storage (XDG Standard):
    - Sessions: ~/.local/share/registry-review-mcp/sessions/
    - Cache: ~/.cache/registry-review-mcp/

    This ensures production data is structurally isolated from the codebase,
    preventing tests from accidentally deleting production sessions.

    Override via environment variables:
    - REGISTRY_REVIEW_SESSIONS_DIR=/custom/path
    - REGISTRY_REVIEW_CACHE_DIR=/custom/path
    """

    model_config = SettingsConfigDict(
        env_prefix="REGISTRY_REVIEW_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    # Paths - XDG Standard for production data isolation
    # Sessions and persistent data go to XDG_DATA_HOME (~/.local/share/)
    # Cache goes to XDG_CACHE_HOME (~/.cache/)
    # Can be overridden via REGISTRY_REVIEW_*_DIR environment variables.
    data_dir: Path = Field(default_factory=lambda: _get_xdg_data_home() / APP_NAME)
    sessions_dir: Path = Field(default_factory=lambda: _get_xdg_data_home() / APP_NAME / "sessions")
    cache_dir: Path = Field(default_factory=lambda: _get_xdg_cache_home() / APP_NAME)

    # Checklists are bundled with the package, read from project directory
    checklists_dir: Path = Field(default_factory=lambda: _get_project_root() / "data" / "checklists")

    # Session
    session_lock_timeout: int = 30  # seconds

    # Document Processing
    pdf_cache_ttl: int = 86400  # 24 hours in seconds

    # Validation
    land_tenure_fuzzy_match: bool = True

    # LLM Extraction (Phase 4.2)
    anthropic_api_key: str = Field(default="")
    llm_extraction_enabled: bool = Field(default=False)  # Conservative default
    llm_backend: Literal["auto", "api", "cli"] = Field(default="auto")

    # Environment-aware model selection (2025-11-26)
    # Dev: Haiku 4.5 ($1/$5 per 1M tokens) - 5x cheaper for testing
    # Production: Sonnet 4.5 ($3/$15 per 1M tokens) - higher quality
    environment: Literal["development", "production"] = Field(default="development")
    llm_model: str = Field(default="")  # Auto-selected based on environment if empty
    llm_model_dev: str = Field(default="claude-haiku-4-5-20251001")  # Haiku 4.5
    llm_model_prod: str = Field(default="claude-sonnet-4-5-20250929")  # Sonnet 4.5

    llm_max_tokens: int = Field(default=4000, ge=1, le=8000)
    llm_temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    llm_max_input_chars: int = Field(default=100000, ge=1000)  # ~25K tokens, configurable
    llm_enable_chunking: bool = Field(default=True)  # Process long docs in chunks
    llm_chunk_size: int = Field(default=80000, ge=10000)  # ~20K tokens per chunk
    llm_chunk_overlap: int = Field(default=2000, ge=0)  # Overlap to avoid missing boundary content
    llm_max_images_per_call: int = Field(default=20, ge=1)  # Max images per API call (cost consideration)
    llm_warn_image_threshold: int = Field(default=10, ge=1)  # Warn when exceeding this many images

    # LLM Response Caching (2025-11-26)
    # Cache LLM responses locally to avoid redundant API calls during development
    llm_cache_enabled: bool = Field(default=True)  # Enable local response caching
    llm_cache_dir: Path = Field(default_factory=lambda: _get_xdg_cache_home() / APP_NAME / "llm")
    llm_cache_ttl: int = Field(default=604800)  # 7 days in seconds

    # Cost Management
    api_call_timeout_seconds: int = Field(default=30, ge=5, le=120)

    # Performance
    enable_caching: bool = True

    # Session Monitoring (for REST API)
    monitor_sessions: bool = False

    def __init__(self, **kwargs):
        """Initialize settings and create required directories.

        After initialization completes, the settings instance is frozen
        and any attempt to modify attributes will raise TypeError.
        """
        super().__init__(**kwargs)
        self._ensure_directories()
        # Freeze settings after initialization
        object.__setattr__(self, '_frozen', True)

    def __setattr__(self, name: str, value) -> None:
        """Prevent modification of settings after initialization.

        This is a critical security measure: the data loss incident of 2025-12-03
        was caused by test fixtures modifying the global settings singleton. By
        making settings immutable, we structurally prevent this class of bugs.

        Raises:
            TypeError: If attempting to modify a frozen settings instance
        """
        if getattr(self, '_frozen', False) and name != '_frozen':
            raise TypeError(
                f"Settings are immutable. Cannot modify '{name}' after initialization. "
                f"Use environment variables to configure settings."
            )
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        """Prevent deletion of settings attributes."""
        if getattr(self, '_frozen', False):
            raise TypeError("Settings are immutable. Cannot delete attributes.")
        super().__delattr__(name)

    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        for dir_path in [self.data_dir, self.checklists_dir, self.sessions_dir, self.cache_dir, self.llm_cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_active_llm_model(self) -> str:
        """Get the active LLM model based on environment.

        Returns:
            Model ID string for API calls

        Logic:
            1. If llm_model is explicitly set, use it (override)
            2. Otherwise, auto-select based on environment:
               - development → Haiku 4.5 (5x cheaper)
               - production → Sonnet 4.5 (higher quality)
        """
        if self.llm_model:
            return self.llm_model

        return self.llm_model_dev if self.environment == "development" else self.llm_model_prod

    def get_checklist_path(self, methodology: str) -> Path:
        """Get the path to a checklist file."""
        return self.checklists_dir / f"{methodology}.json"

    def get_session_path(self, session_id: str) -> Path:
        """Get the path to a session directory."""
        return self.sessions_dir / session_id

    def get_cache_path(self, cache_key: str) -> Path:
        """Get the path to a cached file."""
        return self.cache_dir / f"{cache_key}.cache"

    def get_llm_cache_path(self, cache_key: str) -> Path:
        """Get the path to a cached LLM response.

        Args:
            cache_key: Hash of (requirement_id, document_content, model)

        Returns:
            Path to cached response JSON file
        """
        return self.llm_cache_dir / f"{cache_key}.json"


# Global settings instance
settings = Settings()
