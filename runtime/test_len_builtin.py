"""Tests for len() builtin function.

Covers:
- String length (empty, single char, multi-char, unicode)
- List length (empty, single element, multiple elements)
- Error cases (unsupported types)
- Integration with runtime evaluation
"""

import unittest
from runtime.interpreter_runtime import eval_expr, EvalError


def make_span(start=0, end=10):
    """Helper to create span objects."""
    return {"start": start, "end": end}


class TestLenBuiltin(unittest.TestCase):
    """Test len() builtin with various inputs."""

    def test_len_empty_string(self):
        """len("") returns 0."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "string", "span": make_span(), "value": ""}]
        }
        self.assertEqual(eval_expr(ast), 0)

    def test_len_single_char_string(self):
        """len("a") returns 1."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "string", "span": make_span(), "value": "a"}]
        }
        self.assertEqual(eval_expr(ast), 1)

    def test_len_multi_char_string(self):
        """len("hello") returns 5."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "string", "span": make_span(), "value": "hello"}]
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_len_unicode_string(self):
        """len("héllo") returns 5 (character count, not byte count)."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "string", "span": make_span(), "value": "héllo"}]
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_len_empty_list(self):
        """len([]) returns 0."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "list", "span": make_span(), "items": []}]
        }
        self.assertEqual(eval_expr(ast), 0)

    def test_len_single_element_list(self):
        """len([42]) returns 1."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": [{"kind": "number", "span": make_span(), "value": 42}]
            }]
        }
        self.assertEqual(eval_expr(ast), 1)

    def test_len_multiple_element_list(self):
        """len([1, 2, 3]) returns 3."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
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
        self.assertEqual(eval_expr(ast), 3)

    def test_len_nested_list(self):
        """len([[1, 2], [3, 4]]) returns 2."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": [
                    {"kind": "list", "span": make_span(), "items": [
                        {"kind": "number", "span": make_span(), "value": 1},
                        {"kind": "number", "span": make_span(), "value": 2}
                    ]},
                    {"kind": "list", "span": make_span(), "items": [
                        {"kind": "number", "span": make_span(), "value": 3},
                        {"kind": "number", "span": make_span(), "value": 4}
                    ]}
                ]
            }]
        }
        self.assertEqual(eval_expr(ast), 2)

    def test_len_integer_error(self):
        """len(42) raises E_RT_LEN_UNSUPPORTED_TYPE."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "number", "span": make_span(), "value": 42}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_LEN_UNSUPPORTED_TYPE")
        self.assertIn("int", ctx.exception.message)

    def test_len_boolean_error(self):
        """len(true) raises E_RT_LEN_UNSUPPORTED_TYPE."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "bool", "span": make_span(), "value": True}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_LEN_UNSUPPORTED_TYPE")
        self.assertIn("bool", ctx.exception.message)

    def test_len_null_error(self):
        """len(null) raises E_RT_LEN_UNSUPPORTED_TYPE."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "null", "span": make_span()}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_LEN_UNSUPPORTED_TYPE")

    def test_len_object_error(self):
        """len({a: 1}) raises E_RT_LEN_UNSUPPORTED_TYPE."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{
                "kind": "object",
                "span": make_span(),
                "entries": [{"key": "a", "value": {"kind": "number", "span": make_span(), "value": 1}}]
            }]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, "E_RT_LEN_UNSUPPORTED_TYPE")
        self.assertIn("dict", ctx.exception.message)

    def test_len_on_variable(self):
        """len works on variable containing list."""
        ast = {
            "kind": "let",
            "span": make_span(),
            "name": "my_list",
            "value": {
                "kind": "list",
                "span": make_span(),
                "items": [
                    {"kind": "number", "span": make_span(), "value": 10},
                    {"kind": "number", "span": make_span(), "value": 20}
                ]
            },
            "body": {
                "kind": "call",
                "span": make_span(),
                "target": {"kind": "ident", "span": make_span(), "name": "len"},
                "args": [{"kind": "ident", "span": make_span(), "name": "my_list"}]
            }
        }
        self.assertEqual(eval_expr(ast), 2)

    def test_len_on_string_variable(self):
        """len works on variable containing string."""
        ast = {
            "kind": "let",
            "span": make_span(),
            "name": "my_str",
            "value": {"kind": "string", "span": make_span(), "value": "world"},
            "body": {
                "kind": "call",
                "span": make_span(),
                "target": {"kind": "ident", "span": make_span(), "name": "len"},
                "args": [{"kind": "ident", "span": make_span(), "name": "my_str"}]
            }
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_len_with_range_result(self):
        """len(range(5)) returns 5."""
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
                "target": {"kind": "ident", "span": make_span(), "name": "len"},
                "args": [{"kind": "ident", "span": make_span(), "name": "r"}]
            }
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_len_error_includes_location(self):
        """Error includes location information."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "number", "span": make_span(), "value": 42}]
        }
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertIsNotNone(ctx.exception.location)
        self.assertEqual(ctx.exception.location.get("builtin"), "len")


class TestLenEdgeCases(unittest.TestCase):
    """Edge case tests for len()."""

    def test_len_whitespace_string(self):
        """len counts whitespace characters."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "string", "span": make_span(), "value": "  \t\n  "}]
        }
        self.assertEqual(eval_expr(ast), 6)

    def test_len_string_with_special_chars(self):
        """len counts special characters."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{"kind": "string", "span": make_span(), "value": "!@#$%"}]
        }
        self.assertEqual(eval_expr(ast), 5)

    def test_len_mixed_type_list(self):
        """len works on lists with mixed types."""
        ast = {
            "kind": "call",
            "span": make_span(),
            "target": {"kind": "ident", "span": make_span(), "name": "len"},
            "args": [{
                "kind": "list",
                "span": make_span(),
                "items": [
                    {"kind": "number", "span": make_span(), "value": 1},
                    {"kind": "string", "span": make_span(), "value": "hello"},
                    {"kind": "bool", "span": make_span(), "value": True}
                ]
            }]
        }
        self.assertEqual(eval_expr(ast), 3)


if __name__ == "__main__":
    unittest.main()
