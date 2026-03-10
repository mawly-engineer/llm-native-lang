#!/usr/bin/env python3
"""Automated benchmark runner with JSON output and CI integration.

Usage:
    python3 scripts/run_benchmarks.py                    # Run full suite
    python3 scripts/run_benchmarks.py --category parser    # Run parser category only
    python3 scripts/run_benchmarks.py --output metrics/latest.json
    python3 scripts/run_benchmarks.py --compare metrics/baseline.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.benchmark_suite import (
    BENCHMARK_WORKLOADS,
    export_results,
    run_benchmark_suite,
)


def filter_workloads_by_category(category: str) -> List[Any]:
    """Filter workloads by category."""
    return [w for w in BENCHMARK_WORKLOADS if w.category == category]


def filter_workloads_by_tag(tag: str) -> List[Any]:
    """Filter workloads by tag."""
    return [w for w in BENCHMARK_WORKLOADS if tag in w.tags]


def load_baseline(filepath: str) -> Dict[str, Any]:
    """Load baseline benchmark results for comparison."""
    with open(filepath, "r") as f:
        return json.load(f)


def compare_results(
    current: Dict[str, Any],
    baseline: Dict[str, Any],
    threshold_pct: float = 10.0,
) -> Dict[str, Any]:
    """Compare current results against baseline.
    
    Returns comparison with regressions flagged.
    """
    comparison = {
        "baseline_file": baseline.get("summary", {}).get("benchmark_id", "unknown"),
        "current_file": current.get("summary", {}).get("benchmark_id", "LNG-BENCH-001"),
        "threshold_pct": threshold_pct,
        "overall_regression": False,
        "workload_comparisons": [],
    }
    
    baseline_results = {r["workload_id"]: r for r in baseline.get("results", [])}
    current_results = {r["workload_id"]: r for r in current.get("results", [])}
    
    regressions = 0
    improvements = 0
    
    for workload_id, current_result in current_results.items():
        if workload_id not in baseline_results:
            continue
            
        baseline_result = baseline_results[workload_id]
        baseline_time = baseline_result["avg_total_time_ms"]
        current_time = current_result["avg_total_time_ms"]
        
        if baseline_time == 0:
            pct_change = 0.0
        else:
            pct_change = ((current_time - baseline_time) / baseline_time) * 100
        
        status = "neutral"
        if pct_change > threshold_pct:
            status = "regression"
            regressions += 1
        elif pct_change < -threshold_pct:
            status = "improvement"
            improvements += 1
        
        comparison["workload_comparisons"].append({
            "workload_id": workload_id,
            "baseline_ms": round(baseline_time, 3),
            "current_ms": round(current_time, 3),
            "pct_change": round(pct_change, 2),
            "status": status,
        })
    
    comparison["regressions"] = regressions
    comparison["improvements"] = improvements
    comparison["overall_regression"] = regressions > 0
    comparison["summary"] = f"{regressions} regressions, {improvements} improvements"
    
    return comparison


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run llm-native-lang performance benchmarks"
    )
    parser.add_argument(
        "--category",
        choices=["parser", "evaluator", "memory"],
        help="Run only benchmarks in this category",
    )
    parser.add_argument(
        "--tag",
        help="Run only benchmarks with this tag",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of iterations per workload (default: 5)",
    )
    parser.add_argument(
        "--fuel",
        type=int,
        default=100000,
        help="Fuel limit for evaluation (default: 100000)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for JSON results",
    )
    parser.add_argument(
        "--compare",
        "-c",
        help="Compare against baseline JSON file",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Regression threshold percentage (default: 10.0)",
    )
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="Exit with non-zero code on regression (for CI)",
    )
    
    args = parser.parse_args()
    
    # Select workloads
    if args.category:
        workloads = filter_workloads_by_category(args.category)
        print(f"Running {len(workloads)} workloads in category: {args.category}")
    elif args.tag:
        workloads = filter_workloads_by_tag(args.tag)
        print(f"Running {len(workloads)} workloads with tag: {args.tag}")
    else:
        workloads = None  # Use all default workloads
        print(f"Running full benchmark suite ({len(BENCHMARK_WORKLOADS)} workloads)")
    
    # Run benchmarks
    print(f"\nIterations per workload: {args.iterations}")
    print(f"Fuel limit: {args.fuel}")
    print("-" * 60)
    
    start_time = time.time()
    results = run_benchmark_suite(
        workloads=workloads,
        iterations=args.iterations,
        fuel_limit=args.fuel,
    )
    elapsed = time.time() - start_time
    
    # Print summary
    summary = results["summary"]
    print(f"\n{'='*60}")
    print(f"Benchmark Summary")
    print(f"{'='*60}")
    print(f"Total workloads: {summary['total_workloads']}")
    print(f"Successful: {summary['successful_workloads']}")
    print(f"Failed: {summary['failed_workloads']}")
    print(f"Total time: {summary['total_time_ms']:.2f}ms")
    print(f"Wall clock: {elapsed:.2f}s")
    
    print(f"\nCategory Breakdown:")
    for cat, stats in summary["category_summary"].items():
        print(f"  {cat:12s} - {stats['workloads']} workloads, "
              f"{stats['total_time_ms']:.2f}ms total, "
              f"{stats['success_rate']*100:.0f}% success")
    
    # Comparison mode
    exit_code = 0
    if args.compare:
        print(f"\n{'='*60}")
        print(f"Comparison with Baseline: {args.compare}")
        print(f"{'='*60}")
        
        try:
            baseline = load_baseline(args.compare)
            comparison = compare_results(results, baseline, args.threshold)
            
            print(f"Threshold: {args.threshold}%")
            print(f"\n{comparison['summary']}")
            
            if comparison["workload_comparisons"]:
                print(f"\nWorkload Comparisons:")
                for comp in comparison["workload_comparisons"]:
                    status_icon = "✓" if comp["status"] in ["neutral", "improvement"] else "✗"
                    print(f"  {status_icon} {comp['workload_id']}: "
                          f"{comp['baseline_ms']}ms → {comp['current_ms']}ms "
                          f"({comp['pct_change']:+.1f}%)")
            
            if comparison["overall_regression"]:
                print(f"\n⚠ REGRESSION DETECTED")
                if args.ci_mode:
                    exit_code = 1
        except FileNotFoundError:
            print(f"Error: Baseline file not found: {args.compare}")
            exit_code = 2
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in baseline file: {args.compare}")
            exit_code = 2
    
    # Save results
    if args.output:
        export_results(results, args.output)
        print(f"\nResults saved to: {args.output}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
