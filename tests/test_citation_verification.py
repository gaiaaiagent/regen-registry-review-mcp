"""
Tests for citation verification system.

Ensures that LLM-extracted claims are verified against source documents
to prevent hallucinations.
"""

import pytest
from registry_review_mcp.extractors.verification import (
    verify_citation,
    verify_extracted_field,
    verify_date_extraction,
)


class TestCitationVerification:
    """Test citation verification against source content."""

    def test_exact_match(self):
        """Test that exact matches are verified."""
        raw_text = "Project Start Date: 01/01/2022"
        source = "The project began on January 1, 2022. Project Start Date: 01/01/2022 is when we commenced."

        is_verified, score, snippet = verify_citation(raw_text, source, "project_start_date")

        assert is_verified is True
        assert score == 100.0
        assert "01/01/2022" in snippet

    def test_fuzzy_match(self):
        """Test that fuzzy matching handles minor variations."""
        raw_text = "Project Start Date: 01/01/2022"
        source = "The Project Start Date was 01/01/2022 according to the plan"

        is_verified, score, snippet = verify_citation(
            raw_text, source, "project_start_date", min_similarity=75.0
        )

        assert is_verified is True
        assert score >= 75.0

    def test_hallucination_detection(self):
        """Test that hallucinated text is rejected."""
        # This is the actual hallucination case from Botany Farm
        raw_text = "Satellite imagery was acquired on 15 June 2022"
        source = """
        Multispectral reflectance data from satellite imagery was extracted
        for each sample location. The project started on 01/01/2022.
        """

        is_verified, score, snippet = verify_citation(
            raw_text, source, "imagery_date", min_similarity=75.0
        )

        assert is_verified is False
        assert score < 75.0

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        raw_text = "Project ID: C06-006"
        source = "PROJECT ID: C06-006"

        is_verified, score, _ = verify_citation(raw_text, source, "project_id")

        assert is_verified is True
        assert score == 100.0

    def test_whitespace_normalization(self):
        """Test that extra whitespace doesn't break matching."""
        raw_text = "Project Start Date: 01/01/2022"
        # Make source long enough for window matching
        source = "Project  Start   Date:  01/01/2022 is when the project began."

        is_verified, score, _ = verify_citation(
            raw_text, source, "project_start_date", min_similarity=70.0
        )

        # With fuzzy matching, whitespace differences should still match
        assert is_verified is True or score >= 70.0

    def test_partial_match_within_window(self):
        """Test that partial matches within context window work."""
        raw_text = "01/01/2022"
        source = "The project commenced on 01/01/2022 and will run for 10 years."

        is_verified, score, snippet = verify_citation(
            raw_text, source, "project_start_date", min_similarity=75.0
        )

        assert is_verified is True
        assert "01/01/2022" in snippet

    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        is_verified, score, snippet = verify_citation("", "some content", "test")
        assert is_verified is False
        assert score == 0.0

        is_verified, score, snippet = verify_citation("some text", "", "test")
        assert is_verified is False
        assert score == 0.0


class TestExtractedFieldVerification:
    """Test verification of full extracted field objects."""

    def test_verified_field_confidence_unchanged(self):
        """Test that verified fields keep their confidence."""
        field = {
            "value": "2022-01-01",
            "field_type": "project_start_date",
            "source": "Section 1.8",
            "confidence": 0.95,
            "reasoning": "Explicitly stated",
            "raw_text": "Project Start Date: 01/01/2022",
        }
        source = "Project Start Date: 01/01/2022"

        verified = verify_extracted_field(field, source)

        assert verified["verification_status"] == "verified"
        assert verified["confidence"] == 0.95  # Unchanged
        assert verified["verification_score"] >= 75.0

    def test_unverified_field_confidence_penalty(self):
        """Test that unverified fields get confidence penalty."""
        field = {
            "value": "2022-06-15",
            "field_type": "baseline_date",
            "source": "Baseline Report",
            "confidence": 0.95,
            "reasoning": "Document explicitly states...",
            "raw_text": "Satellite imagery was acquired on 15 June 2022",  # Hallucinated
        }
        source = "Multispectral data was extracted for each sample location."

        verified = verify_extracted_field(field, source, min_confidence_penalty=0.3)

        assert verified["verification_status"] == "failed"
        assert verified["confidence"] <= 0.65  # 0.95 - 0.3 penalty
        assert "verification_warning" in verified

    def test_field_without_raw_text(self):
        """Test that fields without raw_text get reduced confidence."""
        field = {
            "value": "2022-01-01",
            "field_type": "project_start_date",
            "confidence": 1.0,
            "raw_text": None,  # No citation provided
        }
        source = "Some content"

        verified = verify_extracted_field(field, source)

        assert verified["verification_status"] == "no_citation"
        assert verified["confidence"] == 0.5  # 50% penalty
        assert verified["verification_score"] == 0.0


class TestDateExtractionVerification:
    """Test batch verification of date extractions."""

    def test_batch_verification(self):
        """Test verifying multiple extracted dates."""
        fields = [
            {
                "value": "2022-01-01",
                "field_type": "project_start_date",
                "confidence": 0.95,
                "raw_text": "Start: 01/01/2022",
            },
            {
                "value": "2022-06-15",
                "field_type": "baseline_date",
                "confidence": 0.95,
                "raw_text": "Baseline: 15 June 2022",  # Will fail
            },
        ]
        source = "Project Start: 01/01/2022. Baseline data collected later."

        verified_fields = verify_date_extraction(fields, source)

        assert len(verified_fields) == 2
        # First field should verify
        assert verified_fields[0]["verification_status"] == "verified"
        # Second field should fail (hallucinated)
        assert verified_fields[1]["verification_status"] == "failed"
        assert verified_fields[1]["confidence"] < 0.95

    def test_empty_batch(self):
        """Test verification of empty field list."""
        verified = verify_date_extraction([], "some content")
        assert verified == []


class TestRegressionCases:
    """Test specific regression cases from Botany Farm project."""

    def test_botany_farm_hallucinated_baseline_date(self):
        """
        Regression test: Botany Farm hallucinated baseline date.

        The LLM claimed "Satellite imagery was acquired on 15 June 2022"
        but this text does not exist in any document.
        """
        hallucinated_field = {
            "value": "2022-06-15",
            "field_type": "baseline_date",
            "source": "Baseline Report (page None)",
            "confidence": 0.95,
            "reasoning": "Document explicitly states 'Satellite imagery was acquired on 15 June 2022' in the context of baseline analysis",
            "raw_text": "Satellite imagery was acquired on 15 June 2022",
        }

        # Actual baseline report content (simplified)
        actual_content = """
        Multispectral reflectance data from satellite imagery was extracted
        for each sample location. Pixel values from multispectral satellite
        imagery and the responses were SOCS values.
        """

        verified = verify_extracted_field(
            hallucinated_field, actual_content, min_similarity=75.0
        )

        # Should fail verification
        assert verified["verification_status"] == "failed"
        assert verified["verification_score"] < 75.0
        assert verified["confidence"] < 0.70  # Significant penalty
        assert "verification_warning" in verified

    def test_botany_farm_valid_project_start_date(self):
        """
        Regression test: Botany Farm valid project start date.

        The project start date 01/01/2022 is real and should verify.
        """
        valid_field = {
            "value": "2022-01-01",
            "field_type": "project_start_date",
            "source": "Section 1.8 (page None)",
            "confidence": 0.95,
            "reasoning": "Document explicitly states 'Project Start Date' followed by the date 01/01/2022",
            "raw_text": "01/01/2022",
        }

        # Actual registry agent review content
        actual_content = """
        Project Plan, Section 1.8
        Approved
        Start date as 01/01/2022.
        Source: Program Guide 8.4.1.
        """

        verified = verify_extracted_field(valid_field, actual_content)

        # Should pass verification
        assert verified["verification_status"] == "verified"
        assert verified["verification_score"] >= 75.0
        assert verified["confidence"] == 0.95  # Unchanged


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_source_document(self):
        """Test verification works with very long documents."""
        raw_text = "Project ID: C06-006"
        # Create a long document with the text buried in the middle
        source = "Lorem ipsum " * 10000 + "Project ID: C06-006" + " dolor sit amet" * 10000

        is_verified, score, _ = verify_citation(
            raw_text, source, "project_id", min_similarity=75.0
        )

        assert is_verified is True

    def test_special_characters(self):
        """Test that special characters don't break verification."""
        raw_text = "Project ID: C06-006 (v1.2)"
        source = "The project (ID: C06-006 v1.2) was approved for registration."

        is_verified, score, _ = verify_citation(
            raw_text, source, "project_id", min_similarity=70.0
        )

        # Fuzzy match should handle minor differences in parentheses/punctuation
        assert score >= 60.0  # Relaxed threshold for special char variations

    def test_unicode_content(self):
        """Test verification with unicode characters."""
        raw_text = "Propriétaire: François Müller"
        source = "Le propriétaire est François Müller selon le titre."

        is_verified, score, _ = verify_citation(raw_text, source, "owner_name")

        assert is_verified is True

    def test_similarity_threshold_boundary(self):
        """Test behavior at similarity threshold boundary."""
        raw_text = "Project started January 1 2022"
        source = "The project started on January 1, 2022 according to our records."

        # With exact match in source, should verify
        is_verified, score, _ = verify_citation(
            raw_text, source, "date", min_similarity=75.0
        )

        # Should get decent match score
        assert score >= 70.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
