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
            ["expr", "let", "if", "fn", "call", "atom"],
        )

    def test_contract_fingerprint_is_stable(self) -> None:
        self.assertEqual(
            GRAMMAR_FINGERPRINT,
            "ea392c6090422de38b5940948962ccd092368a576bacd2dfa4d4369d9523199d",
        )

    def test_parse_let_expression(self) -> None:
        ast = parse_expr("let x = 1 in x")
        self.assertEqual(ast["kind"], "let")
        self.assertEqual(ast["name"], "x")

    def test_parse_if_expression(self) -> None:
        ast = parse_expr("if x then 1 else 2")
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


if __name__ == "__main__":
    unittest.main()
