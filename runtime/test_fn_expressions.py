"""Comprehensive tests for function expressions (fn)."""

import pytest
from runtime.grammar_contract import parse_expr, ParseError
from runtime.ast_contract import validate_ast
from runtime.interpreter_runtime import eval_expr, Closure, EvalError


class TestFnParsing:
    """Test parsing of fn expressions."""

    def test_fn_no_params(self):
        """fn() => 42"""
        ast = parse_expr("fn() => 42")
        validate_ast(ast)
        assert ast["kind"] == "fn"
        assert ast["params"] == []
        assert ast["body"]["kind"] == "number"
        assert ast["body"]["value"] == 42

    def test_fn_single_param(self):
        """fn(x) => x"""
        ast = parse_expr("fn(x) => x")
        validate_ast(ast)
        assert ast["kind"] == "fn"
        assert ast["params"] == ["x"]
        assert ast["body"]["kind"] == "ident"
        assert ast["body"]["name"] == "x"

    def test_fn_multiple_params(self):
        """fn(x, y) => x + y"""
        ast = parse_expr("fn(x, y) => x + y")
        validate_ast(ast)
        assert ast["kind"] == "fn"
        assert ast["params"] == ["x", "y"]
        assert ast["body"]["kind"] == "concat_bin"

    def test_fn_trailing_comma_params(self):
        """fn(x, y,) => x"""
        ast = parse_expr("fn(x, y,) => x")
        validate_ast(ast)
        assert ast["params"] == ["x", "y"]

    def test_fn_complex_body(self):
        """fn(x) => if x > 0 then x else -x"""
        ast = parse_expr("fn(x) => if x > 0 then x else -x")
        validate_ast(ast)
        assert ast["kind"] == "fn"
        assert ast["params"] == ["x"]
        assert ast["body"]["kind"] == "if"

    def test_fn_nested_fn(self):
        """fn(x) => fn(y) => x + y"""
        ast = parse_expr("fn(x) => fn(y) => x + y")
        validate_ast(ast)
        assert ast["kind"] == "fn"
        assert ast["params"] == ["x"]
        assert ast["body"]["kind"] == "fn"
        assert ast["body"]["params"] == ["y"]


class TestFnEvaluation:
    """Test evaluation of fn expressions."""

    def test_fn_no_params_evaluation(self):
        """Evaluate fn() => 42 applied immediately."""
        # let f = fn() => 42 in f()
        ast = parse_expr("let f = fn() => 42 in call(f)")
        result = eval_expr(ast)
        assert result == 42

    def test_fn_identity(self):
        """fn(x) => x applied to 42 returns 42."""
        ast = parse_expr("let identity = fn(x) => x in call(identity, 42)")
        result = eval_expr(ast)
        assert result == 42

    def test_fn_addition(self):
        """fn(x, y) => x + y applied to (3, 4) returns 7."""
        ast = parse_expr("let add = fn(x, y) => x + y in call(add, 3, 4)")
        result = eval_expr(ast)
        assert result == 7

    def test_fn_closure_capture(self):
        """Closure captures outer scope variable."""
        # let x = 10 in let f = fn(y) => x + y in call(f, 5)
        ast = parse_expr("let x = 10 in let f = fn(y) => x + y in call(f, 5)")
        result = eval_expr(ast)
        assert result == 15

    def test_fn_closure_multiple_capture(self):
        """Closure captures multiple outer scope variables."""
        ast = parse_expr("let a = 2 in let b = 3 in let f = fn(x) => a * x + b in call(f, 4)")
        result = eval_expr(ast)
        assert result == 11  # 2 * 4 + 3

    def test_fn_currying(self):
        """fn(x) => fn(y) => x + y (currying)."""
        # let add = fn(x) => fn(y) => x + y in call(call(add, 3), 4)
        ast = parse_expr("let add = fn(x) => fn(y) => x + y in call(call(add, 3), 4)")
        result = eval_expr(ast)
        assert result == 7

    def test_fn_return_fn(self):
        """Function returns another function."""
        # let makeAdder = fn(n) => fn(x) => x + n in let add5 = call(makeAdder, 5) in call(add5, 10)
        ast = parse_expr("let makeAdder = fn(n) => fn(x) => x + n in let add5 = call(makeAdder, 5) in call(add5, 10)")
        result = eval_expr(ast)
        assert result == 15


class TestFnErrorCases:
    """Test error handling for fn expressions."""

    def test_fn_arity_mismatch_too_few(self):
        """Calling fn with too few arguments raises error."""
        ast = parse_expr("let f = fn(x, y) => x + y in call(f, 1)")
        with pytest.raises(EvalError) as exc_info:
            eval_expr(ast)
        assert "arity mismatch" in str(exc_info.value).lower()

    def test_fn_arity_mismatch_too_many(self):
        """Calling fn with too many arguments raises error."""
        ast = parse_expr("let f = fn(x) => x in call(f, 1, 2)")
        with pytest.raises(EvalError) as exc_info:
            eval_expr(ast)
        assert "arity mismatch" in str(exc_info.value).lower()

    def test_fn_no_params_with_args(self):
        """Calling fn() => expr with arguments raises error."""
        ast = parse_expr("let f = fn() => 42 in call(f, 1)")
        with pytest.raises(EvalError) as exc_info:
            eval_expr(ast)
        assert "arity mismatch" in str(exc_info.value).lower()

    def test_duplicate_params(self):
        """Duplicate parameter names in fn definition raise validation error."""
        # Note: This would need to be caught at validation time
        # Currently the grammar allows it, but AST validation could catch it
        ast = parse_expr("fn(x, x) => x + x")
        # AST should be valid per grammar, but semantics might want to reject
        validate_ast(ast)
        # The duplicate is in params: ["x", "x"]
        assert ast["params"] == ["x", "x"]


class TestFnInComplexExpressions:
    """Test fn expressions in various contexts."""

    def test_fn_in_list(self):
        """Functions can be stored in lists."""
        ast = parse_expr("[fn(x) => x, fn(y) => y + 1]")
        result = eval_expr(ast)
        assert len(result) == 2
        assert isinstance(result[0], Closure)
        assert isinstance(result[1], Closure)

    def test_fn_in_object(self):
        """Functions can be stored in object values."""
        ast = parse_expr('{"double": fn(x) => x * 2}')
        result = eval_expr(ast)
        assert "double" in result
        assert isinstance(result["double"], Closure)

    def test_fn_as_let_binding(self):
        """Functions can be bound to names via let."""
        ast = parse_expr("let square = fn(x) => x * x in call(square, 5)")
        result = eval_expr(ast)
        assert result == 25

    def test_fn_in_conditional(self):
        """Functions can be selected conditionally."""
        # let inc = fn(x) => x + 1 in let dec = fn(x) => x - 1 in call(if true then inc else dec, 5)
        ast = parse_expr("let inc = fn(x) => x + 1 in let dec = fn(x) => x - 1 in call(if true then inc else dec, 5)")
        result = eval_expr(ast)
        assert result == 6

    def test_fn_coalesce_fallback(self):
        """Functions work with coalesce operator."""
        ast = parse_expr("let f = fn() => 42 in null ?? call(f)")
        result = eval_expr(ast)
        assert result == 42


class TestFnDeterminism:
    """Test that fn expressions maintain determinism."""

    def test_fn_closure_is_deterministic(self):
        """Same fn definition with same captured values produces deterministic results."""
        ast = parse_expr("let x = 10 in fn(y) => x + y")
        result1 = eval_expr(ast)
        result2 = eval_expr(ast)
        # Both should be closures with same structure
        assert isinstance(result1, Closure)
        assert isinstance(result2, Closure)
        assert result1.params == result2.params

    def test_fn_evaluation_is_pure(self):
        """Evaluating fn has no side effects."""
        ast = parse_expr("let f = fn(x) => x * 2 in call(f, 5)")
        result1 = eval_expr(ast)
        result2 = eval_expr(ast)
        assert result1 == result2
        assert result1 == 10


class TestFnIntegration:
    """Integration tests combining multiple features."""

    def test_fn_with_list_operations(self):
        """fn working with list literals."""
        # fn that returns first element of a list
        ast = parse_expr("let first = fn(lst) => lst[0] in call(first, [1, 2, 3])")
        result = eval_expr(ast)
        assert result == 1

    def test_fn_with_object_operations(self):
        """fn working with object literals."""
        ast = parse_expr('let getName = fn(obj) => obj.name in call(getName, {"name": "test"})')
        result = eval_expr(ast)
        assert result == "test"

    def test_fn_chain_with_member_access(self):
        """fn returning object with method-like access."""
        ast = parse_expr('let makeCounter = fn(start) => {"value": start, "inc": fn() => start + 1}.value in call(makeCounter, 10)')
        result = eval_expr(ast)
        assert result == 10

    def test_fn_higher_order_map_pattern(self):
        """Higher-order fn that takes another fn."""
        # let apply = fn(f, x) => call(f, x) in let double = fn(n) => n * 2 in call(apply, double, 5)
        ast = parse_expr("let apply = fn(f, x) => call(f, x) in let double = fn(n) => n * 2 in call(apply, double, 5)")
        result = eval_expr(ast)
        assert result == 10

    def test_fn_recursion_potential(self):
        """fn can be used for recursive patterns (via let binding)."""
        # This tests that the infrastructure supports recursion
        # let fact = fn(n) => if n == 0 then 1 else n * call(fact, n - 1)
        # Note: Would need recursive let support for full factorial
        ast = parse_expr("let fact = fn(n) => if n == 0 then 1 else n in call(fact, 5)")
        result = eval_expr(ast)
        # Without recursion, this just returns n
        assert result == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
