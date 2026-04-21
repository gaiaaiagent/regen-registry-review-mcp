"""OCR fallback for image-heavy PDFs (Issue #4).

The fast PDF extractor (PyMuPDF4LLM) renders image blocks as
"intentionally omitted" markers. Ecometric Soil Carbon reports — and more
broadly any registry submission built on InDesign / Illustrator / scan-
derived layouts — embed charts, tables, maps, and credit statements as
graphic assets rather than text runs. When the fast extractor hits one of
those pages the per-page character count collapses and downstream evidence
extraction returns 0/23 requirements covered.

This module adds an opt-in OCR chain that runs on a per-page basis only
when the fast extractor's output looks suspiciously empty. It leans on
PyMuPDF's bundled OCR bridge (`Page.get_textpage_ocr`) which uses the
system Tesseract installation. No new Python dependency is required — but
the system package `tesseract` (and a language pack, e.g. `tesseract-data-eng`)
must be installed at runtime. When Tesseract is missing the helpers degrade
gracefully: the fast extractor logs a one-time warning and returns its
original output untouched.

Results are cached per ``(filepath, mtime, page_num, mode, language, dpi)``
under ``REGISTRY_REVIEW_CACHE_DIR/ocr/`` so a monitoring-report PDF that
takes 30s to OCR the first time returns in milliseconds on subsequent
review sessions.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional

if TYPE_CHECKING:
    import pymupdf

logger = logging.getLogger(__name__)

OCRMode = Literal["auto", "blocks", "full"]

# Module-level cache for the Tesseract availability probe. We evaluate it
# lazily the first time OCR is requested so import order has no side effect
# on settings loading, and we memoize the result so we don't shell out or
# shell-out-equivalent on every page.
_TESSERACT_AVAILABLE: Optional[bool] = None
_TESSERACT_WARNING_EMITTED: bool = False


def is_tesseract_available() -> bool:
    """Return True if PyMuPDF can locate a usable Tesseract install.

    PyMuPDF bundles its own OCR bridge but still needs the Tesseract binary
    on the system path (or at ``TESSDATA_PREFIX``) along with at least one
    language pack. We probe by asking PyMuPDF for its tessdata directory;
    if that raises we treat OCR as unavailable and disable the fallback.
    """
    global _TESSERACT_AVAILABLE
    if _TESSERACT_AVAILABLE is not None:
        return _TESSERACT_AVAILABLE

    try:
        import pymupdf

        tessdata = pymupdf.get_tessdata(os.environ.get("TESSDATA_PREFIX"))
    except Exception as exc:
        logger.debug("Tesseract probe failed: %s", exc)
        _TESSERACT_AVAILABLE = False
        return False

    tessdata_path = Path(tessdata) if tessdata else None
    available = bool(tessdata_path and tessdata_path.exists())
    _TESSERACT_AVAILABLE = available
    return available


def _warn_tesseract_missing_once() -> None:
    """Emit the 'Tesseract not installed' warning at most once per process."""
    global _TESSERACT_WARNING_EMITTED
    if _TESSERACT_WARNING_EMITTED:
        return
    _TESSERACT_WARNING_EMITTED = True
    logger.warning(
        "OCR fallback requested but Tesseract is not installed. "
        "Install with 'sudo pacman -S tesseract tesseract-data-eng' "
        "(Arch / CachyOS) or 'brew install tesseract' (macOS). "
        "Continuing without OCR — image-heavy pages may return empty text."
    )


def _ocr_cache_path(cache_root: Path, filepath: str, page_num: int, mode: str, language: str, dpi: int) -> Path:
    """Deterministic cache path for a single OCRed page.

    Keying on ``mtime`` so a re-exported PDF invalidates its cache entries
    without us having to maintain a side index. Keying on mode/language/dpi
    because the same page OCR'd at 300dpi English vs 150dpi English+Czech
    produces different text and we want both to coexist for benchmark runs.
    """
    try:
        stat = Path(filepath).stat()
        mtime = int(stat.st_mtime_ns)
    except OSError:
        mtime = 0

    key = f"{filepath}::{mtime}::p{page_num}::{mode}::{language}::dpi{dpi}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return cache_root / "ocr" / f"{digest}.txt"


def ocr_page(
    filepath: str,
    page_num: int,
    *,
    mode: OCRMode = "auto",
    language: str = "eng",
    dpi: int = 150,
    cache_root: Optional[Path] = None,
) -> Optional[str]:
    """OCR a single page of a PDF, returning markdown-friendly text.

    Args:
        filepath: Path to the PDF on disk.
        page_num: Zero-indexed page to OCR.
        mode: "blocks" runs OCR against image blocks on the page and
            merges their text into the normal text page; "full" rasterises
            the entire page at ``dpi`` and OCRs the rendered pixmap; "auto"
            tries ``blocks`` first and falls back to ``full`` if that came
            back empty. ``auto`` is the right default for registry
            submissions because it preserves whatever native text the
            publisher did embed while still catching image-only content.
        language: Tesseract language code, e.g. ``"eng"``, ``"eng+ces"``.
        dpi: Rasterisation resolution for ``full`` mode. 150dpi is a
            practical minimum for body copy; charts and tables benefit from
            300dpi but roughly double the time budget.
        cache_root: Root directory under which ``ocr/<digest>.txt`` files
            are written. Defaults to ``~/.cache/registry-review-mcp``.

    Returns:
        The OCRed text, or ``None`` if OCR was requested but no text was
        recovered. Returns the cached result transparently on repeat calls.
    """
    if not is_tesseract_available():
        _warn_tesseract_missing_once()
        return None

    # Lazy imports so tests can exercise the module without PyMuPDF installed
    # and so the Tesseract probe above is authoritative about availability.
    import pymupdf

    cache_root = cache_root or Path.home() / ".cache" / "registry-review-mcp"
    cache_path = _ocr_cache_path(cache_root, filepath, page_num, mode, language, dpi)
    if cache_path.exists():
        try:
            return cache_path.read_text(encoding="utf-8")
        except OSError:
            # Corrupt/unreadable cache entry — rewrite below.
            pass

    try:
        doc = pymupdf.open(filepath)
    except Exception as exc:
        logger.error("OCR open failed for %s: %s", filepath, exc)
        return None

    try:
        if page_num < 0 or page_num >= doc.page_count:
            logger.warning("OCR requested for out-of-range page %s (doc has %s pages)", page_num, doc.page_count)
            return None

        page = doc[page_num]
        text: str = ""

        if mode in ("auto", "blocks"):
            try:
                tp = page.get_textpage_ocr(language=language, dpi=dpi, full=False)
                text = page.get_text("text", textpage=tp)
            except Exception as exc:
                logger.debug("Block-mode OCR failed on page %s: %s", page_num, exc)
                text = ""

        if (not text.strip()) and mode in ("auto", "full"):
            try:
                tp = page.get_textpage_ocr(language=language, dpi=dpi, full=True)
                text = page.get_text("text", textpage=tp)
            except Exception as exc:
                logger.debug("Full-mode OCR failed on page %s: %s", page_num, exc)
                text = ""

        text = text.strip()
        if not text:
            return None

        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(text, encoding="utf-8")
        except OSError as exc:
            # Cache write failure is non-fatal — log and return the text so
            # the caller still benefits from this run's work.
            logger.debug("OCR cache write failed for %s: %s", cache_path, exc)

        return text
    finally:
        doc.close()


def page_needs_ocr(
    text: str,
    page: "pymupdf.Page | Any",
    *,
    density_threshold: int = 50,
) -> bool:
    """Heuristic for whether a PyMuPDF page's extracted text is image-trapped.

    Args:
        text: The text PyMuPDF4LLM returned for the page chunk.
        page: A ``pymupdf.Page`` instance used to count image blocks. Typed
            loosely so the module does not require PyMuPDF at import time.
        density_threshold: Pages with fewer than this many meaningful
            characters (whitespace stripped) are candidates for OCR. 50 is
            a reasonable default: a genuinely blank or title-only page
            would normally come in well under that, and an Ecometric
            infographic page reliably lands in the 0–30 range because of
            the "intentionally omitted" stubs.

    Returns:
        True when the page looks sparse AND has at least one image block.
        False for genuinely text-light pages that simply contain no images
        — those shouldn't eat OCR time.
    """
    clean = "".join(ch for ch in text if not ch.isspace())
    if len(clean) >= density_threshold:
        return False

    try:
        blocks = page.get_text("dict").get("blocks", [])
    except Exception:
        return False

    # PyMuPDF encodes image blocks with ``type == 1`` (text blocks are 0).
    image_blocks = sum(1 for b in blocks if b.get("type") == 1)
    return image_blocks > 0
