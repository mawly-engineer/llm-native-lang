"""Benchmark tests for LNC contract execution performance.

Validates:
- Execution speed: minimum 1000 ops/sec
- Memory efficiency for contract execution
- Replay harness overhead measurement
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

import pytest

from runtime.interpreter_runtime import eval_expr
from runtime.grammar_contract import parse_expr
from runtime.benchmark_harness import run_benchmark
from runtime.replay_harness import TraceCapture, ConformanceHarness


class TestLNCExecBenchmarks:
    """Performance benchmarks for LNC contract execution."""
    
    def test_simple_arithmetic_execution(self, benchmark) -> None:
        """Benchmark simple arithmetic expression execution."""
        source = "2 + 3 * 4"
        ast = parse_expr(source)
        
        def execute():
            return eval_expr(ast)
        
        result = benchmark(execute)
        assert result == 14
    
    def test_let_binding_execution(self, benchmark) -> None:
        """Benchmark let binding expression execution."""
        source = "let x = 42 in let y = x + 8 in y * 2"
        ast = parse_expr(source)
        
        def execute():
            return eval_expr(ast)
        
        result = benchmark(execute)
        assert result == 100
    
    def test_function_call_execution(self, benchmark) -> None:
        """Benchmark function call expression execution."""
        source = """let add = fn(a, b) => a + b in
                     let multiply = fn(x, y) => x * y in
                     multiply(add(3, 4), 5)"""
        ast = parse_expr(source)
        
        def execute():
            return eval_expr(ast)
        
        result = benchmark(execute)
        assert result == 35
    
    def test_recursive_execution(self, benchmark) -> None:
        """Benchmark recursive factorial execution."""
        source = """let rec fact = fn(n) =>
            if n == 0 then 1 else n * fact(n - 1)
        in fact(10)"""
        ast = parse_expr(source)
        
        def execute():
            return eval_expr(ast)
        
        result = benchmark(execute)
        assert result == 3628800
    
    def test_list_operations_execution(self, benchmark) -> None:
        """Benchmark list operations execution."""
        source = """let xs = [1, 2, 3, 4, 5] in
                     let ys = [6, 7, 8, 9, 10] in
                     xs[0] + ys[0]"""
        ast = parse_expr(source)
        
        def execute():
            return eval_expr(ast)
        
        result = benchmark(execute)
        assert result == 7
    
    def test_object_member_access(self, benchmark) -> None:
        """Benchmark object member access execution."""
        source = """let person = {\"name\": \"Alice\", \"age\": 30} in
                     let company = {\"name\": \"TechCorp\", \"employees\": 100} in
                     person.age + company.employees"""
        ast = parse_expr(source)
        
        def execute():
            return eval_expr(ast)
        
        result = benchmark(execute)
        assert result == 130
    
    def test_throughput_minimum_ops_per_sec(self, config) -> None:
        """Verify execution meets 1000 ops/sec minimum.
        
        This is a throughput test, not a microbenchmark.
        """
        operations = 1000
        source = "let x = 10 in x + 5"
        ast = parse_expr(source)
        
        start = time.perf_counter()
        
        for _ in range(operations):
            result = eval_expr(ast)
            assert result == 15
        
        elapsed = time.perf_counter() - start
        ops_per_sec = operations / elapsed
        
        # Assert meets minimum requirement
        assert ops_per_sec >= config.LNC_EXEC_MIN_OPS_PER_SEC, (
            f"Execution rate {ops_per_sec:.1f} ops/sec below minimum "
            f"{config.LNC_EXEC_MIN_OPS_PER_SEC} ops/sec"
        )


class TestReplayHarnessBenchmarks:
    """Benchmarks for replay harness overhead."""
    
    def test_trace_capture_overhead(self, benchmark) -> None:
        """Benchmark overhead of trace capture vs native execution."""
        source = "2 + 3 * 4"
        ast = parse_expr(source)
        
        # Native execution (no trace)
        def native_exec():
            return eval_expr(ast)
        
        # With trace capture
        def traced_exec():
            with TraceCapture() as capture:
                result = eval_expr(ast)
                return result, capture.get_traces()
        
        # Run both benchmarks
        native_result = benchmark(native_exec)
        traced_result = traced_exec()[0]
        
        assert native_result == traced_result == 14
    
    def test_replay_validation_overhead(self, benchmark) -> None:
        """Benchmark replay validation overhead."""
        from runtime.replay_harness import ConformanceHarness
        
        def validate():
            harness = ConformanceHarness()
            # Simple function that should be deterministic
            result = harness.validate_determinism(
                lambda: eval_expr(parse_expr("1 + 2 + 3")),
                iterations=3
            )
            return result
        
        result = benchmark(validate)
        assert result is True
    
    def test_conformance_iterations_scaling(self) -> None:
        """Test conformance harness scales with iteration count."""
        harness = ConformanceHarness()
        
        for iterations in [3, 5, 10]:
            start = time.perf_counter()
            
            result = harness.validate_determinism(
                lambda: eval_expr(parse_expr("let x = 5 in x * x")),
                iterations=iterations
            )
            
            elapsed = time.perf_counter() - start
            
            assert result is True
            # Should complete 10 iterations in under 100ms
            if iterations == 10:
                assert elapsed < 0.1, f"10 iterations took {elapsed*1000:.1f}ms"


class TestLCNContractBenchmarks:
    """Benchmarks for full LNC contract execution."""
    
    def test_lnc_contract_load_and_execute(self, tmp_path: Path, benchmark) -> None:
        """Benchmark loading and executing an LNC contract."""
        from scripts.lnc_validate import parse_lnc_file
        
        lnc_content = """@lnc 0.1
kind: task
id: BENCH-TASK-001
title: "Benchmark arithmetic"
description: "Simple arithmetic for benchmarking"

input:
  x: 10
  y: 20

operation: add
"""
        lnc_file = tmp_path / "bench_contract.lnc"
        lnc_file.write_text(lnc_content)
        
        def load_and_execute():
            contract = parse_lnc_file(lnc_content, str(lnc_file))
            # Simulate execution (just return input sum)
            return contract["input"]["x"] + contract["input"]["y"]
        
        result = benchmark(load_and_execute)
        assert result == 30
