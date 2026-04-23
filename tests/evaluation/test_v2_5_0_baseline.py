"""Slow regression test — asserts full-pipeline agreement ≥ v2.5.0 baseline.

Runs the actual driver (ra-agent-run-fixture.sh) via subprocess for each
registered fixture, then invokes ra-agent-diff.py with --baseline and asserts
the baseline comparison passes.

Markers: expensive + regression. Deselected by default in pytest.ini. Run with:

    uv run pytest -m regression -q tests/evaluation/

Env requirements:
    RRM_FIXTURE_BURTON_LATIMER  — path to Burton Latimer submission dir
    RRM_FIXTURE_ROCKSCAPE        — path to Rockscape Farms submission dir
    TELUS_GPT_OSS_URL / _KEY    — sovereign LLM creds (sourced by wrapper)

Each test takes ~5-30 min depending on response cache state. Total budget ~65 min.

TELUS endpoint unreachable → tests xfail (don't hard-fail CI on external outage).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path.home() / ".claude/local/scripts"
BASELINES_DIR = Path(__file__).parent / "baselines"
DRIVER_SH = SCRIPTS / "ra-agent-run-fixture.sh"
DIFF_PY = SCRIPTS / "ra-agent-diff.py"
TELUS_SECRETS = Path.home() / ".claude/local/secrets/telus-api.env"


FIXTURES = [
    "burton-latimer",
    "rockscape-farms",
]


def _telus_reachable() -> bool:
    """Quick reachability check on the TELUS endpoint (5s TCP connect)."""
    try:
        url = subprocess.check_output(
            [
                "bash", "-c",
                f"set -a; source '{TELUS_SECRETS}'; set +a; echo -n $TELUS_GPT_OSS_URL",
            ],
            timeout=5,
        ).decode().strip()
        if not url:
            return False
        import socket
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not host:
            return False
        with socket.create_connection((host, port), timeout=5):
            pass
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def telus_available() -> bool:
    return _telus_reachable()


@pytest.mark.expensive
@pytest.mark.regression
@pytest.mark.parametrize("fixture", FIXTURES)
def test_v2_5_0_baseline(fixture: str, telus_available: bool, tmp_path: Path):
    """Run full pipeline against fixture, assert diff vs. baseline passes."""
    if not telus_available:
        pytest.xfail("TELUS GPT-OSS endpoint unreachable — skipping regression")
    baseline = BASELINES_DIR / f"{fixture}-v2.5.0.json"
    if not baseline.exists():
        pytest.skip(f"No baseline committed yet for {fixture}")
    if not DRIVER_SH.exists() or not DIFF_PY.exists():
        pytest.skip(f"Driver/diff scripts not present at {SCRIPTS}")
    if not shutil.which("bash"):
        pytest.skip("bash not available")

    # Use an isolated output root per test so parallel runs don't clobber
    output_root = tmp_path / "regen-ai"
    output_root.mkdir(parents=True)

    # --- Step 1: run the driver (~20 min wall-clock, $0 on TELUS) ---
    driver_cmd = [
        "bash", str(DRIVER_SH), fixture,
        "--phase", "f",
        "--output-root", str(output_root),
    ]
    env = dict(os.environ)
    result = subprocess.run(
        driver_cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=2700,  # 45 min max
    )
    if result.returncode != 0:
        pytest.fail(
            f"Driver failed (rc={result.returncode})\n"
            f"STDOUT tail:\n{result.stdout[-2000:]}\n"
            f"STDERR tail:\n{result.stderr[-2000:]}"
        )

    # Sanity: artifacts produced
    art_dir = output_root / "phase-f" / "artifacts"
    reviews = list(art_dir.glob(f"{fixture}-*-review.json"))
    assert reviews, f"No review JSON found in {art_dir}"

    # --- Step 2: run the diff with --baseline ---
    diff_cmd = [
        "uv", "run", "python", str(DIFF_PY),
        "--fixture", fixture,
        "--phase", "f",
        "--output-root", str(output_root),
        "--baseline", str(baseline),
    ]
    diff_result = subprocess.run(
        diff_cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert diff_result.returncode == 0, (
        f"Diff failed (rc={diff_result.returncode})\n"
        f"STDOUT:\n{diff_result.stdout}\n"
        f"STDERR:\n{diff_result.stderr}"
    )

    # --- Step 3: load diff JSON and assert baseline_comparison passes ---
    diff_jsons = sorted(
        (output_root / "phase-f" / "diffs").glob(f"{fixture}-*-diff.json"),
        reverse=True,
    )
    assert diff_jsons, "No diff JSON produced"
    diff_data = json.loads(diff_jsons[0].read_text())
    bc = diff_data.get("baseline_comparison")
    assert bc is not None, "baseline_comparison missing — did --baseline apply?"

    # Hard assertions: over-scoring tightest, under-scoring tight, agreement 2pp
    assert bc["passes_over_scoring"], (
        f"Over-scoring regression: current={diff_data['over_scoring']:.4f} vs "
        f"baseline={bc['baseline_over_scoring']:.4f} (delta={bc['delta_over_scoring']:+.4f}, "
        f"ceiling=+{bc['epsilon_over_scoring']})"
    )
    assert bc["passes_under_scoring"], (
        f"Under-scoring regression: current={diff_data['under_scoring']:.4f} vs "
        f"baseline={bc['baseline_under_scoring']:.4f} (delta={bc['delta_under_scoring']:+.4f}, "
        f"ceiling=+{bc['epsilon_under_scoring']})"
    )
    assert bc["passes_agreement"], (
        f"Agreement regression: current={diff_data['exact_agreement']:.4f} vs "
        f"baseline={bc['baseline_exact_agreement']:.4f} (delta={bc['delta_exact_agreement']:+.4f}, "
        f"floor=-{bc['epsilon_agreement']})"
    )
