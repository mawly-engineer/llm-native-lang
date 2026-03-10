"""Tests for function expressions (fn(params) => body) with closure capture."""

import sys
sys.path.insert(0, '/home/node/.openclaw/workspace/llm-native-lang')

from runtime.grammar_contract import parse_expr, ParseError
from runtime.interpreter_runtime import eval_expr, EvalError, Closure


def test_parse_fn_no_params():
    """parse_expr('fn() => 42') creates fn node with params=[], body=int(42)"""
    ast = parse_expr('fn() => 42')
    assert ast['kind'] == 'fn'
    assert ast['params'] == []
    assert ast['body']['kind'] == 'number'
    assert ast['body']['value'] == 42


def test_parse_fn_single_param():
    """parse_expr('fn(x) => x * 2') creates fn node with params=['x'], body=bin_op"""
    ast = parse_expr('fn(x) => x * 2')
    assert ast['kind'] == 'fn'
    assert ast['params'] == ['x']
    assert ast['body']['kind'] == 'mul_bin'


def test_parse_fn_multiple_params():
    """parse_expr('fn(a, b) => a + b') creates fn node with multiple params"""
    ast = parse_expr('fn(a, b) => a + b')
    assert ast['kind'] == 'fn'
    assert ast['params'] == ['a', 'b']


def test_parse_fn_trailing_comma():
    """parse_expr('fn(x,) => x') handles trailing comma in params"""
    ast = parse_expr('fn(x,) => x')
    assert ast['kind'] == 'fn'
    assert ast['params'] == ['x']


def test_eval_fn_returns_closure():
    """eval('fn() => 42') returns a callable function value"""
    result = eval_expr(parse_expr('fn() => 42'))
    assert isinstance(result, Closure)
    assert result.params == ()
    assert result.body['kind'] == 'number'


def test_immediate_invocation():
    """eval('(fn(x) => x * 2)(5)') returns 10"""
    ast = parse_expr('(fn(x) => x * 2)(5)')
    result = eval_expr(ast)
    assert result == 10


def test_let_bound_function():
    """eval('let double = fn(x) => x * 2 in double(3)') returns 6"""
    ast = parse_expr('let double = fn(x) => x * 2 in double(3)')
    result = eval_expr(ast)
    assert result == 6


def test_multiple_params():
    """eval('let add = fn(a, b) => a + b in add(1, 2)') returns 3"""
    ast = parse_expr('let add = fn(a, b) => a + b in add(1, 2)')
    result = eval_expr(ast)
    assert result == 3


def test_closure_capture():
    """eval('let makeAdder = fn(n) => fn(x) => x + n in makeAdder(5)(3)') returns 8"""
    ast = parse_expr('let makeAdder = fn(n) => fn(x) => x + n in makeAdder(5)(3)')
    result = eval_expr(ast)
    assert result == 8


def test_curried_function():
    """eval('fn(x) => fn(y) => x + y') returns curried function"""
    ast = parse_expr('fn(x) => fn(y) => x + y')
    result = eval_expr(ast)
    assert isinstance(result, Closure)
    # Apply first argument
    inner = eval_expr(parse_expr('(fn(x) => fn(y) => x + y)(5)'))
    assert isinstance(inner, Closure)
    # Apply second argument
    final = eval_expr(parse_expr('(fn(x) => fn(y) => x + y)(5)(3)'))
    assert final == 8


def test_function_in_boolean_context():
    """eval('let f = fn(x) => x > 0 in f(5) or f(-1)') works in boolean context"""
    ast = parse_expr('let f = fn(x) => x > 0 in f(5) or f(-1)')
    result = eval_expr(ast)
    assert result == True


def test_function_in_list():
    """eval('[fn(x) => x, fn(y) => y * 2][0](5)') returns 5"""
    ast = parse_expr('[fn(x) => x, fn(y) => y * 2][0](5)')
    result = eval_expr(ast)
    assert result == 5


def test_arg_count_mismatch_too_many():
    """eval('(fn() => 42)(1)') raises E_RT_ARITY_MISMATCH"""
    ast = parse_expr('(fn() => 42)(1)')
    try:
        eval_expr(ast)
        assert False, "Should have raised EvalError"
    except EvalError as e:
        assert e.code == 'E_RT_ARITY_MISMATCH'


def test_arg_count_mismatch_too_few():
    """eval('(fn(x) => x)()') raises E_RT_ARITY_MISMATCH"""
    ast = parse_expr('(fn(x) => x)()')
    try:
        eval_expr(ast)
        assert False, "Should have raised EvalError"
    except EvalError as e:
        assert e.code == 'E_RT_ARITY_MISMATCH'


def test_nested_function_calls():
    """eval('let f = fn(x) => fn(y) => fn(z) => x + y + z in f(1)(2)(3)') returns 6"""
    ast = parse_expr('let f = fn(x) => fn(y) => fn(z) => x + y + z in f(1)(2)(3)')
    result = eval_expr(ast)
    assert result == 6


def test_closure_with_multiple_captures():
    """Closure captures multiple variables from outer scope"""
    ast = parse_expr('let a = 1 in let b = 2 in let f = fn(x) => a + b + x in f(3)')
    result = eval_expr(ast)
    assert result == 6


def test_function_returning_function():
    """Higher-order function that returns a function"""
    ast = parse_expr('let makeMultiplier = fn(n) => fn(x) => x * n in let triple = makeMultiplier(3) in triple(4)')
    result = eval_expr(ast)
    assert result == 12


def test_shadowing_in_closure():
    """Inner parameter shadows outer captured variable"""
    ast = parse_expr('let x = 10 in let f = fn(x) => x * 2 in f(5)')
    result = eval_expr(ast)
    assert result == 10  # Uses parameter x=5, not outer x=10


if __name__ == '__main__':
    tests = [
        test_parse_fn_no_params,
        test_parse_fn_single_param,
        test_parse_fn_multiple_params,
        test_parse_fn_trailing_comma,
        test_eval_fn_returns_closure,
        test_immediate_invocation,
        test_let_bound_function,
        test_multiple_params,
        test_closure_capture,
        test_curried_function,
        test_function_in_boolean_context,
        test_function_in_list,
        test_arg_count_mismatch_too_many,
        test_arg_count_mismatch_too_few,
        test_nested_function_calls,
        test_closure_with_multiple_captures,
        test_function_returning_function,
        test_shadowing_in_closure,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
