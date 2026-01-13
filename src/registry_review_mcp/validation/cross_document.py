"""Layer 2: Cross-document validation - compare values across multiple documents.

These checks only run when 2+ documents contain the same field type.
They validate consistency of dates, names, and identifiers across sources.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CrossDocumentCheck:
    """Result of a cross-document validation check."""
    check_id: str
    check_type: str  # "date_alignment", "name_consistency", "id_consistency"
    field_name: str
    documents: list[str]
    status: str  # "pass", "warning", "fail"
    message: str
    values: list[Any] = field(default_factory=list)
    similarity: float | None = None  # For fuzzy matching
    flagged_for_review: bool = False


@dataclass
class CrossDocumentValidationResult:
    """Aggregated results from cross-document checks."""
    checks: list[CrossDocumentCheck] = field(default_factory=list)
    documents_analyzed: int = 0
    sufficient_data: bool = False  # True if 2+ documents with overlapping fields

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == "pass")

    @property
    def warnings(self) -> int:
        return sum(1 for c in self.checks if c.status == "warning")

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail")


def _generate_check_id(check_type: str, field_name: str) -> str:
    """Generate unique check ID."""
    import uuid
    return f"XDC-{check_type.upper()[:3]}-{field_name[:10]}-{uuid.uuid4().hex[:6]}"


def _extract_fields_by_document(evidence_data: dict) -> dict[str, dict[str, Any]]:
    """Group structured fields by source document.

    Returns:
        Dict mapping document_id -> {field_name: value}
    """
    by_document: dict[str, dict[str, Any]] = {}

    for req in evidence_data.get("evidence", []):
        for snippet in req.get("evidence_snippets", []):
            fields = snippet.get("structured_fields")
            if not fields:
                continue

            doc_id = snippet.get("document_id") or snippet.get("document_name", "unknown")

            if doc_id not in by_document:
                by_document[doc_id] = {}

            for field_name, value in fields.items():
                # Keep first non-null value per document
                if field_name not in by_document[doc_id] and value is not None:
                    by_document[doc_id][field_name] = value

    return by_document


def check_date_alignment(
    fields_by_doc: dict[str, dict[str, Any]],
    max_delta_days: int = 120
) -> list[CrossDocumentCheck]:
    """Check that dates align across documents within tolerance."""
    results = []

    # Collect all dates grouped by type
    date_fields = [
        "project_start_date", "baseline_date", "crediting_period_start",
        "crediting_period_end", "monitoring_date"
    ]

    for date_field in date_fields:
        dates_found: list[tuple[str, datetime]] = []

        for doc_id, fields in fields_by_doc.items():
            if date_field in fields and fields[date_field]:
                try:
                    date_val = datetime.fromisoformat(str(fields[date_field]))
                    dates_found.append((doc_id, date_val))
                except (ValueError, TypeError):
                    continue

        # Need 2+ documents to compare
        if len(dates_found) < 2:
            continue

        # Compare all pairs
        all_aligned = True
        max_delta = 0
        docs = [d[0] for d in dates_found]
        values = [d[1].isoformat() for d in dates_found]

        for i in range(len(dates_found)):
            for j in range(i + 1, len(dates_found)):
                delta = abs((dates_found[i][1] - dates_found[j][1]).days)
                max_delta = max(max_delta, delta)
                if delta > max_delta_days:
                    all_aligned = False

        if all_aligned:
            results.append(CrossDocumentCheck(
                check_id=_generate_check_id("date", date_field),
                check_type="date_alignment",
                field_name=date_field,
                documents=docs,
                status="pass",
                message=f"'{date_field}' aligned across {len(docs)} documents (max delta: {max_delta} days)",
                values=values
            ))
        else:
            results.append(CrossDocumentCheck(
                check_id=_generate_check_id("date", date_field),
                check_type="date_alignment",
                field_name=date_field,
                documents=docs,
                status="warning",
                message=f"'{date_field}' differs across documents by {max_delta} days (threshold: {max_delta_days})",
                values=values,
                flagged_for_review=True
            ))

    return results


def check_name_consistency(
    fields_by_doc: dict[str, dict[str, Any]],
    fuzzy_threshold: float = 0.8
) -> list[CrossDocumentCheck]:
    """Check that names (owner_name, project_name) are consistent across documents."""
    results = []

    name_fields = ["owner_name", "project_name"]

    for name_field in name_fields:
        names_found: list[tuple[str, str]] = []

        for doc_id, fields in fields_by_doc.items():
            if name_field in fields and fields[name_field]:
                names_found.append((doc_id, str(fields[name_field])))

        # Need 2+ documents to compare
        if len(names_found) < 2:
            continue

        docs = [n[0] for n in names_found]
        values = [n[1] for n in names_found]

        # Check for exact match
        unique_names = set(v.lower().strip() for v in values)

        if len(unique_names) == 1:
            results.append(CrossDocumentCheck(
                check_id=_generate_check_id("name", name_field),
                check_type="name_consistency",
                field_name=name_field,
                documents=docs,
                status="pass",
                message=f"'{name_field}' identical across {len(docs)} documents",
                values=values,
                similarity=1.0
            ))
        else:
            # Check fuzzy similarity
            min_similarity = 1.0
            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    sim = SequenceMatcher(
                        None,
                        values[i].lower(),
                        values[j].lower()
                    ).ratio()
                    min_similarity = min(min_similarity, sim)

            if min_similarity >= fuzzy_threshold:
                results.append(CrossDocumentCheck(
                    check_id=_generate_check_id("name", name_field),
                    check_type="name_consistency",
                    field_name=name_field,
                    documents=docs,
                    status="warning",
                    message=f"'{name_field}' similar but not identical (similarity: {min_similarity:.0%})",
                    values=values,
                    similarity=min_similarity,
                    flagged_for_review=True
                ))
            else:
                results.append(CrossDocumentCheck(
                    check_id=_generate_check_id("name", name_field),
                    check_type="name_consistency",
                    field_name=name_field,
                    documents=docs,
                    status="fail",
                    message=f"'{name_field}' inconsistent across documents: {', '.join(values)}",
                    values=values,
                    similarity=min_similarity,
                    flagged_for_review=True
                ))

    return results


def check_id_consistency(fields_by_doc: dict[str, dict[str, Any]]) -> list[CrossDocumentCheck]:
    """Check that project IDs are consistent across documents."""
    results = []

    ids_found: list[tuple[str, str]] = []

    for doc_id, fields in fields_by_doc.items():
        if "project_id" in fields and fields["project_id"]:
            ids_found.append((doc_id, str(fields["project_id"])))

    # Need 2+ documents to compare
    if len(ids_found) < 2:
        return results

    docs = [i[0] for i in ids_found]
    values = [i[1] for i in ids_found]

    unique_ids = set(values)

    if len(unique_ids) == 1:
        results.append(CrossDocumentCheck(
            check_id=_generate_check_id("id", "project_id"),
            check_type="id_consistency",
            field_name="project_id",
            documents=docs,
            status="pass",
            message=f"Project ID '{values[0]}' consistent across {len(docs)} documents",
            values=values
        ))
    else:
        results.append(CrossDocumentCheck(
            check_id=_generate_check_id("id", "project_id"),
            check_type="id_consistency",
            field_name="project_id",
            documents=docs,
            status="fail",
            message=f"Multiple project IDs found: {', '.join(unique_ids)}",
            values=values,
            flagged_for_review=True
        ))

    return results


def check_numeric_consistency(
    fields_by_doc: dict[str, dict[str, Any]],
    tolerance: float = 0.05  # 5% variance allowed
) -> list[CrossDocumentCheck]:
    """Check that numeric fields (area, percentages) are consistent."""
    results = []

    numeric_fields = [
        "area_hectares", "buffer_pool_percentage",
        "crediting_period_years", "permanence_period_years"
    ]

    for num_field in numeric_fields:
        values_found: list[tuple[str, float]] = []

        for doc_id, fields in fields_by_doc.items():
            if num_field in fields and fields[num_field] is not None:
                try:
                    val = float(fields[num_field])
                    values_found.append((doc_id, val))
                except (ValueError, TypeError):
                    continue

        # Need 2+ documents to compare
        if len(values_found) < 2:
            continue

        docs = [v[0] for v in values_found]
        values = [v[1] for v in values_found]

        max_val = max(values)
        min_val = min(values)

        if max_val == 0:
            variance = 0 if min_val == 0 else 1.0
        else:
            variance = (max_val - min_val) / max_val

        if variance <= tolerance:
            results.append(CrossDocumentCheck(
                check_id=_generate_check_id("num", num_field),
                check_type="numeric_consistency",
                field_name=num_field,
                documents=docs,
                status="pass",
                message=f"'{num_field}' consistent across documents (variance: {variance:.1%})",
                values=values
            ))
        else:
            results.append(CrossDocumentCheck(
                check_id=_generate_check_id("num", num_field),
                check_type="numeric_consistency",
                field_name=num_field,
                documents=docs,
                status="warning",
                message=f"'{num_field}' varies across documents: {min_val} to {max_val} ({variance:.1%} variance)",
                values=values,
                flagged_for_review=True
            ))

    return results


def run_cross_document_checks(evidence_data: dict) -> CrossDocumentValidationResult:
    """Run all cross-document validation checks.

    Args:
        evidence_data: Loaded evidence.json data

    Returns:
        CrossDocumentValidationResult with all check results.
        If insufficient documents (<2), returns empty result with sufficient_data=False.
    """
    result = CrossDocumentValidationResult()

    # Group fields by document
    fields_by_doc = _extract_fields_by_document(evidence_data)
    result.documents_analyzed = len(fields_by_doc)

    logger.info(f"Running cross-document checks across {len(fields_by_doc)} documents")

    if len(fields_by_doc) < 2:
        logger.info("Insufficient documents for cross-document validation (need 2+)")
        result.sufficient_data = False
        return result

    result.sufficient_data = True

    # Run all cross-document check types
    result.checks.extend(check_date_alignment(fields_by_doc))
    result.checks.extend(check_name_consistency(fields_by_doc))
    result.checks.extend(check_id_consistency(fields_by_doc))
    result.checks.extend(check_numeric_consistency(fields_by_doc))

    logger.info(
        f"Cross-document checks complete: {result.passed} passed, "
        f"{result.warnings} warnings, {result.failed} failed"
    )

    return result
