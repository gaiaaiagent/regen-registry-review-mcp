"""Tests for intelligent metadata extraction."""

import pytest

from registry_review_mcp.intelligence.metadata_extractors import MetadataExtractor


class TestProjectIDExtraction:
    """Test project ID extraction."""

    def test_extract_from_filename(self):
        """Test extracting project ID from filename."""
        extractor = MetadataExtractor()

        result = extractor.extract_project_id(
            text="",
            filename="C06-4997_ProjectPlan.pdf"
        )

        assert result["project_id"] == "C06-4997"
        assert result["confidence"] > 0.7
        assert "filename" in result["sources"][0]

    def test_extract_from_content(self):
        """Test extracting project ID from document content."""
        extractor = MetadataExtractor()

        content = """
        Project Plan

        Project ID: C06-4997
        Project Name: Botany Farm Regenerative Agriculture

        This project (C06-4997) applies the Soil Carbon methodology...
        """

        result = extractor.extract_project_id(content, filename="")

        assert result["project_id"] == "C06-4997"
        assert result["confidence"] > 0.5
        assert result["occurrences"] >= 2

    def test_extract_from_both(self):
        """Test extracting from both filename and content (high confidence)."""
        extractor = MetadataExtractor()

        content = "Project C06-4997 is located at Botany Farm. Project ID: C06-4997"

        result = extractor.extract_project_id(
            content,
            filename="BotanyFarm_C06-4997_Baseline.pdf"
        )

        assert result["project_id"] == "C06-4997"
        assert result["confidence"] >= 0.9  # High confidence (both sources)
        assert result["occurrences"] >= 2

    def test_no_project_id(self):
        """Test when no project ID found."""
        extractor = MetadataExtractor()

        result = extractor.extract_project_id(
            "Just some text without a project ID",
            filename="document.pdf"
        )

        assert result["project_id"] is None
        assert result["confidence"] == 0.0


class TestCreditingPeriodExtraction:
    """Test crediting period extraction."""

    def test_extract_from_filename(self):
        """Test extracting year range from filename."""
        extractor = MetadataExtractor()

        result = extractor.extract_crediting_period(
            text="",
            filename="Baseline_Report_2022-2032.pdf"
        )

        assert result["start_year"] == 2022
        assert result["end_year"] == 2032
        assert result["period_string"] == "2022-2032"
        assert result["duration_years"] == 10

    def test_extract_from_content(self):
        """Test extracting year range from content."""
        extractor = MetadataExtractor()

        content = """
        Crediting Period: 2022-2032

        This project will operate over a 10-year crediting period
        from 2022 to 2032.
        """

        result = extractor.extract_crediting_period(content, filename="")

        assert result["start_year"] == 2022
        assert result["end_year"] == 2032
        assert result["confidence"] > 0.5

    def test_no_crediting_period(self):
        """Test when no crediting period found."""
        extractor = MetadataExtractor()

        result = extractor.extract_crediting_period(
            "Some text without dates",
            filename="document.pdf"
        )

        assert result["start_year"] is None
        assert result["end_year"] is None
        assert result["confidence"] == 0.0


class TestMethodologyExtraction:
    """Test methodology extraction."""

    def test_extract_soil_carbon(self):
        """Test extracting Soil Carbon methodology."""
        extractor = MetadataExtractor()

        content = """
        Methodology

        This project applies the Regen Network Soil Carbon v1.2.2
        methodology for carbon credit generation.
        """

        result = extractor.extract_methodology(content, filename="")

        assert result["methodology_name"] == "Soil Carbon"
        assert result["version"] == "1.2.2"
        assert result["full_string"] == "Soil Carbon v1.2.2"
        assert result["confidence"] > 0.5

    def test_extract_grassland(self):
        """Test extracting Grassland methodology."""
        extractor = MetadataExtractor()

        content = "Using Grassland Methodology Version 1.0 for this project."

        result = extractor.extract_methodology(content, filename="")

        assert result["methodology_name"] == "Grassland"
        assert result["version"] == "1.0"

    def test_no_methodology(self):
        """Test when no methodology found."""
        extractor = MetadataExtractor()

        result = extractor.extract_methodology(
            "Just some text",
            filename="document.pdf"
        )

        assert result["methodology_name"] is None
        assert result["version"] is None
        assert result["confidence"] == 0.0


class TestDocumentVersionExtraction:
    """Test document version extraction."""

    def test_extract_version_from_filename(self):
        """Test extracting version from filename."""
        extractor = MetadataExtractor()

        result = extractor.extract_document_version("ProjectPlan_v2.1.pdf")

        assert result["version"] == "2.1"
        assert result["confidence"] == 0.9

    def test_extract_version_underscore_format(self):
        """Test version with underscore format."""
        extractor = MetadataExtractor()

        result = extractor.extract_document_version("Baseline_v1.0.0_final.pdf")

        assert result["version"] == "1.0.0"

    def test_no_version(self):
        """Test when no version in filename."""
        extractor = MetadataExtractor()

        result = extractor.extract_document_version("document.pdf")

        assert result["version"] is None
        assert result["confidence"] == 0.0


class TestCompleteMetadataExtraction:
    """Test extracting all metadata at once."""

    def test_extract_all_from_realistic_document(self):
        """Test extracting all metadata from realistic document."""
        extractor = MetadataExtractor()

        # Simulated document content
        content = """
        # Project Plan

        **Project ID:** C06-4997
        **Project Name:** Botany Farm Regenerative Agriculture
        **Crediting Period:** 2022-2032
        **Methodology:** Regen Network Soil Carbon v1.2.2

        ## 1. Introduction

        This project (C06-4997) will implement regenerative agriculture
        practices over a 10-year period from 2022 to 2032 using the
        Soil Carbon methodology version 1.2.2.
        """

        filename = "C06-4997_ProjectPlan_v2.0.pdf"

        result = extractor.extract_all_metadata(content, filename)

        # Verify all components
        assert result["project_id"]["project_id"] == "C06-4997"
        assert result["project_id"]["confidence"] > 0.8

        assert result["crediting_period"]["start_year"] == 2022
        assert result["crediting_period"]["end_year"] == 2032

        assert result["methodology"]["methodology_name"] == "Soil Carbon"
        assert result["methodology"]["version"] == "1.2.2"

        assert result["document_version"]["version"] == "2.0"

    def test_extract_all_with_missing_data(self):
        """Test extracting when some metadata is missing."""
        extractor = MetadataExtractor()

        content = "Just a document with project C06-4997 and nothing else."
        filename = "document.pdf"

        result = extractor.extract_all_metadata(content, filename)

        # Project ID should be found
        assert result["project_id"]["project_id"] == "C06-4997"

        # Others should be None
        assert result["crediting_period"]["start_year"] is None
        assert result["methodology"]["methodology_name"] is None
        assert result["document_version"]["version"] is None
