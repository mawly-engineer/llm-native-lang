"""Comprehensive tests for object literal support (LNG-CORE-48)."""
import unittest
from runtime.grammar_contract import ParseError, parse_expr
from runtime.interpreter_runtime import EvalError, eval_expr


class ObjectLiteralPositivePathTest(unittest.TestCase):
    """Positive path tests for object literal construction."""

    def test_empty_object_literal(self) -> None:
        """Empty object {} creates empty dict."""
        expr = parse_expr("{}")
        self.assertEqual(expr["kind"], "object")
        self.assertEqual(expr["entries"], [])
        self.assertEqual(eval_expr(expr), {})

    def test_simple_object_literal(self) -> None:
        """Object with single key-value pair."""
        expr = parse_expr('{"a": 1}')
        self.assertEqual(expr["kind"], "object")
        self.assertEqual(len(expr["entries"]), 1)
        self.assertEqual(expr["entries"][0]["key"], "a")
        self.assertEqual(eval_expr(expr), {"a": 1})

    def test_object_literal_multiple_entries(self) -> None:
        """Object with multiple key-value pairs."""
        expr = parse_expr('{"a": 1, "b": 2}')
        self.assertEqual(len(expr["entries"]), 2)
        self.assertEqual(eval_expr(expr), {"a": 1, "b": 2})

    def test_object_literal_with_trailing_comma(self) -> None:
        """Trailing comma after last entry is allowed."""
        expr = parse_expr('{"a": 1, "b": 2,}')
        self.assertEqual(len(expr["entries"]), 2)
        self.assertEqual(eval_expr(expr), {"a": 1, "b": 2})

    def test_object_literal_nested(self) -> None:
        """Nested object literals."""
        expr = parse_expr('{"outer": {"inner": 42}}')
        self.assertEqual(eval_expr(expr), {"outer": {"inner": 42}})

    def test_object_literal_with_expressions(self) -> None:
        """Object values can be expressions."""
        expr = parse_expr('{"computed": 1 + 2}')
        self.assertEqual(eval_expr(expr), {"computed": 3})

    def test_object_literal_mixed_types(self) -> None:
        """Object can have mixed type values."""
        expr = parse_expr('{"str": "hello", "num": 42, "bool": true, "null": null}')
        result = eval_expr(expr)
        self.assertEqual(result["str"], "hello")
        self.assertEqual(result["num"], 42)
        self.assertEqual(result["bool"], True)
        self.assertIsNone(result["null"])

    def test_object_literal_evaluation_order(self) -> None:
        """Object entries evaluate left-to-right."""
        # Test that side effects happen in order
        calls = []
        def track(x):
            calls.append(x)
            return x
        expr = parse_expr('{"a": track(1), "b": track(2)}')
        eval_expr(expr, env={"track": track})
        self.assertEqual(calls, [1, 2])


class ObjectLiteralNegativePathTest(unittest.TestCase):
    """Negative path tests for object literal parsing errors."""

    def test_unclosed_object_raises_parse_error(self) -> None:
        """Unclosed '{' raises E_PARSE."""
        with self.assertRaises(ParseError) as ctx:
            parse_expr('{"a": 1')
        self.assertEqual(ctx.exception.code, "E_PARSE_GENERIC")
        self.assertIn("expected }", ctx.exception.message.lower())

    def test_missing_colon_raises_parse_error(self) -> None:
        """Missing colon between key and value raises E_PARSE."""
        with self.assertRaises(ParseError) as ctx:
            parse_expr('{"a" 1}')
        self.assertIn("expected :", ctx.exception.message.lower())

    def test_non_string_key_raises_parse_error(self) -> None:
        """Non-string key raises E_PARSE."""
        with self.assertRaises(ParseError) as ctx:
            parse_expr('{a: 1}')
        self.assertIn("expected string", ctx.exception.message.lower())

    def test_integer_key_raises_parse_error(self) -> None:
        """Integer literal as key raises E_PARSE."""
        with self.assertRaises(ParseError) as ctx:
            parse_expr('{123: 1}')
        self.assertIn("expected string", ctx.exception.message.lower())


class ObjectLiteralAstValidationTest(unittest.TestCase):
    """AST-level validation tests."""

    def test_duplicate_keys_rejected_by_ast_validation(self) -> None:
        """Duplicate keys in object literal rejected."""
        from runtime.ast_contract import ASTValidationError, validate_ast
        expr = parse_expr('{"a": 1, "a": 2}')
        # AST validation should reject duplicate keys
        with self.assertRaises(ASTValidationError) as ctx:
            validate_ast(expr)
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_object_node_has_required_fields(self) -> None:
        """Object node has kind, span, entries fields."""
        expr = parse_expr('{"x": 1}')
        self.assertIn("kind", expr)
        self.assertIn("span", expr)
        self.assertIn("entries", expr)
        self.assertIsInstance(expr["entries"], list)


if __name__ == "__main__":
    unittest.main()
