import random
import unittest

from runtime.grammar_contract import ParseError, parse_expr
from runtime.interpreter_runtime import EvalError, eval_expr, eval_expr_with_trace


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

    def test_unary_logical_not_evaluates_operand(self) -> None:
        expr = parse_expr("!is_ready()")
        self.assertTrue(eval_expr(expr, env={"is_ready": lambda: False}))

    def test_string_concat_evaluates_deterministically(self) -> None:
        expr = parse_expr('"hi"+"-"+"there"')
        self.assertEqual(eval_expr(expr), "hi-there")

    def test_modulo_evaluates_deterministically(self) -> None:
        expr = parse_expr("10%4")
        self.assertEqual(eval_expr(expr), 2)

    def test_modulo_by_zero_raises_structured_error(self) -> None:
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr("10%0"))
        self.assertEqual(ctx.exception.code, "E_RT_ZERO_DIVISION")

    def test_integer_division_evaluates_deterministically(self) -> None:
        expr = parse_expr("20//3")
        self.assertEqual(eval_expr(expr), 6)

    def test_integer_division_uses_floor_semantics_for_negative_operands(self) -> None:
        expr = parse_expr("-5//2")
        self.assertEqual(eval_expr(expr), -3)

    def test_integer_division_by_zero_raises_structured_error(self) -> None:
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr("10//0"))
        self.assertEqual(ctx.exception.code, "E_RT_ZERO_DIVISION")

    def test_exponentiation_evaluates_deterministically_and_right_associative(self) -> None:
        expr = parse_expr("2**3**2")
        self.assertEqual(eval_expr(expr), 512)

    def test_exponentiation_negative_exponent_raises_structured_error(self) -> None:
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr("2**-1"))
        self.assertEqual(ctx.exception.code, "E_RT_DOMAIN")

    def test_list_literal_evaluates_deterministically(self) -> None:
        expr = parse_expr("[1,2,3]")
        self.assertEqual(eval_expr(expr), [1, 2, 3])

    def test_null_literal_evaluates_to_none(self) -> None:
        expr = parse_expr("null")
        self.assertIsNone(eval_expr(expr))

    def test_index_access_returns_item(self) -> None:
        expr = parse_expr("[9,8,7][1]")
        self.assertEqual(eval_expr(expr), 8)

    def test_index_access_out_of_range_raises_structured_error(self) -> None:
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr("[1][3]"))
        self.assertEqual(ctx.exception.code, "E_RT_INDEX_OUT_OF_RANGE")

    def test_member_access_returns_object_field(self) -> None:
        expr = parse_expr("user.name")
        self.assertEqual(eval_expr(expr, env={"user": {"name": "Luis"}}), "Luis")

    def test_member_access_rejects_non_object_target(self) -> None:
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr("n.value"), env={"n": 3})
        self.assertEqual(ctx.exception.code, "E_RT_TYPE")

    def test_member_access_missing_field_raises_structured_error(self) -> None:
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr("user.missing"), env={"user": {"name": "Luis"}})
        self.assertEqual(ctx.exception.code, "E_RT_MISSING_MEMBER")

    def test_null_coalescing_short_circuits_on_non_null_left(self) -> None:
        expr = parse_expr('"left"??boom()')
        self.assertEqual(eval_expr(expr, env={"boom": lambda: (_ for _ in ()).throw(RuntimeError("boom"))}), "left")

    def test_null_coalescing_falls_back_on_null_left(self) -> None:
        expr = parse_expr("null??7")
        self.assertEqual(eval_expr(expr), 7)

    def test_comparison_and_equality_evaluate_deterministically(self) -> None:
        self.assertTrue(eval_expr(parse_expr("1<2")))
        self.assertTrue(eval_expr(parse_expr("2>=2")))
        self.assertTrue(eval_expr(parse_expr('"a"<"b"')))
        self.assertTrue(eval_expr(parse_expr('"a"=="a"')))
        self.assertTrue(eval_expr(parse_expr("true!=false")))

    def test_comparison_rejects_mixed_or_unsupported_ordering_types(self) -> None:
        with self.assertRaises(EvalError) as mixed_ctx:
            eval_expr(parse_expr('"a"<1'))
        self.assertEqual(mixed_ctx.exception.code, "E_RT_TYPE")

        with self.assertRaises(EvalError) as bool_ctx:
            eval_expr(parse_expr("true<false"))
        self.assertEqual(bool_ctx.exception.code, "E_RT_TYPE")

    def test_equality_rejects_mismatched_operand_types(self) -> None:
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr("1==true"))
        self.assertEqual(ctx.exception.code, "E_RT_TYPE")

    def test_unary_logical_not_rejects_non_bool_operand(self) -> None:
        with self.assertRaises(EvalError) as ctx:
            eval_expr(parse_expr("!1"))
        self.assertEqual(ctx.exception.code, "E_RT_TYPE")

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

    def test_fuel_limit_halts_with_deterministic_reason(self) -> None:
        expr = parse_expr("let x = 1 in let y = 2 in x")
        with self.assertRaises(EvalError) as ctx:
            eval_expr(expr, fuel_limit=2)

        self.assertEqual(ctx.exception.code, "E_RT_FUEL_EXHAUSTED")
        self.assertEqual(ctx.exception.location.get("phase"), "step_budget")
        self.assertEqual(ctx.exception.location.get("halt_reason"), "fuel_exhausted")

    def test_fuel_limit_behavior_is_reproducible(self) -> None:
        expr = parse_expr("let x = 1 in let y = 2 in x")

        with self.assertRaises(EvalError) as first:
            eval_expr(expr, fuel_limit=2)
        with self.assertRaises(EvalError) as second:
            eval_expr(expr, fuel_limit=2)

        self.assertEqual(first.exception.code, second.exception.code)
        self.assertEqual(first.exception.location, second.exception.location)

    def test_invalid_fuel_limit_raises_structured_error(self) -> None:
        expr = parse_expr("1")
        with self.assertRaises(EvalError) as ctx:
            eval_expr(expr, fuel_limit=-1)

        self.assertEqual(ctx.exception.code, "E_RT_FUEL_CONFIG")
        self.assertEqual(ctx.exception.location.get("field"), "fuel_limit")

    def test_eval_trace_ids_are_deterministic_for_same_program(self) -> None:
        expr = parse_expr("let x = 1 in x")
        first_result, first_trace_ids = eval_expr_with_trace(expr)
        second_result, second_trace_ids = eval_expr_with_trace(expr)

        self.assertEqual(first_result, second_result)
        self.assertEqual(first_trace_ids, second_trace_ids)
        self.assertGreater(len(first_trace_ids), 0)

    def test_eval_trace_ids_include_node_kind_suffix(self) -> None:
        expr = parse_expr("10%4")
        _result, trace_ids = eval_expr_with_trace(expr)

        self.assertTrue(all(trace_id.startswith("n-") for trace_id in trace_ids))
        self.assertTrue(any(trace_id.endswith(":modulo_bin") for trace_id in trace_ids))


class InterpreterRuntimePropertyFuzzTest(unittest.TestCase):
    def _gen_expr(self, rng: random.Random, depth: int, vars_in_scope: list[str], allow_fn: bool) -> str:
        if depth <= 0:
            atom_choices = [str(rng.randint(0, 9))]
            atom_choices.extend(vars_in_scope)
            return rng.choice(atom_choices)

        branch = rng.choice(["atom", "let", "if", "call", "paren", "index"])
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
        if branch == "index":
            arr = f"[{rng.randint(0, 9)},{rng.randint(0, 9)}]"
            idx = str(rng.randint(0, 1))
            return f"{arr}[{idx}]"

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
