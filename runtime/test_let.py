"""Tests for let expressions."""
from runtime.interpreter_runtime import eval_expr
from runtime.grammar_contract import parse_expr

def test_simple_let():
    ast = parse_expr("let x = 1 in x + 1")
    result = eval_expr(ast)
    assert result == 2
