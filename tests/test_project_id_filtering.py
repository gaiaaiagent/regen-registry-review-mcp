"""
Tests for project ID filtering logic.

Ensures that document filename prefixes and standalone numbers
are correctly filtered out from project ID extraction.
"""

import pytest
from registry_review_mcp.extractors.llm_extractors import _filter_invalid_project_ids


class TestProjectIDFiltering:
    """Test filtering of invalid project IDs."""

    def test_filter_standalone_numbers(self):
        """Test that standalone numbers are filtered out."""
        extracted = [
            {
                "value": "4997",
                "field_type": "project_id",
                "source": "Document list",
                "confidence": 0.8,
                "raw_text": "4997Botany22",
            },
            {
                "value": "C06-006",
                "field_type": "project_id",
                "source": "Project header",
                "confidence": 1.0,
                "raw_text": "Project ID: C06-006",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1
        assert filtered[0]["value"] == "C06-006"

    def test_filter_filename_prefixes(self):
        """Test that document filename prefixes are filtered."""
        extracted = [
            {
                "value": "4997Botany22",
                "field_type": "project_id",
                "source": "Documents submitted",
                "confidence": 0.7,
                "raw_text": "4997Botany22_Project_Plan.pdf",
            },
            {
                "value": "4998Botany23",
                "field_type": "project_id",
                "source": "Documents submitted",
                "confidence": 0.7,
                "raw_text": "4998Botany23_Monitoring_Report.pdf",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 0  # Both should be filtered

    def test_keep_valid_regen_ids(self):
        """Test that valid Regen Network IDs are kept."""
        extracted = [
            {
                "value": "C06-006",
                "field_type": "project_id",
                "confidence": 1.0,
                "raw_text": "Project ID: C06-006",
            },
            {
                "value": "C12-1234",
                "field_type": "project_id",
                "confidence": 1.0,
                "raw_text": "Project ID: C12-1234",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 2
        assert all(item["value"].startswith("C") for item in filtered)

    def test_keep_valid_vcs_ids(self):
        """Test that valid VCS IDs are kept."""
        extracted = [
            {
                "value": "VCS-1234",
                "field_type": "project_id",
                "confidence": 1.0,
                "raw_text": "VCS Project: VCS-1234",
            },
            {
                "value": "VCS1234",
                "field_type": "project_id",
                "confidence": 1.0,
                "raw_text": "Registry: VCS1234",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 2

    def test_keep_valid_gold_standard_ids(self):
        """Test that valid Gold Standard IDs are kept."""
        extracted = [
            {
                "value": "GS-5678",
                "field_type": "project_id",
                "confidence": 1.0,
                "raw_text": "Gold Standard ID: GS-5678",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1

    def test_filter_document_list_context(self):
        """Test filtering based on document list context."""
        extracted = [
            {
                "value": "4997",
                "field_type": "project_id",
                "confidence": 0.8,
                "raw_text": "Documents Submitted: 4997Botany22_Project_Plan.pdf",
            },
            {
                "value": "C06-006",
                "field_type": "project_id",
                "confidence": 1.0,
                "raw_text": "Project ID: C06-006",  # Separate extraction without doc list context
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        # First should be filtered (document list context)
        # Second should pass (has "Project ID:" context and matches pattern)
        assert len(filtered) == 1
        assert filtered[0]["value"] == "C06-006"

    def test_filter_pdf_extension_context(self):
        """Test filtering when raw_text contains .pdf extension."""
        extracted = [
            {
                "value": "4997",
                "field_type": "project_id",
                "confidence": 0.8,
                "raw_text": "4997Botany22_Public_Project_Plan.pdf",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 0

    def test_keep_project_id_with_context(self):
        """Test that IDs with 'Project ID:' context are kept even if ambiguous pattern."""
        extracted = [
            {
                "value": "CUSTOM-123",
                "field_type": "project_id",
                "confidence": 0.9,
                "raw_text": "Project ID: CUSTOM-123",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1

    def test_empty_input(self):
        """Test handling of empty input."""
        filtered = _filter_invalid_project_ids([])
        assert filtered == []

    def test_missing_raw_text(self):
        """Test handling of missing raw_text field."""
        extracted = [
            {
                "value": "C06-006",
                "field_type": "project_id",
                "confidence": 1.0,
                "raw_text": None,
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        # Should keep if it matches known pattern
        assert len(filtered) == 1


class TestRegressionCasesBotanyFarm:
    """Regression tests for Botany Farm project ID extraction."""

    def test_botany_farm_document_list(self):
        """
        Regression test: Botany Farm project IDs from document list.

        The LLM extracted "4997" and "4998" from the "Documents Submitted" list:
        - 4997Botany22_Project_Plan.pdf
        - 4998Botany23_GHG_Emissions.pdf

        These should be filtered as filename prefixes, not project IDs.
        """
        extracted = [
            {
                "value": "C06-006",
                "field_type": "project_id",
                "source": "Botany_Farm_Project_Registration_Registry_Agent_Review.pdf",
                "confidence": 1.0,
                "raw_text": "Project ID: C06-006",
            },
            {
                "value": "4997",
                "field_type": "project_id",
                "source": "Botany_Farm_Project_Registration_Registry_Agent_Review.pdf",
                "confidence": 0.8,
                "raw_text": "Documents Submitted: 4997Botany22 Project Plan",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        # Should only keep C06-006
        assert len(filtered) == 1
        assert filtered[0]["value"] == "C06-006"

    def test_botany_farm_all_variations(self):
        """Test all ID variations that appeared in Botany Farm extraction."""
        extracted = [
            # Valid project ID
            {"value": "C06-006", "raw_text": "Project ID: C06-006", "field_type": "project_id", "confidence": 1.0},
            # Standalone numbers (should be filtered)
            {"value": "4997", "raw_text": "4997Botany22", "field_type": "project_id", "confidence": 0.8},
            {"value": "4998", "raw_text": "4998Botany23", "field_type": "project_id", "confidence": 0.8},
            # Filename patterns (should be filtered)
            {"value": "4997Botany22", "raw_text": "4997Botany22_Project_Plan.pdf", "field_type": "project_id", "confidence": 0.7},
            {"value": "4998Botany23", "raw_text": "4998Botany23_Monitoring_Report.pdf", "field_type": "project_id", "confidence": 0.7},
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1
        assert filtered[0]["value"] == "C06-006"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_mixed_case_project_id_context(self):
        """Test that 'project id' context check is case-insensitive."""
        extracted = [
            {
                "value": "CUSTOM-ID",
                "field_type": "project_id",
                "confidence": 0.9,
                "raw_text": "PROJECT ID: CUSTOM-ID",
            },
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1

    def test_similar_but_different_numbers(self):
        """Test that similar numbers are handled correctly."""
        extracted = [
            # 3-digit number (should be filtered)
            {"value": "497", "raw_text": "497", "field_type": "project_id", "confidence": 0.5},
            # 4-digit number (should be filtered)
            {"value": "4997", "raw_text": "4997", "field_type": "project_id", "confidence": 0.5},
            # 5-digit number (should be filtered)
            {"value": "49971", "raw_text": "49971", "field_type": "project_id", "confidence": 0.5},
            # Valid pattern
            {"value": "C04-497", "raw_text": "Project ID: C04-497", "field_type": "project_id", "confidence": 1.0},
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1
        assert filtered[0]["value"] == "C04-497"

    def test_climate_action_reserve_ids(self):
        """Test CAR (Climate Action Reserve) ID patterns."""
        extracted = [
            {"value": "CAR1234", "raw_text": "CAR1234", "field_type": "project_id", "confidence": 1.0},
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1

    def test_american_carbon_registry_ids(self):
        """Test ACR (American Carbon Registry) ID patterns."""
        extracted = [
            {"value": "ACR123", "raw_text": "ACR123", "field_type": "project_id", "confidence": 1.0},
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1

    def test_empty_value(self):
        """Test handling of empty values."""
        extracted = [
            {"value": "", "raw_text": "No ID found", "field_type": "project_id", "confidence": 0.0},
            {"value": "C06-006", "raw_text": "Project ID: C06-006", "field_type": "project_id", "confidence": 1.0},
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 1
        assert filtered[0]["value"] == "C06-006"

    def test_whitespace_only_value(self):
        """Test handling of whitespace-only values."""
        extracted = [
            {"value": "   ", "raw_text": "...", "field_type": "project_id", "confidence": 0.5},
        ]

        filtered = _filter_invalid_project_ids(extracted)

        assert len(filtered) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
