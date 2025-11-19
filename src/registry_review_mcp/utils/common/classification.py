"""Document classification utilities.

Centralizes document type classification logic previously scattered across:
- document_tools.py
- upload_tools.py
- Various workflow prompts
"""

import re
from enum import Enum


class DocumentType(str, Enum):
    """Standard document types in registry review."""

    PROJECT_PLAN = "project_plan"
    MONITORING_REPORT = "monitoring_report"
    BASELINE = "baseline"
    VERIFICATION_REPORT = "verification_report"
    AGENT_REVIEW = "agent_review"
    GIS_DATA = "gis_data"
    SUPPORTING = "supporting"
    UNKNOWN = "unknown"


class DocumentClassifier:
    """Unified document classification with pattern matching."""

    # Centralized classification patterns
    PATTERNS = {
        DocumentType.PROJECT_PLAN: [
            r"project[_\s-]*plan",
            r"(?:^|_)pp(?:_|\.)",  # PP_ or .pp
            r"project[_\s-]*description",
        ],
        DocumentType.MONITORING_REPORT: [
            r"monitoring[_\s-]*report",
            r"(?:^|_)mr(?:_|\.)",  # MR_ or .mr
            r"monitoring[_\s-]*plan",
        ],
        DocumentType.BASELINE: [
            r"baseline",
            r"(?:^|_)bl(?:_|\.)",  # BL_ or .bl
            r"baseline[_\s-]*report",
        ],
        DocumentType.VERIFICATION_REPORT: [
            r"verification[_\s-]*report",
            r"(?:^|_)vr(?:_|\.)",  # VR_ or .vr
            r"verif",
        ],
        DocumentType.AGENT_REVIEW: [
            r"agent[_\s-]*review",
            r"registry[_\s-]*agent",
            r"review[_\s-]*memo",
        ],
        DocumentType.GIS_DATA: [
            r"\.shp$",
            r"\.geojson$",
            r"\.kml$",
            r"gis[_\s-]*data",
            r"spatial[_\s-]*data",
        ],
        DocumentType.SUPPORTING: [
            r"supporting",
            r"appendix",
            r"attachment",
            r"supplement",
        ],
    }

    @classmethod
    def classify(cls, filename: str, content: str = "") -> DocumentType:
        """Classify document by filename and optional content.

        Args:
            filename: Name of the file
            content: Optional file content for additional context

        Returns:
            DocumentType classification
        """
        filename_lower = filename.lower()

        # Check each pattern
        for doc_type, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    return doc_type

        # If content provided, check for keywords in content
        if content:
            content_lower = content[:1000].lower()  # Check first 1000 chars
            for doc_type, patterns in cls.PATTERNS.items():
                for pattern in patterns:
                    # Convert pattern to simple keyword for content matching
                    keyword = pattern.replace(r"\b", "").replace(r"[_\s-]*", " ")
                    if keyword in content_lower:
                        return doc_type

        return DocumentType.UNKNOWN

    @classmethod
    def is_primary_document(cls, doc_type: DocumentType) -> bool:
        """Check if document type is a primary project document.

        Primary documents are required for registry submission.
        """
        primary_types = {
            DocumentType.PROJECT_PLAN,
            DocumentType.MONITORING_REPORT,
            DocumentType.BASELINE,
            DocumentType.VERIFICATION_REPORT,
        }
        return doc_type in primary_types

    @classmethod
    def get_display_name(cls, doc_type: DocumentType) -> str:
        """Get human-readable display name for document type."""
        display_names = {
            DocumentType.PROJECT_PLAN: "Project Plan",
            DocumentType.MONITORING_REPORT: "Monitoring Report",
            DocumentType.BASELINE: "Baseline Report",
            DocumentType.VERIFICATION_REPORT: "Verification Report",
            DocumentType.AGENT_REVIEW: "Registry Agent Review",
            DocumentType.GIS_DATA: "GIS/Spatial Data",
            DocumentType.SUPPORTING: "Supporting Document",
            DocumentType.UNKNOWN: "Unknown Document Type",
        }
        return display_names.get(doc_type, doc_type.value)

    @classmethod
    def get_expected_count(cls, doc_type: DocumentType) -> tuple[int, int]:
        """Get expected count range (min, max) for document type.

        Returns:
            Tuple of (minimum_expected, maximum_expected)
        """
        expectations = {
            DocumentType.PROJECT_PLAN: (1, 1),  # Exactly 1
            DocumentType.MONITORING_REPORT: (1, 10),  # 1 or more
            DocumentType.BASELINE: (0, 1),  # 0 or 1
            DocumentType.VERIFICATION_REPORT: (0, 10),  # 0 or more
            DocumentType.AGENT_REVIEW: (0, 1),  # 0 or 1
            DocumentType.GIS_DATA: (0, 20),  # 0 or more
            DocumentType.SUPPORTING: (0, 50),  # 0 or more
            DocumentType.UNKNOWN: (0, 100),  # Any number
        }
        return expectations.get(doc_type, (0, 100))
