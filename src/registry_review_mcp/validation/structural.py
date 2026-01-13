"""Layer 1: Structural validation - rule-based checks on individual fields.

These checks run regardless of how many documents are present.
They validate field presence, formats, ranges, and internal consistency.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Canonical field names that should be extracted
REQUIRED_FIELDS = ["owner_name", "project_start_date"]
RECOMMENDED_FIELDS = ["project_id", "area_hectares", "crediting_period_years"]

# Patterns for format validation
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PROJECT_ID_PATTERNS = [
    re.compile(r"^C\d{2}-\d+$"),  # Standard: C01-1234
    re.compile(r"^\d{4}[A-Za-z]+\d{2}$"),  # Alternative: 4997Botany22
]

# Generic terms that shouldn't be owner names
GENERIC_OWNER_TERMS = [
    "the project", "the farm", "project", "farm", "landowner",
    "owner", "proponent", "applicant", "developer"
]


@dataclass
class CheckResult:
    """Result of a single validation check."""
    check_id: str
    check_type: str  # "required", "format", "range", "consistency", "generic_value"
    field_name: str
    status: str  # "pass", "warning", "fail"
    message: str
    value: Any = None
    source: str | None = None
    flagged_for_review: bool = False


@dataclass
class StructuralValidationResult:
    """Aggregated results from all structural checks."""
    checks: list[CheckResult] = field(default_factory=list)

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

    @property
    def flagged_count(self) -> int:
        return sum(1 for c in self.checks if c.flagged_for_review)


def _generate_check_id(check_type: str, field_name: str) -> str:
    """Generate unique check ID."""
    import uuid
    return f"STR-{check_type.upper()[:3]}-{field_name[:10]}-{uuid.uuid4().hex[:6]}"


def check_required_fields(
    all_fields: dict[str, Any],
    required: list[str] = REQUIRED_FIELDS,
    recommended: list[str] = RECOMMENDED_FIELDS
) -> list[CheckResult]:
    """Check that required and recommended fields are present."""
    results = []

    for field_name in required:
        if field_name in all_fields and all_fields[field_name]:
            results.append(CheckResult(
                check_id=_generate_check_id("req", field_name),
                check_type="required",
                field_name=field_name,
                status="pass",
                message=f"Required field '{field_name}' is present",
                value=all_fields[field_name]
            ))
        else:
            results.append(CheckResult(
                check_id=_generate_check_id("req", field_name),
                check_type="required",
                field_name=field_name,
                status="fail",
                message=f"Required field '{field_name}' is missing",
                flagged_for_review=True
            ))

    for field_name in recommended:
        if field_name not in all_fields or not all_fields[field_name]:
            results.append(CheckResult(
                check_id=_generate_check_id("rec", field_name),
                check_type="recommended",
                field_name=field_name,
                status="warning",
                message=f"Recommended field '{field_name}' is missing",
                flagged_for_review=False
            ))

    return results


def check_field_formats(all_fields: dict[str, Any]) -> list[CheckResult]:
    """Validate field formats (dates, IDs, etc.)."""
    results = []

    # Check date formats
    date_fields = [
        "project_start_date", "crediting_period_start", "crediting_period_end",
        "baseline_date", "monitoring_date", "permanence_start_date", "permanence_end_date"
    ]

    for field_name in date_fields:
        if field_name not in all_fields:
            continue

        value = all_fields[field_name]
        if not value:
            continue

        # Try to parse as ISO date
        if DATE_PATTERN.match(str(value)):
            try:
                datetime.fromisoformat(str(value))
                results.append(CheckResult(
                    check_id=_generate_check_id("fmt", field_name),
                    check_type="format",
                    field_name=field_name,
                    status="pass",
                    message=f"Date '{field_name}' has valid ISO format",
                    value=value
                ))
            except ValueError:
                results.append(CheckResult(
                    check_id=_generate_check_id("fmt", field_name),
                    check_type="format",
                    field_name=field_name,
                    status="warning",
                    message=f"Date '{field_name}' matches pattern but fails parsing: {value}",
                    value=value,
                    flagged_for_review=True
                ))
        else:
            results.append(CheckResult(
                check_id=_generate_check_id("fmt", field_name),
                check_type="format",
                field_name=field_name,
                status="warning",
                message=f"Date '{field_name}' not in ISO format (YYYY-MM-DD): {value}",
                value=value,
                flagged_for_review=True
            ))

    # Check project_id format
    if "project_id" in all_fields and all_fields["project_id"]:
        pid = str(all_fields["project_id"])

        # Check if it's just a year (common extraction error)
        if re.match(r"^\d{4}$", pid):
            results.append(CheckResult(
                check_id=_generate_check_id("fmt", "project_id"),
                check_type="format",
                field_name="project_id",
                status="fail",
                message=f"Project ID appears to be a year, not an ID: '{pid}'",
                value=pid,
                flagged_for_review=True
            ))
        elif any(p.match(pid) for p in PROJECT_ID_PATTERNS):
            results.append(CheckResult(
                check_id=_generate_check_id("fmt", "project_id"),
                check_type="format",
                field_name="project_id",
                status="pass",
                message=f"Project ID has valid format: '{pid}'",
                value=pid
            ))
        else:
            results.append(CheckResult(
                check_id=_generate_check_id("fmt", "project_id"),
                check_type="format",
                field_name="project_id",
                status="warning",
                message=f"Project ID has non-standard format: '{pid}'",
                value=pid,
                flagged_for_review=True
            ))

    return results


def check_field_ranges(all_fields: dict[str, Any]) -> list[CheckResult]:
    """Check that field values are in reasonable ranges."""
    results = []
    now = datetime.now()

    # Check date ranges
    date_fields = [
        "project_start_date", "crediting_period_start", "crediting_period_end",
        "baseline_date", "permanence_start_date", "permanence_end_date"
    ]

    for field_name in date_fields:
        if field_name not in all_fields:
            continue

        value = all_fields[field_name]
        if not value:
            continue

        try:
            date_value = datetime.fromisoformat(str(value))

            # Check: not in distant future (allow 50 years for crediting/permanence end)
            max_future = 50 if "end" in field_name or "permanence" in field_name else 2
            if date_value.year > now.year + max_future:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", field_name),
                    check_type="range",
                    field_name=field_name,
                    status="warning",
                    message=f"Date '{field_name}' is far in the future: {value}",
                    value=value,
                    flagged_for_review=True
                ))

            # Check: not too old (before 1990 for carbon projects)
            elif date_value.year < 1990:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", field_name),
                    check_type="range",
                    field_name=field_name,
                    status="warning",
                    message=f"Date '{field_name}' is unusually old for carbon project: {value}",
                    value=value,
                    flagged_for_review=True
                ))
            else:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", field_name),
                    check_type="range",
                    field_name=field_name,
                    status="pass",
                    message=f"Date '{field_name}' is in reasonable range",
                    value=value
                ))
        except (ValueError, TypeError):
            pass  # Format check handles this

    # Check percentage ranges
    pct_fields = ["buffer_pool_percentage", "leakage_percentage"]
    for field_name in pct_fields:
        if field_name not in all_fields:
            continue

        value = all_fields[field_name]
        if value is None:
            continue

        try:
            pct = float(value)
            if pct < 0 or pct > 100:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", field_name),
                    check_type="range",
                    field_name=field_name,
                    status="fail",
                    message=f"Percentage '{field_name}' out of range (0-100): {pct}",
                    value=pct,
                    flagged_for_review=True
                ))
            else:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", field_name),
                    check_type="range",
                    field_name=field_name,
                    status="pass",
                    message=f"Percentage '{field_name}' in valid range: {pct}%",
                    value=pct
                ))
        except (ValueError, TypeError):
            results.append(CheckResult(
                check_id=_generate_check_id("rng", field_name),
                check_type="range",
                field_name=field_name,
                status="warning",
                message=f"Percentage '{field_name}' is not numeric: {value}",
                value=value,
                flagged_for_review=True
            ))

    # Check area range
    if "area_hectares" in all_fields and all_fields["area_hectares"] is not None:
        try:
            area = float(all_fields["area_hectares"])
            if area <= 0:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", "area_hectares"),
                    check_type="range",
                    field_name="area_hectares",
                    status="fail",
                    message=f"Area must be positive: {area}",
                    value=area,
                    flagged_for_review=True
                ))
            elif area > 1_000_000:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", "area_hectares"),
                    check_type="range",
                    field_name="area_hectares",
                    status="warning",
                    message=f"Area unusually large (>1M ha): {area:,.0f}",
                    value=area,
                    flagged_for_review=True
                ))
            else:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", "area_hectares"),
                    check_type="range",
                    field_name="area_hectares",
                    status="pass",
                    message=f"Area in reasonable range: {area:,.2f} ha",
                    value=area
                ))
        except (ValueError, TypeError):
            pass

    # Check year/period ranges
    period_fields = ["crediting_period_years", "permanence_period_years"]
    for field_name in period_fields:
        if field_name not in all_fields:
            continue

        value = all_fields[field_name]
        if value is None:
            continue

        try:
            years = int(value)
            if years <= 0 or years > 100:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", field_name),
                    check_type="range",
                    field_name=field_name,
                    status="warning",
                    message=f"Period '{field_name}' unusual: {years} years",
                    value=years,
                    flagged_for_review=True
                ))
            else:
                results.append(CheckResult(
                    check_id=_generate_check_id("rng", field_name),
                    check_type="range",
                    field_name=field_name,
                    status="pass",
                    message=f"Period '{field_name}' reasonable: {years} years",
                    value=years
                ))
        except (ValueError, TypeError):
            pass

    return results


def check_internal_consistency(all_fields: dict[str, Any]) -> list[CheckResult]:
    """Check that related fields are internally consistent."""
    results = []

    # Check: crediting_period_end > crediting_period_start
    start = all_fields.get("crediting_period_start")
    end = all_fields.get("crediting_period_end")

    if start and end:
        try:
            start_date = datetime.fromisoformat(str(start))
            end_date = datetime.fromisoformat(str(end))

            if end_date <= start_date:
                results.append(CheckResult(
                    check_id=_generate_check_id("con", "crediting_period"),
                    check_type="consistency",
                    field_name="crediting_period",
                    status="fail",
                    message=f"Crediting period end ({end}) must be after start ({start})",
                    flagged_for_review=True
                ))
            else:
                results.append(CheckResult(
                    check_id=_generate_check_id("con", "crediting_period"),
                    check_type="consistency",
                    field_name="crediting_period",
                    status="pass",
                    message=f"Crediting period dates are consistent ({start} to {end})"
                ))
        except (ValueError, TypeError):
            pass

    # Check: permanence dates consistent
    perm_start = all_fields.get("permanence_start_date") or all_fields.get("permanence_period_start")
    perm_end = all_fields.get("permanence_end_date") or all_fields.get("permanence_period_end")

    if perm_start and perm_end:
        try:
            perm_start_date = datetime.fromisoformat(str(perm_start))
            perm_end_date = datetime.fromisoformat(str(perm_end))

            if perm_end_date <= perm_start_date:
                results.append(CheckResult(
                    check_id=_generate_check_id("con", "permanence_period"),
                    check_type="consistency",
                    field_name="permanence_period",
                    status="fail",
                    message=f"Permanence period end must be after start",
                    flagged_for_review=True
                ))
        except (ValueError, TypeError):
            pass

    return results


def check_generic_values(all_fields: dict[str, Any]) -> list[CheckResult]:
    """Check for generic/placeholder values that shouldn't be extracted."""
    results = []

    # Check owner_name for generic terms
    if "owner_name" in all_fields and all_fields["owner_name"]:
        owner = str(all_fields["owner_name"]).lower().strip()

        for term in GENERIC_OWNER_TERMS:
            if term in owner:
                results.append(CheckResult(
                    check_id=_generate_check_id("gen", "owner_name"),
                    check_type="generic_value",
                    field_name="owner_name",
                    status="fail",
                    message=f"Owner name appears generic: '{all_fields['owner_name']}' (contains '{term}')",
                    value=all_fields["owner_name"],
                    flagged_for_review=True
                ))
                break
        else:
            # No generic terms found
            results.append(CheckResult(
                check_id=_generate_check_id("gen", "owner_name"),
                check_type="generic_value",
                field_name="owner_name",
                status="pass",
                message=f"Owner name appears valid: '{all_fields['owner_name']}'",
                value=all_fields["owner_name"]
            ))

    return results


def extract_all_fields_from_evidence(evidence_data: dict) -> dict[str, Any]:
    """Extract all structured fields from evidence data into flat dict.

    Merges fields from all snippets, preferring higher-confidence extractions.
    """
    all_fields: dict[str, Any] = {}
    field_confidence: dict[str, float] = {}

    for req in evidence_data.get("evidence", []):
        for snippet in req.get("evidence_snippets", []):
            fields = snippet.get("structured_fields")
            if not fields:
                continue

            confidence = snippet.get("confidence", 0.5)

            for field_name, value in fields.items():
                # Keep highest confidence value for each field
                if field_name not in all_fields or confidence > field_confidence.get(field_name, 0):
                    all_fields[field_name] = value
                    field_confidence[field_name] = confidence

    return all_fields


def run_structural_checks(evidence_data: dict) -> StructuralValidationResult:
    """Run all structural validation checks.

    Args:
        evidence_data: Loaded evidence.json data

    Returns:
        StructuralValidationResult with all check results
    """
    # Extract all fields first
    all_fields = extract_all_fields_from_evidence(evidence_data)

    logger.info(f"Running structural checks on {len(all_fields)} extracted fields")

    result = StructuralValidationResult()

    # Run all check types
    result.checks.extend(check_required_fields(all_fields))
    result.checks.extend(check_field_formats(all_fields))
    result.checks.extend(check_field_ranges(all_fields))
    result.checks.extend(check_internal_consistency(all_fields))
    result.checks.extend(check_generic_values(all_fields))

    logger.info(
        f"Structural checks complete: {result.passed} passed, "
        f"{result.warnings} warnings, {result.failed} failed"
    )

    return result
