"""Three-layer validation architecture for Registry Review MCP.

Layer 1 (structural): Rule-based checks on individual fields - always runs
Layer 2 (cross_document): Comparison across multiple documents - conditional
Layer 3 (llm_synthesis): Holistic LLM assessment - single call

The coordinator orchestrates all layers and produces ValidationResult.
"""

from .coordinator import validate_session
from .structural import run_structural_checks
from .cross_document import run_cross_document_checks
from .llm_synthesis import run_llm_synthesis

__all__ = [
    "validate_session",
    "run_structural_checks",
    "run_cross_document_checks",
    "run_llm_synthesis",
]
