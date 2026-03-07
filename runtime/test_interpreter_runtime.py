import random
import unittest

from runtime.grammar_contract import ParseError, parse_expr
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

    def test_unary_negation_evaluates_operand(self) -> None:
        expr = parse_expr("-inc(1)")
        self.assertEqual(eval_expr(expr, env={"inc": lambda x: x + 1}), -2)

    def test_logical_short_circuit_and_skips_rhs_when_left_false(self) -> None:
        expr = parse_expr("false and boom()")
        self.assertFalse(eval_expr(expr, env={"boom": lambda: (_ for _ in ()).throw(RuntimeError("boom"))}))

    def test_logical_short_circuit_or_skips_rhs_when_left_true(self) -> None:
        expr = parse_expr("true or boom()")
        self.assertTrue(eval_expr(expr, env={"boom": lambda: (_ for _ in ()).throw(RuntimeError("boom"))}))

    def test_function_arity_mismatch_raises_structured_error(self) -> None:
        expr = parse_expr("let f = fn(a,b)=>a in f(1)")
        with self.assertRaises(EvalError) as ctx:
            eval_expr(expr)

        self.assertEqual(ctx.exception.code, "E_RT_ARITY_MISMATCH")
        self.assertEqual(ctx.exception.location.get("node_kind"), "call")
        self.assertIn("arity mismatch", ctx.exception.message)

    def test_unknown_identifier_raises_structured_error(self) -> None:
        expr = parse_expr("x")
        with self.assertRaises(EvalError) as ctx:
            eval_expr(expr)

        self.assertEqual(ctx.exception.code, "E_RT_UNKNOWN_IDENTIFIER")
        self.assertEqual(ctx.exception.location.get("identifier"), "x")
        self.assertIn("unknown identifier", ctx.exception.message)

    def test_invalid_ast_raises_structured_error(self) -> None:
        invalid_expr = {"kind": "number", "value": "not-an-int"}
        with self.assertRaises(EvalError) as ctx:
            eval_expr(invalid_expr)

        self.assertEqual(ctx.exception.code, "E_RT_AST_INVALID")
        self.assertEqual(ctx.exception.location.get("phase"), "ast_validation")


class InterpreterRuntimePropertyFuzzTest(unittest.TestCase):
    def _gen_expr(self, rng: random.Random, depth: int, vars_in_scope: list[str], allow_fn: bool) -> str:
        if depth <= 0:
            atom_choices = [str(rng.randint(0, 9))]
            atom_choices.extend(vars_in_scope)
            return rng.choice(atom_choices)

        branch = rng.choice(["atom", "let", "if", "call", "paren"])
        if branch == "atom":
            return self._gen_expr(rng, 0, vars_in_scope, allow_fn)
        if branch == "paren":
            return f"({self._gen_expr(rng, depth - 1, vars_in_scope, allow_fn)})"
        if branch == "if":
            cond = self._gen_expr(rng, depth - 1, vars_in_scope, allow_fn)
            then_expr = self._gen_expr(rng, depth - 1, vars_in_scope, allow_fn)
            else_expr = self._gen_expr(rng, depth - 1, vars_in_scope, allow_fn)
            return f"if {cond} then {then_expr} else {else_expr}"
        if branch == "let":
            name = f"v{rng.randint(0, 4)}"
            value = self._gen_expr(rng, depth - 1, vars_in_scope, allow_fn)
            body = self._gen_expr(rng, depth - 1, vars_in_scope + [name], allow_fn)
            return f"let {name} = {value} in {body}"

        # call branch: keep runtime-safe by calling deterministic host functions
        callee = rng.choice(["id", "inc", "add"])
        if callee in {"id", "inc"}:
            arg = self._gen_expr(rng, depth - 1, vars_in_scope, allow_fn)
            return f"{callee}({arg})"
        arg1 = self._gen_expr(rng, depth - 1, vars_in_scope, allow_fn)
        arg2 = self._gen_expr(rng, depth - 1, vars_in_scope, allow_fn)
        return f"add({arg1},{arg2})"

    def test_parser_and_evaluator_are_deterministic_on_random_valid_programs(self) -> None:
        for seed in range(100):
            rng = random.Random(seed)
            source = self._gen_expr(rng, depth=3, vars_in_scope=[], allow_fn=False)

            ast_first = parse_expr(source)
            ast_second = parse_expr(source)
            self.assertEqual(ast_first, ast_second)

            env = {
                "id": lambda x: x,
                "inc": lambda x: x + 1,
                "add": lambda a, b: a + b,
            }
            result_first = eval_expr(ast_first, env=env)
            result_second = eval_expr(ast_second, env=env)
            self.assertEqual(result_first, result_second)

    def test_parser_rejects_invalid_character_mutations(self) -> None:
        for seed in range(25):
            rng = random.Random(1000 + seed)
            source = self._gen_expr(rng, depth=2, vars_in_scope=[], allow_fn=False)
            mutated = f"{source}@"
            with self.assertRaises(ParseError):
                parse_expr(mutated)


if __name__ == "__main__":
    unittest.main()
