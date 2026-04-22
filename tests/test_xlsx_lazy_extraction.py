"""Lazy spreadsheet extraction in evidence_tools (Phase D).

Before Phase D, the lazy path in ``evidence_tools.extract_all_evidence``
only called ``batch_convert_pdfs_parallel``. Spreadsheets mapped to
requirements were classified during discovery but never got a sidecar
markdown, so ``get_markdown_content`` logged ``No markdown available``
and the LLM never saw XLSX evidence.

Phase D adds ``_convert_mapped_spreadsheets`` as a sibling helper to the
PDF batch conversion. It must:

  * read each spreadsheet via ``extract_spreadsheet``,
  * write a ``.fast.md`` sidecar next to the source file,
  * update the doc dict so downstream ``get_markdown_content`` loads it,
  * survive per-file failures without aborting the batch.

These tests fail before the helper is introduced (ImportError) and pass
once it is wired.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_lazy_xlsx_produces_fast_md_sidecar(sample_xlsx):
    """XLSX: lazy helper writes .fast.md sidecar and updates the doc dict."""
    from registry_review_mcp.tools.evidence_tools import _convert_mapped_spreadsheets

    sidecar = sample_xlsx.with_suffix(".fast.md")
    assert not sidecar.exists(), "precondition: no sidecar yet"

    doc: dict = {
        "document_id": "doc-xlsx-1",
        "filepath": str(sample_xlsx),
        "filename": sample_xlsx.name,
    }

    converted = await _convert_mapped_spreadsheets([doc])

    assert converted == 1
    assert sidecar.exists(), "sidecar .fast.md must be written alongside source"
    md = sidecar.read_text()
    assert '--- Sheet "Farm Data"' in md
    assert "CE-001" in md
    assert "Alice" in md
    assert doc["has_markdown"] is True
    assert doc["markdown_path"] == str(sidecar)
    assert doc["fast_status"] == "complete"
    assert doc["active_quality"] == "fast"
    assert doc["hq_status"] == "not_applicable"


@pytest.mark.asyncio
async def test_lazy_csv_produces_fast_md_sidecar(sample_csv):
    """CSV: same lazy helper handles .csv as a single-sheet workbook."""
    from registry_review_mcp.tools.evidence_tools import _convert_mapped_spreadsheets

    sidecar = sample_csv.with_suffix(".fast.md")
    doc: dict = {
        "document_id": "doc-csv-1",
        "filepath": str(sample_csv),
        "filename": sample_csv.name,
    }

    converted = await _convert_mapped_spreadsheets([doc])

    assert converted == 1
    assert sidecar.exists()
    md = sidecar.read_text()
    assert "P-01" in md
    assert doc["has_markdown"] is True
    assert doc["markdown_path"] == str(sidecar)
    assert doc["fast_status"] == "complete"


@pytest.mark.asyncio
async def test_lazy_spreadsheet_records_failure_without_crashing(tmp_path):
    """When extract_spreadsheet raises, mark the doc failed and continue."""
    from registry_review_mcp.tools.evidence_tools import _convert_mapped_spreadsheets

    bogus_path = tmp_path / "missing.xlsx"
    doc: dict = {
        "document_id": "doc-missing",
        "filepath": str(bogus_path),
        "filename": "missing.xlsx",
    }

    converted = await _convert_mapped_spreadsheets([doc])

    assert converted == 0
    assert doc["fast_status"] == "failed"
    assert "fast_error" in doc


@pytest.mark.asyncio
async def test_lazy_spreadsheet_batch_continues_after_per_file_failure(
    sample_xlsx, sample_csv, tmp_path
):
    """One broken doc must not block the successful ones."""
    from registry_review_mcp.tools.evidence_tools import _convert_mapped_spreadsheets

    good_xlsx = {
        "document_id": "good-xlsx",
        "filepath": str(sample_xlsx),
        "filename": sample_xlsx.name,
    }
    good_csv = {
        "document_id": "good-csv",
        "filepath": str(sample_csv),
        "filename": sample_csv.name,
    }
    bad = {
        "document_id": "bad",
        "filepath": str(tmp_path / "nope.xlsx"),
        "filename": "nope.xlsx",
    }

    converted = await _convert_mapped_spreadsheets([good_xlsx, bad, good_csv])

    assert converted == 2
    assert good_xlsx["fast_status"] == "complete"
    assert good_csv["fast_status"] == "complete"
    assert bad["fast_status"] == "failed"
