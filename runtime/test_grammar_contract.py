import unittest

from runtime.grammar_contract import (
    GRAMMAR_CONTRACT,
    GRAMMAR_FINGERPRINT,
    parse_expr,
)


class GrammarContractTests(unittest.TestCase):
    def test_contract_freezes_required_nonterminals(self) -> None:
        self.assertEqual(
            GRAMMAR_CONTRACT["nonterminals"],
            ["expr", "let", "if", "fn", "logical_or", "logical_and", "call", "unary", "atom"],
        )

    def test_contract_fingerprint_is_stable(self) -> None:
        self.assertEqual(
            GRAMMAR_FINGERPRINT,
            "8d52e082dc8912d18f719e918d624c57a778bfd864c8d22c71ba7e2a11ba399a",
        )

    def test_parse_let_expression(self) -> None:
        ast = parse_expr("let x = 1 in x")
        self.assertEqual(ast["kind"], "let")
        self.assertEqual(ast["name"], "x")

    def test_parse_if_expression(self) -> None:
        ast = parse_expr("if true then 1 else 2")
        self.assertEqual(ast["kind"], "if")

    def test_parse_fn_expression(self) -> None:
        ast = parse_expr("fn(a,b) => a")
        self.assertEqual(ast["kind"], "fn")
        self.assertEqual(ast["params"], ["a", "b"])

    def test_parse_call_expression(self) -> None:
        ast = parse_expr("sum(1,2)")
        self.assertEqual(ast["kind"], "call")
        self.assertEqual(ast["callee"], "sum")
        self.assertEqual(len(ast["args"]), 2)

    def test_parse_unary_negation_expression(self) -> None:
        ast = parse_expr("-1")
        self.assertEqual(ast["kind"], "unary_neg")
        self.assertEqual(ast["operand"]["kind"], "number")

    def test_unary_negation_wraps_call_for_precedence_safety(self) -> None:
        ast = parse_expr("-sum(1)")
        self.assertEqual(ast["kind"], "unary_neg")
        self.assertEqual(ast["operand"]["kind"], "call")
        self.assertEqual(ast["operand"]["callee"], "sum")

    def test_parse_bool_literals_as_literal_nodes(self) -> None:
        ast_true = parse_expr("true")
        ast_false = parse_expr("false")
        self.assertEqual(ast_true["kind"], "bool")
        self.assertTrue(ast_true["value"])
        self.assertEqual(ast_false["kind"], "bool")
        self.assertFalse(ast_false["value"])

    def test_parse_logical_and_or_with_precedence(self) -> None:
        ast = parse_expr("true or false and true")
        self.assertEqual(ast["kind"], "logical_bin")
        self.assertEqual(ast["op"], "or")
        self.assertEqual(ast["left"]["kind"], "bool")
        self.assertEqual(ast["right"]["kind"], "logical_bin")
        self.assertEqual(ast["right"]["op"], "and")

    def test_parser_emits_deterministic_source_spans(self) -> None:
        ast = parse_expr("let x = 1 in x")
        self.assertEqual(ast["span"], {"start": 0, "end": 14})
        self.assertEqual(ast["value"]["span"], {"start": 8, "end": 9})
        self.assertEqual(ast["body"]["span"], {"start": 13, "end": 14})


if __name__ == "__main__":
    unittest.main()
