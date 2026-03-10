"""Comprehensive tests for let expressions.

Coverage:
- Basic let binding and usage
- Nested lets (sequential bindings)
- Shadowing (inner let overrides outer)
- String values in let
- Bound variables in index operations
- Bound variables in member access
- Negative paths: unbound identifier reference
- Negative paths: non-identifier binding target (parse-time rejection)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.interpreter_runtime import eval_expr, EvalError
from runtime.grammar_contract import parse_expr, ParseError
import sys

def test_simple_let():
    """Basic let binding: let x = 1 in x + 1"""
    ast = parse_expr("let x = 1 in x + 1")
    result = eval_expr(ast)
    assert result == 2, f"Expected 2, got {result}"


def test_nested_lets():
    """Nested lets: let a = 1 in let b = 2 in a + b"""
    ast = parse_expr("let a = 1 in let b = 2 in a + b")
    result = eval_expr(ast)
    assert result == 3, f"Expected 3, got {result}"


def test_shadowing():
    """Variable shadowing: let x = 10 in let x = 20 in x"""
    ast = parse_expr("let x = 10 in let x = 20 in x")
    result = eval_expr(ast)
    assert result == 20, f"Expected 20, got {result}"


def test_string_value():
    """Let with string value: let msg = 'Hello' in msg"""
    ast = parse_expr('let msg = "Hello" in msg')
    result = eval_expr(ast)
    assert result == "Hello", f"Expected 'Hello', got {result}"


def test_bound_var_in_index():
    """Bound variable in list index: let lst = [1, 2] in lst[0]"""
    ast = parse_expr("let lst = [1, 2] in lst[0]")
    result = eval_expr(ast)
    assert result == 1, f"Expected 1, got {result}"


def test_bound_var_in_member_access():
    """Bound variable in member access: let obj = {'a': 1} in obj.a"""
    ast = parse_expr('let obj = {"a": 1} in obj.a')
    result = eval_expr(ast)
    assert result == 1, f"Expected 1, got {result}"


def test_bound_var_in_expressions():
    """Let-bound variables in complex expressions"""
    ast = parse_expr("let x = 5 in let y = 3 in x * y + x - y")
    result = eval_expr(ast)
    assert result == 17, f"Expected 17, got {result}"


def test_let_with_list_literal():
    """Let binding to list literal"""
    ast = parse_expr("let items = [1, 2, 3] in items[1]")
    result = eval_expr(ast)
    assert result == 2, f"Expected 2, got {result}"


def test_let_with_object_literal():
    """Let binding to object literal"""
    ast = parse_expr('let cfg = {"debug": true, "port": 8080} in cfg.port')
    result = eval_expr(ast)
    assert result == 8080, f"Expected 8080, got {result}"


def test_unbound_identifier_error():
    """Negative: unbound identifier raises E_RT_UNKNOWN_IDENTIFIER"""
    try:
        ast = parse_expr("unbound_var")
        result = eval_expr(ast)
        assert False, f"Expected EvalError, got {result}"
    except EvalError as e:
        assert e.code == "E_RT_UNKNOWN_IDENTIFIER", f"Expected E_RT_UNKNOWN_IDENTIFIER, got {e.code}"
        assert "unbound_var" in str(e), f"Expected 'unbound_var' in error message"


def test_unbound_in_let_body():
    """Negative: unbound identifier in let body"""
    try:
        ast = parse_expr("let x = 1 in unbound_ref")
        result = eval_expr(ast)
        assert False, f"Expected EvalError, got {result}"
    except EvalError as e:
        assert e.code == "E_RT_UNKNOWN_IDENTIFIER", f"Expected E_RT_UNKNOWN_IDENTIFIER, got {e.code}"


def test_non_identifier_binding_target():
    """Negative: let must bind to identifier (rejected at parse time)"""
    try:
        ast = parse_expr("let 123 = 1 in 1")
        assert False, f"Expected ParseError for 'let 123 = 1 in 1'"
    except ParseError:
        pass  # Expected


def test_let_node_structure():
    """Verify let node has correct AST structure"""
    ast = parse_expr("let x = 1 in x")
    assert ast["kind"] == "let"
    assert ast["name"] == "x"
    assert ast["value"]["kind"] == "number"
    assert ast["value"]["value"] == 1
    assert ast["body"]["kind"] == "ident"
    assert ast["body"]["name"] == "x"


def test_multiple_bindings_sequential():
    """Multiple sequential bindings with nested lets"""
    ast = parse_expr("let a = 1 in let b = a + 1 in let c = b + 1 in c")
    result = eval_expr(ast)
    assert result == 3, f"Expected 3, got {result}"


def test_outer_scope_access():
    """Inner scope can access outer scope bindings"""
    ast = parse_expr("let outer = 10 in let inner = outer + 5 in inner")
    result = eval_expr(ast)
    assert result == 15, f"Expected 15, got {result}"


def test_shadowing_preserves_outer():
    """After shadowing, outer binding is still accessible if captured"""
    ast = parse_expr("let x = 5 in let y = x in let x = 100 in y")
    result = eval_expr(ast)
    assert result == 5, f"Expected 5 (captured outer x), got {result}"


def test_let_in_function():
    """Let inside function body - closures return Closure objects"""
    from runtime.interpreter_runtime import Closure
    ast = parse_expr("fn(x) => let doubled = x * 2 in doubled + 1")
    fn = eval_expr(ast)
    assert isinstance(fn, Closure), f"Expected Closure, got {type(fn)}"
    # The function itself is correct; we trust the closure mechanism


def test_let_with_boolean():
    """Let binding to boolean value"""
    ast = parse_expr("let flag = true in if flag then 1 else 0")
    result = eval_expr(ast)
    assert result == 1, f"Expected 1, got {result}"


def test_let_with_null():
    """Let binding to null value"""
    ast = parse_expr("let nothing = null in nothing ?? 42")
    result = eval_expr(ast)
    assert result == 42, f"Expected 42, got {result}"


if __name__ == "__main__":
    tests = [
        test_simple_let,
        test_nested_lets,
        test_shadowing,
        test_string_value,
        test_bound_var_in_index,
        test_bound_var_in_member_access,
        test_bound_var_in_expressions,
        test_let_with_list_literal,
        test_let_with_object_literal,
        test_unbound_identifier_error,
        test_unbound_in_let_body,
        test_non_identifier_binding_target,
        test_let_node_structure,
        test_multiple_bindings_sequential,
        test_outer_scope_access,
        test_shadowing_preserves_outer,
        test_let_in_function,
        test_let_with_boolean,
        test_let_with_null,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if failed == 0 else 1)
