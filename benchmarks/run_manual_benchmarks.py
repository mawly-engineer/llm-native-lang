#!/usr/bin/env python3
"""Manual benchmark runner (no pytest-benchmark required)."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.lnd_validate import LNDValidator, parse_yaml_lite
from runtime.interpreter_runtime import eval_expr
from runtime.grammar_contract import parse_expr
from runtime.replay_harness import TraceCapture, ConformanceHarness


def benchmark_lnd_parse():
    """Benchmark LND parsing speed."""
    content = '''@lnd 0.2
kind: work_item
id: TEST-ITEM-001
status: active
updated_at_utc: 2026-03-11T20:22:00Z
title: "Sample work item"
objective: language_core_capability
priority: p0
stage: create
bucket: language
description: |
  This is a sample work item used for benchmarking
next_id: 2
'''
    
    # Warmup
    for _ in range(10):
        parse_yaml_lite(content)
    
    # Benchmark
    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        parse_yaml_lite(content)
    elapsed = time.perf_counter() - start
    
    files_per_sec = iterations / elapsed
    avg_ms = (elapsed / iterations) * 1000
    
    print(f"LND Parse Benchmark:")
    print(f"  Iterations: {iterations}")
    print(f"  Total time: {elapsed*1000:.2f}ms")
    print(f"  Avg time: {avg_ms:.4f}ms per file")
    print(f"  Throughput: {files_per_sec:.1f} files/sec")
    print(f"  Status: {'PASS' if files_per_sec >= 100 else 'FAIL'} (min: 100 files/sec)")
    return files_per_sec >= 100


def benchmark_lnc_execution():
    """Benchmark LNC contract execution."""
    source = "let x = 10 in let y = x + 5 in y * 2"
    ast = parse_expr(source)
    
    # Warmup
    for _ in range(10):
        eval_expr(ast)
    
    # Benchmark
    iterations = 10000
    start = time.perf_counter()
    for _ in range(iterations):
        eval_expr(ast)
    elapsed = time.perf_counter() - start
    
    ops_per_sec = iterations / elapsed
    avg_ms = (elapsed / iterations) * 1000
    
    print(f"\nLNC Execution Benchmark:")
    print(f"  Iterations: {iterations}")
    print(f"  Total time: {elapsed*1000:.2f}ms")
    print(f"  Avg time: {avg_ms:.4f}ms per op")
    print(f"  Throughput: {ops_per_sec:.1f} ops/sec")
    print(f"  Status: {'PASS' if ops_per_sec >= 1000 else 'FAIL'} (min: 1000 ops/sec)")
    return ops_per_sec >= 1000


def benchmark_replay_harness():
    """Benchmark replay harness overhead."""
    source = "let x = 5 in x + 10"
    ast = parse_expr(source)
    
    # Native execution
    native_times = []
    for _ in range(100):
        start = time.perf_counter()
        eval_expr(ast)
        native_times.append(time.perf_counter() - start)
    native_avg = sum(native_times) / len(native_times)
    
    # Traced execution
    traced_times = []
    for _ in range(100):
        capture = TraceCapture()
        capture.start_capture("benchmark", input_args=[])
        start = time.perf_counter()
        result = eval_expr(ast)
        capture.record_output(result)
        traced_times.append(time.perf_counter() - start)
    traced_avg = sum(traced_times) / len(traced_times)
    
    overhead_pct = ((traced_avg - native_avg) / native_avg) * 100
    
    print(f"\nReplay Harness Benchmark:")
    print(f"  Native avg: {native_avg*1000:.4f}ms")
    print(f"  Traced avg: {traced_avg*1000:.4f}ms")
    print(f"  Overhead: {overhead_pct:.1f}%")
    print(f"  Status: {'PASS' if overhead_pct < 500 else 'FAIL'} (max: 500%)")
    
    # Determinism test: run same expression 10 times, check results match
    results = []
    for _ in range(10):
        results.append(eval_expr(parse_expr("2 + 3 + 4")))
    all_match = all(r == results[0] for r in results)
    print(f"  Determinism: {'PASS' if all_match else 'FAIL'}")
    
    return overhead_pct < 500 and all_match


def main():
    print("=" * 60)
    print("llm-native-lang Performance Benchmark Suite")
    print("=" * 60)
    
    results = []
    results.append(("LND Parse", benchmark_lnd_parse()))
    results.append(("LNC Execution", benchmark_lnc_execution()))
    results.append(("Replay Harness", benchmark_replay_harness()))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    print(f"Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
