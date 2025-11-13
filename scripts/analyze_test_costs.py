#!/usr/bin/env python3
"""Analyze API costs across test suite runs.

Usage:
    # Run with cost tracking enabled
    TRACK_TEST_COSTS=1 pytest tests/ -v

    # Analyze costs
    python scripts/analyze_test_costs.py
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


def analyze_costs():
    """Analyze and report test suite API costs."""

    # Look for cost tracking files in /tmp
    cost_files = list(Path('/tmp').glob('test_*.json'))

    if not cost_files:
        print("No test cost files found.")
        print("\nTo track costs, run:")
        print("  pytest tests/ -v")
        print("\nCost tracking files are automatically created in /tmp/")
        return

    total_cost = 0.0
    total_calls = 0
    total_input_tokens = 0
    total_output_tokens = 0
    cached_calls = 0

    by_extractor = defaultdict(lambda: {'cost': 0.0, 'calls': 0, 'tokens': 0})
    expensive_tests = []

    print(f"Found {len(cost_files)} test cost tracking files\n")
    print("=" * 80)
    print(f"{'Test File':<40} {'Cost':>10} {'Calls':>8} {'Tokens':>12}")
    print("=" * 80)

    for file in sorted(cost_files):
        try:
            with open(file) as f:
                data = json.load(f)
                cost = data.get('total_cost_usd', 0.0)
                calls = data.get('total_api_calls', 0)
                input_tok = data.get('total_input_tokens', 0)
                output_tok = data.get('total_output_tokens', 0)
                total_tokens = input_tok + output_tok

                # Count cached calls
                api_calls = data.get('api_calls', [])
                cached = sum(1 for call in api_calls if call.get('cached', False))

                total_cost += cost
                total_calls += calls
                total_input_tokens += input_tok
                total_output_tokens += output_tok
                cached_calls += cached

                # Track by extractor
                for call in api_calls:
                    extractor = call.get('extractor', 'unknown')
                    by_extractor[extractor]['cost'] += call.get('cost_usd', 0.0)
                    by_extractor[extractor]['calls'] += 1
                    by_extractor[extractor]['tokens'] += call.get('input_tokens', 0) + call.get('output_tokens', 0)

                if cost > 0:
                    print(f"{file.name:<40} ${cost:>9.4f} {calls:>8} {total_tokens:>12,}")
                    if cost > 0.10:  # Flag expensive tests
                        expensive_tests.append((file.name, cost, calls))

        except Exception as e:
            print(f"Error reading {file.name}: {e}", file=sys.stderr)

    print("=" * 80)
    print(f"{'TOTAL':<40} ${total_cost:>9.4f} {total_calls:>8} {total_input_tokens + total_output_tokens:>12,}")
    print("=" * 80)

    print(f"\n=== SUMMARY ===")
    print(f"Total API Calls: {total_calls:,}")
    print(f"  - Real API calls: {total_calls - cached_calls:,}")
    print(f"  - Cached calls: {cached_calls:,}")
    print(f"Total Input Tokens: {total_input_tokens:,}")
    print(f"Total Output Tokens: {total_output_tokens:,}")
    print(f"Total Cost: ${total_cost:.4f}")
    if total_calls > 0:
        print(f"Cache Hit Rate: {cached_calls/total_calls*100:.1f}%")
        print(f"Average Cost per Call: ${total_cost/total_calls:.4f}")

    if by_extractor:
        print(f"\n=== COST BY EXTRACTOR ===")
        for extractor, stats in sorted(by_extractor.items(), key=lambda x: x[1]['cost'], reverse=True):
            print(f"{extractor:>12}: ${stats['cost']:>8.4f} ({stats['calls']:>3} calls, {stats['tokens']:>8,} tokens)")

    if expensive_tests:
        print(f"\n=== EXPENSIVE TESTS (>${0.10:.2f}) ===")
        for test_name, cost, calls in sorted(expensive_tests, key=lambda x: x[1], reverse=True):
            print(f"  {test_name:<40} ${cost:.4f} ({calls} calls)")

    print(f"\n=== OPTIMIZATION RECOMMENDATIONS ===")

    # Calculate potential savings
    mockable_tests = len([t for t in expensive_tests if t[1] > 0.05])
    estimated_savings = sum(t[1] for t in expensive_tests if t[1] > 0.05) * 0.8  # 80% reduction with mocks

    if mockable_tests > 0:
        print(f"1. Mock {mockable_tests} expensive tests → Save ~${estimated_savings:.2f} per run")

    if cached_calls < total_calls * 0.5:
        print(f"2. Current cache hit rate is {cached_calls/total_calls*100:.1f}% → Target 80%+ with fixtures")

    if total_calls > 100:
        print(f"3. Consider pytest-xdist for parallel execution → Reduce wall time by 50-70%")

    real_calls = total_calls - cached_calls
    if real_calls > 50:
        print(f"4. Use @pytest.mark.slow for {real_calls} API tests → Skip with '-m \"not slow\"' during development")


if __name__ == '__main__':
    analyze_costs()
