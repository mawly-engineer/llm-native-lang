"""Comprehensive tests for power operator (**)."""

import unittest
from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr, EvalError


class TestPowerOperatorParsing(unittest.TestCase):
    """Tests for parsing power operator expressions."""

    def test_parse_simple_power(self):
        node = parse_expr('2 ** 3')
        self.assertEqual(node['kind'], 'power_bin')
        self.assertEqual(node['left']['kind'], 'number')
        self.assertEqual(node['left']['value'], 2)
        self.assertEqual(node['right']['kind'], 'number')
        self.assertEqual(node['right']['value'], 3)

    def test_parse_power_with_variables(self):
        node = parse_expr('x ** y')
        self.assertEqual(node['kind'], 'power_bin')
        self.assertEqual(node['left']['kind'], 'ident')
        self.assertEqual(node['left']['name'], 'x')
        self.assertEqual(node['right']['kind'], 'ident')
        self.assertEqual(node['right']['name'], 'y')

    def test_parse_right_associative(self):
        # 2 ** 3 ** 2 should parse as 2 ** (3 ** 2)
        node = parse_expr('2 ** 3 ** 2')
        self.assertEqual(node['kind'], 'power_bin')
        self.assertEqual(node['left']['value'], 2)
        self.assertEqual(node['right']['kind'], 'power_bin')
        self.assertEqual(node['right']['left']['value'], 3)
        self.assertEqual(node['right']['right']['value'], 2)


class TestPowerOperatorEvaluation(unittest.TestCase):
    """Tests for evaluating power operator."""

    def test_basic_power(self):
        self.assertEqual(eval_expr(parse_expr('2 ** 3')), 8)

    def test_larger_power(self):
        self.assertEqual(eval_expr(parse_expr('2 ** 10')), 1024)

    def test_different_bases(self):
        self.assertEqual(eval_expr(parse_expr('3 ** 2')), 9)

    def test_power_to_zero(self):
        self.assertEqual(eval_expr(parse_expr('10 ** 0')), 1)

    def test_zero_to_zero(self):
        # Mathematical convention: 0**0 = 1
        self.assertEqual(eval_expr(parse_expr('0 ** 0')), 1)

    def test_zero_to_positive(self):
        self.assertEqual(eval_expr(parse_expr('0 ** 5')), 0)

    def test_power_to_one(self):
        self.assertEqual(eval_expr(parse_expr('5 ** 1')), 5)


class TestPowerOperatorNegativeExponent(unittest.TestCase):
    """Tests for negative exponents (rejected per language design)."""

    def test_negative_exponent_rejected(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('2 ** -1'))
        self.assertEqual(ctx.exception.code, 'E_RT_DOMAIN')
        self.assertIn('non-negative exponent', ctx.exception.message)

    def test_negative_exponent_larger_rejected(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('2 ** -2'))
        self.assertEqual(ctx.exception.code, 'E_RT_DOMAIN')

    def test_negative_exponent_base_10_rejected(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('10 ** -1'))
        self.assertEqual(ctx.exception.code, 'E_RT_DOMAIN')

    def test_negative_exponent_returns_error(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('5 ** -1'))
        self.assertEqual(ctx.exception.code, 'E_RT_DOMAIN')


class TestPowerOperatorFloatExponent(unittest.TestCase):
    """Tests for fractional exponents (roots)."""

    def test_fractional_exponent_square_root(self):
        self.assertEqual(eval_expr(parse_expr('4 ** 0.5')), 2.0)

    def test_fractional_exponent_cube_root(self):
        # Note: 1/3 uses exact_div which requires divisible operands
        # Use float literal instead
        self.assertEqual(eval_expr(parse_expr('8 ** 0.3333333333333333')), 2.0)

    def test_fractional_exponent_returns_float(self):
        result = eval_expr(parse_expr('9 ** 0.5'))
        self.assertIsInstance(result, float)
        self.assertEqual(result, 3.0)


class TestPowerOperatorRightAssociativity(unittest.TestCase):
    """Tests for right-associative behavior."""

    def test_right_associative_simple(self):
        # 2 ** 3 ** 2 = 2 ** (3 ** 2) = 2 ** 9 = 512
        # NOT (2 ** 3) ** 2 = 8 ** 2 = 64
        self.assertEqual(eval_expr(parse_expr('2 ** 3 ** 2')), 512)

    def test_right_associative_chain(self):
        # 2 ** 2 ** 3 = 2 ** (2 ** 3) = 2 ** 8 = 256
        self.assertEqual(eval_expr(parse_expr('2 ** 2 ** 3')), 256)


class TestPowerOperatorWithLet(unittest.TestCase):
    """Tests for power operator with let bindings."""

    def test_power_with_bound_variable(self):
        self.assertEqual(eval_expr(parse_expr('let x = 3 in 2 ** x')), 8)

    def test_power_with_bound_base(self):
        self.assertEqual(eval_expr(parse_expr('let base = 3 in base ** 2')), 9)

    def test_power_with_both_bound(self):
        self.assertEqual(eval_expr(parse_expr('let x = 2 in let y = 3 in x ** y')), 8)


class TestPowerOperatorNegativePath(unittest.TestCase):
    """Negative path tests for power operator."""

    def test_type_error_string_base(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('"hello" ** 2'))
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')
        self.assertIn('int or float', ctx.exception.message)

    def test_type_error_string_exponent(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('2 ** "hello"'))
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')
        self.assertIn('int or float', ctx.exception.message)

    def test_type_error_bool_base(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('true ** 2'))
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')

    def test_type_error_bool_exponent(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('2 ** true'))
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')

    def test_type_error_null_base(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('null ** 2'))
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')

    def test_type_error_null_exponent(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('2 ** null'))
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')

    def test_type_error_list_base(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('[1, 2] ** 2'))
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')

    def test_type_error_object_base(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('{"a": 1} ** 2'))
        self.assertEqual(ctx.exception.code, 'E_RT_TYPE')


class TestPowerOperatorPrecedence(unittest.TestCase):
    """Tests for power operator precedence."""

    def test_power_higher_than_multiplicative(self):
        # 2 * 3 ** 2 = 2 * (3 ** 2) = 2 * 9 = 18
        self.assertEqual(eval_expr(parse_expr('2 * 3 ** 2')), 18)

    def test_power_higher_than_additive(self):
        # 2 + 3 ** 2 = 2 + 9 = 11
        self.assertEqual(eval_expr(parse_expr('2 + 3 ** 2')), 11)

    def test_power_lower_than_unary(self):
        # (-2) ** 2 = 4
        self.assertEqual(eval_expr(parse_expr('(-2) ** 2')), 4)

    def test_power_with_parentheses(self):
        # (2 + 3) ** 2 = 25
        self.assertEqual(eval_expr(parse_expr('(2 + 3) ** 2')), 25)


class TestPowerOperatorIntegration(unittest.TestCase):
    """Integration tests with other language features."""

    def test_power_in_if_expression(self):
        self.assertEqual(eval_expr(parse_expr('if 2 > 1 then 3 ** 2 else 2 ** 3')), 9)

    def test_power_in_comparison(self):
        self.assertEqual(eval_expr(parse_expr('2 ** 3 < 3 ** 2')), True)  # 8 < 9

    def test_power_with_equality(self):
        self.assertEqual(eval_expr(parse_expr('2 ** 3 == 8')), True)

    def test_power_in_function(self):
        self.assertEqual(eval_expr(parse_expr('(fn(x) => x ** 2)(5)')), 25)

    def test_power_in_let_function(self):
        self.assertEqual(eval_expr(parse_expr(
            'let square = fn(x) => x ** 2 in square(4)'
        )), 16)

    def test_power_in_recursive_function(self):
        # 2 ** n via recursive function
        self.assertEqual(eval_expr(parse_expr(
            'let rec pow2 = fn(n) => if n == 0 then 1 else 2 * pow2(n - 1) in pow2(10)'
        )), 1024)


class TestPowerOperatorEdgeCases(unittest.TestCase):
    """Edge case tests."""

    def test_one_to_any_power(self):
        self.assertEqual(eval_expr(parse_expr('1 ** 100')), 1)

    def test_any_to_zero_power(self):
        self.assertEqual(eval_expr(parse_expr('42 ** 0')), 1)

    def test_large_exponent(self):
        # Should handle reasonably large exponents
        self.assertEqual(eval_expr(parse_expr('2 ** 20')), 1048576)

    def test_base_one_negative_exponent_rejected(self):
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr('1 ** -5'))
        self.assertEqual(ctx.exception.code, 'E_RT_DOMAIN')

    def test_nested_power(self):
        # (2 ** 3) ** 2 = 8 ** 2 = 64
        self.assertEqual(eval_expr(parse_expr('(2 ** 3) ** 2')), 64)

    def test_power_with_float_base(self):
        # Float bases should work
        result = eval_expr(parse_expr('2.5 ** 2'))
        self.assertIsInstance(result, float)
        self.assertEqual(result, 6.25)

    def test_power_with_float_exponent(self):
        # Float exponents should work
        result = eval_expr(parse_expr('9 ** 0.5'))
        self.assertIsInstance(result, float)
        self.assertEqual(result, 3.0)


if __name__ == "__main__":
    unittest.main()
