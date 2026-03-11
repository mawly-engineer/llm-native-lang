"""Tests for min() builtin function.

Covers:
- Two argument min (a, b)
- Collection min with list
- Empty collection error
- Type mismatch error
- Integration with runtime evaluation
"""

import unittest
from runtime.interpreter_runtime import eval_expr, EvalError


def make_span(start=0, end=10):
    """Helper to create span objects."""
    return {"start": start, "end": end}


class TestMinBuiltin(unittest.TestCase):
    """Test min() builtin with various inputs."""

    def test_min_two_ints(self):
        """min(5, 3) returns 3."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 5},
                {"kind": "number", "span": make_span(), "value": 3}
            ]
        }
        self.assertEqual(eval_expr(ast), 3)

    def test_min_two_floats(self):
        """min(3.5, 2.5) returns 2.5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 3.5},
                {"kind": "number", "span": make_span(), "value": 2.5}
            ]
        }
        self.assertEqual(eval_expr(ast), 2.5)

    def test_min_int_and_float(self):
        """min(3, 2.5) returns 2.5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 3},
                {"kind": "number", "span": make_span(), "value": 2.5}
            ]
        }
        self.assertEqual(eval_expr(ast), 2.5)

    def test_min_three_args(self):
        """min(7, 3, 5) returns 3."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 7},
                {"kind": "number", "span": make_span(), "value": 3},
                {"kind": "number", "span": make_span(), "value": 5}
            ]
        }
        self.assertEqual(eval_expr(ast), 3)

    def test_min_collection_list(self):
        """min([3, 1, 4, 1, 5]) returns 1."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": [
                    {"kind": "number", "span": make_span(), "value": 3},
                    {"kind": "number", "span": make_span(), "value": 1},
                    {"kind": "number", "span": make_span(), "value": 4},
                    {"kind": "number", "span": make_span(), "value": 1},
                    {"kind": "number", "span": make_span(), "value": 5}
                ]
            }]
        }
        self.assertEqual(eval_expr(ast), 1)

    def test_min_collection_float_list(self):
        """min([3.5, 2.5, 4.5]) returns 2.5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": [
                    {"kind": "number", "span": make_span(), "value": 3.5},
                    {"kind": "number", "span": make_span(), "value": 2.5},
                    {"kind": "number", "span": make_span(), "value": 4.5}
                ]
            }]
        }
        self.assertEqual(eval_expr(ast), 2.5)

    def test_min_empty_collection_error(self):
        """min([]) raises E_RT_MIN_EMPTY_COLLECTION."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": []
            }]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_MIN_EMPTY_COLLECTION")

    def test_min_no_args_error(self):
        """min() raises E_RT_MIN_EMPTY_COLLECTION."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": []
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_MIN_EMPTY_COLLECTION")

    def test_min_string_type_error(self):
        """min("a", "b") raises E_RT_MIN_TYPE_MISMATCH."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "string", "span": make_span(), "value": "a"},
                {"kind": "string", "span": make_span(), "value": "b"}
            ]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_MIN_TYPE_MISMATCH")

    def test_min_collection_with_string_error(self):
        """min([1, "a", 3]) raises E_RT_MIN_TYPE_MISMATCH."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": [
                    {"kind": "number", "span": make_span(), "value": 1},
                    {"kind": "string", "span": make_span(), "value": "a"},
                    {"kind": "number", "span": make_span(), "value": 3}
                ]
            }]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_MIN_TYPE_MISMATCH")

    def test_min_bool_type_error(self):
        """min(true, false) raises E_RT_MIN_TYPE_MISMATCH."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "bool", "span": make_span(), "value": True},
                {"kind": "bool", "span": make_span(), "value": False}
            ]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_MIN_TYPE_MISMATCH")

    def test_min_negative_numbers(self):
        """min(-5, -3, -10) returns -10."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "number", "span": make_span(), "value": -5},
                {"kind": "number", "span": make_span(), "value": -3},
                {"kind": "number", "span": make_span(), "value": -10}
            ]
        }
        self.assertEqual(eval_expr(ast), -10)

    def test_min_single_element_list(self):
        """min([42]) returns 42."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": [
                    {"kind": "number", "span": make_span(), "value": 42}
                ]
            }]
        }
        self.assertEqual(eval_expr(ast), 42)

    def test_min_with_variables(self):
        """min works on variables."""
        ast = {
            "kind": "let",
            "span": make_span(),
            "name": "a",
            "value": {"kind": "number", "span": make_span(), "value": 10},
            "body": {
                "kind": "let",
                "span": make_span(),
                "name": "b",
                "value": {"kind": "number", "span": make_span(), "value": 5},
                "body": {
                    "kind": "call",
                    "span": make_span(),
                    "target": {"kind": "ident", "span": make_span(), "name": "min"},
                    "args": [
                        {"kind": "ident", "span": make_span(), "name": "a"},
                        {"kind": "ident", "span": make_span(), "name": "b"}
                    ]
                }
            }
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_min_with_range_result(self):
        """min(range(5)) returns 0."""
        ast = {
            "kind": "let",
            "span": make_span(),
            "name": "r",
            "value": {
                "kind": "call",
                "span": make_span(),
                "target": {"kind": "ident", "span": make_span(), "name": "range"},
                "args": [{"kind": "number", "span": make_span(), "value": 5}]
            },
            "body": {
                "kind": "call",
                "span": make_span(),
                "target": {"kind": "ident", "span": make_span(), "name": "min"},
                "args": [{"kind": "ident", "span": make_span(), "name": "r"}]
            }
        }
        self.assertEqual(eval_expr(ast), 0)

    def test_min_error_includes_location(self):
        """Error includes location information."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "string", "span": make_span(), "value": "a"},
                {"kind": "string", "span": make_span(), "value": "b"}
            ]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertIsNotNone(ctx.exception.location)
        self.assertEqual(ctx.exception.location.get("builtin"), "min")


class TestMinEdgeCases(unittest.TestCase):
    """Edge case tests for min()."""

    def test_min_same_values(self):
        """min(5, 5) returns 5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 5},
                {"kind": "number", "span": make_span(), "value": 5}
            ]
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_min_zero_values(self):
        """min(0, 1) returns 0."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 0},
                {"kind": "number", "span": make_span(), "value": 1}
            ]
        }
        self.assertEqual(eval_expr(ast), 0)

    def test_min_with_large_numbers(self):
        """min handles large numbers."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "min"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 1000000},
                {"kind": "number", "span": make_span(), "value": 999999}
            ]
        }
        self.assertEqual(eval_expr(ast), 999999)


if __name__ == "__main__":
    unittest.main()
