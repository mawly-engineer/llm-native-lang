import unittest

from runtime.grammar_contract import parse_expr
from runtime.interpreter_runtime import EvalError, eval_expr


class InterpreterRuntimeLexicalScopeTest(unittest.TestCase):
    def test_let_bindings_are_lexically_scoped(self) -> None:
        expr = parse_expr("let x = 1 in let x = 2 in x")
        self.assertEqual(eval_expr(expr), 2)

    def test_inner_let_does_not_leak_to_outer_scope(self) -> None:
        expr = parse_expr("let x = 1 in let y = let x = 2 in x in x")
        self.assertEqual(eval_expr(expr), 1)

    def test_fn_closure_captures_definition_scope(self) -> None:
        expr = parse_expr("let x = 41 in let addx = fn(y)=>x in let x = 1 in addx(0)")
        self.assertEqual(eval_expr(expr), 41)

    def test_fn_argument_shadows_captured_binding(self) -> None:
        expr = parse_expr("let x = 7 in let f = fn(x)=>x in f(3)")
        self.assertEqual(eval_expr(expr), 3)

    def test_function_arity_mismatch_raises_error(self) -> None:
        expr = parse_expr("let f = fn(a,b)=>a in f(1)")
        with self.assertRaises(EvalError) as ctx:
            eval_expr(expr)

        self.assertIn("arity mismatch", str(ctx.exception))

    def test_unknown_identifier_raises_error(self) -> None:
        expr = parse_expr("x")
        with self.assertRaises(EvalError) as ctx:
            eval_expr(expr)

        self.assertIn("unknown identifier", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
