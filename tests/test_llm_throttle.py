"""Phase E — LLM throttle tests.

Phase D's per-run 504 counts climbed above 200 on heavier fixtures
because ``evidence_tools.extract_all_evidence`` spawns up to 5 concurrent
requirement extractors, and each extractor hits ``call_llm`` per mapped
document. With 23 requirements × 2–3 mapped docs × 5 concurrency, the
TELUS Cloudflare gateway periodically saturated and 504'd the tail.

The throttle sits between ``call_llm`` callers and the backend dispatch.
Two knobs:

- ``LLM_MAX_CONCURRENT`` (default 4): semaphore depth.
- ``LLM_MIN_INTERVAL_MS`` (default 100): minimum monotonic gap between
  successive ``call_llm`` entries, serialized across the process.

Together they bound aggregate RPS at roughly
``min(LLM_MAX_CONCURRENT, 1000 / LLM_MIN_INTERVAL_MS)`` requests per
second — a soft fix that absorbs gateway weather without eliminating it.
"""

from __future__ import annotations

import asyncio
import time

import pytest


def _get_module():
    from registry_review_mcp.llm import throttle

    return throttle


@pytest.fixture(autouse=True)
def _reset_throttle_between_tests(monkeypatch):
    """Each test gets a fresh throttle tuned via env vars."""
    # Clear env for a clean default.
    monkeypatch.delenv("LLM_MAX_CONCURRENT", raising=False)
    monkeypatch.delenv("LLM_MIN_INTERVAL_MS", raising=False)
    _get_module().reset_for_tests()
    yield
    _get_module().reset_for_tests()


class TestConstruction:
    def test_default_max_concurrent_is_four(self):
        mod = _get_module()
        assert mod.get_throttle().max_concurrent == 4

    def test_default_min_interval_ms_is_one_hundred(self):
        mod = _get_module()
        assert mod.get_throttle().min_interval_ms == 100

    def test_env_override_max_concurrent(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_CONCURRENT", "2")
        mod = _get_module()
        mod.reset_for_tests()
        assert mod.get_throttle().max_concurrent == 2

    def test_env_override_min_interval_ms(self, monkeypatch):
        monkeypatch.setenv("LLM_MIN_INTERVAL_MS", "250")
        mod = _get_module()
        mod.reset_for_tests()
        assert mod.get_throttle().min_interval_ms == 250


class TestSemaphore:
    async def test_peak_concurrency_respects_limit(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_CONCURRENT", "2")
        monkeypatch.setenv("LLM_MIN_INTERVAL_MS", "0")
        mod = _get_module()
        mod.reset_for_tests()

        active = 0
        peak = 0
        lock = asyncio.Lock()

        async def worker():
            nonlocal active, peak
            async with mod.acquire_slot():
                async with lock:
                    active += 1
                    peak = max(peak, active)
                await asyncio.sleep(0.02)
                async with lock:
                    active -= 1

        # Spawn 10 concurrent workers — throttle should cap peak at 2.
        await asyncio.gather(*[worker() for _ in range(10)])
        assert peak == 2, f"expected peak=2, got peak={peak}"

    async def test_single_worker_no_contention(self):
        mod = _get_module()
        async with mod.acquire_slot():
            pass  # must not hang or raise


class TestInterval:
    async def test_min_interval_enforced(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_CONCURRENT", "1")
        monkeypatch.setenv("LLM_MIN_INTERVAL_MS", "60")
        mod = _get_module()
        mod.reset_for_tests()

        start = time.monotonic()
        # Three sequential acquisitions with 60 ms interval → ≥ 120 ms total.
        for _ in range(3):
            async with mod.acquire_slot():
                pass
        elapsed_ms = (time.monotonic() - start) * 1000
        assert elapsed_ms >= 110, (
            f"expected ≥110 ms across 3 acquires at 60 ms interval, got {elapsed_ms:.1f} ms"
        )

    async def test_zero_interval_disables_gating(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_CONCURRENT", "1")
        monkeypatch.setenv("LLM_MIN_INTERVAL_MS", "0")
        mod = _get_module()
        mod.reset_for_tests()

        start = time.monotonic()
        for _ in range(20):
            async with mod.acquire_slot():
                pass
        elapsed_ms = (time.monotonic() - start) * 1000
        # 20 no-op acquires should be effectively instantaneous (<50 ms).
        assert elapsed_ms < 50, f"zero interval still gated: {elapsed_ms:.1f} ms"


class TestTelemetry:
    def test_throttle_exposes_peak_permits(self):
        mod = _get_module()
        t = mod.get_throttle()
        # Telemetry hooks for the Phase E closing journal.
        assert hasattr(t, "active_permits_peak")
        assert t.active_permits_peak == 0

    async def test_peak_permits_updates_under_load(self, monkeypatch):
        monkeypatch.setenv("LLM_MAX_CONCURRENT", "3")
        monkeypatch.setenv("LLM_MIN_INTERVAL_MS", "0")
        mod = _get_module()
        mod.reset_for_tests()

        async def worker():
            async with mod.acquire_slot():
                await asyncio.sleep(0.01)

        await asyncio.gather(*[worker() for _ in range(8)])
        assert mod.get_throttle().active_permits_peak >= 2
        assert mod.get_throttle().active_permits_peak <= 3
