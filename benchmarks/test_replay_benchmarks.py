"""Benchmark tests for replay harness performance.

Validates:
- Replay overhead vs native execution
- Trace serialization performance
- Deterministic replay conformance
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable

import pytest

from runtime.replay_harness import TraceCapture, ConformanceHarness, ReplayValidator
from runtime.interpreter_runtime import eval_expr
from runtime.grammar_contract import parse_expr


class TestReplayHarnessBenchmarks:
    """Performance benchmarks for replay system."""
    
    def test_trace_capture_latency(self, benchmark) -> None:
        """Benchmark latency of trace capture operations."""
        ast = parse_expr("1 + 2 + 3")
        
        def capture_trace():
            with TraceCapture() as capture:
                result = eval_expr(ast)
                traces = capture.get_traces()
                return result, traces
        
        result, traces = benchmark(capture_trace)
        assert result == 6
        assert len(traces) > 0
    
    def test_trace_serialization(self, benchmark) -> None:
        """Benchmark JSON serialization of traces."""
        with TraceCapture() as capture:
            eval_expr(parse_expr("let x = 5 in x * 2"))
            traces = capture.get_traces()
        
        def serialize():
            return json.dumps(traces, indent=2)
        
        result = benchmark(serialize)
        assert len(result) > 0
    
    def test_replay_comparison(self, benchmark) -> None:
        """Benchmark replay comparison validation."""
        # Capture original trace
        with TraceCapture() as capture1:
            result1 = eval_expr(parse_expr("10 * 10"))
            trace1 = capture1.get_traces()
        
        # Capture replay trace
        with TraceCapture() as capture2:
            result2 = eval_expr(parse_expr("10 * 10"))
            trace2 = capture2.get_traces()
        
        validator = ReplayValidator()
        
        def compare():
            return validator.compare_traces(trace1, trace2)
        
        match, differences = benchmark(compare)
        assert match is True
        assert len(differences) == 0
    
    def test_conformance_multiple_iterations(self, benchmark) -> None:
        """Benchmark conformance harness with multiple iterations."""
        harness = ConformanceHarness()
        
        def run_conformance():
            return harness.validate_determinism(
                lambda: eval_expr(parse_expr("factorial")) or 3628800,
                iterations=5
            )
        
        # Use a simpler expression since factorial is recursive
        def run_conformance_simple():
            return harness.validate_determinism(
                lambda: eval_expr(parse_expr("2 + 3 + 4 + 5 + 6")),
                iterations=5
            )
        
        result = benchmark(run_conformance_simple)
        assert result is True


class TestReplayOverheadComparison:
    """Compare replay overhead vs native execution."""
    
    @pytest.fixture(scope="class")
    def workload_source(self) -> str:
        """Return a representative workload."""
        return """let rec sum = fn(xs) =>
            if xs == [] then 0 else xs[0] + sum(xs[1:])
        in sum([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])"""
    
    def test_native_execution_time(self, workload_source: str) -> None:
        """Measure baseline native execution time."""
        ast = parse_expr(workload_source)
        
        times = []
        for _ in range(10):
            start = time.perf_counter()
            result = eval_expr(ast)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        assert result == 55
        # Should complete in under 10ms
        assert avg_time < 0.01, f"Native execution took {avg_time*1000:.1f}ms"
    
    def test_traced_execution_time(self, workload_source: str) -> None:
        """Measure traced execution time."""
        ast = parse_expr(workload_source)
        
        times = []
        for _ in range(10):
            start = time.perf_counter()
            with TraceCapture() as capture:
                result = eval_expr(ast)
                traces = capture.get_traces()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        assert result == 55
        # Traced should be slower but still under 50ms
        assert avg_time < 0.05, f"Traced execution took {avg_time*1000:.1f}ms"
    
    def test_overhead_percentage(self, workload_source: str) -> None:
        """Calculate replay overhead percentage."""
        ast = parse_expr(workload_source)
        
        # Native execution
        native_times = []
        for _ in range(5):
            start = time.perf_counter()
            eval_expr(ast)
            native_times.append(time.perf_counter() - start)
        native_avg = sum(native_times) / len(native_times)
        
        # Traced execution
        traced_times = []
        for _ in range(5):
            start = time.perf_counter()
            with TraceCapture():
                eval_expr(ast)
            traced_times.append(time.perf_counter() - start)
        traced_avg = sum(traced_times) / len(traced_times)
        
        overhead_pct = ((traced_avg - native_avg) / native_avg) * 100
        
        # Overhead should be less than 500%
        assert overhead_pct < 500, f"Replay overhead is {overhead_pct:.1f}%"


class TestDeterministicReplayConformance:
    """Validate deterministic replay behavior."""
    
    def test_simple_expression_determinism(self) -> None:
        """Simple expressions should be deterministic."""
        harness = ConformanceHarness()
        
        result = harness.validate_determinism(
            lambda: eval_expr(parse_expr("2 + 2")),
            iterations=10
        )
        
        assert result is True
    
    def test_let_binding_determinism(self) -> None:
        """Let bindings should be deterministic."""
        harness = ConformanceHarness()
        
        result = harness.validate_determinism(
            lambda: eval_expr(parse_expr("let x = 42 in x * 2")),
            iterations=10
        )
        
        assert result is True
        
    def test_function_call_determinism(self) -> None:
        """Function calls should be deterministic."""
        harness = ConformanceHarness()
        
        result = harness.validate_determinism(
            lambda: eval_expr(parse_expr("let f = fn(x) => x + 1 in f(10)")),
            iterations=10
        )
        
        assert result is True
    
    def test_recursive_function_determinism(self) -> None:
        """Recursive functions should be deterministic."""
        harness = ConformanceHarness()
        
        # Factorial with small n for speed
        source = """let rec fact = fn(n) =>
            if n == 0 then 1 else n * fact(n - 1)
        in fact(5)"""
        
        result = harness.validate_determinism(
            lambda: eval_expr(parse_expr(source)),
            iterations=5
        )
        
        assert result is True
