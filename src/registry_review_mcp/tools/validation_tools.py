"""Cross-document validation tools."""

import logging
import re
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from ..config.settings import settings
from ..utils.tool_helpers import generate_validation_id
from ..models.validation import (
    DateField,
    DateAlignmentValidation,
    LandTenureField,
    LandTenureValidation,
    ProjectIDOccurrence,
    ProjectIDValidation,
    ValidationSummary,
    ValidationResult,
)
from ..utils.state import StateManager, get_session_or_raise

logger = logging.getLogger(__name__)


def extract_page_number(source: str) -> int | None:
    """Extract page number from source string.

    Handles formats like:
    - "Document Name, Page 5"
    - "Document Name, p. 5"
    - "Document Name (Page 5)"
    - "Page 5"
    """
    if not source:
        return None

    # Try various page number patterns
    patterns = [
        r'[Pp]age\s+(\d+)',  # "Page 5" or "page 5"
        r'[Pp]\.\s*(\d+)',   # "p. 5"
        r'\((\d+)\)',        # "(5)"
    ]

    for pattern in patterns:
        match = re.search(pattern, source)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue

    return None


async def validate_date_alignment(
    session_id: str,
    field1_name: str,
    field1_value: datetime,
    field1_source: str,
    field2_name: str,
    field2_value: datetime,
    field2_source: str,
    max_delta_days: int = 120
) -> dict[str, Any]:
    """
    Validate that two dates are within acceptable range.

    Args:
        session_id: Session identifier
        field1_name: Name of first date field
        field1_value: First date value
        field1_source: Source citation for first date
        field2_name: Name of second date field
        field2_value: Second date value
        field2_source: Source citation for second date
        max_delta_days: Maximum allowed days between dates

    Returns:
        Validation result dictionary
    """
    # Calculate delta (absolute value)
    delta = abs((field2_value - field1_value).days)

    # Determine status
    if delta <= max_delta_days:
        status = "pass"
        message = f"Dates within acceptable range ({delta} days apart, max {max_delta_days} days)"
        flagged = False
    else:
        status = "fail"
        message = f"Dates exceeds maximum allowed delta ({delta} days apart, max {max_delta_days} days)"
        flagged = True

    # Extract document IDs from sources (format: "DOC-123, Page 5")
    doc1_id = field1_source.split(",")[0].strip()
    doc2_id = field2_source.split(",")[0].strip()

    # Create validation result
    validation = DateAlignmentValidation(
        validation_id=generate_validation_id("date_alignment"),
        validation_type="date_alignment",
        date1=DateField(
            field_name=field1_name,
            value=field1_value,
            source=field1_source,
            document_id=doc1_id,
            confidence=0.95
        ),
        date2=DateField(
            field_name=field2_name,
            value=field2_value,
            source=field2_source,
            document_id=doc2_id,
            confidence=0.95
        ),
        delta_days=delta,
        max_allowed_days=max_delta_days,
        status=status,
        message=message,
        flagged_for_review=flagged
    )

    return validation.model_dump()


async def validate_land_tenure(
    session_id: str,
    fields: list[dict[str, Any]],
    fuzzy_match_threshold: float = 0.8
) -> dict[str, Any]:
    """
    Cross-validate land tenure information from multiple documents.

    Args:
        session_id: Session identifier
        fields: List of land tenure field dictionaries
        fuzzy_match_threshold: Minimum similarity score for fuzzy matching (0.0-1.0)

    Returns:
        Validation result dictionary
    """
    if len(fields) < 2:
        return {
            "validation_id": f"VAL-TENURE-{uuid.uuid4().hex[:8]}",
            "validation_type": "land_tenure",
            "fields": fields,
            "owner_name_match": True,
            "owner_name_similarity": 1.0,
            "area_consistent": True,
            "tenure_type_consistent": True,
            "status": "pass",
            "message": "Only one land tenure record found",
            "discrepancies": [],
            "flagged_for_review": False
        }

    # Convert to Pydantic models
    tenure_fields = [LandTenureField(**f) for f in fields]

    # Check owner name consistency
    owner_names = [f.owner_name for f in tenure_fields]
    unique_names = set(owner_names)

    # Calculate similarity between all name pairs
    if len(unique_names) == 1:
        # Exact match
        owner_name_match = True
        owner_name_similarity = 1.0
        name_status = "exact match"
    else:
        # Use fuzzy matching with enhanced surname checking
        similarities = []
        for i in range(len(owner_names)):
            for j in range(i + 1, len(owner_names)):
                # Calculate string similarity
                similarity = SequenceMatcher(None, owner_names[i].lower(), owner_names[j].lower()).ratio()

                # Check if surnames match (last word in each name)
                name1_parts = owner_names[i].split()
                name2_parts = owner_names[j].split()
                if name1_parts and name2_parts:
                    surname1 = name1_parts[-1].lower()
                    surname2 = name2_parts[-1].lower()
                    surname_match = surname1 == surname2

                    # Boost similarity if surnames match
                    if surname_match and similarity < fuzzy_match_threshold:
                        similarity = max(similarity, fuzzy_match_threshold + 0.05)

                similarities.append(similarity)

        owner_name_similarity = min(similarities) if similarities else 0.0
        owner_name_match = owner_name_similarity >= fuzzy_match_threshold

        if owner_name_similarity >= fuzzy_match_threshold:
            name_status = f"fuzzy match ({owner_name_similarity:.2f} similarity)"
        else:
            name_status = f"mismatch ({owner_name_similarity:.2f} similarity)"

    # Check area consistency (allow small variations, e.g., rounding)
    areas = [f.area_hectares for f in tenure_fields if f.area_hectares is not None]
    if len(areas) > 1:
        max_area = max(areas)
        min_area = min(areas)
        area_variance = (max_area - min_area) / max_area if max_area > 0 else 0
        area_consistent = area_variance < 0.05  # 5% tolerance
    else:
        area_consistent = True

    # Check tenure type consistency
    tenure_types = [f.tenure_type for f in tenure_fields if f.tenure_type is not None]
    tenure_type_consistent = len(set(tenure_types)) <= 1 if tenure_types else True

    # Determine overall status
    discrepancies = []
    if not owner_name_match:
        discrepancies.append(f"Owner names differ: {', '.join(unique_names)}")
    if not area_consistent:
        discrepancies.append(f"Area inconsistent: {min(areas):.2f} ha vs {max(areas):.2f} ha")
    if not tenure_type_consistent:
        discrepancies.append(f"Tenure types differ: {', '.join(set(tenure_types))}")

    if not discrepancies:
        status = "pass"
        message = f"Land tenure consistent across documents ({name_status})"
        flagged = owner_name_similarity < 1.0  # Flag even successful fuzzy matches for review
    elif owner_name_match and area_consistent:
        status = "warning"
        message = f"Minor inconsistencies detected ({name_status})"
        flagged = True
    else:
        status = "fail"
        message = f"Land tenure mismatch: significant discrepancies detected"
        flagged = True

    validation = LandTenureValidation(
        validation_id=generate_validation_id("land_tenure"),
        validation_type="land_tenure",
        fields=tenure_fields,
        owner_name_match=owner_name_match,
        owner_name_similarity=owner_name_similarity,
        area_consistent=area_consistent,
        tenure_type_consistent=tenure_type_consistent,
        status=status,
        message=message,
        discrepancies=discrepancies,
        flagged_for_review=flagged
    )

    return validation.model_dump()


async def validate_project_id(
    session_id: str,
    occurrences: list[dict[str, Any]],
    total_documents: int,
    expected_pattern: str = r"^C\d{2}-\d+$",
    min_occurrences: int = 3
) -> dict[str, Any]:
    """
    Validate project ID consistency across documents.

    Args:
        session_id: Session identifier
        occurrences: List of project ID occurrence dictionaries
        total_documents: Total number of documents in session
        expected_pattern: Regex pattern for valid project IDs
        min_occurrences: Minimum number of occurrences required

    Returns:
        Validation result dictionary
    """
    if not occurrences:
        return {
            "validation_id": f"VAL-PID-{uuid.uuid4().hex[:8]}",
            "validation_type": "project_id",
            "expected_pattern": expected_pattern,
            "found_ids": [],
            "primary_id": None,
            "occurrences": [],
            "total_occurrences": 0,
            "documents_with_id": 0,
            "total_documents": total_documents,
            "status": "fail",
            "message": "No project IDs found in documents",
            "flagged_for_review": True
        }

    # Convert to Pydantic models
    occurrence_models = [ProjectIDOccurrence(**o) for o in occurrences]

    # Extract unique project IDs
    found_ids = list(set(o.project_id for o in occurrence_models))

    # Determine primary ID (most frequent)
    id_counts = {}
    for occurrence in occurrence_models:
        id_counts[occurrence.project_id] = id_counts.get(occurrence.project_id, 0) + 1

    primary_id = max(id_counts, key=id_counts.get) if id_counts else None

    # Count documents with IDs
    documents_with_id = len(set(o.document_id for o in occurrence_models))

    # Validate pattern compliance
    pattern_valid = all(re.match(expected_pattern, pid) for pid in found_ids)

    # Determine status
    issues = []

    if not pattern_valid:
        issues.append(f"Invalid project ID format (expected pattern: {expected_pattern})")

    if len(found_ids) > 1:
        issues.append(f"Multiple project IDs found: {', '.join(found_ids)}")

    if len(occurrence_models) < min_occurrences:
        issues.append(f"Insufficient occurrences ({len(occurrence_models)} found, {min_occurrences} required)")

    if documents_with_id < min_occurrences:
        issues.append(f"Project ID appears in only {documents_with_id}/{total_documents} documents")

    if not issues:
        status = "pass"
        message = f"Project ID {primary_id} consistent across {documents_with_id}/{total_documents} documents"
        flagged = False
    elif len(found_ids) == 1 and pattern_valid:
        status = "warning"
        message = f"Project ID {primary_id} found but with minor issues: {'; '.join(issues)}"
        flagged = True
    else:
        status = "fail"
        message = f"Project ID validation failed: {'; '.join(issues)}"
        flagged = True

    validation = ProjectIDValidation(
        validation_id=generate_validation_id("project_id"),
        validation_type="project_id",
        expected_pattern=expected_pattern,
        found_ids=found_ids,
        primary_id=primary_id,
        occurrences=occurrence_models,
        total_occurrences=len(occurrence_models),
        documents_with_id=documents_with_id,
        total_documents=total_documents,
        status=status,
        message=message,
        flagged_for_review=flagged
    )

    return validation.model_dump()


def extract_structured_fields_from_evidence(evidence_data: dict[str, Any]) -> dict[str, list]:
    """
    Extract pre-extracted structured fields from evidence snippets.

    This function reads structured_fields that were populated during evidence
    extraction (Stage D) by type-aware LLM prompts. These fields are already
    validated and don't need re-extraction via regex.

    Routing is based on FIELD NAMES, not requirement IDs, making the code
    more flexible and less coupled to specific checklist schemas.

    Args:
        evidence_data: Evidence JSON data with structured_fields in snippets

    Returns:
        Dictionary with categorized fields:
        - dates: List of date fields
        - tenure: List of land tenure fields (grouped by document)
        - project_ids: List of project ID occurrences
    """
    # Field name → category routing (decoupled from requirement IDs)
    TENURE_FIELDS = {"owner_name", "area_hectares", "tenure_type"}
    DATE_FIELDS = {
        "project_start_date",
        "crediting_period_start",
        "crediting_period_end",
        "baseline_date",
        "monitoring_date",
    }

    dates = []
    tenure_by_doc: dict[str, dict[str, Any]] = {}  # document_id -> tenure fields
    project_ids = []

    for req in evidence_data.get("evidence", []):
        req_id = req.get("requirement_id", "")

        for snippet in req.get("evidence_snippets", []):
            fields = snippet.get("structured_fields")
            if not fields:
                continue

            doc_id = snippet.get("document_id", "unknown")
            doc_name = snippet.get("document_name", "unknown")
            page = snippet.get("page")
            confidence = snippet.get("confidence", 0.8)

            # Route by field names (not requirement IDs)
            for field_name, field_value in fields.items():
                if field_name in TENURE_FIELDS:
                    # Land tenure fields - group by document for cross-validation
                    if doc_id not in tenure_by_doc:
                        tenure_by_doc[doc_id] = {
                            "document_id": doc_id,
                            "document_name": doc_name,
                            "page": page,
                            "source": f"{req_id}, {doc_name}",
                            "confidence": confidence,
                        }

                    # Merge with conflict detection
                    if field_name in tenure_by_doc[doc_id]:
                        existing = tenure_by_doc[doc_id][field_name]
                        if existing != field_value:
                            logger.warning(
                                f"Field conflict for {doc_id}.{field_name}: "
                                f"'{existing}' vs '{field_value}' - keeping first value"
                            )
                            continue  # Keep existing value
                    tenure_by_doc[doc_id][field_name] = field_value

                elif field_name in DATE_FIELDS:
                    # Date fields
                    dates.append({
                        "date_type": field_name,
                        "date_value": field_value,
                        "date_str": field_value,
                        "document_id": doc_id,
                        "document_name": doc_name,
                        "page": page,
                        "source": req_id,
                        "confidence": confidence,
                    })

                elif field_name == "project_id":
                    # Project ID field
                    project_ids.append({
                        "project_id": field_value,
                        "document_id": doc_id,
                        "document_name": doc_name,
                        "page": page,
                        "source": req_id,
                        "confidence": confidence,
                    })

    # Convert tenure dict to list
    tenure_fields = list(tenure_by_doc.values())

    return {
        "dates": dates,
        "tenure": tenure_fields,
        "project_ids": project_ids,
    }


async def cross_validate(session_id: str) -> dict[str, Any]:
    """
    Run all cross-document validation checks for a session.

    Uses a three-layer validation architecture:
    - Layer 1 (Structural): Rule-based sanity checks on individual fields
    - Layer 2 (Cross-Document): Comparison across multiple documents (2+ required)
    - Layer 3 (LLM Synthesis): Single LLM call for holistic coherence assessment

    This approach ensures meaningful validation even for single-document submissions
    and provides intelligent sanity checks beyond simple cross-document comparison.

    Args:
        session_id: Session identifier

    Returns:
        Complete validation results with backward-compatible structure
    """
    from ..validation.coordinator import validate_session

    logger.info(f"Running three-layer validation for session {session_id}")

    # Run the three-layer validation
    result = await validate_session(session_id)

    # Convert to Pydantic model for backward compatibility
    # The coordinator already builds backward-compatible structures
    result_dict = result.to_dict()

    # Map to existing Pydantic model structure
    validation_result = ValidationResult(
        session_id=result.session_id,
        validated_at=result.validated_at,
        # Backward-compatible fields (populated by coordinator)
        date_alignments=result_dict.get("date_alignments", []),
        land_tenure=result_dict.get("land_tenure", []),
        project_ids=result_dict.get("project_ids", []),
        contradictions=result_dict.get("contradictions", []),
        # Sanity checks from structural layer
        sanity_checks=result_dict.get("sanity_checks", []),
        # Three-layer structure (new format)
        structural=result_dict.get("structural"),
        cross_document=result_dict.get("cross_document"),
        llm_synthesis=result_dict.get("llm_synthesis"),
        # Fact sheet data for UI
        fact_sheets=result_dict.get("fact_sheets"),
        # Summary with enhanced metrics
        summary=ValidationSummary(
            total_validations=result.summary.total_checks,
            validations_passed=result.summary.passed,
            validations_failed=result.summary.failed,
            validations_warning=result.summary.warnings,
            items_flagged=result.summary.flagged_for_review,
            pass_rate=result.summary.pass_rate,
            extraction_method="three_layer",
            structural_checks=result.summary.structural_checks,
            cross_document_checks=result.summary.cross_document_checks,
            llm_synthesis_available=result.summary.llm_synthesis_available,
        ),
        all_passed=result.all_passed,
    )

    logger.info(
        f"Validation complete: {result.summary.total_checks} checks, "
        f"{result.summary.passed} passed, {result.summary.warnings} warnings, "
        f"{result.summary.failed} failed, {result.summary.flagged_for_review} flagged"
    )

    return validation_result.model_dump()


def calculate_validation_summary(
    validations: dict[str, list[dict]], extraction_method: str = "regex"
) -> dict[str, Any]:
    """
    Calculate summary statistics from validation results.

    Args:
        validations: Dictionary of validation type to list of validation results
        extraction_method: Method used for field extraction ("llm", "regex", etc.)

    Returns:
        Summary statistics dictionary
    """
    all_validations = []
    for validation_type, validation_list in validations.items():
        all_validations.extend(validation_list)

    total = len(all_validations)
    passed = sum(1 for v in all_validations if v["status"] == "pass")
    failed = sum(1 for v in all_validations if v["status"] == "fail")
    warning = sum(1 for v in all_validations if v["status"] == "warning")
    flagged = sum(1 for v in all_validations if v.get("flagged_for_review", False))

    pass_rate = passed / total if total > 0 else 0.0

    summary = ValidationSummary(
        total_validations=total,
        validations_passed=passed,
        validations_failed=failed,
        validations_warning=warning,
        items_flagged=flagged,
        pass_rate=pass_rate,
        extraction_method=extraction_method
    )

    return summary.model_dump()


__all__ = [
    "validate_date_alignment",
    "validate_land_tenure",
    "validate_project_id",
    "cross_validate",
    "calculate_validation_summary",
    "extract_structured_fields_from_evidence",
]
