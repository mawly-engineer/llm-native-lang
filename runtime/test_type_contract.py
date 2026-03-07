import unittest

from runtime.grammar_contract import parse_expr
from runtime.type_contract import (
    TYPE_ANY,
    TYPE_BOOL,
    TYPE_NUMBER,
    TypeCheckError,
    check_expr,
    fn_type,
)


class TypeContractTests(unittest.TestCase):
    def test_number_literal_is_number(self) -> None:
        self.assertEqual(check_expr(parse_expr("42")), TYPE_NUMBER)

    def test_let_binds_value_type_in_body(self) -> None:
        expr = parse_expr("let x = 1 in x")
        self.assertEqual(check_expr(expr), TYPE_NUMBER)

    def test_if_requires_bool_condition(self) -> None:
        expr = parse_expr("if true then 1 else 2")
        self.assertEqual(check_expr(expr), TYPE_NUMBER)

    def test_if_rejects_non_bool_condition(self) -> None:
        with self.assertRaises(TypeCheckError):
            check_expr(parse_expr("if 1 then 1 else 2"))

    def test_if_rejects_branch_type_mismatch(self) -> None:
        with self.assertRaises(TypeCheckError):
            check_expr(
                parse_expr("if true then 1 else false"),
            )

    def test_function_returns_fn_type(self) -> None:
        expr = parse_expr("fn(a,b) => a")
        self.assertEqual(check_expr(expr), fn_type(TYPE_ANY, TYPE_ANY, returns=TYPE_ANY))

    def test_call_checks_arity_and_arg_types(self) -> None:
        env = {"sum": fn_type(TYPE_NUMBER, TYPE_NUMBER, returns=TYPE_NUMBER)}
        self.assertEqual(check_expr(parse_expr("sum(1,2)"), env=env), TYPE_NUMBER)

        with self.assertRaises(TypeCheckError):
            check_expr(parse_expr("sum(1)"), env=env)

    def test_unary_negation_requires_number_operand(self) -> None:
        self.assertEqual(check_expr(parse_expr("-42")), TYPE_NUMBER)
        with self.assertRaises(TypeCheckError):
            check_expr(parse_expr("-true"))

    def test_logical_and_or_require_bool_operands(self) -> None:
        self.assertEqual(check_expr(parse_expr("true and false")), TYPE_BOOL)
        self.assertEqual(check_expr(parse_expr("true or false")), TYPE_BOOL)
        with self.assertRaises(TypeCheckError):
            check_expr(parse_expr("1 and true"))

    def test_unknown_identifier_fails(self) -> None:
        with self.assertRaises(TypeCheckError):
            check_expr(parse_expr("x"))

    def test_non_function_callee_fails(self) -> None:
        with self.assertRaises(TypeCheckError):
            check_expr(parse_expr("x(1)"), env={"x": TYPE_NUMBER})

    def test_call_argument_type_mismatch_fails(self) -> None:
        env = {"is_zero": fn_type(TYPE_NUMBER, returns=TYPE_BOOL)}
        with self.assertRaises(TypeCheckError):
            check_expr(parse_expr("is_zero(true)"), env=env)


if __name__ == "__main__":
    unittest.main()
