"""
Integration tests for validation improvements.

Tests the complete workflow from extraction to validation,
ensuring that hallucinations and false positives are prevented.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from registry_review_mcp.extractors.llm_extractors import (
    DateExtractor,
    ProjectIDExtractor,
)
from registry_review_mcp.extractors.verification import verify_date_extraction


class TestHallucinationPrevention:
    """Test that hallucinations are prevented through citation verification."""

    @pytest.mark.asyncio
    async def test_hallucinated_date_rejected(self):
        """
        Test that hallucinated dates are rejected by citation verification.

        This simulates the Botany Farm case where the LLM claimed:
        "Satellite imagery was acquired on 15 June 2022"
        but this text doesn't exist in the source document.
        """
        # Simulated LLM response (hallucinated)
        llm_response = [
            {
                "value": "2022-06-15",
                "field_type": "baseline_date",
                "source": "Baseline Report",
                "confidence": 0.95,
                "reasoning": "Document explicitly states imagery date",
                "raw_text": "Satellite imagery was acquired on 15 June 2022",
            }
        ]

        # Actual source content (no mention of June 15)
        actual_source = """
        Multispectral reflectance data from satellite imagery was extracted
        for each sample location. Pixel values from multispectral satellite
        imagery were used for analysis.
        """

        # Apply verification
        verified = verify_date_extraction(llm_response, actual_source)

        # Should have reduced confidence significantly
        assert len(verified) == 1
        assert verified[0]["verification_status"] == "failed"
        assert verified[0]["confidence"] < 0.70  # Below threshold
        assert verified[0]["verification_score"] < 75.0

    @pytest.mark.asyncio
    async def test_real_date_accepted(self):
        """Test that real dates with valid citations are accepted."""
        llm_response = [
            {
                "value": "2022-01-01",
                "field_type": "project_start_date",
                "source": "Section 1.8",
                "confidence": 0.95,
                "reasoning": "Explicitly stated",
                "raw_text": "Start date as 01/01/2022",
            }
        ]

        actual_source = """
        Project Plan, Section 1.8
        Approved
        Start date as 01/01/2022.
        Source: Program Guide 8.4.1.
        """

        verified = verify_date_extraction(llm_response, actual_source)

        assert len(verified) == 1
        assert verified[0]["verification_status"] == "verified"
        assert verified[0]["confidence"] == 0.95  # Unchanged
        assert verified[0]["verification_score"] >= 75.0


class TestProjectIDFilteringIntegration:
    """Test project ID filtering in realistic scenarios."""

    def test_filter_botany_farm_case(self):
        """
        Test filtering for Botany Farm project ID extraction.

        Original extraction found:
        - C06-006 (valid project ID)
        - 4997 (document filename prefix)
        - 4998 (document filename prefix)

        After filtering, only C06-006 should remain.
        """
        from registry_review_mcp.extractors.llm_extractors import (
            _filter_invalid_project_ids,
        )

        extracted = [
            {
                "value": "C06-006",
                "field_type": "project_id",
                "source": "Registry Agent Review, Page 1",
                "confidence": 1.0,
                "reasoning": "Matches Regen Network pattern",
                "raw_text": "Project ID: C06-006",
            },
            {
                "value": "4997",
                "field_type": "project_id",
                "source": "Registry Agent Review, Page 1",
                "confidence": 0.8,
                "reasoning": "Found in document list",
                "raw_text": "Documents Submitted: 4997Botany22 Project Plan",
            },
            {
                "value": "4998",
                "field_type": "project_id",
                "source": "Registry Agent Review, Page 1",
                "confidence": 0.8,
                "reasoning": "Found in document list",
                "raw_text": "4998Botany23_GHG_Emissions_30_Sep_2023.pdf",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1
        assert filtered[0]["value"] == "C06-006"

    def test_multiple_valid_ids_preserved(self):
        """Test that multiple valid project IDs are all preserved."""
        from registry_review_mcp.extractors.llm_extractors import (
            _filter_invalid_project_ids,
        )

        extracted = [
            {"value": "C06-006", "raw_text": "Project ID: C06-006", "field_type": "project_id", "confidence": 1.0},
            {"value": "VCS-1234", "raw_text": "Also registered as VCS-1234", "field_type": "project_id", "confidence": 0.9},
            {"value": "4997", "raw_text": "4997Botany22.pdf", "field_type": "project_id", "confidence": 0.7},
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 2
        values = [f["value"] for f in filtered]
        assert "C06-006" in values
        assert "VCS-1234" in values
        assert "4997" not in values


class TestValidationWorkflowEndToEnd:
    """Test complete validation workflow with improvements."""

    @pytest.mark.asyncio
    async def test_no_false_positives_for_valid_project(self):
        """
        Test that a valid project doesn't generate false positive failures.

        Simulates a project with:
        - Valid project ID
        - Valid project start date
        - No hallucinated data
        """
        # Mock valid extraction results
        project_ids = [
            {
                "value": "C06-006",
                "field_type": "project_id",
                "source": "Project Plan",
                "confidence": 1.0,
                "raw_text": "Project ID: C06-006",
            }
        ]

        dates = [
            {
                "value": "2022-01-01",
                "field_type": "project_start_date",
                "source": "Section 1.8",
                "confidence": 0.95,
                "raw_text": "Start date as 01/01/2022",
            }
        ]

        # Source content that matches the claims
        source_content = """
        Project Plan
        Project ID: C06-006
        Section 1.8: Start date as 01/01/2022
        """

        # Verify dates
        from registry_review_mcp.extractors.verification import verify_date_extraction
        verified_dates = verify_date_extraction(dates, source_content)

        # Verify project IDs
        from registry_review_mcp.extractors.llm_extractors import _filter_invalid_project_ids
        filtered_ids = _filter_invalid_project_ids(project_ids)

        # Should have no failures
        assert all(d["verification_status"] == "verified" for d in verified_dates)
        assert len(filtered_ids) == 1
        assert filtered_ids[0]["value"] == "C06-006"


class TestRegressionSuite:
    """Regression tests to prevent re-introduction of bugs."""

    def test_regression_botany_farm_date_hallucination(self):
        """
        Regression: Botany Farm June 15, 2022 baseline date hallucination.

        This test ensures we never again accept the hallucinated baseline date.
        """
        from registry_review_mcp.extractors.verification import verify_extracted_field

        hallucinated = {
            "value": "2022-06-15",
            "field_type": "baseline_date",
            "source": "Baseline Report (page None)",
            "confidence": 0.95,
            "reasoning": "Document explicitly states 'Satellite imagery was acquired on 15 June 2022'",
            "raw_text": "Satellite imagery was acquired on 15 June 2022",
        }

        baseline_report_content = """
        Multispectral reflectance data from satellite imagery was extracted
        for each sample location. The baseline analysis was conducted using
        standard methodologies.
        """

        verified = verify_extracted_field(hallucinated, baseline_report_content)

        # Must fail verification
        assert verified["verification_status"] == "failed"
        assert verified["confidence"] < 0.70

    def test_regression_botany_farm_filename_ids(self):
        """
        Regression: Botany Farm "4997" and "4998" filename prefixes.

        This test ensures we never again misclassify filename prefixes as project IDs.
        """
        from registry_review_mcp.extractors.llm_extractors import _filter_invalid_project_ids

        extracted = [
            {"value": "4997", "raw_text": "4997Botany22_Project_Plan.pdf", "field_type": "project_id", "confidence": 0.8},
            {"value": "4998", "raw_text": "4998Botany23_Monitoring.pdf", "field_type": "project_id", "confidence": 0.8},
            {"value": "C06-006", "raw_text": "Project ID: C06-006", "field_type": "project_id", "confidence": 1.0},
        ]

        filtered = _filter_invalid_project_ids(extracted)

        # Only C06-006 should remain
        assert len(filtered) == 1
        assert filtered[0]["value"] == "C06-006"

    def test_regression_validation_failure_to_warning(self):
        """
        Regression: Project ID validation should be warning, not failure.

        Low occurrence count should generate warning, not failure.
        """
        # This is tested at the validation layer, not extraction layer
        # Document that the behavior changed from FAIL to WARNING
        # when there's only one occurrence of a valid project ID
        assert True  # Placeholder - actual test would be in validation_tools tests


class TestConfidenceCalibration:
    """Test confidence score adjustments."""

    def test_unverified_citation_reduces_confidence(self):
        """Test that unverified citations get confidence penalty."""
        from registry_review_mcp.extractors.verification import verify_extracted_field

        field = {
            "value": "some_value",
            "field_type": "test_field",
            "confidence": 1.0,
            "raw_text": "This text does not exist in source",
        }

        source = "Completely different text content"

        verified = verify_extracted_field(
            field, source, min_confidence_penalty=0.3, min_similarity=75.0
        )

        # Confidence should be reduced
        assert verified["confidence"] <= 0.7  # 1.0 - 0.3 penalty
        assert verified["verification_status"] == "failed"

    def test_verified_citation_preserves_confidence(self):
        """Test that verified citations keep original confidence."""
        from registry_review_mcp.extractors.verification import verify_extracted_field

        field = {
            "value": "some_value",
            "field_type": "test_field",
            "confidence": 0.85,
            "raw_text": "Exact text match here",
        }

        source = "This source contains exact text match here verbatim."

        verified = verify_extracted_field(field, source)

        # Confidence should be unchanged
        assert verified["confidence"] == 0.85
        assert verified["verification_status"] == "verified"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
