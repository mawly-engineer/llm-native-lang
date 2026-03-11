"""Tests for the replay conformance harness."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from typing import Any, Dict

from runtime.replay_conformance import (
    ExecutionTrace,
    ReplayConformanceResult,
    TraceCaptureHook,
    capture_execution_trace,
    evaluate_batch_replay_conformance,
    evaluate_replay_conformance,
    serialize_trace_to_file,
    deserialize_trace_from_file,
)
from runtime.ast_contract import validate_ast


def _make_span(start_offset: int = 0, end_offset: int = 1) -> Dict[str, Any]:
    """Create a valid span object for AST nodes."""
    return {
        "start": start_offset,
        "end": end_offset,
    }


class ExecutionTraceTest(unittest.TestCase):
    """Tests for ExecutionTrace data class."""

    def test_trace_creation(self) -> None:
        trace = ExecutionTrace(
            program="let x = 1 in x",
            trace_ids=["n-000001:let", "n-000002:number"],
            final_result=1,
            fuel_used=2,
        )
        self.assertEqual(trace.program, "let x = 1 in x")
        self.assertEqual(trace.trace_ids, ["n-000001:let", "n-000002:number"])
        self.assertEqual(trace.final_result, 1)
        self.assertEqual(trace.fuel_used, 2)

    def test_trace_to_dict(self) -> None:
        trace = ExecutionTrace(
            program="test",
            trace_ids=["id1", "id2"],
            final_result=42,
            fuel_used=10,
            builtin_calls=[{"builtin": "abs", "args": [-5], "result": 5}],
        )
        d = trace.to_dict()
        self.assertEqual(d["program"], "test")
        self.assertEqual(d["final_result"], 42)
        self.assertEqual(d["fuel_used"], 10)
        self.assertEqual(len(d["builtin_calls"]), 1)

    def test_trace_to_json(self) -> None:
        trace = ExecutionTrace(
            program="let x = 1 in x",
            trace_ids=["n-000001:let"],
            final_result=1,
            fuel_used=2,
        )
        json_str = trace.to_json()
        # Should be valid JSON
        data = json.loads(json_str)
        self.assertEqual(data["program"], "let x = 1 in x")

    def test_trace_signature_deterministic(self) -> None:
        trace1 = ExecutionTrace(
            program="let x = 1 in x",
            trace_ids=["n-000001:let"],
            final_result=1,
            fuel_used=2,
        )
        trace2 = ExecutionTrace(
            program="let x = 1 in x",
            trace_ids=["n-000001:let"],
            final_result=1,
            fuel_used=2,
        )
        self.assertEqual(trace1.signature(), trace2.signature())

    def test_trace_signature_unique(self) -> None:
        trace1 = ExecutionTrace(
            program="let x = 1 in x",
            trace_ids=["n-000001:let"],
            final_result=1,
            fuel_used=2,
        )
        trace2 = ExecutionTrace(
            program="let x = 2 in x",
            trace_ids=["n-000001:let"],
            final_result=2,
            fuel_used=2,
        )
        self.assertNotEqual(trace1.signature(), trace2.signature())

    def test_serialize_value_nested(self) -> None:
        trace = ExecutionTrace(
            program="test",
            trace_ids=[],
            final_result={"a": [1, 2, {"b": 3}]},
            fuel_used=None,
        )
        d = trace.to_dict()
        self.assertEqual(d["final_result"]["a"][2]["b"], 3)


class TraceCaptureHookTest(unittest.TestCase):
    """Tests for TraceCaptureHook."""

    def test_record_call(self) -> None:
        hook = TraceCaptureHook()
        hook.record_call("abs", (-5,), 5)
        self.assertEqual(len(hook.builtin_calls), 1)
        self.assertEqual(hook.builtin_calls[0]["builtin"], "abs")

    def test_record_multiple_calls(self) -> None:
        hook = TraceCaptureHook()
        hook.record_call("min", ([1, 2, 3],), 1)
        hook.record_call("max", ([1, 2, 3],), 3)
        self.assertEqual(len(hook.builtin_calls), 2)


class ReplayConformanceTest(unittest.TestCase):
    """Tests for replay conformance evaluation."""

    def _create_simple_ast(self, value: int) -> Dict[str, Any]:
        """Create a simple AST node for testing."""
        return {
            "kind": "number",
            "value": value,
            "span": _make_span(),
        }

    def test_capture_execution_trace_basic(self) -> None:
        ast = self._create_simple_ast(42)
        trace = capture_execution_trace(ast)
        self.assertEqual(trace.final_result, 42)
        self.assertIsInstance(trace.trace_ids, list)
        self.assertTrue(len(trace.trace_ids) > 0)

    def test_capture_execution_trace_with_fuel(self) -> None:
        ast = self._create_simple_ast(42)
        trace = capture_execution_trace(ast, fuel_limit=100)
        self.assertIsNotNone(trace.fuel_used)

    def test_evaluate_replay_conformance_deterministic(self) -> None:
        ast = self._create_simple_ast(7)
        result = evaluate_replay_conformance(ast, repeats=4)
        self.assertTrue(result.conformance)
        self.assertEqual(len(result.signatures), 4)
        self.assertEqual(len(set(result.signatures)), 1)
        self.assertEqual(result.mismatch_indices, [])
        self.assertEqual(len(result.traces), 4)

    def test_evaluate_replay_conformance_requires_repeat_count(self) -> None:
        ast = self._create_simple_ast(1)
        with self.assertRaises(ValueError) as ctx:
            evaluate_replay_conformance(ast, repeats=1)
        self.assertIn("repeats must be an integer >= 2", str(ctx.exception))

    def test_evaluate_batch_replay_conformance(self) -> None:
        asts = [
            self._create_simple_ast(1),
            self._create_simple_ast(2),
            self._create_simple_ast(3),
        ]
        summary = evaluate_batch_replay_conformance(asts, repeats=3)
        self.assertTrue(summary["conformance"])
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["passed"], 3)
        self.assertEqual(summary["failed"], 0)

    def test_evaluate_batch_with_non_deterministic_detection(self) -> None:
        # All deterministic programs should pass
        asts = [
            self._create_simple_ast(i) for i in range(5)
        ]
        summary = evaluate_batch_replay_conformance(asts, repeats=3)
        self.assertEqual(len(summary["non_deterministic_programs"]), 0)

    def test_replay_conformance_result_to_dict(self) -> None:
        ast = self._create_simple_ast(42)
        result = evaluate_replay_conformance(ast, repeats=3)
        d = result.to_dict()
        self.assertIn("source", d)
        self.assertIn("signatures", d)
        self.assertIn("traces", d)
        self.assertEqual(d["repeats"], 3)


class TraceSerializationTest(unittest.TestCase):
    """Tests for trace serialization/deserialization."""

    def test_serialize_and_deserialize_trace(self) -> None:
        trace = ExecutionTrace(
            program="let x = 1 in x",
            trace_ids=["n-000001:let", "n-000002:number"],
            final_result={"value": 1, "type": "int"},
            fuel_used=5,
            builtin_calls=[{"builtin": "abs", "args": [-5], "result": 5}],
        )
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        
        try:
            serialize_trace_to_file(trace, filepath)
            loaded = deserialize_trace_from_file(filepath)
            
            self.assertEqual(loaded.program, trace.program)
            self.assertEqual(loaded.trace_ids, trace.trace_ids)
            self.assertEqual(loaded.fuel_used, trace.fuel_used)
        finally:
            os.unlink(filepath)

    def test_serialize_to_file_creates_valid_json(self) -> None:
        trace = ExecutionTrace(
            program="test",
            trace_ids=["id1"],
            final_result=42,
            fuel_used=None,
        )
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name
        
        try:
            serialize_trace_to_file(trace, filepath)
            with open(filepath) as f:
                data = json.load(f)
            self.assertEqual(data["program"], "test")
        finally:
            os.unlink(filepath)


class IntegrationTest(unittest.TestCase):
    """Integration tests for the complete replay conformance system."""

    def test_complex_program_trace(self) -> None:
        """Test trace capture for a more complex program structure."""
        ast = {
            "kind": "list",
            "items": [
                {"kind": "number", "value": 1, "span": _make_span(0, 1)},
                {"kind": "number", "value": 2, "span": _make_span(3, 4)},
                {"kind": "number", "value": 3, "span": _make_span(6, 7)},
            ],
            "span": _make_span(0, 1, 1, 8, 1, 9),
        }
        
        trace = capture_execution_trace(ast)
        self.assertEqual(trace.final_result, [1, 2, 3])
        self.assertTrue(len(trace.trace_ids) >= 4)  # list + 3 numbers

    def test_nested_structure_trace(self) -> None:
        """Test trace capture for nested structures."""
        ast = {
            "kind": "object",
            "entries": [
                {"key": "a", "value": {"kind": "number", "value": 1, "span": _make_span(5, 6)}},
                {"key": "b", "value": {"kind": "number", "value": 2, "span": _make_span(15, 16)}},
            ],
            "span": _make_span(0, 18),
        }
        
        trace = capture_execution_trace(ast)
        self.assertEqual(trace.final_result, {"a": 1, "b": 2})


if __name__ == "__main__":
    unittest.main()
