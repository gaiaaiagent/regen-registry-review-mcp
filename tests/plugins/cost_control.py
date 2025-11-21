"""Pytest plugin for cost control via test sampling.

This plugin allows intelligent sampling of expensive tests to reduce API costs
while maintaining reasonable test coverage.

Usage:
    # Run all expensive tests (local development)
    pytest -m expensive

    # Run 25% random sample (CI cost savings)
    pytest -m expensive --sample=0.25

    # Auto-sample 25% in CI environment
    CI=1 pytest -m expensive

    # With cost cap (future enhancement)
    pytest -m expensive --max-cost=1.00

Features:
    - Random sampling of expensive tests
    - Automatic 25% sampling in CI
    - Configurable sample rate via --sample flag
    - Budget cap support (--max-cost, future)
"""

import os
import random
import pytest


def pytest_addoption(parser):
    """Add command-line options for cost control."""
    parser.addoption(
        "--sample",
        type=float,
        default=1.0,
        help="Fraction of expensive tests to run (0.0-1.0). Default: 1.0 (all tests)"
    )
    parser.addoption(
        "--max-cost",
        type=float,
        help="Maximum API cost in USD before aborting (future enhancement)"
    )


def pytest_collection_modifyitems(config, items):
    """Sample expensive tests based on --sample rate or CI environment.

    Auto-samples 25% of expensive tests in CI unless --sample explicitly set.
    Skips non-sampled tests with clear reason message.
    """
    # Determine sample rate
    sample_rate = config.getoption("--sample")

    # Auto-sample 25% in CI unless explicitly overridden
    if os.getenv("CI") and sample_rate == 1.0:
        sample_rate = 0.25
        print(f"\n💰 CI detected: Auto-sampling {sample_rate:.0%} of expensive tests")

    # No sampling needed if rate is 100%
    if sample_rate >= 1.0:
        return

    # Find expensive tests
    expensive_tests = [item for item in items if "expensive" in item.keywords]

    if not expensive_tests:
        return  # No expensive tests to sample

    # Determine sample size (at least 1 test)
    sample_count = max(1, int(len(expensive_tests) * sample_rate))

    # Set random seed for reproducibility (same day = same sample)
    # This ensures consistent CI results within a day
    from datetime import date
    seed = int(date.today().strftime("%Y%m%d"))
    random.seed(seed)

    # Random sample
    sampled_tests = random.sample(expensive_tests, sample_count)

    # Mark non-sampled tests to skip
    skipped_count = 0
    for item in expensive_tests:
        if item not in sampled_tests:
            item.add_marker(
                pytest.mark.skip(reason=f"Not in {sample_rate:.0%} sample (cost control)")
            )
            skipped_count += 1

    # Print sampling summary
    print(f"\n🎲 Sampling Strategy:")
    print(f"   • Total expensive tests: {len(expensive_tests)}")
    print(f"   • Sample rate: {sample_rate:.0%}")
    print(f"   • Running: {sample_count} tests")
    print(f"   • Skipping: {skipped_count} tests")
    print(f"   • Seed: {seed} (daily rotation)")
