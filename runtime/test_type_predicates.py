"""Tests for type predicate built-ins (is_int, is_string, is_bool, etc.)."""

import pytest
from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import eval_expr


class TestIsInt:
    """Tests for is_int type predicate."""

    def test_is_int_with_positive_int(self):
        node = parse_expr("is_int(42)")
        result = eval_expr(node)
        assert result is True

    def test_is_int_with_zero(self):
        node = parse_expr("is_int(0)")
        result = eval_expr(node)
        assert result is True

    def test_is_int_with_negative_int(self):
        node = parse_expr("is_int(-5)")
        result = eval_expr(node)
        assert result is True

    def test_is_int_with_float(self):
        node = parse_expr("is_int(3.14)")
        result = eval_expr(node)
        assert result is False

    def test_is_int_with_string(self):
        node = parse_expr('is_int("hello")')
        result = eval_expr(node)
        assert result is False

    def test_is_int_with_bool(self):
        # bool is NOT int in this language
        node = parse_expr("is_int(true)")
        result = eval_expr(node)
        assert result is False

    def test_is_int_with_list(self):
        node = parse_expr("is_int([1, 2])")
        result = eval_expr(node)
        assert result is False

    def test_is_int_with_object(self):
        node = parse_expr('is_int({"a": 1})')
        result = eval_expr(node)
        assert result is False

    def test_is_int_with_null(self):
        node = parse_expr("is_int(null)")
        result = eval_expr(node)
        assert result is False


class TestIsFloat:
    """Tests for is_float type predicate."""

    def test_is_float_with_float(self):
        node = parse_expr("is_float(3.14)")
        result = eval_expr(node)
        assert result is True

    def test_is_float_with_int(self):
        node = parse_expr("is_float(42)")
        result = eval_expr(node)
        assert result is False

    def test_is_float_with_string(self):
        node = parse_expr('is_float("3.14")')
        result = eval_expr(node)
        assert result is False


class TestIsString:
    """Tests for is_string type predicate."""

    def test_is_string_with_string(self):
        node = parse_expr('is_string("hello")')
        result = eval_expr(node)
        assert result is True

    def test_is_string_with_empty_string(self):
        node = parse_expr('is_string("")')
        result = eval_expr(node)
        assert result is True

    def test_is_string_with_int(self):
        node = parse_expr("is_string(42)")
        result = eval_expr(node)
        assert result is False

    def test_is_string_with_list(self):
        node = parse_expr('is_string(["a", "b"])')
        result = eval_expr(node)
        assert result is False


class TestIsBool:
    """Tests for is_bool type predicate."""

    def test_is_bool_with_true(self):
        node = parse_expr("is_bool(true)")
        result = eval_expr(node)
        assert result is True

    def test_is_bool_with_false(self):
        node = parse_expr("is_bool(false)")
        result = eval_expr(node)
        assert result is True

    def test_is_bool_with_int(self):
        # int is NOT bool in this language
        node = parse_expr("is_bool(1)")
        result = eval_expr(node)
        assert result is False

    def test_is_bool_with_zero(self):
        node = parse_expr("is_bool(0)")
        result = eval_expr(node)
        assert result is False

    def test_is_bool_with_string(self):
        node = parse_expr('is_bool("true")')
        result = eval_expr(node)
        assert result is False


class TestIsList:
    """Tests for is_list type predicate."""

    def test_is_list_with_list(self):
        node = parse_expr("is_list([1, 2, 3])")
        result = eval_expr(node)
        assert result is True

    def test_is_list_with_empty_list(self):
        node = parse_expr("is_list([])")
        result = eval_expr(node)
        assert result is True

    def test_is_list_with_nested_list(self):
        node = parse_expr("is_list([[1, 2], [3, 4]])")
        result = eval_expr(node)
        assert result is True

    def test_is_list_with_string(self):
        node = parse_expr('is_list("not a list")')
        result = eval_expr(node)
        assert result is False

    def test_is_list_with_object(self):
        node = parse_expr('is_list({"a": 1})')
        result = eval_expr(node)
        assert result is False


class TestIsObject:
    """Tests for is_object type predicate."""

    def test_is_object_with_object(self):
        node = parse_expr('is_object({"a": 1})')
        result = eval_expr(node)
        assert result is True

    def test_is_object_with_empty_object(self):
        node = parse_expr("is_object({})")
        result = eval_expr(node)
        assert result is True

    def test_is_object_with_nested_object(self):
        node = parse_expr('is_object({"outer": {"inner": 42}})')
        result = eval_expr(node)
        assert result is True

    def test_is_object_with_list(self):
        node = parse_expr("is_object([1, 2])")
        result = eval_expr(node)
        assert result is False

    def test_is_object_with_null(self):
        node = parse_expr("is_object(null)")
        result = eval_expr(node)
        assert result is False


class TestIsNull:
    """Tests for is_null type predicate."""

    def test_is_null_with_null(self):
        node = parse_expr("is_null(null)")
        result = eval_expr(node)
        assert result is True

    def test_is_null_with_zero(self):
        node = parse_expr("is_null(0)")
        result = eval_expr(node)
        assert result is False

    def test_is_null_with_false(self):
        node = parse_expr("is_null(false)")
        result = eval_expr(node)
        assert result is False

    def test_is_null_with_empty_string(self):
        node = parse_expr('is_null("")')
        result = eval_expr(node)
        assert result is False

    def test_is_null_with_empty_list(self):
        node = parse_expr("is_null([])")
        result = eval_expr(node)
        assert result is False


class TestIsFunction:
    """Tests for is_function type predicate."""

    def test_is_function_with_lambda(self):
        node = parse_expr("is_function(fn(x) => x)")
        result = eval_expr(node)
        assert result is True

    def test_is_function_with_let_bound_fn(self):
        node = parse_expr("let f = fn(x) => x in is_function(f)")
        result = eval_expr(node)
        assert result is True

    def test_is_function_with_no_params(self):
        node = parse_expr("is_function(fn() => 42)")
        result = eval_expr(node)
        assert result is True

    def test_is_function_with_int(self):
        node = parse_expr("is_function(42)")
        result = eval_expr(node)
        assert result is False

    def test_is_function_with_list(self):
        node = parse_expr("is_function([1, 2, 3])")
        result = eval_expr(node)
        assert result is False


class TestTypePredicatesWithVariables:
    """Tests for type predicates with variable bindings."""

    def test_is_int_with_variable(self):
        node = parse_expr("let x = 5 in is_int(x)")
        result = eval_expr(node)
        assert result is True

    def test_is_string_with_variable(self):
        node = parse_expr('let msg = "hello" in is_string(msg)')
        result = eval_expr(node)
        assert result is True

    def test_is_list_with_variable(self):
        node = parse_expr("let xs = [1, 2] in is_list(xs)")
        result = eval_expr(node)
        assert result is True

    def test_is_object_with_variable(self):
        node = parse_expr('let obj = {"a": 1} in is_object(obj)')
        result = eval_expr(node)
        assert result is True


class TestTypePredicatesWithLogicalOperators:
    """Tests for type predicates combined with logical operators."""

    def test_is_int_and_comparison(self):
        node = parse_expr("let x = 5 in is_int(x) and x > 0")
        result = eval_expr(node)
        assert result is True

    def test_is_string_or_is_list(self):
        node = parse_expr('is_string("hello") or is_list("hello")')
        result = eval_expr(node)
        assert result is True

    def test_is_int_and_is_positive(self):
        # Combined type check and comparison
        node = parse_expr("let x = 10 in is_int(x) and x >= 0")
        result = eval_expr(node)
        assert result is True

    def test_type_guard_pattern(self):
        # Simulate type guard: if is_int(x) then x + 1 else 0
        node = parse_expr("let x = 5 in if is_int(x) then x + 1 else 0")
        result = eval_expr(node)
        assert result == 6


class TestTypePredicatesWithExpressions:
    """Tests for type predicates with evaluated expressions."""

    def test_is_int_with_arithmetic_result(self):
        node = parse_expr("is_int(2 + 3)")
        result = eval_expr(node)
        assert result is True

    def test_is_list_with_list_literal(self):
        node = parse_expr("is_list([1 + 1, 2 + 2])")
        result = eval_expr(node)
        assert result is True

    def test_is_object_with_expr_values(self):
        node = parse_expr('is_object({"sum": 1 + 2})')
        result = eval_expr(node)
        assert result is True

    def test_is_string_with_concatenation(self):
        # String concatenation returns a string
        node = parse_expr('is_string("hello" + " world")')
        result = eval_expr(node)
        assert result is True


class TestTypePredicatesNegativePaths:
    """Tests that type predicates never raise errors."""

    def test_is_int_with_function(self):
        # Should return False, not raise
        node = parse_expr("is_int(fn() => 42)")
        result = eval_expr(node)
        assert result is False

    def test_is_function_with_null(self):
        # Should return False, not raise
        node = parse_expr("is_function(null)")
        result = eval_expr(node)
        assert result is False

    def test_is_list_with_object(self):
        # Should return False, not raise
        node = parse_expr('is_list({"a": 1})')
        result = eval_expr(node)
        assert result is False

    def test_is_object_with_list(self):
        # Should return False, not raise
        node = parse_expr("is_object([1, 2])")
        result = eval_expr(node)
        assert result is False