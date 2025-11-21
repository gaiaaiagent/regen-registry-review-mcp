"""LLM-native analysis implementation.

This module provides a drop-in replacement for:
- evidence_tools.extract_all_evidence()
- validation_tools.cross_validate()
- llm_extractors field extraction

Using a single unified LLM call instead of 100+ separate operations.

Feature flag: settings.use_llm_native_extraction (default: False)
"""

import logging
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic

from ..config.settings import settings
from ..models.errors import SessionNotFoundError, DocumentExtractionError
from ..prompts.unified_analysis import (
    analyze_with_llm,
    UnifiedAnalysisResult
)
from ..utils.state import StateManager, get_session_or_raise

logger = logging.getLogger(__name__)


async def load_all_markdown(session_id: str) -> tuple[list[dict], dict[str, str]]:
    """Load all document metadata and markdown content.

    Args:
        session_id: Session identifier

    Returns:
        Tuple of (documents metadata list, markdown content dict)

    Raises:
        SessionNotFoundError: If session or documents not found
    """
    state_manager = StateManager(session_id)

    if not state_manager.exists("documents.json"):
        raise SessionNotFoundError(
            f"Documents not discovered for session {session_id}",
            details={"session_id": session_id}
        )

    # Load document metadata
    docs_data = state_manager.read_json("documents.json")
    documents = docs_data.get("documents", [])

    # Load markdown content for each document
    markdown_contents = {}

    for doc in documents:
        doc_id = doc["document_id"]

        # Try to get markdown content
        markdown_path = None

        # First: Check if document has markdown_path from discovery
        if doc.get("has_markdown") and doc.get("markdown_path"):
            markdown_path = Path(doc["markdown_path"])

        # Fallback: Try to find markdown manually
        if not markdown_path or not markdown_path.exists():
            pdf_path = Path(doc["filepath"])

            # Try 1: .md next to .pdf
            markdown_path = pdf_path.with_suffix(".md")

            # Try 2: In subdirectory with same name (marker output structure)
            if not markdown_path.exists():
                pdf_stem = pdf_path.stem  # filename without extension
                subdir_path = pdf_path.parent / pdf_stem / f"{pdf_stem}.md"
                if subdir_path.exists():
                    markdown_path = subdir_path

        # Load markdown if found
        if markdown_path and markdown_path.exists():
            markdown_contents[doc_id] = markdown_path.read_text(encoding="utf-8")
        else:
            # No markdown available - log warning but continue
            logger.warning(f"No markdown found for {doc['filename']}")
            markdown_contents[doc_id] = f"[No markdown content available for {doc['filename']}]"

    return documents, markdown_contents


async def analyze_session_unified(session_id: str) -> dict[str, Any]:
    """Perform unified analysis using single LLM call.

    This function replaces the sequential workflow:
    1. evidence_tools.extract_all_evidence()
    2. validation_tools.cross_validate()
    3. Multiple llm_extractors calls

    With a single LLM orchestration that does everything in one pass.

    Args:
        session_id: Session identifier

    Returns:
        Dictionary with:
            - evidence: Evidence extraction results (compatible with evidence.json)
            - validation: Validation results (compatible with validation.json)
            - extracted_fields: Structured field extractions
            - overall_assessment: Quality assessment

    Raises:
        SessionNotFoundError: If session doesn't exist
        DocumentExtractionError: If LLM analysis fails
    """
    logger.info(f"Starting unified LLM analysis for session {session_id}")

    # Load session and documents
    state_manager = StateManager(session_id)
    documents, markdown_contents = await load_all_markdown(session_id)

    # Load checklist
    checklist_path = settings.get_checklist_path("soil-carbon-v1.2.2")
    import json
    with open(checklist_path, "r") as f:
        checklist_data = json.load(f)
    requirements = checklist_data.get("requirements", [])

    logger.info(
        f"Analyzing {len(documents)} documents against {len(requirements)} requirements"
    )

    # Initialize Anthropic client
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Single unified LLM call
    result: UnifiedAnalysisResult = await analyze_with_llm(
        documents=documents,
        markdown_contents=markdown_contents,
        requirements=requirements,
        anthropic_client=client
    )

    logger.info(
        f"Analysis complete: {result.requirements_covered}/{len(requirements)} covered"
    )

    # Convert to format compatible with existing system

    # 1. Evidence extraction format (for evidence.json)
    evidence_result = {
        "session_id": session_id,
        "requirements_total": len(requirements),
        "requirements_covered": result.requirements_covered,
        "requirements_partial": result.requirements_partial,
        "requirements_missing": result.requirements_missing,
        "requirements_flagged": 0,  # LLM doesn't use flagged status
        "overall_coverage": result.overall_coverage,
        "evidence": [
            {
                "requirement_id": req_ev.requirement_id,
                "requirement_text": next(
                    (r["requirement_text"] for r in requirements if r["requirement_id"] == req_ev.requirement_id),
                    ""
                ),
                "category": next(
                    (r["category"] for r in requirements if r["requirement_id"] == req_ev.requirement_id),
                    ""
                ),
                "status": req_ev.status,
                "confidence": req_ev.confidence,
                "mapped_documents": [
                    {
                        "document_id": md.document_id,
                        "document_name": md.document_name,
                        "filepath": next(
                            (d["filepath"] for d in documents if d["document_id"] == md.document_id),
                            ""
                        ),
                        "relevance_score": md.relevance_score,
                        "keywords_found": []  # LLM doesn't use keywords
                    }
                    for md in req_ev.mapped_documents
                ],
                "evidence_snippets": [
                    {
                        "text": snip.text,
                        "document_id": req_ev.mapped_documents[0].document_id if req_ev.mapped_documents else "",
                        "document_name": req_ev.mapped_documents[0].document_name if req_ev.mapped_documents else "",
                        "page": snip.page,
                        "section": snip.section,
                        "confidence": snip.confidence,
                        "keywords_matched": []  # LLM doesn't use keywords
                    }
                    for snip in req_ev.evidence_snippets
                ],
                "notes": req_ev.notes
            }
            for req_ev in result.requirements_evidence
        ]
    }

    # 2. Validation format (for validation.json) - matches ValidationResult model schema
    from datetime import datetime, UTC

    validation_result = {
        "session_id": session_id,
        "validated_at": datetime.now(UTC).isoformat(),
        # LLM validation checks - store as generic validations for now
        # (not date/tenure/project_id specific since LLM does unified analysis)
        "date_alignments": [],
        "land_tenure": [],
        "project_ids": [],
        "contradictions": [],
        "validations": {
            check.check_type: {
                "status": check.status,
                "message": check.message,
                "details": check.details or {}
            }
            for check in result.validation_checks
        },
        "summary": {
            "total_validations": len(result.validation_checks),
            "validations_passed": sum(1 for c in result.validation_checks if c.status == "pass"),
            "validations_warning": sum(1 for c in result.validation_checks if c.status == "warning"),
            "validations_failed": sum(1 for c in result.validation_checks if c.status == "fail"),
            "items_flagged": 0,  # LLM ValidationCheck doesn't have flagged_for_review field
            "pass_rate": sum(1 for c in result.validation_checks if c.status == "pass") / len(result.validation_checks) if result.validation_checks else 0.0,
            "extraction_method": "llm"
        },
        "all_passed": all(c.status == "pass" for c in result.validation_checks) if result.validation_checks else True
    }

    # 3. Extracted fields (new format)
    fields_result = {
        field.field_name: {
            "value": field.field_value,
            "source_document": field.source_document,
            "page": field.page,
            "confidence": field.confidence
        }
        for field in result.extracted_fields
    }

    # Save results
    state_manager.write_json("evidence.json", evidence_result)
    state_manager.write_json("validation.json", validation_result)
    state_manager.write_json("extracted_fields.json", fields_result)

    # Update session
    state_manager.update_json(
        "session.json",
        {
            "workflow_progress.evidence_extraction": "completed",
            "workflow_progress.cross_validation": "completed",
            "statistics.requirements_covered": result.requirements_covered,
            "statistics.requirements_partial": result.requirements_partial,
            "statistics.requirements_missing": result.requirements_missing,
        }
    )

    logger.info("Results saved to session state")

    return {
        "evidence": evidence_result,
        "validation": validation_result,
        "extracted_fields": fields_result,
        "overall_assessment": result.overall_assessment,
        "flagged_items": result.flagged_items
    }


async def extract_all_evidence_llm(session_id: str) -> dict[str, Any]:
    """Drop-in replacement for evidence_tools.extract_all_evidence().

    Uses unified LLM analysis instead of keyword-based search.

    Args:
        session_id: Session identifier

    Returns:
        Evidence extraction result (same format as evidence_tools)
    """
    result = await analyze_session_unified(session_id)
    return result["evidence"]


async def cross_validate_llm(session_id: str) -> dict[str, Any]:
    """Drop-in replacement for validation_tools.cross_validate().

    Uses unified LLM analysis instead of separate extraction + validation.

    Args:
        session_id: Session identifier

    Returns:
        Validation result (same format as validation_tools)
    """
    result = await analyze_session_unified(session_id)
    return result["validation"]
