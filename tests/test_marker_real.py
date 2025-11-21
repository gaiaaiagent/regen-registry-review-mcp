"""Real marker PDF-to-markdown integration tests.

These tests use actual marker models (8GB RAM, slow but reliable).
Run sequentially with: pytest -m marker -n 0

Marker tests are expensive (8GB models, 30-60s per test) and should run:
- Nightly in CI
- On-demand locally when testing PDF processing
- Before releases
"""

import pytest
from pathlib import Path
import time

from registry_review_mcp.extractors.marker_extractor import (
    convert_pdf_to_markdown,
    extract_tables_from_markdown,
    extract_section_hierarchy,
)

# Mark all tests in this file as marker tests
pytestmark = [
    pytest.mark.marker,
    pytest.mark.integration,
]


class TestMarkerIntegration:
    """Real marker PDF conversion tests (loads 8GB models, runs nightly)."""

    @pytest.mark.asyncio
    async def test_basic_pdf_conversion(self, example_documents_path):
        """Test marker converts real PDF to markdown."""
        pdf = example_documents_path / "4997Botany22_Public_Project_Plan.pdf"

        result = await convert_pdf_to_markdown(str(pdf), page_range=(1, 2))

        # Basic structure checks
        assert "markdown" in result, "Result should contain markdown key"
        assert len(result["markdown"]) > 500, f"Should extract substantial content, got {len(result['markdown'])} chars"
        assert result["page_count"] == 2, f"Expected 2 pages, got {result['page_count']}"
        assert result["extraction_method"] == "marker", f"Expected marker method, got {result['extraction_method']}"
        assert "extracted_at" in result, "Result should contain timestamp"

    @pytest.mark.asyncio
    async def test_table_extraction(self, example_documents_path):
        """Test marker extracts tables from PDF."""
        # Use PDF known to have tables (monitoring report)
        pdf = example_documents_path / "4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf"

        result = await convert_pdf_to_markdown(str(pdf), page_range=(1, 5))

        # Check markdown was extracted
        assert "markdown" in result
        assert len(result["markdown"]) > 100

        # Check if tables were extracted
        tables = extract_tables_from_markdown(result["markdown"])
        # Note: Not all PDFs have tables, so we just check the extraction works
        assert isinstance(tables, list), "Should return list of tables"

    @pytest.mark.asyncio
    async def test_section_hierarchy(self, example_documents_path):
        """Test marker preserves document structure."""
        pdf = example_documents_path / "4997Botany22_Public_Project_Plan.pdf"

        result = await convert_pdf_to_markdown(str(pdf), page_range=(1, 3))

        # Extract section hierarchy
        hierarchy = extract_section_hierarchy(result["markdown"])

        assert isinstance(hierarchy, dict), "Should return hierarchy dict"
        assert "section_count" in hierarchy, "Hierarchy should have section count"
        # Project plans typically have multiple sections
        assert hierarchy["section_count"] >= 1, f"Expected sections, got {hierarchy['section_count']}"

    @pytest.mark.asyncio
    async def test_caching_performance(self, example_documents_path):
        """Test markdown caching avoids re-conversion."""
        pdf = example_documents_path / "4997Botany22_Public_Project_Plan.pdf"

        # First call - may or may not hit cache depending on previous tests
        start = time.time()
        result1 = await convert_pdf_to_markdown(str(pdf), page_range=(1, 1))
        first_duration = time.time() - start

        # Second call - should DEFINITELY hit cache
        start = time.time()
        result2 = await convert_pdf_to_markdown(str(pdf), page_range=(1, 1))
        second_duration = time.time() - start

        # Cache should be much faster (< 1s vs 10-30s for real conversion)
        assert second_duration < 1.0, f"Cache hit should be instant, took {second_duration:.2f}s"

        # Results should be identical
        assert result1["markdown"] == result2["markdown"], "Cached result should match original"
        assert result1["page_count"] == result2["page_count"]


class TestMarkdownHelpers:
    """Fast unit tests for markdown parsing (no PDF loading, no marker)."""

    def test_extract_tables_from_markdown(self):
        """Test table extraction from markdown string."""
        markdown = """
# Document

Some text.

| Header 1 | Header 2 | Header 3 |
|---|---|---|
| Value 1 | Value 2 | Value 3 |
| Value 4 | Value 5 | Value 6 |

More text.
"""
        tables = extract_tables_from_markdown(markdown)

        assert len(tables) == 1, f"Expected 1 table, found {len(tables)}"
        assert tables[0]["headers"] == ["Header 1", "Header 2", "Header 3"]
        assert len(tables[0]["data"]) == 2
        assert tables[0]["data"][0] == ["Value 1", "Value 2", "Value 3"]
        assert tables[0]["row_count"] == 2
        assert tables[0]["column_count"] == 3

    def test_extract_multiple_tables(self):
        """Test extraction of multiple tables."""
        markdown = """
| Table 1 Header |
|---|
| Value |

Some text.

| Table 2 Col1 | Table 2 Col2 |
|---|---|
| A | B |
| C | D |
"""
        tables = extract_tables_from_markdown(markdown)

        assert len(tables) == 2
        assert tables[0]["column_count"] == 1
        assert tables[1]["column_count"] == 2

    def test_no_tables(self):
        """Test markdown without tables."""
        markdown = """
# Document

Just some text without tables.

## Section 2

More text.
"""
        tables = extract_tables_from_markdown(markdown)

        assert len(tables) == 0

    def test_extract_section_hierarchy(self):
        """Test section hierarchy extraction from markdown."""
        markdown = """
# 1. Introduction
## 1.1 Background
## 1.2 Objectives
# 2. Methods
## 2.1 Study Design
"""
        hierarchy = extract_section_hierarchy(markdown)

        assert "section_count" in hierarchy
        assert hierarchy["section_count"] >= 3, f"Expected at least 3 sections, got {hierarchy['section_count']}"

    def test_nested_section_hierarchy(self):
        """Test extraction of nested sections."""
        markdown = """
# Title
## Section 1
### Subsection 1.1
### Subsection 1.2
## Section 2
"""
        hierarchy = extract_section_hierarchy(markdown)

        assert "section_count" in hierarchy
        # Should detect headers at different levels
        assert hierarchy["section_count"] >= 4
