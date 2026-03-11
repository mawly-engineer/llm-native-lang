"""Tests for abs() builtin function.

Covers:
- Positive integers
- Negative integers  
- Zero
- Positive floats
- Negative floats
- Error cases (unsupported types: strings, lists, bools, null, objects)
- Integration with runtime evaluation
"""

import unittest
from runtime.interpreter_runtime import eval_expr, EvalError


def make_span(start=0, end=10):
    """Helper to create span objects."""
    return {"start": start, "end": end}


class TestAbsBuiltin(unittest.TestCase):
    """Test abs() builtin with various inputs."""

    def test_abs_positive_int(self):
        """abs(5) returns 5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": 5}]
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_abs_negative_int(self):
        """abs(-5) returns 5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": -5}]
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_abs_zero(self):
        """abs(0) returns 0."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": 0}]
        }
        self.assertEqual(eval_expr(ast), 0)

    def test_abs_positive_float(self):
        """abs(3.14) returns 3.14."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": 3.14}]
        }
        self.assertEqual(eval_expr(ast), 3.14)

    def test_abs_negative_float(self):
        """abs(-3.14) returns 3.14."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": -3.14}]
        }
        self.assertEqual(eval_expr(ast), 3.14)

    def test_abs_large_positive_int(self):
        """abs(1000000) returns 1000000."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": 1000000}]
        }
        self.assertEqual(eval_expr(ast), 1000000)

    def test_abs_large_negative_int(self):
        """abs(-1000000) returns 1000000."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": -1000000}]
        }
        self.assertEqual(eval_expr(ast), 1000000)

    def test_abs_float_zero(self):
        """abs(0.0) returns 0.0."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": 0.0}]
        }
        self.assertEqual(eval_expr(ast), 0.0)

    def test_abs_string_error(self):
        """abs("hello") raises E_RT_ABS_UNSUPPORTED_TYPE."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "string", "span": make_span(), "value": "hello"}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_ABS_UNSUPPORTED_TYPE")
        self.assertIn("str", ctx.exception.message)

    def test_abs_list_error(self):
        """abs([1, 2, 3]) raises E_RT_ABS_UNSUPPORTED_TYPE."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": [
                    {"kind": "number", "span": make_span(), "value": 1},
                    {"kind": "number", "span": make_span(), "value": 2},
                    {"kind": "number", "span": make_span(), "value": 3}
                ]
            }]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_ABS_UNSUPPORTED_TYPE")
        self.assertIn("list", ctx.exception.message)

    def test_abs_bool_error(self):
        """abs(true) raises E_RT_ABS_UNSUPPORTED_TYPE."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "bool", "span": make_span(), "value": True}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_ABS_UNSUPPORTED_TYPE")
        self.assertIn("bool", ctx.exception.message)

    def test_abs_null_error(self):
        """abs(null) raises E_RT_ABS_UNSUPPORTED_TYPE."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "null", "span": make_span()}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_ABS_UNSUPPORTED_TYPE")

    def test_abs_object_error(self):
        """abs({a: 1}) raises E_RT_ABS_UNSUPPORTED_TYPE."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{
                "kind": "object",
                "span": make_span(),
                "entries": [{"key": "a", "value": {"kind": "number", "span": make_span(), "value": 1}}]
            }]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_ABS_UNSUPPORTED_TYPE")
        self.assertIn("dict", ctx.exception.message)

    def test_abs_on_variable(self):
        """abs works on variable containing int."""
        ast = {
            "kind": "let",
            "span": make_span(),
            "name": "x",
            "value": {"kind": "number", "span": make_span(), "value": -42},
            "body": {
                "kind": "call",
                "span": make_span(),
                "target": {"kind": "ident", "span": make_span(), "name": "abs"},
                "args": [{"kind": "ident", "span": make_span(), "name": "x"}]
            }
        }
        self.assertEqual(eval_expr(ast), 42)

    def test_abs_on_float_variable(self):
        """abs works on variable containing float."""
        ast = {
            "kind": "let",
            "span": make_span(),
            "name": "x",
            "value": {"kind": "number", "span": make_span(), "value": -2.5},
            "body": {
                "kind": "call",
                "span": make_span(),
                "target": {"kind": "ident", "span": make_span(), "name": "abs"},
                "args": [{"kind": "ident", "span": make_span(), "name": "x"}]
            }
        }
        self.assertEqual(eval_expr(ast), 2.5)

    def test_abs_nested_in_expression(self):
        """abs can be used in larger expressions."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{
                "kind": "concat_bin",
                "span": make_span(),
                "op": "-",
                "left": {"kind": "number", "span": make_span(), "value": 10},
                "right": {"kind": "number", "span": make_span(), "value": 25}
            }]
        }
        # abs(10 - 25) = abs(-15) = 15
        self.assertEqual(eval_expr(ast), 15)

    def test_abs_error_includes_location(self):
        """Error includes location information."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "string", "span": make_span(), "value": "bad"}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertIsNotNone(ctx.exception.location)
        self.assertEqual(ctx.exception.location.get("builtin"), "abs")


class TestAbsEdgeCases(unittest.TestCase):
    """Edge case tests for abs()."""

    def test_abs_small_positive_float(self):
        """abs works with small positive floats."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": 0.001}]
        }
        self.assertEqual(eval_expr(ast), 0.001)

    def test_abs_small_negative_float(self):
        """abs works with small negative floats."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": -0.001}]
        }
        self.assertEqual(eval_expr(ast), 0.001)

    def test_abs_very_large_int(self):
        """abs works with very large integers."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "abs"},
            "args": [{"kind": "number", "span": make_span(), "value": -999999999}]
        }
        self.assertEqual(eval_expr(ast), 999999999)


if __name__ == "__main__":
    unittest.main()
