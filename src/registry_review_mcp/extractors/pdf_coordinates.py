"""PDF coordinate resolver for mapping text to bounding boxes.

This module provides utilities to find the precise PDF coordinates of text
that was extracted by the evidence pipeline, enabling PDF highlighting in the UI.

The approach is two-phase:
1. Text extraction happens via PyMuPDF4LLM (fast, markdown output)
2. Coordinates are resolved in bulk after evidence extraction

Performance optimization: Uses bulk processing to open each PDF once and
resolve all snippets for that document before closing.
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from rapidfuzz import fuzz

from ..models.evidence import BoundingBox

if TYPE_CHECKING:
    from ..models.evidence import EvidenceSnippet

logger = logging.getLogger(__name__)


def resolve_text_coordinates(
    pdf_path: Path | str,
    text: str,
    page_hint: int | None = None,
    fuzzy_threshold: float = 80.0,
) -> Optional[BoundingBox]:
    """Find the bounding box for a text snippet in a PDF.

    Uses PyMuPDF (fitz) to search for the text and return normalized coordinates.

    Args:
        pdf_path: Path to the PDF file
        text: Text snippet to find
        page_hint: Optional page number hint (1-indexed) to search first
        fuzzy_threshold: Minimum fuzzy match score (0-100) to accept

    Returns:
        BoundingBox with normalized coordinates (0-1), or None if not found
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed, cannot resolve coordinates")
        return None

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        logger.warning(f"PDF not found: {pdf_path}")
        return None

    # Normalize the search text (remove extra whitespace)
    search_text = " ".join(text.split())[:500]  # Limit to 500 chars for search

    try:
        doc = fitz.open(str(pdf_path))

        # Build page search order (hint page first, then all others)
        pages_to_search = list(range(len(doc)))
        if page_hint is not None and 0 < page_hint <= len(doc):
            hint_idx = page_hint - 1  # Convert to 0-indexed
            pages_to_search.remove(hint_idx)
            pages_to_search.insert(0, hint_idx)

        for page_idx in pages_to_search:
            page = doc[page_idx]

            # Try exact search first
            rects = page.search_for(search_text, quads=False)
            if rects:
                # Found exact match
                rect = rects[0]  # Take first match
                bbox = _normalize_rect(rect, page, page_idx + 1)

                # Add additional rects if multi-line
                if len(rects) > 1:
                    bbox.rects = [
                        {"x0": r.x0 / page.rect.width, "y0": r.y0 / page.rect.height,
                         "x1": r.x1 / page.rect.width, "y1": r.y1 / page.rect.height}
                        for r in rects[1:5]  # Limit to 5 rects
                    ]

                bbox.match_score = 1.0
                doc.close()
                return bbox

            # Try fuzzy matching on page text
            page_text = page.get_text()
            if fuzz.partial_ratio(search_text.lower(), page_text.lower()) >= fuzzy_threshold:
                # Text is on this page but not exact match
                # Try searching for first 50 chars
                short_search = search_text[:50]
                rects = page.search_for(short_search, quads=False)
                if rects:
                    rect = rects[0]
                    bbox = _normalize_rect(rect, page, page_idx + 1)
                    bbox.match_score = fuzz.partial_ratio(search_text.lower(), page_text.lower()) / 100
                    doc.close()
                    return bbox

        doc.close()
        logger.debug(f"Text not found in PDF: {search_text[:50]}...")
        return None

    except Exception as e:
        logger.error(f"Error resolving coordinates: {e}")
        return None


def _normalize_rect(rect, page, page_num: int) -> BoundingBox:
    """Convert PyMuPDF Rect to normalized BoundingBox."""
    page_width = page.rect.width
    page_height = page.rect.height

    return BoundingBox(
        page=page_num,
        x0=max(0.0, min(1.0, rect.x0 / page_width)),
        y0=max(0.0, min(1.0, rect.y0 / page_height)),
        x1=max(0.0, min(1.0, rect.x1 / page_width)),
        y1=max(0.0, min(1.0, rect.y1 / page_height)),
    )


def resolve_snippet_coordinates(
    session_dir: Path,
    snippet_text: str,
    document_id: str,
    page: int | None = None,
) -> Optional[BoundingBox]:
    """Resolve coordinates for an evidence snippet using session documents.

    Looks up the document path from the session and resolves coordinates.

    Args:
        session_dir: Path to the session directory
        snippet_text: Text to find
        document_id: Document ID from the evidence
        page: Page number hint (1-indexed)

    Returns:
        BoundingBox or None
    """
    import json

    # Load documents.json to get file path
    documents_path = session_dir / "documents.json"
    if not documents_path.exists():
        logger.warning("documents.json not found")
        return None

    with open(documents_path) as f:
        documents_data = json.load(f)

    # Find the document
    for doc in documents_data.get("documents", []):
        if doc.get("document_id") == document_id:
            filepath = doc.get("filepath")
            if filepath:
                return resolve_text_coordinates(
                    pdf_path=filepath,
                    text=snippet_text,
                    page_hint=page,
                )

    logger.warning(f"Document not found: {document_id}")
    return None


def batch_resolve_coordinates(
    session_dir: Path,
    snippets: list[dict],
) -> list[dict]:
    """Resolve coordinates for multiple snippets.

    Args:
        session_dir: Path to session directory
        snippets: List of dicts with text, document_id, page keys

    Returns:
        Same list with bounding_box added to each snippet
    """
    results = []
    for snippet in snippets:
        bbox = resolve_snippet_coordinates(
            session_dir=session_dir,
            snippet_text=snippet.get("text", ""),
            document_id=snippet.get("document_id", ""),
            page=snippet.get("page"),
        )

        snippet_copy = dict(snippet)
        if bbox:
            snippet_copy["bounding_box"] = bbox.model_dump()
        results.append(snippet_copy)

    return results


def enrich_snippets_with_coordinates(
    snippets: list["EvidenceSnippet"],
    doc_metadata: dict[str, dict],
    min_similarity: float = 0.8,
) -> int:
    """Bulk coordinate extraction - opens each PDF once, processes all snippets.

    This function mutates snippets in-place to add bounding_box field.
    Optimized to minimize file I/O by grouping snippets by document.

    IMPORTANT: When the text is found on a different page than the LLM-extracted
    page number, this function updates BOTH bounding_box.page AND snippet.page
    to the actual page where the text was found. This ensures page consistency
    since PyMuPDF's page detection is ground truth.

    Args:
        snippets: List of EvidenceSnippet objects to enrich
        doc_metadata: Dict mapping document_id -> document dict with 'filepath' key
        min_similarity: Minimum fuzzy match score (0-1) to accept. Default 0.8

    Returns:
        Number of snippets successfully enriched with coordinates
    """
    # === DEBUG LOGGING: Entry point ===
    logger.info(f"[COORD-ENRICH] Starting coordinate enrichment for {len(snippets)} snippets")
    logger.info(f"[COORD-ENRICH] doc_metadata contains {len(doc_metadata)} documents")

    # Log available document IDs and their filepaths
    for doc_id, doc_info in doc_metadata.items():
        filepath = doc_info.get("filepath", "NO_FILEPATH")
        logger.info(f"[COORD-ENRICH] Available doc: {doc_id} -> {filepath}")

    try:
        import fitz  # PyMuPDF
        logger.info(f"[COORD-ENRICH] PyMuPDF version: {fitz.version}")
    except ImportError:
        logger.error("[COORD-ENRICH] PyMuPDF not installed, cannot resolve coordinates")
        return 0

    # Group snippets by document for efficient processing
    snippets_by_doc: dict[str, list["EvidenceSnippet"]] = defaultdict(list)
    for snippet in snippets:
        if snippet.text and snippet.document_id:
            snippets_by_doc[snippet.document_id].append(snippet)
        else:
            logger.warning(f"[COORD-ENRICH] Skipping snippet - missing text or document_id: text={bool(snippet.text)}, doc_id={snippet.document_id}")

    logger.info(f"[COORD-ENRICH] Grouped snippets into {len(snippets_by_doc)} document groups")

    enriched_count = 0
    page_mismatch_count = 0

    # Process each document's snippets
    for doc_id, doc_snippets in snippets_by_doc.items():
        logger.info(f"[COORD-ENRICH] Processing document: {doc_id} with {len(doc_snippets)} snippets")

        doc = doc_metadata.get(doc_id)
        if not doc:
            logger.error(f"[COORD-ENRICH] FAILED: No metadata for document '{doc_id}' - available keys: {list(doc_metadata.keys())}")
            continue

        filepath = doc.get("filepath")
        logger.info(f"[COORD-ENRICH] Document {doc_id} filepath: {filepath}")

        if not filepath:
            logger.error(f"[COORD-ENRICH] FAILED: No filepath in metadata for {doc_id} - doc keys: {list(doc.keys())}")
            continue

        path_obj = Path(filepath)
        if not path_obj.exists():
            logger.error(f"[COORD-ENRICH] FAILED: PDF file does not exist: {filepath}")
            # Try to diagnose path issues
            parent = path_obj.parent
            if parent.exists():
                logger.info(f"[COORD-ENRICH] Parent directory exists: {parent}")
                logger.info(f"[COORD-ENRICH] Files in parent: {list(parent.iterdir())[:10]}")
            else:
                logger.error(f"[COORD-ENRICH] Parent directory does not exist: {parent}")
            continue

        # Only process PDFs
        if not filepath.lower().endswith(".pdf"):
            logger.info(f"[COORD-ENRICH] Skipping non-PDF file: {filepath}")
            continue

        logger.info(f"[COORD-ENRICH] Opening PDF: {filepath}")

        try:
            pdf_doc = fitz.open(filepath)
            page_count = len(pdf_doc)
            logger.info(f"[COORD-ENRICH] PDF opened successfully: {page_count} pages")

            snippets_processed = 0
            snippets_found = 0

            # Process all snippets for this document
            for snippet in doc_snippets:
                snippets_processed += 1

                # Skip if already has bounding box
                if snippet.bounding_box is not None:
                    logger.debug(f"[COORD-ENRICH] Snippet already has bounding box, skipping")
                    continue

                # Prepare search text (first 500 chars, normalized)
                search_text = " ".join(snippet.text.split())[:500]
                logger.debug(f"[COORD-ENRICH] Searching for text: '{search_text[:80]}...'")

                # Determine pages to search (hint page first)
                pages_to_search = list(range(page_count))
                if snippet.page and 0 < snippet.page <= page_count:
                    hint_idx = snippet.page - 1
                    pages_to_search.remove(hint_idx)
                    pages_to_search.insert(0, hint_idx)

                # Search for text
                found = False
                for page_idx in pages_to_search:
                    page = pdf_doc[page_idx]

                    # Try exact search first
                    rects = page.search_for(search_text, quads=False)
                    if rects:
                        rect = rects[0]
                        actual_page = page_idx + 1
                        snippet.bounding_box = _create_bounding_box(
                            rect, page, actual_page, 1.0, rects[1:5]
                        )
                        # Sync page number: bounding_box.page is ground truth
                        if snippet.page != actual_page:
                            if snippet.page is not None:
                                logger.info(
                                    f"Page mismatch corrected: {doc_id} snippet "
                                    f"claimed page {snippet.page}, found on page {actual_page}"
                                )
                                page_mismatch_count += 1
                            snippet.page = actual_page
                        enriched_count += 1
                        snippets_found += 1
                        found = True
                        logger.debug(f"[COORD-ENRICH] EXACT MATCH found on page {actual_page}")
                        break

                    # Try fuzzy matching on page text
                    page_text = page.get_text()
                    similarity = fuzz.partial_ratio(
                        search_text.lower(), page_text.lower()
                    ) / 100

                    if similarity >= min_similarity:
                        # Try multiple candidate phrases from the text
                        # PDF tables often split text that LLM concatenates
                        candidates = _extract_search_candidates(search_text)
                        logger.debug(f"[COORD-ENRICH] Fuzzy match ({similarity:.2f}) on page {page_idx+1}, trying {len(candidates)} candidates")
                        for candidate in candidates:
                            rects = page.search_for(candidate, quads=False)
                            if rects:
                                rect = rects[0]
                                actual_page = page_idx + 1
                                snippet.bounding_box = _create_bounding_box(
                                    rect, page, actual_page, similarity
                                )
                                # Sync page number: bounding_box.page is ground truth
                                if snippet.page != actual_page:
                                    if snippet.page is not None:
                                        logger.info(
                                            f"Page mismatch corrected: {doc_id} snippet "
                                            f"claimed page {snippet.page}, found on page {actual_page}"
                                        )
                                        page_mismatch_count += 1
                                    snippet.page = actual_page
                                enriched_count += 1
                                snippets_found += 1
                                found = True
                                logger.debug(f"[COORD-ENRICH] FUZZY MATCH found on page {actual_page} with candidate: '{candidate[:40]}...'")
                                break
                        if found:
                            break

                if not found:
                    logger.warning(
                        f"[COORD-ENRICH] NOT FOUND in {doc_id}: '{search_text[:80]}...'"
                    )

            pdf_doc.close()
            logger.info(f"[COORD-ENRICH] Document {doc_id}: {snippets_found}/{snippets_processed} snippets enriched")

        except Exception as e:
            logger.error(f"[COORD-ENRICH] Exception processing PDF {filepath}: {e}", exc_info=True)
            continue

    # Log comprehensive summary
    logger.info(f"[COORD-ENRICH] === ENRICHMENT COMPLETE ===")
    logger.info(f"[COORD-ENRICH] Total snippets: {len(snippets)}")
    logger.info(f"[COORD-ENRICH] Documents processed: {len(snippets_by_doc)}")
    logger.info(f"[COORD-ENRICH] Snippets enriched: {enriched_count}")
    logger.info(f"[COORD-ENRICH] Success rate: {(enriched_count / len(snippets) * 100) if snippets else 0:.1f}%")

    # Log summary of page mismatches if any were found
    if page_mismatch_count > 0:
        mismatch_rate = (page_mismatch_count / enriched_count * 100) if enriched_count > 0 else 0
        logger.warning(
            f"Page number corrections: {page_mismatch_count}/{enriched_count} snippets "
            f"({mismatch_rate:.1f}%) had incorrect LLM-extracted page numbers"
        )

    return enriched_count


def _extract_search_candidates(text: str, min_len: int = 20) -> list[str]:
    """Extract candidate search phrases from evidence text.

    LLM evidence often concatenates table cells (e.g., "Credit Class Name: GHG Benefits...")
    but the PDF has them as separate text blocks. This function extracts multiple
    phrases to try, prioritizing distinctive content over labels.

    Strategy:
    1. Split on common separators (colon, period, newline)
    2. Extract word sequences of 4+ words from different positions
    3. Return candidates in order of distinctiveness (longer, middle content first)
    """
    candidates = []

    # Strategy 1: Split on separators and take each part
    import re
    parts = re.split(r'[:.\n]', text)
    for part in parts:
        part = part.strip()
        if len(part) >= min_len:
            candidates.append(part[:80])  # Limit length for search

    # Strategy 2: Try word sequences from different starting points
    words = text.split()
    if len(words) >= 4:
        # Start from word 2 (skip potential label words)
        for start in [2, 4, 0]:
            if start < len(words) - 3:
                phrase = " ".join(words[start:start + 6])
                if len(phrase) >= min_len and phrase not in candidates:
                    candidates.append(phrase)

    # Fallback: first 50 chars (original behavior)
    if not candidates and len(text) >= min_len:
        candidates.append(text[:50])

    return candidates


def _create_bounding_box(
    rect, page, page_num: int, match_score: float, extra_rects=None
) -> BoundingBox:
    """Create a normalized BoundingBox from a PyMuPDF Rect."""
    page_width = page.rect.width
    page_height = page.rect.height

    bbox = BoundingBox(
        page=page_num,
        x0=max(0.0, min(1.0, rect.x0 / page_width)),
        y0=max(0.0, min(1.0, rect.y0 / page_height)),
        x1=max(0.0, min(1.0, rect.x1 / page_width)),
        y1=max(0.0, min(1.0, rect.y1 / page_height)),
        match_score=match_score,
    )

    # Add extra rects for multi-line text
    if extra_rects:
        bbox.rects = [
            {
                "x0": r.x0 / page_width,
                "y0": r.y0 / page_height,
                "x1": r.x1 / page_width,
                "y1": r.y1 / page_height,
            }
            for r in extra_rects
        ]

    return bbox


def validate_page_consistency(snippets: list[dict]) -> dict:
    """Validate that page numbers match between snippet.page and bounding_box.page.

    This function can be used to audit existing evidence data for page mismatches.
    It does NOT modify the snippets, only reports on inconsistencies.

    Args:
        snippets: List of evidence snippet dictionaries (from evidence.json)

    Returns:
        Dictionary with validation results:
        - total: Total snippets checked
        - with_bounding_box: Snippets that have bounding_box
        - mismatches: List of mismatched snippets with details
        - mismatch_count: Number of mismatches
        - mismatch_rate: Percentage of snippets with mismatches
    """
    total = len(snippets)
    with_bbox = 0
    mismatches = []

    for snippet in snippets:
        bbox = snippet.get("bounding_box")
        if bbox is None:
            continue

        with_bbox += 1
        snippet_page = snippet.get("page")
        bbox_page = bbox.get("page")

        if snippet_page is not None and bbox_page is not None and snippet_page != bbox_page:
            mismatches.append({
                "document_id": snippet.get("document_id", "unknown"),
                "document_name": snippet.get("document_name", "unknown"),
                "snippet_page": snippet_page,
                "bounding_box_page": bbox_page,
                "difference": bbox_page - snippet_page,
                "text_preview": snippet.get("text", "")[:100],
            })

    mismatch_count = len(mismatches)
    mismatch_rate = (mismatch_count / with_bbox * 100) if with_bbox > 0 else 0

    return {
        "total": total,
        "with_bounding_box": with_bbox,
        "mismatches": mismatches,
        "mismatch_count": mismatch_count,
        "mismatch_rate": mismatch_rate,
    }
