# Testing Runbook

Last updated: 2026-02-07

## Quick Reference

```bash
# Run fast tests (always safe, no API calls)
pytest

# That's it. Do not add flags unless you know exactly what you're doing.
```

## Why This Matters

This project has expensive API-based tests that call the Anthropic API and cost real money. The `pytest.ini` is configured to exclude them by default. The fast test suite (~229 tests) runs in seconds and covers all critical paths without API calls.

## Test Markers

| Marker | Cost | Description | How to Run |
|--------|------|-------------|------------|
| (default) | Free | Fast unit and smoke tests | `pytest` |
| `expensive` | $$ | LLM extraction and integration | `pytest -m expensive` |
| `accuracy` | $$$ | Ground truth validation with Botany Farm | `pytest -m accuracy` |
| `marker` | Free but slow | Marker PDF extraction (needs 8GB+ RAM) | `pytest -m marker` |
| `integration` | $ | Full workflow integration | `pytest -m integration` |

## What to Run When

| Scenario | Command |
|----------|---------|
| Before any commit | `pytest` |
| After changing extractors or LLM code | `pytest` then consider `pytest -m expensive` if the change is significant |
| After changing report generation | `pytest` (includes `test_report_generation.py`) |
| After changing validation logic | `pytest` (includes `test_validation.py` and `test_validation_improvements.py`) |
| Before deploying to production | `pytest` (must be green) |
| Verifying Botany Farm accuracy | `pytest -m accuracy` (costs API tokens) |
| Full confidence check | `pytest -m "expensive or accuracy"` (costs significant API tokens) |

## Red Flags

If you run `pytest` and see **zero tests deselected**, you are running expensive tests. Stop and check your command — you probably added `-m ""` or some other flag that overrides the default marker exclusion.

The expected output should look something like:
```
229 passed, 15 deselected
```

The "deselected" count confirms expensive tests are being properly skipped.

## Test Infrastructure

| File | Purpose |
|------|---------|
| `tests/conftest.py` | Environment isolation, fixtures, temp directory management |
| `tests/factories.py` | Test data factories for sessions, documents, evidence |
| `tests/botany_farm_ground_truth.json` | Reference data for accuracy tests |
| `tests/plugins/cost_control.py` | Cost limiting plugin |

## Adding New Tests

New tests for non-API functionality should run without any markers (they'll be included in the default `pytest` run). If a test calls the Anthropic API, mark it:

```python
@pytest.mark.expensive
async def test_that_calls_anthropic():
    ...
```

If a test validates accuracy against ground truth data:

```python
@pytest.mark.accuracy
async def test_botany_farm_specific_field():
    ...
```
