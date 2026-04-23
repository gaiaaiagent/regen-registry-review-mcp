"""LLM throttle — shared gate upstream of ``call_llm``.

Phase D observed sustained TELUS Cloudflare gateway 504 pressure on
heavier fixtures. The pipeline already limits in-flight extractors via
``evidence_tools.extract_all_evidence``'s ``asyncio.Semaphore(5)``, but
each extractor fires multiple LLM calls per mapped document, so
aggregate RPS outran the gateway. The cache caught most retries,
but the telemetry still showed 100-200 504s per run.

This module adds an explicit aggregate throttle:

- :class:`Throttle`: holds semaphore depth + minimum interval.
- :func:`acquire_slot`: async context manager callers wrap around a
  backend call. Enforces semaphore depth and minimum monotonic interval.
- :func:`get_throttle`: returns the process-wide throttle. Caches on
  first access so env vars are read once.
- :func:`reset_for_tests`: clears the cached instance so unit tests
  can tweak env vars between cases without leaking state.

Env-configurable (read at first access):

- ``LLM_MAX_CONCURRENT``: semaphore depth. Default 4.
- ``LLM_MIN_INTERVAL_MS``: minimum gap between successive acquisitions.
  Default 100 ms.

Disable entirely with ``LLM_MAX_CONCURRENT=0``. Semaphore is not bound
but interval still fires if configured; set both to 0 for true disable.

Telemetry:

- ``Throttle.active_permits_peak``: the high-water mark of
  simultaneously-held permits. Read by the Phase E closing journal to
  quantify whether the throttle actually bit.
- ``Throttle.calls_throttled``: count of acquisitions that had to wait
  for either the semaphore or the interval.
"""

from __future__ import annotations

import asyncio
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field


@dataclass
class Throttle:
    """Aggregate LLM-call throttle for a process.

    Attributes:
        max_concurrent: Semaphore depth. ``0`` disables the semaphore.
        min_interval_ms: Minimum monotonic gap between successive
            acquisitions. ``0`` disables the interval gate.
        active_permits_peak: High-water mark of simultaneously-held
            permits. Useful for the closing journal's telemetry.
        calls_throttled: Count of acquisitions that waited for either
            the semaphore or the interval.
    """

    max_concurrent: int = 4
    min_interval_ms: int = 100
    active_permits_peak: int = 0
    calls_throttled: int = 0
    _semaphore: asyncio.Semaphore | None = field(default=None, repr=False)
    _active_permits: int = field(default=0, repr=False)
    _last_entry_monotonic_ms: float = field(default=0.0, repr=False)
    _interval_lock: asyncio.Lock | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.max_concurrent > 0:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._interval_lock = asyncio.Lock()


_throttle: Throttle | None = None


def _read_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def get_throttle() -> Throttle:
    """Return the process-wide throttle instance, creating on first call."""
    global _throttle
    if _throttle is None:
        _throttle = Throttle(
            max_concurrent=_read_env_int("LLM_MAX_CONCURRENT", 4),
            min_interval_ms=_read_env_int("LLM_MIN_INTERVAL_MS", 100),
        )
    return _throttle


def reset_for_tests() -> None:
    """Drop the cached throttle so env var changes re-read cleanly.

    Called by the throttle test fixture between cases. Safe to call
    in production too — the next :func:`get_throttle` just rebuilds.
    """
    global _throttle
    _throttle = None


@asynccontextmanager
async def acquire_slot():
    """Async context manager: acquire a throttle slot for one LLM call.

    Holds a semaphore permit for the duration of the ``async with`` block
    and enforces ``min_interval_ms`` between successive acquisitions
    across the whole process.
    """
    t = get_throttle()
    entered_without_wait = True

    # Semaphore gate: acquire before interval so we don't hold timing
    # state for a permit we don't yet own.
    if t._semaphore is not None:
        # Fast path: try_acquire-ish — tests for instant acquisition.
        if t._semaphore.locked():
            entered_without_wait = False
        await t._semaphore.acquire()

    try:
        # Interval gate: serialized across the whole process.
        if t.min_interval_ms > 0 and t._interval_lock is not None:
            async with t._interval_lock:
                now_ms = time.monotonic() * 1000.0
                wait_ms = t.min_interval_ms - (now_ms - t._last_entry_monotonic_ms)
                if wait_ms > 0:
                    entered_without_wait = False
                    await asyncio.sleep(wait_ms / 1000.0)
                t._last_entry_monotonic_ms = time.monotonic() * 1000.0

        # Telemetry — count after both gates are cleared.
        t._active_permits += 1
        if t._active_permits > t.active_permits_peak:
            t.active_permits_peak = t._active_permits
        if not entered_without_wait:
            t.calls_throttled += 1

        yield
    finally:
        t._active_permits -= 1
        if t._semaphore is not None:
            t._semaphore.release()
