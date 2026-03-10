"""Comprehensive tests for comparison operators (<, <=, >, >=, ==, !=)."""

import pytest
from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr, EvalError


class TestNumericComparisons:
    """Test numeric comparison operators with integers and floats."""

    def test_less_than_int_true(self):
        result = eval_expr(parse_expr("5 < 10"))
        assert result is True

    def test_less_than_int_false(self):
        result = eval_expr(parse_expr("10 < 5"))
        assert result is False

    def test_less_than_equal_true(self):
        result = eval_expr(parse_expr("10 <= 10"))
        assert result is True

    def test_less_than_equal_false(self):
        result = eval_expr(parse_expr("10 <= 5"))
        assert result is False

    def test_greater_than_int_true(self):
        result = eval_expr(parse_expr("15 > 10"))
        assert result is True

    def test_greater_than_int_false(self):
        result = eval_expr(parse_expr("5 > 10"))
        assert result is False

    def test_greater_than_equal_true(self):
        result = eval_expr(parse_expr("10 >= 10"))
        assert result is True

    def test_greater_than_equal_false(self):
        result = eval_expr(parse_expr("5 >= 10"))
        assert result is False

    def test_float_less_than_true(self):
        result = eval_expr(parse_expr("3.14 < 3.15"))
        assert result is True

    def test_float_less_than_false(self):
        result = eval_expr(parse_expr("3.15 < 3.14"))
        assert result is False

    def test_mixed_int_float_comparison(self):
        result = eval_expr(parse_expr("5 < 5.5"))
        assert result is True

    def test_mixed_float_int_comparison(self):
        result = eval_expr(parse_expr("5.5 > 5"))
        assert result is True


class TestStringComparisons:
    """Test string comparison operators with lexicographic ordering."""

    def test_string_less_than_true(self):
        result = eval_expr(parse_expr('"abc" < "def"'))
        assert result is True

    def test_string_less_than_false(self):
        result = eval_expr(parse_expr('"def" < "abc"'))
        assert result is False

    def test_string_less_than_equal_true(self):
        result = eval_expr(parse_expr('"abc" <= "abc"'))
        assert result is True

    def test_string_greater_than_true(self):
        result = eval_expr(parse_expr('"xyz" > "abc"'))
        assert result is True

    def test_string_greater_than_equal_true(self):
        result = eval_expr(parse_expr('"hello" >= "hello"'))
        assert result is True


class TestEqualityComparisons:
    """Test equality (==) and inequality (!=) operators."""

    def test_int_equality_true(self):
        result = eval_expr(parse_expr("5 == 5"))
        assert result is True

    def test_int_equality_false(self):
        result = eval_expr(parse_expr("5 == 10"))
        assert result is False

    def test_int_inequality_true(self):
        result = eval_expr(parse_expr("5 != 10"))
        assert result is True

    def test_int_inequality_false(self):
        result = eval_expr(parse_expr("5 != 5"))
        assert result is False

    def test_string_equality_true(self):
        result = eval_expr(parse_expr('"hello" == "hello"'))
        assert result is True

    def test_string_equality_false(self):
        result = eval_expr(parse_expr('"hello" == "world"'))
        assert result is False

    def test_string_inequality_true(self):
        result = eval_expr(parse_expr('"hello" != "world"'))
        assert result is True

    def test_boolean_equality_true(self):
        result = eval_expr(parse_expr("true == true"))
        assert result is True

    def test_boolean_equality_false(self):
        result = eval_expr(parse_expr("true == false"))
        assert result is False

    def test_null_equality_true(self):
        result = eval_expr(parse_expr("null == null"))
        assert result is True

    def test_null_inequality(self):
        result = eval_expr(parse_expr("null != 5"))
        assert result is True


class TestComparisonIntegration:
    """Test comparisons in complex expressions."""

    def test_comparison_in_if_condition(self):
        result = eval_expr(parse_expr("if 5 > 3 then 1 else 0"))
        assert result == 1

    def test_comparison_in_if_condition_false(self):
        result = eval_expr(parse_expr("if 3 > 5 then 1 else 0"))
        assert result == 0

    def test_comparison_with_logical_and(self):
        result = eval_expr(parse_expr("(5 > 3) and (10 < 20)"))
        assert result is True

    def test_comparison_with_logical_or(self):
        result = eval_expr(parse_expr("(5 > 10) or (3 < 7)"))
        assert result is True

    def test_comparison_chained_with_let(self):
        result = eval_expr(parse_expr("let x = 10 in x > 5"))
        assert result is True

    def test_comparison_in_complex_expression(self):
        result = eval_expr(parse_expr("let a = 5 in let b = 10 in a < b and b > a"))
        assert result is True


class TestComparisonNegativePaths:
    """Test negative paths: type errors and invalid comparisons."""

    def test_int_string_comparison_raises_type_error(self):
        with pytest.raises(EvalError) as exc:
            eval_expr(parse_expr('5 < "hello"'))
        assert exc.value.code == "E_RT_TYPE"

    def test_string_int_comparison_raises_type_error(self):
        with pytest.raises(EvalError) as exc:
            eval_expr(parse_expr('"hello" > 5'))
        assert exc.value.code == "E_RT_TYPE"

    def test_boolean_less_than_raises_type_error(self):
        with pytest.raises(EvalError) as exc:
            eval_expr(parse_expr("true < false"))
        assert exc.value.code == "E_RT_TYPE"

    def test_boolean_greater_than_raises_type_error(self):
        with pytest.raises(EvalError) as exc:
            eval_expr(parse_expr("true > false"))
        assert exc.value.code == "E_RT_TYPE"

    def test_null_less_than_raises_type_error(self):
        with pytest.raises(EvalError) as exc:
            eval_expr(parse_expr("null < 5"))
        assert exc.value.code == "E_RT_TYPE"

    def test_different_types_equality_raises_type_error(self):
        with pytest.raises(EvalError) as exc:
            eval_expr(parse_expr('5 == "5"'))
        assert exc.value.code == "E_RT_TYPE"


class TestComparisonEdgeCases:
    """Test edge cases and boundary values."""

    def test_compare_zero(self):
        result = eval_expr(parse_expr("0 < 1"))
        assert result is True

    def test_compare_negative_numbers(self):
        result = eval_expr(parse_expr("-10 < -5"))
        assert result is True

    def test_compare_negative_to_positive(self):
        result = eval_expr(parse_expr("-5 < 5"))
        assert result is True

    def test_empty_string_comparison(self):
        result = eval_expr(parse_expr('"" < "a"'))
        assert result is True

    def test_same_value_all_comparisons(self):
        exprs = [
            ("5 <= 5", True),
            ("5 >= 5", True),
            ("5 == 5", True),
            ("5 != 5", False),
            ("5 < 5", False),
            ("5 > 5", False),
        ]
        for expr, expected in exprs:
            result = eval_expr(parse_expr(expr))
            assert result == expected, f"Failed for {expr}"

    def test_large_number_comparison(self):
        result = eval_expr(parse_expr("1000000 > 999999"))
        assert result is True