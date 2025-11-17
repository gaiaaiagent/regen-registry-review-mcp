"""
Citation verification for LLM-extracted fields.

Prevents hallucination by verifying that extracted claims actually exist
in the source documents using fuzzy text matching.
"""

import logging
from pathlib import Path
from rapidfuzz import fuzz
from typing import Any

logger = logging.getLogger(__name__)


def verify_citation(
    raw_text: str,
    source_content: str,
    field_type: str,
    min_similarity: float = 75.0,
) -> tuple[bool, float, str]:
    """
    Verify that a claimed raw_text citation actually exists in source content.

    Uses fuzzy matching to account for OCR errors, formatting differences,
    and minor variations while still catching hallucinations.

    Args:
        raw_text: The text the LLM claims was extracted (e.g., "Project Start Date: 01/01/2022")
        source_content: The actual source document content
        field_type: Type of field being verified (for logging)
        min_similarity: Minimum fuzzy match score (0-100) to consider verified

    Returns:
        Tuple of (is_verified, best_match_score, best_match_snippet)

    Example:
        >>> verify_citation(
        ...     "Project Start Date: 01/01/2022",
        ...     "...Project Start Date: 01/01/2022...",
        ...     "project_start_date"
        ... )
        (True, 100.0, "Project Start Date: 01/01/2022")
    """
    if not raw_text or not source_content:
        return (False, 0.0, "")

    # Normalize for comparison
    raw_text_normalized = raw_text.strip().lower()

    # Try exact match first (fastest)
    if raw_text_normalized in source_content.lower():
        return (True, 100.0, raw_text)

    # Try fuzzy matching on sliding windows
    # Window size = raw_text length ± 50% to account for context
    window_size = int(len(raw_text) * 1.5)
    step_size = max(1, len(raw_text) // 4)

    best_score = 0.0
    best_snippet = ""

    source_lower = source_content.lower()

    for i in range(0, len(source_content) - window_size + 1, step_size):
        window = source_content[i:i + window_size]
        window_lower = source_lower[i:i + window_size]

        # Use token_set_ratio to handle word order differences
        score = fuzz.token_set_ratio(raw_text_normalized, window_lower)

        if score > best_score:
            best_score = score
            best_snippet = window.strip()

    is_verified = best_score >= min_similarity

    if not is_verified:
        logger.warning(
            f"Citation verification failed for {field_type}: "
            f"claimed='{raw_text[:100]}...', best_match_score={best_score:.1f}%"
        )

    return (is_verified, best_score, best_snippet)


def verify_extracted_field(
    field: dict[str, Any],
    source_content: str,
    min_confidence_penalty: float = 0.3,
    min_similarity: float = 75.0,
) -> dict[str, Any]:
    """
    Verify an extracted field's citation and adjust confidence if needed.

    Args:
        field: ExtractedField dict with keys: value, field_type, source, confidence, reasoning, raw_text
        source_content: Full source document content
        min_confidence_penalty: Penalty to apply if verification fails
        min_similarity: Minimum fuzzy match score to consider verified

    Returns:
        Modified field dict with updated confidence and verification metadata
    """
    raw_text = field.get("raw_text")
    field_type = field.get("field_type", "unknown")
    original_confidence = field.get("confidence", 0.0)

    if not raw_text:
        # No raw_text to verify - reduce confidence significantly
        logger.warning(
            f"No raw_text provided for {field_type}={field.get('value')} - "
            f"reducing confidence from {original_confidence:.2f} to {original_confidence * 0.5:.2f}"
        )
        field["confidence"] = original_confidence * 0.5
        field["verification_status"] = "no_citation"
        field["verification_score"] = 0.0
        return field

    # Verify the citation
    is_verified, match_score, best_snippet = verify_citation(
        raw_text, source_content, field_type, min_similarity
    )

    # Update field with verification results
    field["verification_status"] = "verified" if is_verified else "failed"
    field["verification_score"] = match_score
    field["best_match_snippet"] = best_snippet if best_snippet else None

    if not is_verified:
        # Penalize confidence for unverified claims
        new_confidence = max(0.0, original_confidence - min_confidence_penalty)
        logger.warning(
            f"Unverified citation for {field_type}={field.get('value')}: "
            f"confidence reduced from {original_confidence:.2f} to {new_confidence:.2f}"
        )
        field["confidence"] = new_confidence
        field["verification_warning"] = (
            f"Could not verify claimed text '{raw_text[:50]}...' in source document "
            f"(best match: {match_score:.1f}%)"
        )

    return field


def verify_date_extraction(
    extracted_fields: list[dict[str, Any]],
    source_content: str,
) -> list[dict[str, Any]]:
    """
    Verify all extracted date fields against source content.

    Wrapper around verify_extracted_field for batch processing.

    Args:
        extracted_fields: List of ExtractedField dicts
        source_content: Full source document content

    Returns:
        List of verified fields with updated confidence scores
    """
    verified_fields = []

    for field in extracted_fields:
        verified_field = verify_extracted_field(field, source_content)
        verified_fields.append(verified_field)

    # Log summary
    total = len(verified_fields)
    verified_count = sum(1 for f in verified_fields if f.get("verification_status") == "verified")
    failed_count = total - verified_count

    if failed_count > 0:
        logger.warning(
            f"Citation verification: {verified_count}/{total} verified, {failed_count} failed"
        )
    else:
        logger.info(f"Citation verification: all {total} fields verified")

    return verified_fields
