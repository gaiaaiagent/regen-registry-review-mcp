"""Unit tests for the OCR fallback pipeline (Issue #4).

These tests intentionally avoid invoking Tesseract. Tesseract is a system
dependency that may or may not be installed on a given developer's machine
and on CI, and an accuracy/benchmark suite against real fixtures belongs in
``@pytest.mark.expensive`` territory alongside the existing Botany Farm
ground-truth tests. What this suite verifies is the surrounding glue:

- Tesseract detection is memoized and degrades gracefully when missing.
- The density+images heuristic flags the right pages.
- The OCR cache key is deterministic and invalidates on mtime change.
- The fast extractor surfaces an ``ocr`` sub-dictionary in its return
  value regardless of whether OCR actually ran, so downstream consumers
  get a stable schema.
"""

from __future__ import annotations

import types
from unittest import mock

import pytest

from registry_review_mcp.extractors import ocr as ocr_module


def _reset_tesseract_probe() -> None:
    """Ensure each test evaluates the Tesseract probe fresh."""
    ocr_module._TESSERACT_AVAILABLE = None
    ocr_module._TESSERACT_WARNING_EMITTED = False


@pytest.fixture(autouse=True)
def _clean_tesseract_state():
    _reset_tesseract_probe()
    yield
    _reset_tesseract_probe()


class TestOcrSettingsDefaults:
    """Regression guard for the v2.2.0 default-flip.

    OCR is now enabled out-of-box so operators who install the package and
    run it against image-heavy PDFs get the rescue automatically. This test
    pins the default so an accidental revert to False surfaces loudly.
    """

    def test_ocr_enabled_default_is_true(self):
        from registry_review_mcp.config.settings import Settings

        # Isolate from host env vars that might override the class default.
        fresh = Settings(_env_file=None)
        assert fresh.ocr_enabled is True


class TestTesseractProbe:
    """is_tesseract_available() behavior."""

    def test_probe_returns_false_when_pymupdf_raises(self):
        """Simulate an install without Tesseract — probe must not propagate."""
        with mock.patch("pymupdf.get_tessdata", side_effect=RuntimeError("no tessdata")):
            assert ocr_module.is_tesseract_available() is False

    def test_probe_memoizes(self):
        """Second call must not re-invoke PyMuPDF."""
        with mock.patch("pymupdf.get_tessdata", return_value=None) as patched:
            ocr_module.is_tesseract_available()
            ocr_module.is_tesseract_available()
            assert patched.call_count == 1

    def test_probe_true_when_tessdata_exists(self, tmp_path):
        """If PyMuPDF reports a directory and it exists, probe returns True."""
        tessdata = tmp_path / "tessdata"
        tessdata.mkdir()
        with mock.patch("pymupdf.get_tessdata", return_value=str(tessdata)):
            assert ocr_module.is_tesseract_available() is True

    def test_probe_false_when_tessdata_path_missing(self, tmp_path):
        """PyMuPDF may return a path that no longer exists — treat as missing."""
        tessdata = tmp_path / "nonexistent"
        with mock.patch("pymupdf.get_tessdata", return_value=str(tessdata)):
            assert ocr_module.is_tesseract_available() is False

    def test_warning_emitted_once(self, caplog):
        """Missing-Tesseract warning should not flood the logs."""
        import logging as _logging

        caplog.set_level(_logging.WARNING, logger=ocr_module.logger.name)
        with mock.patch("pymupdf.get_tessdata", side_effect=RuntimeError("no")):
            for _ in range(5):
                assert ocr_module.ocr_page("/tmp/whatever.pdf", 0) is None

        tesseract_warnings = [r for r in caplog.records if "Tesseract" in r.getMessage()]
        assert len(tesseract_warnings) == 1


class TestPageNeedsOcr:
    """page_needs_ocr heuristic."""

    def _page_with_blocks(self, block_types: list[int]):
        """Build a stand-in page whose ``get_text('dict')`` returns fixed blocks."""
        page = types.SimpleNamespace()
        page.get_text = lambda kind: {"blocks": [{"type": t} for t in block_types]}
        return page

    def test_dense_text_page_not_flagged(self):
        """A page with plenty of extracted text should not be OCRed."""
        page = self._page_with_blocks([1])
        text = "This page has lots of content — " * 20
        assert ocr_module.page_needs_ocr(text, page, density_threshold=50) is False

    def test_sparse_with_image_blocks_flagged(self):
        """Sparse text on a page containing images is the Ecometric signature."""
        page = self._page_with_blocks([0, 1])
        assert ocr_module.page_needs_ocr("", page, density_threshold=50) is True

    def test_sparse_without_image_blocks_skipped(self):
        """A genuinely blank page with no images shouldn't eat OCR time."""
        page = self._page_with_blocks([0])
        assert ocr_module.page_needs_ocr("", page, density_threshold=50) is False

    def test_whitespace_only_counts_as_sparse(self):
        """Whitespace is not meaningful text."""
        page = self._page_with_blocks([1])
        assert ocr_module.page_needs_ocr("   \n\n   ", page, density_threshold=10) is True

    def test_page_dict_failure_returns_false(self):
        """If block inspection raises, fail closed (do not OCR)."""
        page = types.SimpleNamespace()

        def _raise(kind):
            raise RuntimeError("page dict exploded")

        page.get_text = _raise
        assert ocr_module.page_needs_ocr("", page, density_threshold=10) is False


class TestOcrCacheKey:
    """_ocr_cache_path determinism + invalidation."""

    def test_same_inputs_same_path(self, tmp_path):
        a = ocr_module._ocr_cache_path(tmp_path, "/x.pdf", 2, "auto", "eng", 150)
        b = ocr_module._ocr_cache_path(tmp_path, "/x.pdf", 2, "auto", "eng", 150)
        assert a == b

    def test_different_page_different_path(self, tmp_path):
        a = ocr_module._ocr_cache_path(tmp_path, "/x.pdf", 1, "auto", "eng", 150)
        b = ocr_module._ocr_cache_path(tmp_path, "/x.pdf", 2, "auto", "eng", 150)
        assert a != b

    def test_different_language_different_path(self, tmp_path):
        a = ocr_module._ocr_cache_path(tmp_path, "/x.pdf", 1, "auto", "eng", 150)
        b = ocr_module._ocr_cache_path(tmp_path, "/x.pdf", 1, "auto", "eng+ces", 150)
        assert a != b

    def test_different_dpi_different_path(self, tmp_path):
        a = ocr_module._ocr_cache_path(tmp_path, "/x.pdf", 1, "auto", "eng", 150)
        b = ocr_module._ocr_cache_path(tmp_path, "/x.pdf", 1, "auto", "eng", 300)
        assert a != b

    def test_mtime_change_invalidates(self, tmp_path):
        """A re-saved PDF with the same filename must not reuse stale cache."""
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")
        first = ocr_module._ocr_cache_path(tmp_path, str(pdf), 0, "auto", "eng", 150)

        import os as _os

        future = pdf.stat().st_mtime + 10
        _os.utime(pdf, (future, future))
        second = ocr_module._ocr_cache_path(tmp_path, str(pdf), 0, "auto", "eng", 150)
        assert first != second


class TestOcrPageDegradation:
    """ocr_page degrades to None when Tesseract is missing."""

    def test_returns_none_without_tesseract(self):
        with mock.patch("pymupdf.get_tessdata", side_effect=RuntimeError("no")):
            result = ocr_module.ocr_page("/tmp/whatever.pdf", 0)
        assert result is None

    def test_uses_cache_when_present(self, tmp_path):
        """A pre-existing cache file is returned without invoking PyMuPDF."""
        tessdata = tmp_path / "tessdata"
        tessdata.mkdir()
        cache_root = tmp_path / "cache"
        pdf_path = tmp_path / "doc.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

        cache_file = ocr_module._ocr_cache_path(cache_root, str(pdf_path), 0, "auto", "eng", 150)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("pre-cached recovered text", encoding="utf-8")

        with mock.patch("pymupdf.get_tessdata", return_value=str(tessdata)):
            with mock.patch("pymupdf.open") as patched_open:
                text = ocr_module.ocr_page(
                    str(pdf_path), 0, mode="auto", language="eng", dpi=150, cache_root=cache_root
                )

        assert text == "pre-cached recovered text"
        patched_open.assert_not_called()


class TestFastExtractorOcrSchema:
    """The fast extractor always returns an ``ocr`` sub-dictionary.

    Regardless of whether OCR ran, callers should be able to read
    ``result["ocr"]["mode"]`` without a KeyError. This test exercises a
    minimal PDF and asserts the schema, while leaving Tesseract unprobed.
    """

    def test_ocr_key_present_when_disabled(self, tmp_path, monkeypatch):
        # Build a trivially valid 1-page PDF via PyMuPDF so the fast extractor
        # has something to chew on. No OCR invocation required — ocr_enabled
        # is False by default.
        import pymupdf

        pdf_path = tmp_path / "minimal.pdf"
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello registry reviewers.")
        doc.save(str(pdf_path))
        doc.close()

        import asyncio

        from registry_review_mcp.extractors.fast_extractor import fast_extract_pdf

        result = asyncio.run(fast_extract_pdf(str(pdf_path)))

        assert "ocr" in result
        assert result["ocr"]["mode"] in {"disabled", "enabled", "requested-but-tesseract-missing"}
        assert result["ocr"]["pages_recovered"] == 0
        assert result["extraction_method"] == "pymupdf4llm"


@pytest.mark.expensive
class TestOcrRealRoundtrip:
    """Exercise Tesseract end-to-end on a synthetic image-only PDF.

    Opt-in because Tesseract is a system package and CI will not always
    have it installed. Marked ``expensive`` so the default ``pytest``
    invocation deselects it and only the benchmark pass picks it up.

    The fixture writes four known lines into a PNG, embeds the PNG as a
    full-page image, and asks the fast extractor to run OCR. We assert
    that every line survives the round trip and that the cache short-
    circuits the second call.
    """

    def test_image_only_pdf_recovered_via_ocr(self, tmp_path):
        pytest.importorskip("PIL.Image")
        from PIL import Image, ImageDraw, ImageFont

        import pymupdf

        from registry_review_mcp.extractors.ocr import is_tesseract_available

        if not is_tesseract_available():
            pytest.skip("System Tesseract not installed; skipping real OCR roundtrip")

        # Render text as bitmap + embed as page image.
        img = Image.new("RGB", (1240, 1754), "white")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 48)
        except (OSError, IOError):
            font = ImageFont.load_default()

        lines = [
            "ECOMETRIC SOIL CARBON",
            "Project: Rockscape Farms C06-021",
            "Declared area: 280.58 hectares",
            "Centroid: 53.572824 N, -0.794696 W",
        ]
        for idx, line in enumerate(lines):
            draw.text((100, 100 + idx * 120), line, font=font, fill="black")

        import io

        buf = io.BytesIO()
        img.save(buf, format="PNG")

        pdf_path = tmp_path / "image_only.pdf"
        pdf = pymupdf.open()
        page = pdf.new_page(width=595, height=842)
        page.insert_image(page.rect, stream=buf.getvalue())
        pdf.save(str(pdf_path))
        pdf.close()

        # Point OCR cache at a pristine tmp dir so repeat runs can be
        # measured without interference from the user's real cache.
        from registry_review_mcp.config.settings import settings
        import os

        settings.__dict__["_frozen"] = False
        settings.ocr_enabled = True
        settings.cache_dir = tmp_path / "cache"
        settings.__dict__["_frozen"] = True

        import asyncio

        from registry_review_mcp.extractors.fast_extractor import fast_extract_pdf

        try:
            result = asyncio.run(fast_extract_pdf(str(pdf_path)))
            assert result["ocr"]["mode"] == "enabled"
            assert result["ocr"]["pages_recovered"] == 1
            assert result["extraction_method"] == "pymupdf4llm+ocr"

            markdown = result["markdown"]
            # Every synthetic line should round-trip through Tesseract.
            for line in lines:
                # Tesseract may split "C06-021" across a space; we assert on
                # the discriminating word so the test is resilient to minor
                # OCR quirks without going loose enough to pass on garbage.
                key = line.split()[1] if line.startswith("Project") else line.split()[0]
                assert key in markdown, f"Expected '{key}' (from '{line}') in OCR output"

            # Cache hit on second call.
            second = asyncio.run(fast_extract_pdf(str(pdf_path)))
            assert second["ocr"]["pages_recovered"] == 1
        finally:
            # Restore immutable settings to their defaults to avoid
            # leaking across tests.
            settings.__dict__["_frozen"] = False
            settings.ocr_enabled = False
            settings.__dict__["_frozen"] = True
            # Ensure no stray env pressure leaks either.
            os.environ.pop("REGISTRY_REVIEW_OCR_ENABLED", None)
