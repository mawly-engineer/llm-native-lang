"""Tests for max() builtin function.

Covers:
- Two argument max (a, b)
- Collection max with list
- Empty collection error
- Type mismatch error
- Integration with runtime evaluation
"""

import unittest
from runtime.interpreter_runtime import eval_expr, EvalError


def make_span(start=0, end=10):
    """Helper to create span objects."""
    return {"start": start, "end": end}


class TestMaxBuiltin(unittest.TestCase):
    """Test max() builtin with various inputs."""

    def test_max_two_ints(self):
        """max(5, 3) returns 5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 5},
                {"kind": "number", "span": make_span(), "value": 3}
            ]
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_max_two_floats(self):
        """max(3.5, 2.5) returns 3.5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 3.5},
                {"kind": "number", "span": make_span(), "value": 2.5}
            ]
        }
        self.assertEqual(eval_expr(ast), 3.5)

    def test_max_int_and_float(self):
        """max(3, 2.5) returns 3."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 3},
                {"kind": "number", "span": make_span(), "value": 2.5}
            ]
        }
        self.assertEqual(eval_expr(ast), 3)

    def test_max_three_args(self):
        """max(7, 3, 5) returns 7."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 7},
                {"kind": "number", "span": make_span(), "value": 3},
                {"kind": "number", "span": make_span(), "value": 5}
            ]
        }
        self.assertEqual(eval_expr(ast), 7)

    def test_max_collection_list(self):
        """max([3, 1, 4, 1, 5]) returns 5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
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
        self.assertEqual(eval_expr(ast), 5)

    def test_max_collection_float_list(self):
        """max([3.5, 2.5, 4.5]) returns 4.5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
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
        self.assertEqual(eval_expr(ast), 4.5)

    def test_max_empty_collection_error(self):
        """max([]) raises E_RT_MAX_EMPTY_COLLECTION."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": []
            }]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_MAX_EMPTY_COLLECTION")

    def test_max_no_args_error(self):
        """max() raises E_RT_MAX_EMPTY_COLLECTION."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": []
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_MAX_EMPTY_COLLECTION")

    def test_max_string_type_error(self):
        """max("a", "b") raises E_RT_MAX_TYPE_MISMATCH."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "string", "span": make_span(), "value": "a"},
                {"kind": "string", "span": make_span(), "value": "b"}
            ]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_MAX_TYPE_MISMATCH")

    def test_max_collection_with_string_error(self):
        """max([1, "a", 3]) raises E_RT_MAX_TYPE_MISMATCH."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
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
        self.assertEqual(ctx.exception.code, "E_RT_MAX_TYPE_MISMATCH")

    def test_max_bool_type_error(self):
        """max(true, false) raises E_RT_MAX_TYPE_MISMATCH."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "bool", "span": make_span(), "value": True},
                {"kind": "bool", "span": make_span(), "value": False}
            ]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_MAX_TYPE_MISMATCH")

    def test_max_negative_numbers(self):
        """max(-5, -3, -10) returns -3."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "number", "span": make_span(), "value": -5},
                {"kind": "number", "span": make_span(), "value": -3},
                {"kind": "number", "span": make_span(), "value": -10}
            ]
        }
        self.assertEqual(eval_expr(ast), -3)

    def test_max_single_element_list(self):
        """max([42]) returns 42."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": [
                    {"kind": "number", "span": make_span(), "value": 42}
                ]
            }]
        }
        self.assertEqual(eval_expr(ast), 42)

    def test_max_with_variables(self):
        """max works on variables."""
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
                    "target": {"kind": "ident", "span": make_span(), "name": "max"},
                    "args": [
                        {"kind": "ident", "span": make_span(), "name": "a"},
                        {"kind": "ident", "span": make_span(), "name": "b"}
                    ]
                }
            }
        }
        self.assertEqual(eval_expr(ast), 10)

    def test_max_with_range_result(self):
        """max(range(5)) returns 4."""
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
                "target": {"kind": "ident", "span": make_span(), "name": "max"},
                "args": [{"kind": "ident", "span": make_span(), "name": "r"}]
            }
        }
        self.assertEqual(eval_expr(ast), 4)

    def test_max_error_includes_location(self):
        """Error includes location information."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "string", "span": make_span(), "value": "a"},
                {"kind": "string", "span": make_span(), "value": "b"}
            ]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertIsNotNone(ctx.exception.location)
        self.assertEqual(ctx.exception.location.get("builtin"), "max")


class TestMaxEdgeCases(unittest.TestCase):
    """Edge case tests for max()."""

    def test_max_same_values(self):
        """max(5, 5) returns 5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 5},
                {"kind": "number", "span": make_span(), "value": 5}
            ]
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_max_zero_values(self):
        """max(0, 1) returns 1."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 0},
                {"kind": "number", "span": make_span(), "value": 1}
            ]
        }
        self.assertEqual(eval_expr(ast), 1)

    def test_max_with_large_numbers(self):
        """max handles large numbers."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "max"},
            "args": [
                {"kind": "number", "span": make_span(), "value": 1000000},
                {"kind": "number", "span": make_span(), "value": 999999}
            ]
        }
        self.assertEqual(eval_expr(ast), 1000000)


if __name__ == "__main__":
    unittest.main()
