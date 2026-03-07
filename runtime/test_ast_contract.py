import unittest

from runtime.ast_contract import (
    AST_SCHEMA,
    AST_SCHEMA_FINGERPRINT,
    ASTValidationError,
    validate_ast,
)
from runtime.grammar_contract import parse_expr


class ASTContractTests(unittest.TestCase):
    def test_schema_freezes_core_node_kinds(self) -> None:
        self.assertEqual(
            list(AST_SCHEMA["nodes"].keys()),
            ["let", "if", "fn", "call", "ident", "number"],
        )

    def test_schema_fingerprint_stable(self) -> None:
        self.assertEqual(
            AST_SCHEMA_FINGERPRINT,
            "1dbeac1a9ef11bcc6fb61560906e9b3400704ae13e196e07b3ee4c952a093d4b",
        )

    def test_parsed_core_nodes_validate(self) -> None:
        for source in [
            "let x = 1 in x",
            "if x then 1 else 2",
            "fn(a,b) => a",
            "sum(1,2)",
            "x",
            "42",
        ]:
            validate_ast(parse_expr(source))

    def test_fn_params_must_be_unique(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "fn", "params": ["a", "a"], "body": {"kind": "ident", "name": "a"}})

    def test_call_args_must_be_list(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "call", "callee": "sum", "args": "bad"})

    def test_let_name_required(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "let", "name": "", "value": {"kind": "number", "value": 1}, "body": {"kind": "number", "value": 2}})


if __name__ == "__main__":
    unittest.main()
