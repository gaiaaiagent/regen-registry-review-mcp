"""Tests for prior review detection and parsing."""

import pytest

from registry_review_mcp.intelligence.prior_review_detector import PriorReviewDetector


class TestPriorReviewDetection:
    """Test prior review document detection."""

    def test_detect_from_filename(self):
        """Test detecting review from filename (low confidence, needs content too)."""
        detector = PriorReviewDetector()

        result = detector.is_prior_review(
            text="",
            filename="Registry_Review_Report_2023.pdf"
        )

        # Filename alone is not enough - need content indicators too
        assert result["is_review"] is False  # Changed: filename alone not sufficient
        assert result["confidence"] < 0.5  # Low confidence
        assert "filename" in result["indicators_found"][0]

    def test_detect_from_content_high_confidence(self):
        """Test detecting review from content with high confidence."""
        detector = PriorReviewDetector()

        content = """
        # Registry Review Report

        ## Review Findings

        This document contains the registry review findings for Project C06-4997.

        ### Corrective Action Requests (CARs)

        CAR-001: Missing baseline documentation
        """

        result = detector.is_prior_review(content, filename="")

        assert result["is_review"] is True
        assert result["confidence"] >= 0.9  # Multiple indicators
        assert result["indicator_count"] >= 3

    def test_detect_from_content_medium_confidence(self):
        """Test medium confidence detection."""
        detector = PriorReviewDetector()

        content = """
        Project Review

        Review Status: Approved with conditions
        """

        result = detector.is_prior_review(content, filename="")

        assert result["is_review"] is True
        assert 0.5 <= result["confidence"] < 0.9
        assert result["indicator_count"] == 2

    def test_not_a_review(self):
        """Test when document is not a review."""
        detector = PriorReviewDetector()

        content = """
        Project Plan

        This is a standard project plan with no review content.
        """

        result = detector.is_prior_review(content, filename="ProjectPlan.pdf")

        assert result["is_review"] is False
        assert result["confidence"] == 0.0


class TestReviewMetadataExtraction:
    """Test review metadata extraction."""

    def test_extract_reviewer(self):
        """Test extracting reviewer name."""
        detector = PriorReviewDetector()

        content = """
        Registry Review Report

        Reviewed by: John Smith
        Review Date: 12/15/2023
        """

        result = detector.extract_review_metadata(content, filename="")

        assert result["reviewer"] == "John Smith"
        assert result["review_date"] == "12/15/2023"

    def test_extract_review_status(self):
        """Test extracting review status."""
        detector = PriorReviewDetector()

        content = """
        Review Status: Approved with conditions

        Overall assessment shows compliance with minor clarifications needed.
        """

        result = detector.extract_review_metadata(content, filename="")

        assert result["review_status"] == "Approved"
        assert result["confidence"] > 0.0

    def test_extract_all_metadata(self):
        """Test extracting complete metadata."""
        detector = PriorReviewDetector()

        content = """
        # Registry Review Report

        Lead Reviewer: Sarah Johnson
        Date of Review: 03/20/2024
        Review Status: Approved

        ## Summary
        This project meets all requirements.
        """

        result = detector.extract_review_metadata(content, filename="")

        assert result["reviewer"] == "Sarah Johnson"
        assert result["review_date"] == "03/20/2024"
        assert result["review_status"] == "Approved"
        assert result["confidence"] >= 0.8  # All fields found

    def test_partial_metadata(self):
        """Test when only some metadata is present."""
        detector = PriorReviewDetector()

        content = """
        Review Report

        Reviewed by: Alice Brown

        No date or status information available.
        """

        result = detector.extract_review_metadata(content, filename="")

        assert result["reviewer"] == "Alice Brown"
        assert result["review_date"] is None
        assert result["review_status"] is None
        assert result["confidence"] > 0.0  # Some fields found


class TestReviewFindingsParsing:
    """Test parsing of review findings."""

    def test_parse_simple_finding(self):
        """Test parsing a simple finding."""
        detector = PriorReviewDetector()

        content = """
        ## Requirements Review

        REQ-001: Project Description
        Finding: Conformant
        Evidence: See Project Plan, page 3
        """

        findings = detector.parse_review_findings(content)

        assert len(findings) >= 1
        assert findings[0]["requirement_ref"] == "REQ-001"
        assert findings[0]["finding"] == "Conformant"

    def test_parse_multiple_findings(self):
        """Test parsing multiple findings."""
        detector = PriorReviewDetector()

        content = """
        ## Requirements Review

        REQ-001: Project Description
        ✓ Conformant

        REQ-002: Baseline Assessment
        ✗ Non-Conformant

        REQ-003: Monitoring Plan
        ✓ Conformant
        """

        findings = detector.parse_review_findings(content)

        assert len(findings) == 3
        assert findings[0]["requirement_ref"] == "REQ-001"
        assert findings[0]["finding"] == "Conformant"
        assert findings[1]["requirement_ref"] == "REQ-002"
        assert findings[1]["finding"] == "Non-Conformant"
        assert findings[2]["requirement_ref"] == "REQ-003"

    def test_parse_with_evidence_snippets(self):
        """Test parsing findings with evidence."""
        detector = PriorReviewDetector()

        content = """
        Requirement 3.2: Land Tenure Documentation
        Finding: Conformant
        Evidence: Land ownership documents provided in Annex A, page 12
        See: Section 2.3 of Project Plan
        """

        findings = detector.parse_review_findings(content)

        assert len(findings) >= 1
        finding = findings[0]
        assert finding["requirement_ref"] == "3.2"
        assert finding["finding"] == "Conformant"
        assert len(finding["evidence_snippet"]) > 0
        assert "page 12" in finding["evidence_snippet"] or "Section 2.3" in finding["evidence_snippet"]

    def test_parse_checkbox_findings(self):
        """Test parsing checkbox-style findings."""
        detector = PriorReviewDetector()

        content = """
        Requirements Checklist:

        [x] REQ-001: Project boundaries defined
        [ ] REQ-002: Stakeholder consultation
        [✓] REQ-003: Risk assessment completed
        """

        findings = detector.parse_review_findings(content)

        # Should find at least the requirements mentioned
        assert len(findings) >= 1
        requirement_refs = [f["requirement_ref"] for f in findings]
        assert any("001" in ref for ref in requirement_refs)


class TestPriorEvidenceExtraction:
    """Test extracting prior evidence for specific requirements."""

    def test_extract_evidence_for_requirement(self):
        """Test extracting evidence for a specific requirement."""
        detector = PriorReviewDetector()

        content = """
        ## REQ-001: Project Description

        Evidence: Project description documented in Section 1.2 of the Project Plan.
        See page 5 for complete details.

        The project area is clearly defined with coordinates provided.
        """

        evidence = detector.extract_prior_evidence(content, "REQ-001")

        assert len(evidence) >= 1
        assert "page 5" in evidence[0]["text"] or "Section 1.2" in evidence[0]["text"]
        assert evidence[0]["confidence"] > 0.5

    def test_extract_evidence_with_citations(self):
        """Test evidence with strong citation indicators."""
        detector = PriorReviewDetector()

        content = """
        REQ-042: Baseline Carbon Stocks

        Evidence: Documented in Baseline Report § 3.4, page 23-25
        Measurement methodology follows Soil Carbon v1.2.2
        """

        evidence = detector.extract_prior_evidence(content, "REQ-042")

        assert len(evidence) >= 1
        # Should have high confidence due to page numbers and section symbol
        assert evidence[0]["confidence"] >= 0.7

    def test_no_evidence_found(self):
        """Test when no evidence found for requirement."""
        detector = PriorReviewDetector()

        content = """
        This document discusses various topics but does not mention REQ-999.
        """

        evidence = detector.extract_prior_evidence(content, "REQ-999")

        assert len(evidence) == 0


class TestCompleteAnalysis:
    """Test complete prior review analysis."""

    def test_analyze_complete_review_document(self):
        """Test analyzing a complete review document."""
        detector = PriorReviewDetector()

        content = """
        # Registry Review Report

        **Reviewer:** Michael Chen
        **Review Date:** 06/10/2024
        **Overall Status:** Approved with conditions

        ## Review Findings

        ### REQ-001: Project Description
        Finding: Conformant
        Evidence: Project Plan § 1.2, pages 3-5

        ### REQ-002: Baseline Assessment
        Finding: Non-Conformant
        Evidence: Baseline methodology incomplete, see CAR-001

        ### REQ-003: Monitoring Plan
        Finding: Conformant
        Evidence: Monitoring protocol documented in Appendix B

        ## Corrective Action Requests

        CAR-001: Complete baseline carbon stock calculations using approved methodology
        """

        result = detector.analyze_document(content, filename="Review_Report_2024.pdf")

        # Should be detected as a review
        assert result["is_prior_review"] is True
        assert result["confidence"] >= 0.7

        # Should extract metadata
        metadata = result["metadata"]
        assert metadata["reviewer"] == "Michael Chen"
        assert metadata["review_date"] == "06/10/2024"
        assert metadata["review_status"] == "Approved"

        # Should parse findings
        assert result["findings_count"] >= 3
        findings = result["findings"]
        req_refs = [f["requirement_ref"] for f in findings]
        assert "REQ-001" in req_refs
        assert "REQ-002" in req_refs
        assert "REQ-003" in req_refs

    def test_analyze_non_review_document(self):
        """Test analyzing a non-review document."""
        detector = PriorReviewDetector()

        content = """
        # Project Plan

        This is a standard project plan with project description,
        baseline information, and monitoring protocols.

        No review findings or reviewer information.
        """

        result = detector.analyze_document(content, filename="ProjectPlan.pdf")

        assert result["is_prior_review"] is False
        assert result["confidence"] < 0.5
        assert "reason" in result

    def test_analyze_borderline_document(self):
        """Test analyzing a borderline case."""
        detector = PriorReviewDetector()

        content = """
        Project Validation Report

        This report validates the project design but is not a full review.
        """

        result = detector.analyze_document(content, filename="Validation.pdf")

        # May or may not be detected as review depending on content
        # Just verify the structure is correct
        assert "is_prior_review" in result
        assert "confidence" in result
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0
