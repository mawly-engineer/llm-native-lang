"""Comprehensive tests for logical operators (and/or) with short-circuit evaluation.

Covers:
- Basic boolean logic for and/or
- Short-circuit evaluation behavior
- Chained operators
- Precedence (and binds tighter than or)
- Integration with other constructs (if, let, comparison)
- Type checking with proper error codes
- Negative paths (non-boolean operands)
"""

import unittest
from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr, EvalError


class LogicalOperatorTests(unittest.TestCase):
    """Test suite for logical and/or operators."""

    def test_and_both_true(self):
        """true and true -> true"""
        ast = parse_expr('true and true')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_and_left_true_right_false(self):
        """true and false -> false"""
        ast = parse_expr('true and false')
        result = eval_expr(ast)
        self.assertEqual(result, False)

    def test_and_left_false_right_true(self):
        """false and true -> false (short-circuit: right not evaluated)"""
        ast = parse_expr('false and true')
        result = eval_expr(ast)
        self.assertEqual(result, False)

    def test_and_both_false(self):
        """false and false -> false"""
        ast = parse_expr('false and false')
        result = eval_expr(ast)
        self.assertEqual(result, False)

    def test_or_both_true(self):
        """true or true -> true"""
        ast = parse_expr('true or true')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_or_left_true_right_false(self):
        """true or false -> true (short-circuit: right not evaluated)"""
        ast = parse_expr('true or false')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_or_left_false_right_true(self):
        """false or true -> true"""
        ast = parse_expr('false or true')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_or_both_false(self):
        """false or false -> false"""
        ast = parse_expr('false or false')
        result = eval_expr(ast)
        self.assertEqual(result, False)

    # Short-circuit tests
    def test_and_short_circuit_left_false(self):
        """false and (1/0 > 0) should NOT raise division by zero"""
        ast = parse_expr('false and (1 / 0 > 0)')
        result = eval_expr(ast)
        self.assertEqual(result, False)

    def test_or_short_circuit_left_true(self):
        """true or (1/0 > 0) should NOT raise division by zero"""
        ast = parse_expr('true or (1 / 0 > 0)')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_and_no_short_circuit_left_true(self):
        """true and (1/0 > 0) SHOULD raise division by zero"""
        ast = parse_expr('true and (1 / 0 > 0)')
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, 'E_RT_ZERO_DIVISION')

    def test_or_no_short_circuit_left_false(self):
        """false or (1/0 > 0) SHOULD raise division by zero"""
        ast = parse_expr('false or (1 / 0 > 0)')
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, 'E_RT_ZERO_DIVISION')

    # Chained operators
    def test_and_chained(self):
        """true and true and false -> false"""
        ast = parse_expr('true and true and false')
        result = eval_expr(ast)
        self.assertEqual(result, False)

    def test_or_chained(self):
        """false or false or true -> true"""
        ast = parse_expr('false or false or true')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    # Precedence: and binds tighter than or
    def test_precedence_and_binds_tighter_than_or(self):
        """true and true or false and false -> true"""
        # Should parse as: (true and true) or (false and false) -> true or false -> true
        ast = parse_expr('true and true or false and false')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_precedence_with_parentheses(self):
        """true and (false or true) -> true"""
        ast = parse_expr('true and (false or true)')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    # Integration with if expressions
    def test_in_if_condition(self):
        """if true and false then 1 else 2 -> 2"""
        ast = parse_expr('if true and false then 1 else 2')
        result = eval_expr(ast)
        self.assertEqual(result, 2)

    def test_in_if_condition_or(self):
        """if false or true then 1 else 2 -> 1"""
        ast = parse_expr('if false or true then 1 else 2')
        result = eval_expr(ast)
        self.assertEqual(result, 1)

    # Integration with let expressions
    def test_with_let_binding(self):
        """let ok = true in ok and true -> true"""
        ast = parse_expr('let ok = true in ok and true')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_with_let_binding_or(self):
        """let x = false in x or true -> true"""
        ast = parse_expr('let x = false in x or true')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    # Integration with comparison operators
    def test_with_comparison_and(self):
        """1 < 2 and 3 > 1 -> true"""
        ast = parse_expr('1 < 2 and 3 > 1')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_with_comparison_or(self):
        """1 > 2 or 3 > 1 -> true"""
        ast = parse_expr('1 > 2 or 3 > 1')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_with_comparison_both_false(self):
        """1 > 2 and 3 < 1 -> false"""
        ast = parse_expr('1 > 2 and 3 < 1')
        result = eval_expr(ast)
        self.assertEqual(result, False)

    # Type checking - left operand not bool
    def test_type_error_and_left_not_bool(self):
        """1 and true should raise E_RT_TYPE"""
        ast = parse_expr('1 and true')
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')
        self.assertIn('left operand', ctx.exception.message.lower())

    def test_type_error_or_left_not_bool(self):
        """1 or false should raise E_RT_TYPE"""
        ast = parse_expr('1 or false')
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')
        self.assertIn('left operand', ctx.exception.message.lower())

    # Type checking - right operand not bool
    def test_type_error_and_right_not_bool(self):
        """true and 1 should raise E_RT_TYPE"""
        ast = parse_expr('true and 1')
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')
        self.assertIn('right operand', ctx.exception.message.lower())

    def test_type_error_or_right_not_bool(self):
        """false or 1 should raise E_RT_TYPE"""
        ast = parse_expr('false or 1')
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')
        self.assertIn('right operand', ctx.exception.message.lower())

    # Type checking - string operand
    def test_type_error_string_and(self):
        """"hello" and true should raise E_RT_TYPE"""
        ast = parse_expr('"hello" and true')
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')

    def test_type_error_string_or(self):
        """"hello" or false should raise E_RT_TYPE"""
        ast = parse_expr('"hello" or false')
        with self.assertRaises(EvalError) as ctx:
            eval_expr(ast)
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')

    # Complex expressions
    def test_complex_boolean_logic(self):
        """Complex nested boolean expression"""
        ast = parse_expr('(1 < 2 and 3 > 0) or (5 == 6 and false)')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_complex_with_let(self):
        """let a = true in let b = false in a and !b"""
        ast = parse_expr('let a = true in let b = false in a and !b')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    # Negation combined with logical (using ! for unary_not)
    def test_not_with_and(self):
        """!false and true -> true"""
        ast = parse_expr('!false and true')
        result = eval_expr(ast)
        self.assertEqual(result, True)

    def test_not_with_or(self):
        """!true or false -> false"""
        ast = parse_expr('!true or false')
        # ! binds tighter than and/or, so this is (!true) or false -> false or false -> false
        result = eval_expr(ast)
        self.assertEqual(result, False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
