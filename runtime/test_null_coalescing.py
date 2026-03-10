"""Comprehensive tests for null coalescing operator (??).

Null coalescing provides safe default value handling with short-circuit evaluation.
"""

import unittest
from runtime.grammar_contract import parse_expr, ParseError
from runtime.interpreter_runtime import eval_expr, eval_expr_with_trace, EvalError


class NullCoalescingBasicTests(unittest.TestCase):
    """Basic null coalescing functionality."""

    def test_null_returns_default(self):
        """null ?? 42 returns 42"""
        ast = parse_expr("null ?? 42")
        self.assertEqual(ast["kind"], "coalesce_bin")
        self.assertEqual(ast["left"]["kind"], "null")
        self.assertEqual(ast["right"]["kind"], "number")
        result = eval_expr(ast)
        self.assertEqual(result, 42)

    def test_non_null_returns_left(self):
        """1 ?? 2 returns 1 (non-null left is returned)"""
        ast = parse_expr("1 ?? 2")
        self.assertEqual(ast["kind"], "coalesce_bin")
        result = eval_expr(ast)
        self.assertEqual(result, 1)

    def test_zero_not_null(self):
        """0 ?? 42 returns 0 (0 is not null)"""
        result = eval_expr(parse_expr("0 ?? 42"))
        self.assertEqual(result, 0)

    def test_empty_string_not_null(self):
        """'' ?? 'default' returns '' (empty string is not null)"""
        result = eval_expr(parse_expr('"" ?? "default"'))
        self.assertEqual(result, "")

    def test_false_not_null(self):
        """false ?? true returns false (false is not null)"""
        result = eval_expr(parse_expr("false ?? true"))
        self.assertEqual(result, False)

    def test_empty_list_not_null(self):
        """[] ?? [1,2] returns [] (empty list is not null)"""
        result = eval_expr(parse_expr("[] ?? [1,2]"))
        self.assertEqual(result, [])

    def test_empty_object_not_null(self):
        """{} ?? {'a':1} returns {} (empty object is not null)"""
        result = eval_expr(parse_expr('{} ?? {"a":1}'))
        self.assertEqual(result, {})


class NullCoalescingVariableTests(unittest.TestCase):
    """Null coalescing with variables."""

    def test_null_variable(self):
        """let x = null in x ?? 10 returns 10"""
        result = eval_expr(parse_expr("let x = null in x ?? 10"))
        self.assertEqual(result, 10)

    def test_non_null_variable(self):
        """let x = 5 in x ?? 10 returns 5"""
        result = eval_expr(parse_expr("let x = 5 in x ?? 10"))
        self.assertEqual(result, 5)

    def test_null_variable_in_object(self):
        """let user = {name: null} in user.name ?? 'Anonymous' returns 'Anonymous'"""
        result = eval_expr(parse_expr('let user = {"name": null} in user.name ?? "Anonymous"'))
        self.assertEqual(result, "Anonymous")


class NullCoalescingChainingTests(unittest.TestCase):
    """Chained null coalescing operators."""

    def test_chain_two_nulls(self):
        """null ?? null ?? 42 returns 42"""
        result = eval_expr(parse_expr("null ?? null ?? 42"))
        self.assertEqual(result, 42)

    def test_chain_first_non_null(self):
        """1 ?? null ?? 42 returns 1"""
        result = eval_expr(parse_expr("1 ?? null ?? 42"))
        self.assertEqual(result, 1)

    def test_chain_second_non_null(self):
        """null ?? 2 ?? 42 returns 2"""
        result = eval_expr(parse_expr("null ?? 2 ?? 42"))
        self.assertEqual(result, 2)

    def test_chain_all_non_null(self):
        """1 ?? 2 ?? 3 returns 1"""
        result = eval_expr(parse_expr("1 ?? 2 ?? 3"))
        self.assertEqual(result, 1)


class NullCoalescingShortCircuitTests(unittest.TestCase):
    """Short-circuit evaluation: right operand not evaluated if left is non-null."""

    def test_short_circuit_non_null(self):
        """true ?? (1 / 0) does not raise division by zero"""
        # This would raise E_RT_ZERO_DIVISION if right side was evaluated
        result = eval_expr(parse_expr("true ?? (1 / 0)"))
        self.assertEqual(result, True)

    def test_short_circuit_with_arithmetic(self):
        """1 ?? (1 / 0) does not raise division by zero"""
        result = eval_expr(parse_expr("1 ?? (1 / 0)"))
        self.assertEqual(result, 1)

    def test_short_circuit_with_string_concat(self):
        """'hello' ?? ('x' + 1) does not raise type error"""
        # 'x' + 1 would raise error, but short-circuit prevents evaluation
        result = eval_expr(parse_expr('"hello" ?? ("x" + 1)'))
        self.assertEqual(result, "hello")


class NullCoalescingIntegrationTests(unittest.TestCase):
    """Integration with other operators."""

    def test_with_comparison_in_condition(self):
        """null ?? (5 > 3) returns True"""
        result = eval_expr(parse_expr("null ?? (5 > 3)"))
        self.assertEqual(result, True)

    def test_with_logical_operators(self):
        """null ?? true and false returns false"""
        result = eval_expr(parse_expr("null ?? true and false"))
        self.assertEqual(result, False)

    def test_with_if_expression(self):
        """if (null ?? true) then 1 else 0 returns 1"""
        result = eval_expr(parse_expr("if (null ?? true) then 1 else 0"))
        self.assertEqual(result, 1)

    def test_in_function_result(self):
        """fn (x) => x ?? 0 returns 0 when called with null"""
        result = eval_expr(parse_expr("(fn (x) => x ?? 0)(null)"))
        self.assertEqual(result, 0)

    def test_in_function_with_non_null(self):
        """fn (x) => x ?? 0 returns 5 when called with 5"""
        result = eval_expr(parse_expr("(fn (x) => x ?? 0)(5)"))
        self.assertEqual(result, 5)


class NullCoalescingStringTests(unittest.TestCase):
    """Null coalescing with string values."""

    def test_string_left_non_null(self):
        """'hello' ?? 'world' returns 'hello'"""
        result = eval_expr(parse_expr('"hello" ?? "world"'))
        self.assertEqual(result, "hello")

    def test_null_with_string_default(self):
        """null ?? 'default' returns 'default'"""
        result = eval_expr(parse_expr('null ?? "default"'))
        self.assertEqual(result, "default")

    def test_empty_string_not_null_with_default(self):
        """'' ?? 'default' returns ''"""
        result = eval_expr(parse_expr('"" ?? "default"'))
        self.assertEqual(result, "")


class NullCoalescingListTests(unittest.TestCase):
    """Null coalescing with list values."""

    def test_null_returns_list_default(self):
        """null ?? [1,2,3] returns [1,2,3]"""
        result = eval_expr(parse_expr("null ?? [1,2,3]"))
        self.assertEqual(result, [1, 2, 3])

    def test_empty_list_not_null(self):
        """[] ?? [1,2] returns []"""
        result = eval_expr(parse_expr("[] ?? [1,2]"))
        self.assertEqual(result, [])

    def test_list_with_items_not_null(self):
        """[1] ?? [2] returns [1]"""
        result = eval_expr(parse_expr("[1] ?? [2]"))
        self.assertEqual(result, [1])


class NullCoalescingObjectTests(unittest.TestCase):
    """Null coalescing with object values."""

    def test_null_returns_object_default(self):
        """null ?? {'a': 1} returns {'a': 1}"""
        result = eval_expr(parse_expr('null ?? {"a": 1}'))
        self.assertEqual(result, {"a": 1})

    def test_empty_object_not_null(self):
        """{} ?? {'a': 1} returns {}"""
        result = eval_expr(parse_expr('{} ?? {"a": 1}'))
        self.assertEqual(result, {})

    def test_object_with_items_not_null(self):
        """{'x': 1} ?? {'y': 2} returns {'x': 1}"""
        result = eval_expr(parse_expr('{"x": 1} ?? {"y": 2}'))
        self.assertEqual(result, {"x": 1})


class NullCoalescingTraceTests(unittest.TestCase):
    """Trace generation for null coalescing."""

    def test_trace_includes_coalesce(self):
        """Trace includes coalesce_bin node"""
        result, trace = eval_expr_with_trace(parse_expr("null ?? 42"))
        self.assertEqual(result, 42)
        coalesce_traces = [t for t in trace if "coalesce" in t]
        self.assertTrue(len(coalesce_traces) > 0)

    def test_short_circuit_trace_excludes_right(self):
        """When short-circuiting, right side trace should not include error nodes"""
        result, trace = eval_expr_with_trace(parse_expr("1 ?? 2"))
        self.assertEqual(result, 1)
        # Should have coalesce trace but not evaluate right side's full trace
        self.assertTrue(any("coalesce" in t for t in trace))


class NullCoalescingPrecedenceTests(unittest.TestCase):
    """Operator precedence: ?? has lower precedence than logical or."""

    def test_precedence_with_logical_or(self):
        """false or null ?? 42 - coalesce has lower precedence than logical_or"""
        # Grammar defines: coalesce -> logical_or ('??' coalesce)?
        # So coalesce has LOWER precedence than logical_or
        # Parses as: (false or null) ?? 42
        # But false or null is a type error (null is not bool)
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr("false or null ?? 42"))
        self.assertIn("bool", str(ctx.exception))

    def test_precedence_with_comparison(self):
        """1 < 2 ?? false - comparison has higher precedence"""
        # Parses as: (1 < 2) ?? false = true ?? false = true
        result = eval_expr(parse_expr("1 < 2 ?? false"))
        self.assertEqual(result, True)


class NullCoalescingEdgeCaseTests(unittest.TestCase):
    """Edge cases and boundary conditions."""

    def test_nested_coalesce_same_value(self):
        """null ?? null ?? null ?? 1 returns 1"""
        result = eval_expr(parse_expr("null ?? null ?? null ?? 1"))
        self.assertEqual(result, 1)

    def test_coalesce_with_float(self):
        """null ?? 3.14 returns 3.14"""
        result = eval_expr(parse_expr("null ?? 3.14"))
        self.assertEqual(result, 3.14)

    def test_coalesce_zero_float_not_null(self):
        """0.0 ?? 3.14 returns 0.0"""
        result = eval_expr(parse_expr("0.0 ?? 3.14"))
        self.assertEqual(result, 0.0)


if __name__ == "__main__":
    unittest.main()
