# Benchmark Fixtures

Real registry submissions used to benchmark and validate the extraction
pipeline. These fixtures are **not checked in** — they are multi-hundred-MB
project dossiers owned by the submitting organizations. Point the test
suite at them via environment variables.

The maintainer keeps fixtures under
`~/.claude/local/ventures/docs/{venture-slug}/sources/{project-slug}/`
but any absolute path works. No repo-owned filesystem convention is implied.

## Env-var contract

| Variable | Purpose | Example |
|----------|---------|---------|
| `RRM_FIXTURE_BURTON_LATIMER` | Root of the Burton Latimer Farms submission tree | `/home/alice/regen/burton-latimer` |
| `RRM_FIXTURE_BOTANY_FARM` | Botany Farm 22-23 fixture (bundled under `examples/22-23` historically) | `/path/to/botany-farm` |

Any fixture referenced by a test marked `@pytest.mark.expensive` follows this
pattern. Missing env var ⇒ test is skipped, never failed.

## Fixture index

### Burton Latimer Farms (UK Ecometric Soil Carbon v1.2.2)

- **Methodology:** Ecometric Soil Carbon v1.2.2 (23 requirements)
- **Contents:** 36 PDFs, 16 XLSX workbooks, 10 shapefiles, ~411 MB on disk
- **Ground truth:** `Burton Latimer Farms Project Registration Registry Agent Review.docx` — 25-row / 6-column review table (Category / Requirement / Accepted Evidence / Submitted Material / Approved / Comments)
- **Benchmark baseline (v2.2.0):**
  - 90.9% sparse-page rescue rate (50 / 55 pages)
  - +11.3% total character recovery (365,148 → 406,294)
  - ~228s runtime on an i7-13700F / RTX 4070 box (6.3s / PDF)

### Botany Farm 22-23 (Ecometric Soil Carbon — earlier submission)

- **Use:** cross-check fixture for OCR regression. Historically surfaced the
  "intentionally omitted" image-stub pattern that the density heuristic keys off.
- **Signature win:** GHG Emissions page 1,655 → 5,792 chars (+250%), 8/11
  image-heavy pages recovered with OCR enabled.

## Running the expensive suite

Fast tests (default, ~3s):
```bash
uv run pytest
```

Expensive suite (requires one or more fixture env vars + Tesseract):
```bash
export RRM_FIXTURE_BURTON_LATIMER=/absolute/path/to/burton-latimer
uv run pytest -m expensive
```

Target a single fixture:
```bash
uv run pytest -m expensive -k burton_latimer -v
```

## Tesseract requirement

OCR-dependent expensive tests require Tesseract on the host:

| OS | Install |
|----|---------|
| Arch / CachyOS | `sudo pacman -S tesseract tesseract-data-eng` |
| Debian / Ubuntu | `sudo apt install tesseract-ocr tesseract-ocr-eng` |
| Fedora | `sudo dnf install tesseract tesseract-langpack-eng` |
| macOS | `brew install tesseract` |

Multi-language OCR (e.g. CSSCP Czech-Slovak): install the appropriate
language pack and set `REGISTRY_REVIEW_OCR_LANGUAGE=eng+ces` (or equivalent).
