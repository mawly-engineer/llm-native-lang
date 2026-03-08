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
            ["expr", "let", "if", "fn", "logical_or", "logical_and", "unary", "postfix", "atom"],
        )

    def test_contract_fingerprint_is_stable(self) -> None:
        self.assertEqual(
            GRAMMAR_FINGERPRINT,
            "4ddca2ba7cadcb48bff046881b2adf65d98c79289fdcc17e27221b09e919c66b",
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

    def test_parse_list_literal(self) -> None:
        ast = parse_expr("[1,2,3]")
        self.assertEqual(ast["kind"], "list")
        self.assertEqual(len(ast["items"]), 3)

    def test_parse_index_access(self) -> None:
        ast = parse_expr("arr[1]")
        self.assertEqual(ast["kind"], "index")
        self.assertEqual(ast["target"]["kind"], "ident")
        self.assertEqual(ast["index"]["kind"], "number")

    def test_parser_emits_deterministic_source_spans(self) -> None:
        ast = parse_expr("let x = [1,2] in x[0]")
        self.assertEqual(ast["span"], {"start": 0, "end": 21})
        self.assertEqual(ast["value"]["span"], {"start": 8, "end": 13})
        self.assertEqual(ast["body"]["span"], {"start": 17, "end": 21})


if __name__ == "__main__":
    unittest.main()
