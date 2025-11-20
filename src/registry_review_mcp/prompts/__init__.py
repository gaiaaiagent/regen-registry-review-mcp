"""Prompts module - 8-stage workflow."""

from . import (
    A_initialize,
    B_document_discovery,
    C_requirement_mapping,
    D_evidence_extraction,
    E_cross_validation,
    F_report_generation,
    G_human_review,
    H_completion,
)

__all__ = [
    "A_initialize",
    "B_document_discovery",
    "C_requirement_mapping",
    "D_evidence_extraction",
    "E_cross_validation",
    "F_report_generation",
    "G_human_review",
    "H_completion",
]
