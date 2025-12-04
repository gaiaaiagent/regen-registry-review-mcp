"""Fast PDF extraction using PyMuPDF4LLM.

Provides quick markdown extraction (~1-3 seconds per document) optimized for:
- Immediate post-upload feedback
- Quick evidence extraction
- Good enough quality for most registry documents
- Clean markdown output suitable for LLM processing

Performance: 100x faster than marker with 75-90% quality retention.
"""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..models.errors import DocumentExtractionError

logger = logging.getLogger(__name__)


async def fast_extract_pdf(filepath: str) -> dict[str, Any]:
    """Fast PDF to markdown extraction using PyMuPDF4LLM.

    Optimized for registry review documents with good structure preservation
    and markdown output suitable for LLM processing.

    Speed: ~1-3 seconds per document (vs 5-15 minutes for marker)
    Quality: 75-90% word overlap with marker (good enough for most cases)

    Args:
        filepath: Path to PDF file

    Returns:
        Dictionary with:
            - filepath: str - Original PDF path
            - markdown: str - Full markdown text
            - pages: list[dict] - Per-page chunks with metadata
            - page_count: int - Number of pages
            - extracted_at: str - ISO timestamp
            - extraction_method: str - "pymupdf4llm"
            - tables_found: int - Count of detected markdown tables
            - total_chars: int - Character count

    Raises:
        DocumentExtractionError: If extraction fails or file not found

    Example:
        >>> result = await fast_extract_pdf("ProjectPlan.pdf")
        >>> print(f"Extracted {result['page_count']} pages in 2.3s")
        >>> print(result["markdown"][:200])
        # Project Plan

        ## 1. Overview

        This project applies the Soil Carbon methodology...
    """
    try:
        import pymupdf4llm
    except ImportError:
        raise DocumentExtractionError(
            "PyMuPDF4LLM not installed. Install with: uv pip install pymupdf4llm",
            details={"package": "pymupdf4llm"},
        )

    try:
        file_path = Path(filepath)
        if not file_path.exists():
            raise DocumentExtractionError(
                f"PDF file not found: {filepath}",
                details={"filepath": filepath},
            )

        logger.info(f"⚡️ Fast extracting {file_path.name} using PyMuPDF4LLM...")

        # Extract as page chunks (better for RAG/citation)
        page_chunks = pymupdf4llm.to_markdown(
            str(file_path),
            page_chunks=True,
            # Note: Could add header=False, footer=False to exclude headers/footers
        )

        # Combine for full text with page markers for citation extraction
        # Use format: "--- Page N ---" which matches extract_page_from_markers() patterns
        pages_with_markers = []
        for i, chunk in enumerate(page_chunks, 1):
            page_marker = f"--- Page {i} ---"
            pages_with_markers.append(f"{page_marker}\n\n{chunk['text']}")
        full_markdown = "\n\n".join(pages_with_markers)

        # Count tables (simple markdown table detection)
        table_pattern = re.compile(r'\|.*\|.*\n\|[-:| ]+\|', re.MULTILINE)
        tables_found = len(table_pattern.findall(full_markdown))

        result = {
            "filepath": filepath,
            "markdown": full_markdown,
            "pages": page_chunks,  # Each has: text, metadata, page_num
            "page_count": len(page_chunks),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "extraction_method": "pymupdf4llm",
            "tables_found": tables_found,
            "total_chars": len(full_markdown),
        }

        char_count = len(full_markdown)
        logger.info(
            f"✅ Fast extraction complete: {file_path.name} "
            f"({len(page_chunks)} pages, {char_count:,} chars, "
            f"{tables_found} tables)"
        )

        return result

    except DocumentExtractionError:
        raise
    except Exception as e:
        logger.error(f"❌ Fast extraction failed for {filepath}: {str(e)}")
        raise DocumentExtractionError(
            f"Failed to extract PDF with PyMuPDF4LLM: {str(e)}",
            details={"filepath": filepath, "error": str(e), "error_type": type(e).__name__},
        )


async def fast_extract_with_quality_check(filepath: str) -> dict[str, Any]:
    """Fast extraction with quality heuristics.

    Performs fast extraction and checks quality indicators. If quality
    is suspect, raises an error so caller can fall back to marker.

    Quality checks:
    - At least one page extracted
    - Minimum 100 characters of text
    - At least 70% alphanumeric/space characters (not garbled)

    Args:
        filepath: Path to PDF file

    Returns:
        Fast extraction result (same as fast_extract_pdf)

    Raises:
        DocumentExtractionError: If extraction fails or quality is poor
    """
    result = await fast_extract_pdf(filepath)

    # Quality check 1: At least one page
    if result["page_count"] == 0:
        raise DocumentExtractionError(
            "No pages extracted - document may be corrupt or empty",
            details={"filepath": filepath},
        )

    # Quality check 2: Minimum text
    if len(result["markdown"]) < 100:
        raise DocumentExtractionError(
            "Insufficient text extracted - document may be scanned or image-based",
            details={"filepath": filepath, "chars_extracted": len(result["markdown"])},
        )

    # Quality check 3: Text quality ratio
    text_chars = sum(c.isalnum() or c.isspace() for c in result["markdown"])
    quality_ratio = text_chars / len(result["markdown"]) if result["markdown"] else 0

    if quality_ratio < 0.7:
        raise DocumentExtractionError(
            "Low text quality - document may require OCR or have encoding issues",
            details={
                "filepath": filepath,
                "quality_ratio": round(quality_ratio, 3),
                "threshold": 0.7,
            },
        )

    logger.info(f"   Quality check passed: {quality_ratio:.1%} text ratio")
    return result


async def batch_fast_extract_pdfs(
    filepaths: list[str],
) -> dict[str, dict[str, Any]]:
    """Batch fast extract multiple PDFs.

    Processes PDFs sequentially (fast enough that parallelization not needed).

    Args:
        filepaths: List of PDF file paths

    Returns:
        Dictionary mapping filepath -> extraction result
        {
            "path/to/file.pdf": {
                "filepath": "path/to/file.pdf",
                "markdown": "...",
                "pages": [...],
                ...
            },
            ...
        }

    Example:
        >>> pdfs = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
        >>> results = await batch_fast_extract_pdfs(pdfs)
        >>> print(f"Extracted {len(results)} PDFs in 8 seconds")
    """
    if not filepaths:
        return {}

    results = {}
    successful = 0
    failed = 0

    logger.info(f"⚡️ Fast extracting {len(filepaths)} PDFs")
    print(f"⚡️ Fast extracting {len(filepaths)} PDFs...", flush=True)

    for i, filepath in enumerate(filepaths, 1):
        try:
            print(f"   [{i}/{len(filepaths)}] Extracting {Path(filepath).name}...", flush=True)

            result = await fast_extract_pdf(filepath)
            results[filepath] = result
            successful += 1

            char_count = result["total_chars"]
            print(f"   ✓ Extracted ({char_count:,} chars)", flush=True)

        except Exception as e:
            logger.error(f"Failed to extract {filepath}: {e}")
            print(f"   ✗ Failed: {e}", flush=True)
            failed += 1
            results[filepath] = {
                "filepath": filepath,
                "error": str(e),
                "success": False,
            }

    logger.info(f"✅ Batch extraction complete: {successful} successful, {failed} failed")
    print(f"\n✅ Batch complete: {successful} successful, {failed} failed\n", flush=True)

    return results
