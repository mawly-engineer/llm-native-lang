"""Comprehensive tests for power operator (**)."""

from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr, EvalError
import pytest


class TestPowerOperatorParsing:
    """Tests for parsing power operator expressions."""

    def test_parse_simple_power(self):
        node = parse_expr('2 ** 3')
        assert node['kind'] == 'power_bin'
        assert node['left']['kind'] == 'number'
        assert node['left']['value'] == 2
        assert node['right']['kind'] == 'number'
        assert node['right']['value'] == 3

    def test_parse_power_with_variables(self):
        node = parse_expr('x ** y')
        assert node['kind'] == 'power_bin'
        assert node['left']['kind'] == 'ident'
        assert node['left']['name'] == 'x'
        assert node['right']['kind'] == 'ident'
        assert node['right']['name'] == 'y'

    def test_parse_right_associative(self):
        # 2 ** 3 ** 2 should parse as 2 ** (3 ** 2)
        node = parse_expr('2 ** 3 ** 2')
        assert node['kind'] == 'power_bin'
        assert node['left']['value'] == 2
        assert node['right']['kind'] == 'power_bin'
        assert node['right']['left']['value'] == 3
        assert node['right']['right']['value'] == 2


class TestPowerOperatorEvaluation:
    """Tests for evaluating power operator."""

    def test_basic_power(self):
        assert eval_expr(parse_expr('2 ** 3')) == 8

    def test_larger_power(self):
        assert eval_expr(parse_expr('2 ** 10')) == 1024

    def test_different_bases(self):
        assert eval_expr(parse_expr('3 ** 2')) == 9

    def test_power_to_zero(self):
        assert eval_expr(parse_expr('10 ** 0')) == 1

    def test_zero_to_zero(self):
        # Mathematical convention: 0**0 = 1
        assert eval_expr(parse_expr('0 ** 0')) == 1

    def test_zero_to_positive(self):
        assert eval_expr(parse_expr('0 ** 5')) == 0

    def test_power_to_one(self):
        assert eval_expr(parse_expr('5 ** 1')) == 5


class TestPowerOperatorNegativeExponent:
    """Tests for negative exponents (should produce float)."""

    def test_negative_exponent(self):
        assert eval_expr(parse_expr('2 ** -1')) == 0.5

    def test_negative_exponent_larger(self):
        assert eval_expr(parse_expr('2 ** -2')) == 0.25

    def test_negative_exponent_base_10(self):
        assert eval_expr(parse_expr('10 ** -1')) == 0.1

    def test_negative_exponent_returns_float(self):
        result = eval_expr(parse_expr('5 ** -1'))
        assert isinstance(result, float)
        assert result == 0.2


class TestPowerOperatorFloatExponent:
    """Tests for fractional exponents (roots)."""

    def test_fractional_exponent_square_root(self):
        assert eval_expr(parse_expr('4 ** 0.5')) == 2.0

    def test_fractional_exponent_cube_root(self):
        assert eval_expr(parse_expr('8 ** (1/3)')) == 2.0

    def test_fractional_exponent_returns_float(self):
        result = eval_expr(parse_expr('9 ** 0.5'))
        assert isinstance(result, float)
        assert result == 3.0


class TestPowerOperatorRightAssociativity:
    """Tests for right-associative behavior."""

    def test_right_associative_simple(self):
        # 2 ** 3 ** 2 = 2 ** (3 ** 2) = 2 ** 9 = 512
        # NOT (2 ** 3) ** 2 = 8 ** 2 = 64
        assert eval_expr(parse_expr('2 ** 3 ** 2')) == 512

    def test_right_associative_chain(self):
        # 2 ** 2 ** 3 = 2 ** (2 ** 3) = 2 ** 8 = 256
        assert eval_expr(parse_expr('2 ** 2 ** 3')) == 256


class TestPowerOperatorWithLet:
    """Tests for power operator with let bindings."""

    def test_power_with_bound_variable(self):
        assert eval_expr(parse_expr('let x = 3 in 2 ** x')) == 8

    def test_power_with_bound_base(self):
        assert eval_expr(parse_expr('let base = 3 in base ** 2')) == 9

    def test_power_with_both_bound(self):
        assert eval_expr(parse_expr('let x = 2 in let y = 3 in x ** y')) == 8


class TestPowerOperatorNegativePath:
    """Negative path tests for power operator."""

    def test_type_error_string_base(self):
        with pytest.raises(EvalError) as exc_info:
            eval_expr(parse_expr('"hello" ** 2'))
        assert exc_info.value.code == 'E_RT_TYPE'
        assert 'int or float' in exc_info.value.message

    def test_type_error_string_exponent(self):
        with pytest.raises(EvalError) as exc_info:
            eval_expr(parse_expr('2 ** "hello"'))
        assert exc_info.value.code == 'E_RT_TYPE'
        assert 'int or float' in exc_info.value.message

    def test_type_error_bool_base(self):
        with pytest.raises(EvalError) as exc_info:
            eval_expr(parse_expr('true ** 2'))
        assert exc_info.value.code == 'E_RT_TYPE'

    def test_type_error_bool_exponent(self):
        with pytest.raises(EvalError) as exc_info:
            eval_expr(parse_expr('2 ** true'))
        assert exc_info.value.code == 'E_RT_TYPE'

    def test_type_error_null_base(self):
        with pytest.raises(EvalError) as exc_info:
            eval_expr(parse_expr('null ** 2'))
        assert exc_info.value.code == 'E_RT_TYPE'

    def test_type_error_null_exponent(self):
        with pytest.raises(EvalError) as exc_info:
            eval_expr(parse_expr('2 ** null'))
        assert exc_info.value.code == 'E_RT_TYPE'

    def test_type_error_list_base(self):
        with pytest.raises(EvalError) as exc_info:
            eval_expr(parse_expr('[1, 2] ** 2'))
        assert exc_info.value.code == 'E_RT_TYPE'

    def test_type_error_object_base(self):
        with pytest.raises(EvalError) as exc_info:
            eval_expr(parse_expr('{"a": 1} ** 2'))
        assert exc_info.value.code == 'E_RT_TYPE'


class TestPowerOperatorPrecedence:
    """Tests for power operator precedence."""

    def test_power_higher_than_multiplicative(self):
        # 2 * 3 ** 2 = 2 * (3 ** 2) = 2 * 9 = 18
        assert eval_expr(parse_expr('2 * 3 ** 2')) == 18

    def test_power_higher_than_additive(self):
        # 2 + 3 ** 2 = 2 + 9 = 11
        assert eval_expr(parse_expr('2 + 3 ** 2')) == 11

    def test_power_lower_than_unary(self):
        # (-2) ** 2 = 4
        assert eval_expr(parse_expr('(-2) ** 2')) == 4

    def test_power_with_parentheses(self):
        # (2 + 3) ** 2 = 25
        assert eval_expr(parse_expr('(2 + 3) ** 2')) == 25


class TestPowerOperatorIntegration:
    """Integration tests with other language features."""

    def test_power_in_if_expression(self):
        assert eval_expr(parse_expr('if 2 > 1 then 3 ** 2 else 2 ** 3')) == 9

    def test_power_in_comparison(self):
        assert eval_expr(parse_expr('2 ** 3 < 3 ** 2')) == False  # 8 < 9

    def test_power_with_equality(self):
        assert eval_expr(parse_expr('2 ** 3 == 8')) == True

    def test_power_in_function(self):
        assert eval_expr(parse_expr('(fn(x) => x ** 2)(5)')) == 25

    def test_power_in_let_function(self):
        assert eval_expr(parse_expr(
            'let square = fn(x) => x ** 2 in square(4)'
        )) == 16

    def test_power_in_recursive_function(self):
        # 2 ** n via recursive function
        assert eval_expr(parse_expr(
            'let rec pow2 = fn(n) => if n == 0 then 1 else 2 * pow2(n - 1) in pow2(10)'
        )) == 1024


class TestPowerOperatorEdgeCases:
    """Edge case tests."""

    def test_one_to_any_power(self):
        assert eval_expr(parse_expr('1 ** 100')) == 1

    def test_any_to_zero_power(self):
        assert eval_expr(parse_expr('42 ** 0')) == 1

    def test_large_exponent(self):
        # Should handle reasonably large exponents
        assert eval_expr(parse_expr('2 ** 20')) == 1048576

    def test_base_one_negative_exponent(self):
        assert eval_expr(parse_expr('1 ** -5')) == 1.0

    def test_nested_power(self):
        # (2 ** 3) ** 2 = 8 ** 2 = 64
        assert eval_expr(parse_expr('(2 ** 3) ** 2')) == 64

    def test_power_with_float_base(self):
        # Float bases should work
        result = eval_expr(parse_expr('2.5 ** 2'))
        assert isinstance(result, float)
        assert result == 6.25

    def test_power_with_float_exponent(self):
        # Float exponents should work
        result = eval_expr(parse_expr('9 ** 0.5'))
        assert isinstance(result, float)
        assert result == 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
