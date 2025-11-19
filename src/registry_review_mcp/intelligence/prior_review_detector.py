"""Intelligent prior review detection and parsing.

Detects and parses previous registry review documents:
- Identifies documents that are prior registry reviews
- Extracts review metadata (date, reviewer, methodology, status)
- Parses review structure (requirements, evidence, findings)
- Maps prior evidence to current requirements
- Provides confidence scoring for reusability

This enables building upon prior review work and avoiding duplicate effort.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PriorReviewDetector:
    """Detect and parse prior registry review documents."""

    # Patterns that indicate a registry review document
    REVIEW_INDICATORS = [
        # Explicit review headers
        r"registry\s+review",
        r"review\s+report",
        r"compliance\s+review",
        r"validation\s+report",
        r"verification\s+report",

        # Review-specific sections
        r"review\s+findings",
        r"reviewer\s+comments",
        r"non-conformance",
        r"corrective\s+action\s+request",
        r"CAR\s*[-:]",  # CAR: Corrective Action Request

        # Review status indicators
        r"approved\s+with\s+conditions",
        r"pending\s+clarification",
        r"review\s+status",
    ]

    # Patterns for extracting review metadata (capture 2-4 capitalized words for name)
    # Handles markdown bold syntax: **Label:** Value or Label: Value
    REVIEWER_PATTERNS = [
        r"\*\*Reviewed\s+[Bb]y:\*\*\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        r"\*\*Reviewer:\*\*\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        r"\*\*Lead\s+[Rr]eviewer:\*\*\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        r"[Rr]eviewed\s+by[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?=\s*\n|\s*$)",
        r"[Rr]eviewer[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?=\s*\n|\s*$)",
        r"[Ll]ead\s+[Rr]eviewer[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})(?=\s*\n|\s*$)",
    ]

    REVIEW_DATE_PATTERNS = [
        r"\*\*Review\s+Date:\*\*\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"\*\*Date\s+of\s+Review:\*\*\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"[Rr]eview\s+[Dd]ate[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"[Dd]ate\s+of\s+[Rr]eview[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"[Rr]eviewed\s+on[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
    ]

    REVIEW_STATUS_PATTERNS = [
        r"\*\*Overall\s+Status:\*\*\s+(\w+(?:\s+\w+)*)",
        r"\*\*Review\s+Status:\*\*\s+(\w+(?:\s+\w+)*)",
        r"\*\*Decision:\*\*\s+(\w+(?:\s+\w+)*)",
        r"[Rr]eview\s+[Ss]tatus[:\s]+(\w+(?:\s+\w+)*)",
        r"[Oo]verall\s+[Ss]tatus[:\s]+(\w+(?:\s+\w+)*)",
        r"[Dd]ecision[:\s]+(\w+(?:\s+\w+)*)",
    ]

    # Requirement reference patterns (e.g., "REQ-001", "Requirement 3.2")
    REQUIREMENT_REF_PATTERNS = [
        r"(REQ-\d{3,4})",  # REQ-001, REQ-0042
        r"requirement\s+(\d+(?:\.\d+)*)",  # Requirement 3.2
        r"section\s+(\d+(?:\.\d+)*)\s+requirement",  # Section 3.2 requirement
    ]

    # Finding/status patterns
    FINDING_PATTERNS = [
        r"(?:finding|status)[:\s]+([\w\-]+(?:\s+[\w\-]+)*)",  # Finding: Conformant or Non-Conformant
        r"✓\s*([\w\-]+(?:\s+[\w\-]+)*)",  # ✓ Conformant
        r"✗\s*([\w\-]+(?:\s+[\w\-]+)*)",  # ✗ Non-Conformant
        r"\[([xX✓✗])\]",  # [x] or [✓]
    ]

    def __init__(self):
        """Initialize prior review detector."""
        self.compiled_indicators = [
            re.compile(p, re.IGNORECASE) for p in self.REVIEW_INDICATORS
        ]
        self.compiled_reviewer = [
            re.compile(p, re.IGNORECASE) for p in self.REVIEWER_PATTERNS
        ]
        self.compiled_date = [
            re.compile(p, re.IGNORECASE) for p in self.REVIEW_DATE_PATTERNS
        ]
        self.compiled_status = [
            re.compile(p, re.IGNORECASE) for p in self.REVIEW_STATUS_PATTERNS
        ]
        self.compiled_requirement_refs = [
            re.compile(p, re.IGNORECASE) for p in self.REQUIREMENT_REF_PATTERNS
        ]
        self.compiled_findings = [
            re.compile(p, re.IGNORECASE) for p in self.FINDING_PATTERNS
        ]

    def is_prior_review(self, text: str, filename: str = "") -> dict[str, Any]:
        """Detect if document is a prior registry review.

        Args:
            text: Document text (markdown preferred)
            filename: Document filename

        Returns:
            Dictionary with:
                - is_review: bool - Whether document is a review
                - confidence: float (0.0-1.0)
                - indicators_found: list[str] - Which indicators were matched
                - indicator_count: int - Number of indicators found
        """
        indicators_found = []

        # Check filename first
        if filename:
            filename_lower = filename.lower()
            if any(word in filename_lower for word in ["review", "validation", "verification"]):
                indicators_found.append(f"filename: {filename}")

        # Search text (first 10000 chars - review indicators usually appear early)
        search_text = text[:10000] if len(text) > 10000 else text

        for i, pattern in enumerate(self.compiled_indicators):
            matches = pattern.findall(search_text)
            if matches:
                indicator_text = self.REVIEW_INDICATORS[i]
                indicators_found.append(f"content: {indicator_text}")

        indicator_count = len(indicators_found)

        # Calculate confidence
        # High confidence: 3+ indicators
        # Medium confidence: 2 content indicators
        # Require at least 2 content indicators to consider it a review

        # Count content indicators (not filename)
        content_indicator_count = sum(1 for ind in indicators_found if "content:" in ind)

        if indicator_count >= 3 and content_indicator_count >= 2:
            confidence = 0.95
            is_review = True
        elif content_indicator_count >= 2:
            confidence = 0.75
            is_review = True
        elif content_indicator_count == 1:
            # Single content indicator - not enough
            confidence = 0.40
            is_review = False
        elif indicator_count == 1:  # Filename only
            confidence = 0.30
            is_review = False
        else:
            confidence = 0.0
            is_review = False

        return {
            "is_review": is_review,
            "confidence": round(confidence, 2),
            "indicators_found": indicators_found[:5],  # Limit to top 5
            "indicator_count": indicator_count,
        }

    def extract_review_metadata(self, text: str, filename: str = "") -> dict[str, Any]:
        """Extract review metadata from document.

        Args:
            text: Document text
            filename: Document filename

        Returns:
            Dictionary with:
                - reviewer: str | None - Reviewer name
                - review_date: str | None - Review date
                - review_status: str | None - Overall status
                - confidence: float - Confidence in metadata extraction
        """
        metadata = {
            "reviewer": None,
            "review_date": None,
            "review_status": None,
            "confidence": 0.0,
        }

        # Search text (first 5000 chars - metadata usually at start)
        search_text = text[:5000] if len(text) > 5000 else text

        # Extract reviewer
        for pattern in self.compiled_reviewer:
            match = pattern.search(search_text)
            if match:
                metadata["reviewer"] = match.group(1).strip()
                break

        # Extract review date
        for pattern in self.compiled_date:
            match = pattern.search(search_text)
            if match:
                metadata["review_date"] = match.group(1).strip()
                break

        # Extract review status
        for pattern in self.compiled_status:
            match = pattern.search(search_text)
            if match:
                status_text = match.group(1).strip()
                # Normalize common status values
                status_lower = status_text.lower()
                if "approved" in status_lower:
                    metadata["review_status"] = "Approved"
                elif "pending" in status_lower:
                    metadata["review_status"] = "Pending"
                elif "rejected" in status_lower or "non-conformant" in status_lower:
                    metadata["review_status"] = "Non-Conformant"
                else:
                    metadata["review_status"] = status_text
                break

        # Calculate confidence based on fields found
        fields_found = sum(1 for v in [metadata["reviewer"], metadata["review_date"], metadata["review_status"]] if v is not None)

        if fields_found == 3:
            metadata["confidence"] = 0.90
        elif fields_found == 2:
            metadata["confidence"] = 0.70
        elif fields_found == 1:
            metadata["confidence"] = 0.50
        else:
            metadata["confidence"] = 0.0

        return metadata

    def parse_review_findings(self, text: str) -> list[dict[str, Any]]:
        """Parse review findings from document.

        Extracts individual requirement reviews with their findings.

        Args:
            text: Document text (markdown preferred)

        Returns:
            List of finding dictionaries with:
                - requirement_ref: str - Requirement reference (e.g., "REQ-001")
                - finding: str - Finding status (e.g., "Conformant")
                - evidence_snippet: str - Evidence text
                - line_number: int - Line in document
        """
        findings = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines):
            # Look for requirement references
            requirement_ref = None
            for pattern in self.compiled_requirement_refs:
                match = pattern.search(line)
                if match:
                    requirement_ref = match.group(1).strip()
                    break

            if not requirement_ref:
                continue

            # Look for finding status in same line or next few lines
            finding_status = None
            evidence_lines = []

            # Check current line and next 5 lines for finding
            for offset in range(6):
                check_line_num = line_num + offset
                if check_line_num >= len(lines):
                    break

                check_line = lines[check_line_num]

                # Collect evidence snippets (lines that look like evidence)
                if offset > 0 and check_line.strip():
                    # Look for lines with "Evidence:", bullet points, or citations
                    if any(indicator in check_line.lower() for indicator in ['evidence:', 'see:', 'page', '§', 'section']):
                        evidence_lines.append(check_line.strip())

                # First priority: check for checkmark symbols (most reliable)
                if finding_status is None:
                    if '✓' in check_line:
                        finding_status = "Conformant"
                        continue  # Keep looking for evidence
                    elif '✗' in check_line:
                        finding_status = "Non-Conformant"
                        continue  # Keep looking for evidence

                # Second priority: look for finding patterns
                if finding_status is None:
                    for pattern in self.compiled_findings:
                        match = pattern.search(check_line)
                        if match:
                            finding_text = match.group(1).strip()
                            # Normalize finding status
                            finding_lower = finding_text.lower()
                            if finding_lower in ['x', 'conformant', 'compliant', 'met']:
                                finding_status = "Conformant"
                            elif finding_lower in ['non-conformant', 'not met', 'pending']:
                                finding_status = "Non-Conformant"
                            else:
                                finding_status = finding_text
                            break

            # Create finding record
            if requirement_ref:
                finding_record = {
                    "requirement_ref": requirement_ref,
                    "finding": finding_status or "Unknown",
                    "evidence_snippet": " ".join(evidence_lines[:3]) if evidence_lines else "",
                    "line_number": line_num + 1,  # 1-indexed
                }
                findings.append(finding_record)

        return findings

    def extract_prior_evidence(self, text: str, requirement_id: str) -> list[dict[str, Any]]:
        """Extract prior evidence for a specific requirement.

        Args:
            text: Document text
            requirement_id: Requirement ID to search for (e.g., "REQ-001")

        Returns:
            List of evidence snippets with:
                - text: str - Evidence text
                - line_number: int - Line in document
                - confidence: float - Relevance confidence
        """
        evidence_snippets = []
        lines = text.split('\n')

        # Normalize requirement ID for matching
        req_id_normalized = requirement_id.upper().strip()

        # Find lines mentioning this requirement
        for line_num, line in enumerate(lines):
            if req_id_normalized in line.upper():
                # Extract context (current line + next 10 lines)
                context_lines = lines[line_num:min(line_num + 10, len(lines))]

                # Look for evidence indicators
                for offset, context_line in enumerate(context_lines):
                    context_lower = context_line.lower()
                    if any(indicator in context_lower for indicator in ['evidence:', 'documented in', 'see page', 'section']):
                        # Calculate confidence based on evidence quality indicators
                        confidence = 0.6  # Base confidence

                        if 'page' in context_lower or '§' in context_line:
                            confidence += 0.2  # Has citation

                        if len(context_line.strip()) > 50:
                            confidence += 0.1  # Substantial text

                        evidence_snippets.append({
                            "text": context_line.strip(),
                            "line_number": line_num + offset + 1,
                            "confidence": min(round(confidence, 2), 1.0),
                        })

        return evidence_snippets

    def analyze_document(self, text: str, filename: str = "") -> dict[str, Any]:
        """Comprehensive prior review analysis.

        Args:
            text: Document text
            filename: Document filename

        Returns:
            Complete analysis with detection, metadata, and findings
        """
        # Step 1: Detect if this is a review
        detection = self.is_prior_review(text, filename)

        if not detection["is_review"]:
            return {
                "is_prior_review": False,
                "confidence": detection["confidence"],
                "reason": "No review indicators found",
            }

        # Step 2: Extract metadata
        metadata = self.extract_review_metadata(text, filename)

        # Step 3: Parse findings
        findings = self.parse_review_findings(text)

        # Step 4: Calculate overall confidence
        overall_confidence = (detection["confidence"] + metadata["confidence"]) / 2

        return {
            "is_prior_review": True,
            "confidence": round(overall_confidence, 2),
            "detection": detection,
            "metadata": metadata,
            "findings": findings,
            "findings_count": len(findings),
            "analyzed_at": datetime.now().isoformat(),
        }


# Singleton instance
_prior_review_detector = None


def get_prior_review_detector() -> PriorReviewDetector:
    """Get singleton prior review detector instance."""
    global _prior_review_detector
    if _prior_review_detector is None:
        _prior_review_detector = PriorReviewDetector()
    return _prior_review_detector
