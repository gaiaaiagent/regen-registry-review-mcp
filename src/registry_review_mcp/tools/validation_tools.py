"""Cross-document validation tools."""

import re
import uuid
from datetime import datetime, UTC
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from ..config.settings import settings
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
from ..utils.state import StateManager


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
        validation_id=f"VAL-DATE-{uuid.uuid4().hex[:8]}",
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
        validation_id=f"VAL-TENURE-{uuid.uuid4().hex[:8]}",
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
        validation_id=f"VAL-PID-{uuid.uuid4().hex[:8]}",
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


def extract_project_ids_from_evidence(evidence_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract project ID occurrences from evidence data.

    Args:
        evidence_data: Evidence JSON data

    Returns:
        List of project ID occurrences with document references
    """
    import re

    project_ids = []
    id_pattern = re.compile(r'\b(\d{4})\b|C\d{2}-(\d{4})')

    # Extract from document names
    for req in evidence_data.get('evidence', []):
        for snip in req.get('evidence_snippets', []):
            doc_name = snip['document_name']
            # Look for 4-digit IDs in document names
            matches = id_pattern.findall(doc_name)
            for match in matches:
                project_id = match[0] if match[0] else match[1]
                # Only consider valid project IDs (exclude years like 2023, 2024)
                if project_id and int(project_id) < 9000:
                    project_ids.append({
                        'project_id': project_id,
                        'document_id': snip.get('document_id'),
                        'document_name': doc_name,
                        'source': 'document_name'
                    })

    return project_ids


def extract_dates_from_evidence(evidence_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract dates from evidence snippets with context.

    Args:
        evidence_data: Evidence JSON data

    Returns:
        List of date fields with context and source
    """
    import re
    from datetime import datetime

    dates = []
    date_patterns = [
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', '%m/%d/%Y'),  # MM/DD/YYYY or MM-DD-YYYY
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', '%Y/%m/%d'),  # YYYY/MM/DD or YYYY-MM-DD
    ]

    # Focus on specific requirements that contain dates
    date_requirements = {
        'REQ-007': 'project_start_date',
        'REQ-018': 'baseline_date',
        'REQ-019': 'monitoring_date',
    }

    for req in evidence_data.get('evidence', []):
        req_id = req['requirement_id']
        if req_id in date_requirements:
            date_type = date_requirements[req_id]

            for snip in req.get('evidence_snippets', []):
                text = snip['text']

                # Try each date pattern
                for pattern, date_format in date_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        try:
                            if len(match) == 3:
                                # Parse the date
                                if date_format == '%m/%d/%Y':
                                    date_str = f"{match[0]}/{match[1]}/{match[2]}"
                                else:
                                    date_str = f"{match[0]}/{match[1]}/{match[2]}"

                                parsed_date = datetime.strptime(date_str, date_format)

                                # Only include reasonable dates (2000-2030 range for project dates)
                                if 2000 <= parsed_date.year <= 2030:
                                    dates.append({
                                        'date_type': date_type,
                                        'date_value': parsed_date.isoformat(),
                                        'date_str': date_str,
                                        'document_id': snip.get('document_id'),
                                        'document_name': snip['document_name'],
                                        'page': snip.get('page'),
                                        'source': req_id
                                    })
                        except (ValueError, IndexError):
                            continue

    return dates


def extract_land_tenure_from_evidence(evidence_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract land tenure information from evidence snippets.

    Args:
        evidence_data: Evidence JSON data

    Returns:
        List of land tenure fields
    """
    import re

    tenure_fields = []

    # Focus on REQ-002 (land tenure requirement)
    for req in evidence_data.get('evidence', []):
        if req['requirement_id'] == 'REQ-002':
            for snip in req.get('evidence_snippets', []):
                text = snip['text']
                text_lower = text.lower()

                # Look for owner name patterns
                # Pattern: "Landowner: Name" or "Owner: Name" or "Land Steward: Name"
                owner_patterns = [
                    r'(?:land\s*owner|owner|land\s*steward)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+).*(?:owner|steward)',
                ]

                for pattern in owner_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        owner_name = match if isinstance(match, str) else match[0]
                        # Filter out common false positives
                        if len(owner_name.split()) >= 2 and len(owner_name) > 5:
                            tenure_fields.append({
                                'owner_name': owner_name.strip(),
                                'document_id': snip.get('document_id'),
                                'document_name': snip['document_name'],
                                'page': snip.get('page'),
                                'source': 'REQ-002'
                            })

                # Look for area information
                area_pattern = r'(\d+(?:\.\d+)?)\s*(?:ha|hectares)'
                area_matches = re.findall(area_pattern, text_lower)
                if area_matches:
                    for area_str in area_matches:
                        try:
                            area = float(area_str)
                            if area > 0 and area < 100000:  # Reasonable range
                                tenure_fields.append({
                                    'area_hectares': area,
                                    'document_id': snip.get('document_id'),
                                    'document_name': snip['document_name'],
                                    'page': snip.get('page'),
                                    'source': 'REQ-002'
                                })
                        except ValueError:
                            continue

    return tenure_fields


async def cross_validate(session_id: str) -> dict[str, Any]:
    """
    Run all cross-document validation checks for a session.

    This function:
    1. Loads evidence data
    2. Extracts structured fields (dates, land tenure, project IDs)
    3. Runs validation checks using extracted data
    4. Returns complete validation results

    Args:
        session_id: Session identifier

    Returns:
        Complete validation results
    """
    from datetime import datetime

    state_manager = StateManager(session_id)

    # Load session data
    session_data = state_manager.read_json("session.json")

    # Try to load evidence data (required for validation)
    evidence_path = state_manager.session_dir / "evidence.json"
    if not evidence_path.exists():
        # No evidence yet, return empty results
        validation_result = ValidationResult(
            session_id=session_id,
            validated_at=datetime.now(UTC),
            date_alignments=[],
            land_tenure=[],
            project_ids=[],
            contradictions=[],
            summary=ValidationSummary(
                total_validations=0,
                validations_passed=0,
                validations_failed=0,
                validations_warning=0,
                items_flagged=0,
                pass_rate=0.0
            ),
            all_passed=True
        )
        state_manager.write_json("validation.json", validation_result.model_dump())
        return validation_result.model_dump()

    evidence_data = state_manager.read_json("evidence.json")

    # Extract structured fields from evidence (LLM or regex)
    extraction_method = "regex"
    try:
        if settings.llm_extraction_enabled and settings.anthropic_api_key:
            import sys

            from ..extractors.llm_extractors import extract_fields_with_llm

            print("Using LLM-powered field extraction", file=sys.stderr)

            # LLM extraction
            raw_fields = await extract_fields_with_llm(session_id, evidence_data)

            # Transform dates to validation format
            dates = []
            for field in raw_fields.get("dates", []):
                if field.confidence >= settings.llm_confidence_threshold:
                    dates.append({
                        "date_type": field.field_type,
                        "date_value": field.value,
                        "date_str": field.value,
                        "document_id": None,  # Will be populated if available
                        "document_name": field.source.split(",")[0].strip(),
                        "page": None,  # Extract from source if available
                        "source": field.source,
                        "confidence": field.confidence
                    })

            # Transform tenure fields to validation format
            from ..extractors.llm_extractors import group_fields_by_document

            # Filter by confidence and group by document
            tenure_raw = [f for f in raw_fields.get("tenure", []) if f.confidence >= settings.llm_confidence_threshold]
            tenure_fields = group_fields_by_document(tenure_raw)

            # Transform project IDs to validation format
            project_ids = []
            for field in raw_fields.get("project_ids", []):
                if field.confidence >= settings.llm_confidence_threshold:
                    project_ids.append({
                        "project_id": field.value,
                        "document_id": field.source.split(",")[0].strip() if "," in field.source else None,
                        "document_name": field.source.split(",")[0].strip(),
                        "page": None,  # TODO: Extract from source
                        "section": field.source,
                        "confidence": field.confidence
                    })

            extraction_method = "llm"
        else:
            raise ValueError("LLM extraction not enabled")

    except Exception as e:
        import sys
        print(f"LLM extraction failed: {e}. Using regex fallback.", file=sys.stderr)

        # Regex extraction (fallback)
        project_ids = extract_project_ids_from_evidence(evidence_data)
        dates = extract_dates_from_evidence(evidence_data)
        tenure_fields = extract_land_tenure_from_evidence(evidence_data)
        extraction_method = "regex_fallback" if settings.llm_extraction_enabled else "regex"

    # Run validation checks
    validation_results = {
        'date_alignments': [],
        'land_tenure': [],
        'project_ids': [],
        'contradictions': []
    }

    # 1. Date alignment validation
    # Group dates by type and check if pairs are within 120-day threshold
    project_start_dates = [d for d in dates if d['date_type'] == 'project_start_date']
    baseline_dates = [d for d in dates if d['date_type'] == 'baseline_date']

    if project_start_dates and baseline_dates:
        # Validate first occurrence of each type
        for psd in project_start_dates[:3]:  # Check up to 3 pairs
            for bd in baseline_dates[:3]:
                try:
                    date1 = datetime.fromisoformat(psd['date_value'])
                    date2 = datetime.fromisoformat(bd['date_value'])

                    result = await validate_date_alignment(
                        session_id=session_id,
                        field1_name='project_start_date',
                        field1_value=date1,
                        field1_source=f"{psd['document_name']} (page {psd.get('page', '?')})",
                        field2_name='baseline_date',
                        field2_value=date2,
                        field2_source=f"{bd['document_name']} (page {bd.get('page', '?')})",
                        max_delta_days=120
                    )
                    validation_results['date_alignments'].append(result)
                except (ValueError, KeyError):
                    continue

    # 2. Project ID validation
    if project_ids:
        # Build project ID occurrences
        id_occurrences = []
        for pid_data in project_ids:
            id_occurrences.append({
                'project_id': pid_data['project_id'],
                'document_id': pid_data['document_id'],
                'document_name': pid_data['document_name'],
                'location': 'document_name',
                'confidence': 1.0
            })

        if id_occurrences:
            # Get total document count
            total_docs = len(set(pid_data['document_id'] for pid_data in project_ids))

            result = await validate_project_id(
                session_id=session_id,
                occurrences=id_occurrences,
                total_documents=total_docs
            )
            validation_results['project_ids'].append(result)

    # 3. Land tenure validation
    # Extract unique owner names
    owner_names = [f['owner_name'] for f in tenure_fields if 'owner_name' in f]
    if len(owner_names) >= 2:
        # Check first 2 owner names for consistency
        tenure_data = []
        for i, name in enumerate(owner_names[:2]):
            matching_field = next((f for f in tenure_fields if f.get('owner_name') == name), None)
            if matching_field:
                tenure_data.append({
                    'owner_name': name,
                    'area_hectares': matching_field.get('area_hectares', 0.0),
                    'tenure_type': 'unknown',
                    'document_id': matching_field['document_id'],
                    'document_name': matching_field['document_name'],
                    'page': matching_field.get('page'),
                    'source': f"REQ-002, {matching_field['document_name']}",
                    'confidence': 0.8  # Moderate confidence from regex extraction
                })

        if len(tenure_data) >= 2:
            result = await validate_land_tenure(
                session_id=session_id,
                fields=tenure_data
            )
            validation_results['land_tenure'].append(result)

    # Calculate summary
    summary = calculate_validation_summary(validation_results, extraction_method)

    # Build final result
    validation_result = ValidationResult(
        session_id=session_id,
        validated_at=datetime.now(UTC),
        date_alignments=validation_results['date_alignments'],
        land_tenure=validation_results['land_tenure'],
        project_ids=validation_results['project_ids'],
        contradictions=validation_results['contradictions'],
        summary=ValidationSummary(**summary),
        all_passed=summary['pass_rate'] == 1.0
    )

    # Save validation results
    state_manager.write_json("validation.json", validation_result.model_dump())

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
]
