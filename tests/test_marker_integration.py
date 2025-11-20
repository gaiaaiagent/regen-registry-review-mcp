"""Tests for marker PDF-to-markdown integration.

Tests cover:
- Marker module functionality
- PDF text extraction with marker
- Markdown storage during document discovery
- Evidence extraction using markdown
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from registry_review_mcp.extractors.marker_extractor import (
    convert_pdf_to_markdown,
    extract_tables_from_markdown,
    extract_section_hierarchy,
)
from registry_review_mcp.tools.document_tools import extract_pdf_text
from registry_review_mcp.tools.evidence_tools import get_markdown_content


class TestMarkerExtractor:
    """Test marker PDF to markdown conversion."""

    @pytest.mark.marker
    @pytest.mark.asyncio
    @patch("registry_review_mcp.extractors.marker_extractor.get_marker_models")
    async def test_convert_pdf_to_markdown_basic(self, mock_get_models, tmp_path):
        """Test basic PDF to markdown conversion."""
        # Create a test PDF file
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\nTest PDF content")

        # Mock marker models and conversion
        mock_convert_fn = Mock(return_value=(
            "# Test Document\n\nThis is a test.",
            {},  # images
            {"page_count": 1}  # metadata
        ))
        mock_get_models.return_value = {
            "models": Mock(),
            "convert_fn": mock_convert_fn
        }

        # Convert
        result = await convert_pdf_to_markdown(str(test_pdf))

        # Verify
        assert "markdown" in result
        assert result["markdown"] == "# Test Document\n\nThis is a test."
        assert result["page_count"] == 1
        assert result["extraction_method"] == "marker"
        assert "extracted_at" in result

    @pytest.mark.marker
    @pytest.mark.asyncio
    @patch("registry_review_mcp.extractors.marker_extractor.get_marker_models")
    async def test_convert_with_page_range(self, mock_get_models, tmp_path):
        """Test conversion with page range."""
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\nTest PDF content")

        mock_convert_fn = Mock(return_value=(
            "# Page 1\n\nContent",
            {},
            {"page_count": 1}
        ))
        mock_get_models.return_value = {
            "models": Mock(),
            "convert_fn": mock_convert_fn
        }

        # Convert with page range
        result = await convert_pdf_to_markdown(
            str(test_pdf),
            page_range=(1, 1)
        )

        # Verify conversion function was called with correct args
        assert mock_convert_fn.called
        call_kwargs = mock_convert_fn.call_args[1]
        assert call_kwargs["start_page"] == 0  # 0-indexed
        assert call_kwargs["max_pages"] == 1

    @pytest.mark.marker
    @pytest.mark.asyncio
    @patch("registry_review_mcp.extractors.marker_extractor.get_marker_models")
    async def test_markdown_caching(self, mock_get_models, tmp_path):
        """Test that markdown conversion results are cached."""
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\nTest PDF content")

        mock_convert_fn = Mock(return_value=(
            "# Test\n\nContent",
            {},
            {"page_count": 1}
        ))
        mock_get_models.return_value = {
            "models": Mock(),
            "convert_fn": mock_convert_fn
        }

        # First call
        result1 = await convert_pdf_to_markdown(str(test_pdf))

        # Second call (should hit cache)
        result2 = await convert_pdf_to_markdown(str(test_pdf))

        # Verify same result
        assert result1 == result2

        # Verify conversion only called once (cached second time)
        assert mock_convert_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_file_not_found_error(self):
        """Test error handling for missing file."""
        with pytest.raises(Exception) as exc_info:
            await convert_pdf_to_markdown("/nonexistent/file.pdf")

        assert "not found" in str(exc_info.value).lower()


class TestTableExtraction:
    """Test markdown table extraction."""

    def test_extract_simple_table(self):
        """Test extraction of simple markdown table."""
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

        assert len(tables) == 1
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


class TestSectionHierarchy:
    """Test section hierarchy extraction."""

    def test_extract_simple_hierarchy(self):
        """Test extraction of simple section hierarchy."""
        markdown = """
# 1. Introduction
## 1.1 Background
## 1.2 Objectives
# 2. Methods
## 2.1 Study Design
"""
        hierarchy = extract_section_hierarchy(markdown)

        assert hierarchy["section_count"] == 5
        sections = hierarchy["sections"]
        assert sections[0]["level"] == 1
        assert sections[0]["title"] == "1. Introduction"
        assert sections[1]["level"] == 2
        assert sections[1]["title"] == "1.1 Background"

    def test_nested_hierarchy(self):
        """Test deeply nested sections."""
        markdown = """
# 1. Top
## 1.1 Second
### 1.1.1 Third
#### 1.1.1.1 Fourth
# 2. Another Top
"""
        hierarchy = extract_section_hierarchy(markdown)

        assert hierarchy["section_count"] == 5
        sections = hierarchy["sections"]
        assert sections[0]["level"] == 1
        assert sections[1]["level"] == 2
        assert sections[2]["level"] == 3
        assert sections[3]["level"] == 4

    def test_no_sections(self):
        """Test markdown without headers."""
        markdown = "Just plain text without headers."
        hierarchy = extract_section_hierarchy(markdown)

        assert hierarchy["section_count"] == 0
        assert len(hierarchy["sections"]) == 0


class TestPDFTextExtraction:
    """Test PDF text extraction with marker."""

    @pytest.mark.asyncio
    @patch("registry_review_mcp.extractors.marker_extractor.convert_pdf_to_markdown")
    async def test_extract_pdf_text_uses_marker(self, mock_convert, tmp_path):
        """Test that extract_pdf_text now uses marker."""
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")

        # Mock marker conversion
        mock_convert.return_value = {
            "markdown": "# Test\n\nContent here.",
            "images": {},
            "metadata": {},
            "page_count": 1,
            "extracted_at": "2025-11-17T00:00:00Z",
            "extraction_method": "marker"
        }

        # Extract
        result = await extract_pdf_text(str(test_pdf))

        # Verify marker was used
        assert mock_convert.called
        assert result["extraction_method"] == "marker"
        assert "markdown" in result
        assert result["full_text"] == result["markdown"]  # Backward compat

    @pytest.mark.asyncio
    @patch("registry_review_mcp.extractors.marker_extractor.convert_pdf_to_markdown")
    @patch("registry_review_mcp.extractors.marker_extractor.extract_tables_from_markdown")
    async def test_extract_with_tables(self, mock_extract_tables, mock_convert, tmp_path):
        """Test table extraction from markdown."""
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")

        mock_convert.return_value = {
            "markdown": "# Test\n\n| A | B |\n|---|---|\n| 1 | 2 |",
            "images": {},
            "metadata": {},
            "page_count": 1,
            "extracted_at": "2025-11-17T00:00:00Z",
            "extraction_method": "marker"
        }

        mock_extract_tables.return_value = [
            {
                "headers": ["A", "B"],
                "data": [["1", "2"]],
                "row_count": 1,
                "column_count": 2,
                "raw_markdown": "| A | B |\n|---|---|\n| 1 | 2 |"
            }
        ]

        # Extract with tables
        result = await extract_pdf_text(str(test_pdf), extract_tables=True)

        # Verify tables extracted
        assert mock_extract_tables.called
        assert result["tables"] is not None
        assert len(result["tables"]) == 1


class TestEvidenceExtractionWithMarkdown:
    """Test evidence extraction using markdown."""

    @pytest.mark.asyncio
    async def test_get_markdown_content_from_document_metadata(self, tmp_path):
        """Test getting markdown from document metadata."""
        # Create markdown file
        md_path = tmp_path / "test.md"
        md_content = "# Test Document\n\nContent here."
        md_path.write_text(md_content, encoding="utf-8")

        # Document with markdown_path
        document = {
            "filepath": str(tmp_path / "test.pdf"),
            "has_markdown": True,
            "markdown_path": str(md_path)
        }

        # Get markdown
        content = await get_markdown_content(document, "test_session")

        assert content == md_content

    @pytest.mark.asyncio
    async def test_get_markdown_content_fallback(self, tmp_path):
        """Test fallback to .md file next to PDF."""
        # Create PDF and markdown file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        md_path = tmp_path / "test.md"
        md_content = "# Test\n\nFallback markdown."
        md_path.write_text(md_content, encoding="utf-8")

        # Document without markdown_path (fallback scenario)
        document = {
            "filepath": str(pdf_path),
            "has_markdown": False
        }

        # Get markdown (should find .md via fallback)
        content = await get_markdown_content(document, "test_session")

        assert content == md_content

    @pytest.mark.asyncio
    async def test_get_markdown_content_none_if_missing(self, tmp_path):
        """Test returns None if markdown not found."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        document = {
            "filepath": str(pdf_path),
            "has_markdown": False
        }

        # Get markdown (should return None)
        content = await get_markdown_content(document, "test_session")

        assert content is None


class TestMarkerQuality:
    """Test marker extraction quality improvements.

    These are integration-style tests that verify marker provides
    better quality than pdfplumber for common document patterns.
    """

    @pytest.mark.marker
    @pytest.mark.asyncio
    @patch("registry_review_mcp.extractors.marker_extractor.get_marker_models")
    async def test_preserves_section_structure(self, mock_get_models, tmp_path):
        """Test that marker preserves document section structure."""
        test_pdf = tmp_path / "structured.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")

        # Simulate marker preserving section structure
        mock_convert_fn = Mock(return_value=(
            "# 1. Introduction\n\n## 1.1 Background\n\nText here.\n\n## 1.2 Objectives\n\nMore text.",
            {},
            {"page_count": 1}
        ))
        mock_get_models.return_value = {
            "models": Mock(),
            "convert_fn": mock_convert_fn
        }

        result = await convert_pdf_to_markdown(str(test_pdf))

        # Verify structure preserved
        markdown = result["markdown"]
        assert "# 1. Introduction" in markdown
        assert "## 1.1 Background" in markdown
        assert "## 1.2 Objectives" in markdown

        # Extract hierarchy
        hierarchy = extract_section_hierarchy(markdown)
        assert hierarchy["section_count"] == 3

    @pytest.mark.marker
    @pytest.mark.asyncio
    @patch("registry_review_mcp.extractors.marker_extractor.get_marker_models")
    async def test_table_extraction_quality(self, mock_get_models, tmp_path):
        """Test that marker extracts tables correctly."""
        test_pdf = tmp_path / "tables.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")

        # Simulate marker extracting well-formatted table
        mock_convert_fn = Mock(return_value=(
            "# Data\n\n| Parameter | Value | Unit |\n|---|---|---|\n| Temperature | 25 | °C |\n| Pressure | 101.3 | kPa |",
            {},
            {"page_count": 1}
        ))
        mock_get_models.return_value = {
            "models": Mock(),
            "convert_fn": mock_convert_fn
        }

        result = await convert_pdf_to_markdown(str(test_pdf))

        # Extract tables
        tables = extract_tables_from_markdown(result["markdown"])

        assert len(tables) == 1
        assert tables[0]["headers"] == ["Parameter", "Value", "Unit"]
        assert tables[0]["data"][0] == ["Temperature", "25", "°C"]
        assert tables[0]["data"][1] == ["Pressure", "101.3", "kPa"]
