"""Tests for the range builtin function."""

import unittest
from runtime.interpreter_runtime import eval_expr, EvalError


def make_span(start=0, end=10):
    """Helper to create span objects."""
    return {"start": start, "end": end}


class RangeBuiltinTests(unittest.TestCase):
    """Test cases for range builtin function."""

    def test_range_single_arg(self):
        """range(stop) generates [0, 1, ..., stop-1]"""
        # AST for: range(5)
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [{"kind": "number", "span": make_span(), "value": 5}]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [0, 1, 2, 3, 4])

    def test_range_single_arg_zero(self):
        """range(0) returns empty list"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [{"kind": "number", "span": make_span(), "value": 0}]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [])

    def test_range_single_arg_negative(self):
        """range(-3) returns empty list"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [{"kind": "number", "span": make_span(), "value": -3}]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [])

    def test_range_two_args(self):
        """range(start, stop) generates [start, ..., stop-1]"""
        # AST for: range(1, 5)
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 1},
                {"kind": "number", "span": make_span(), "value": 5}
            ]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [1, 2, 3, 4])

    def test_range_two_args_start_equals_stop(self):
        """range(5, 5) returns empty list"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 5},
                {"kind": "number", "span": make_span(), "value": 5}
            ]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [])

    def test_range_two_args_start_greater_than_stop(self):
        """range(10, 5) returns empty list"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 10},
                {"kind": "number", "span": make_span(), "value": 5}
            ]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [])

    def test_range_three_args_positive_step(self):
        """range(start, stop, step) with positive step"""
        # AST for: range(0, 10, 2)
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 0},
                {"kind": "number", "span": make_span(), "value": 10},
                {"kind": "number", "span": make_span(), "value": 2}
            ]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [0, 2, 4, 6, 8])

    def test_range_three_args_negative_step(self):
        """range(start, stop, step) with negative step"""
        # AST for: range(10, 0, -2)
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 10},
                {"kind": "number", "span": make_span(), "value": 0},
                {"kind": "number", "span": make_span(), "value": -2}
            ]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [10, 8, 6, 4, 2])

    def test_range_three_args_negative_step_reverse(self):
        """range(5, 1, -1) generates [5, 4, 3, 2]"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 5},
                {"kind": "number", "span": make_span(), "value": 1},
                {"kind": "number", "span": make_span(), "value": -1}
            ]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [5, 4, 3, 2])

    def test_range_step_zero_raises_error(self):
        """range with step=0 raises E_RT_RANGE_STEP_ZERO"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 0},
                {"kind": "number", "span": make_span(), "value": 10},
                {"kind": "number", "span": make_span(), "value": 0}
            ]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_RANGE_STEP_ZERO")

    def test_range_type_error_string_arg(self):
        """range with string arg raises TypeError (from Python)"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [{"kind": "string", "span": make_span(), "value": "hello"}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_HOST_CALL_ARITY")

    def test_range_type_error_bool_arg(self):
        """range with bool arg is treated as int (True=1, False=0)"""
        # In Python, bool is subclass of int, so True=1, False=0
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [{"kind": "bool", "span": make_span(), "value": True}]
        }
        # This should fail because we check isinstance(val, int) and not isinstance(val, bool)
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_HOST_CALL_ARITY")

    def test_range_large_range(self):
        """range can generate large lists"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [{"kind": "number", "span": make_span(), "value": 100}]
        }
        result = eval_expr(ast)
        self.assertEqual(len(result), 100)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[99], 99)

    def test_range_negative_numbers(self):
        """range with negative start/stop"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [
                {"kind": "number", "span": make_span(), "value": -5},
                {"kind": "number", "span": make_span(), "value": 5}
            ]
        }
        result = eval_expr(ast)
        self.assertEqual(result, [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4])

    def test_range_no_args(self):
        """range() with no args raises TypeError"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": []
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_HOST_CALL_ARITY")

    def test_range_too_many_args(self):
        """range with 4+ args raises TypeError"""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "range"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 0},
                {"kind": "number", "span": make_span(), "value": 10},
                {"kind": "number", "span": make_span(), "value": 1},
                {"kind": "number", "span": make_span(), "value": 5}
            ]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_HOST_CALL_ARITY")


if __name__ == "__main__":
    unittest.main()
