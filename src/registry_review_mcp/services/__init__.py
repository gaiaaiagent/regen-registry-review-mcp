"""Services layer for document processing orchestration.

This module provides interface-agnostic services that can be used by both
the MCP server and REST API. The key service is DocumentProcessor which
orchestrates dual-track PDF extraction (fast + high-quality).
"""

from .document_processor import DocumentProcessor, get_conversion_status
from .background_jobs import JobManager, get_job_manager

__all__ = [
    "DocumentProcessor",
    "get_conversion_status",
    "JobManager",
    "get_job_manager",
]
