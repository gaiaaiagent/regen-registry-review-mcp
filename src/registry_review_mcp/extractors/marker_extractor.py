"""High-quality PDF to markdown conversion using marker.

Marker provides state-of-the-art PDF extraction with:
- Complex multi-column layout handling
- Table extraction to markdown
- Section hierarchy preservation
- Equation support (LaTeX)
- OCR for scanned documents
- Image descriptions

This module provides a clean interface to marker with caching and error handling.

Environment Variables:
    USE_MARKER: Set to "true" to use heavy Marker models. Default uses fast PyMuPDF extraction.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..models.errors import DocumentExtractionError
from ..utils.cache import Cache

logger = logging.getLogger(__name__)

# Check if we should use heavy Marker models (default: use fast extraction)
USE_MARKER = os.environ.get("USE_MARKER", "").lower() == "true"

# Global model cache (loaded once, reused across conversions)
_marker_models = None

# Markdown cache (separate from PDF cache)
pdf_markdown_cache = Cache(namespace="marker_pdf")


def get_marker_models():
    """Lazy-load marker models (loads once on first use).

    Models are ~1GB and take 5-10 seconds to load. We load them once
    and cache globally for the lifetime of the process.

    Returns:
        Loaded marker model dictionary

    Raises:
        DocumentExtractionError: If marker import or model loading fails
    """
    global _marker_models

    if _marker_models is None:
        try:
            logger.info("Loading marker models (one-time initialization, ~5-10 seconds)...")
            from marker.models import create_model_dict
            from marker.converters.pdf import PdfConverter

            _marker_models = {
                "models": create_model_dict(),
                "converter_cls": PdfConverter,
            }
            logger.info("✅ Marker models loaded successfully")
        except ImportError as e:
            raise DocumentExtractionError(
                "Marker library not installed. Install with: uv sync",
                details={"error": str(e)},
            )
        except Exception as e:
            raise DocumentExtractionError(
                f"Failed to load marker models: {str(e)}",
                details={"error": str(e)},
            )

    return _marker_models


async def convert_pdf_to_markdown(
    filepath: str,
    page_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Convert PDF to markdown using marker.

    Provides high-quality extraction with:
    - Preserved document structure (headers, lists, tables)
    - Markdown formatting for easy parsing
    - Table extraction as markdown tables
    - Image descriptions
    - OCR for scanned pages

    Args:
        filepath: Path to PDF file
        page_range: Optional tuple of (start_page, end_page) (1-indexed, inclusive)

    Returns:
        Dictionary with:
            - filepath: str - Original PDF path
            - markdown: str - Full markdown content
            - images: dict - Extracted images with descriptions
            - metadata: dict - Document metadata from marker
            - page_count: int - Number of pages processed
            - extracted_at: str - ISO timestamp
            - extraction_method: str - "marker"

    Raises:
        DocumentExtractionError: If conversion fails or file not found

    Example:
        >>> result = await convert_pdf_to_markdown("ProjectPlan.pdf")
        >>> print(result["markdown"][:200])
        # 1. Project Overview

        ## 1.1 Project Description

        This project applies the Regen Network Soil Carbon v1.2.2...
    """
    # Check cache
    cache_key = f"marker:{filepath}:{page_range}"
    cached = pdf_markdown_cache.get(cache_key)
    if cached is not None:
        logger.info(f"📦 Using cached markdown for {Path(filepath).name}")
        return cached

    try:
        file_path = Path(filepath)
        if not file_path.exists():
            raise DocumentExtractionError(
                f"PDF file not found: {filepath}",
                details={"filepath": filepath},
            )

        # Use fast extraction by default (unless USE_MARKER=true)
        if not USE_MARKER:
            logger.info(f"⚡ Fast extraction for {file_path.name} (PyMuPDF)")
            from .fast_extractor import fast_extract_pdf
            result = await fast_extract_pdf(filepath)
            # Cache the result
            pdf_markdown_cache.set(cache_key, result)
            return result

        logger.info(f"🔄 Converting {file_path.name} to markdown using marker...")

        # Load models (lazy, cached globally)
        marker_resources = get_marker_models()
        models = marker_resources["models"]
        converter_cls = marker_resources["converter_cls"]

        # Prepare converter config
        config = {
            "disable_tqdm": True,  # Disable progress bars in library code
        }

        # Handle page range
        if page_range:
            start_page = page_range[0] - 1  # Convert to 0-indexed
            end_page = page_range[1]  # Inclusive end page
            config["page_range"] = (start_page, end_page)
            logger.info(f"   Converting pages {page_range[0]}-{page_range[1]}")

        # Convert PDF to markdown using new marker API
        converter = converter_cls(
            config=config,
            artifact_dict=models,
            processor_list=None,  # Use default processors
            renderer=None,  # Use default renderer
        )
        rendered = converter(str(file_path))

        # Extract results from rendered output
        full_text = rendered.markdown
        images = rendered.images if hasattr(rendered, 'images') else {}
        metadata = rendered.metadata if hasattr(rendered, 'metadata') else {}

        # Extract page count from metadata or estimate
        page_count = metadata.get("page_count", 0)
        if page_count == 0 and page_range:
            page_count = page_range[1] - page_range[0] + 1

        result = {
            "filepath": filepath,
            "markdown": full_text,
            "images": images,
            "metadata": metadata,
            "page_count": page_count,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "extraction_method": "marker",
        }

        # Cache the result
        pdf_markdown_cache.set(cache_key, result)

        char_count = len(full_text)
        logger.info(
            f"✅ Conversion complete: {file_path.name} "
            f"({page_count} pages, {char_count:,} chars)"
        )

        return result

    except DocumentExtractionError:
        # Re-raise our own errors
        raise
    except Exception as e:
        logger.error(f"❌ Marker conversion failed for {filepath}: {str(e)}")
        raise DocumentExtractionError(
            f"Failed to convert PDF to markdown: {str(e)}",
            details={"filepath": filepath, "error": str(e), "error_type": type(e).__name__},
        )


def extract_tables_from_markdown(markdown: str) -> list[dict[str, Any]]:
    """Extract tables from markdown format.

    Parses markdown tables (format: | col1 | col2 |) into structured data.

    Args:
        markdown: Markdown text containing tables

    Returns:
        List of table dictionaries with:
            - headers: list[str] - Column headers
            - data: list[list[str]] - Table rows
            - raw_markdown: str - Original markdown table

    Example:
        >>> markdown = '''
        ... | Header 1 | Header 2 |
        ... |---|---|
        ... | Value 1 | Value 2 |
        ... '''
        >>> tables = extract_tables_from_markdown(markdown)
        >>> print(tables[0]["headers"])
        ['Header 1', 'Header 2']
    """
    import re

    tables = []

    # Pattern to match markdown tables (multi-line with pipes)
    # Matches sequences like: |col1|col2|\n|---|---|\n|val1|val2|
    table_pattern = re.compile(
        r'(?:^\|.+\|[ \t]*$\n?)+',  # One or more lines starting/ending with |
        re.MULTILINE
    )

    for match in table_pattern.finditer(markdown):
        table_text = match.group(0).strip()

        # Split into rows
        rows = [
            line.strip()
            for line in table_text.split('\n')
            if line.strip()
        ]

        # Parse each row into cells
        parsed_rows = []
        for row in rows:
            # Remove leading/trailing pipes and split
            cells = [
                cell.strip()
                for cell in row.split('|')[1:-1]  # Skip empty first/last from split
            ]
            parsed_rows.append(cells)

        # Filter out separator rows (contain only dashes and pipes)
        data_rows = [
            row for row in parsed_rows
            if row and not all(
                all(c in '-: ' for c in cell)
                for cell in row
            )
        ]

        # First row is headers, rest is data
        if data_rows:
            headers = data_rows[0] if data_rows else []
            data = data_rows[1:] if len(data_rows) > 1 else []

            tables.append({
                "headers": headers,
                "data": data,
                "row_count": len(data),
                "column_count": len(headers),
                "raw_markdown": table_text,
            })

    return tables


def extract_section_hierarchy(markdown: str) -> dict[str, Any]:
    """Extract section hierarchy from markdown headers.

    Parses markdown headers (# Header 1, ## Header 2, etc.) into a
    hierarchical structure useful for intelligent navigation and citation.

    Args:
        markdown: Markdown text with headers

    Returns:
        Dictionary with:
            - sections: list[dict] - Flat list of sections with level/title
            - hierarchy: dict - Nested hierarchy of sections

    Example:
        >>> markdown = '''
        ... # 1. Introduction
        ... ## 1.1 Background
        ... ## 1.2 Objectives
        ... # 2. Methods
        ... '''
        >>> hierarchy = extract_section_hierarchy(markdown)
        >>> print(hierarchy["sections"])
        [
            {"level": 1, "title": "1. Introduction", "line": 0},
            {"level": 2, "title": "1.1 Background", "line": 1},
            {"level": 2, "title": "1.2 Objectives", "line": 2},
            {"level": 1, "title": "2. Methods", "line": 3}
        ]
    """
    import re

    sections = []

    # Pattern to match markdown headers: # Header, ## Header, etc.
    header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    for match in header_pattern.finditer(markdown):
        level = len(match.group(1))  # Number of # symbols
        title = match.group(2).strip()
        line_start = markdown[:match.start()].count('\n')

        sections.append({
            "level": level,
            "title": title,
            "line": line_start,
            "position": match.start(),
        })

    # Build hierarchy (nested structure)
    hierarchy = _build_hierarchy_recursive(sections, 0, 1)

    return {
        "sections": sections,
        "hierarchy": hierarchy,
        "section_count": len(sections),
    }


def _build_hierarchy_recursive(sections: list[dict], start_idx: int, target_level: int) -> list[dict]:
    """Recursively build section hierarchy.

    Helper for extract_section_hierarchy().

    Args:
        sections: Flat list of sections
        start_idx: Starting index in sections list
        target_level: Current hierarchy level to process

    Returns:
        List of section dictionaries with 'children' key for sub-sections
    """
    result = []
    i = start_idx

    while i < len(sections):
        section = sections[i]

        if section["level"] < target_level:
            # Higher level section, stop processing
            break
        elif section["level"] == target_level:
            # Same level, add to result
            section_copy = section.copy()

            # Look ahead for children
            children_start = i + 1
            if children_start < len(sections) and sections[children_start]["level"] > target_level:
                section_copy["children"] = _build_hierarchy_recursive(
                    sections, children_start, target_level + 1
                )
                # Skip processed children
                i = _skip_children(sections, i, target_level)
            else:
                section_copy["children"] = []

            result.append(section_copy)
            i += 1
        else:
            # Deeper level, shouldn't happen in well-formed markdown
            i += 1

    return result


def _skip_children(sections: list[dict], parent_idx: int, parent_level: int) -> int:
    """Skip all children of a section.

    Helper for _build_hierarchy_recursive().

    Args:
        sections: Flat list of sections
        parent_idx: Index of parent section
        parent_level: Level of parent section

    Returns:
        Index of next section at same or higher level
    """
    i = parent_idx + 1
    while i < len(sections) and sections[i]["level"] > parent_level:
        i += 1
    return i - 1
