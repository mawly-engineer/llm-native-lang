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
            "eea290ab19cb0fac65146079ae4592e03f71ea6e95af7f1a892cb103bb845afb",
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

    def test_all_core_nodes_include_source_span(self) -> None:
        ast = parse_expr("let x = sum(1,2) in x")

        def assert_spans(node):
            self.assertIn("span", node)
            self.assertIsInstance(node["span"]["start"], int)
            self.assertIsInstance(node["span"]["end"], int)
            self.assertGreaterEqual(node["span"]["start"], 0)
            self.assertGreaterEqual(node["span"]["end"], node["span"]["start"])

            kind = node["kind"]
            if kind == "let":
                assert_spans(node["value"])
                assert_spans(node["body"])
            elif kind == "if":
                assert_spans(node["cond"])
                assert_spans(node["then"])
                assert_spans(node["else"])
            elif kind == "fn":
                assert_spans(node["body"])
            elif kind == "call":
                for arg in node["args"]:
                    assert_spans(arg)

        assert_spans(ast)

    def test_fn_params_must_be_unique(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "fn", "span": {"start": 0, "end": 12}, "params": ["a", "a"], "body": {"kind": "ident", "span": {"start": 11, "end": 12}, "name": "a"}})

    def test_call_args_must_be_list(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "call", "span": {"start": 0, "end": 6}, "callee": "sum", "args": "bad"})

    def test_let_name_required(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "let", "span": {"start": 0, "end": 14}, "name": "", "value": {"kind": "number", "span": {"start": 8, "end": 9}, "value": 1}, "body": {"kind": "number", "span": {"start": 13, "end": 14}, "value": 2}})


if __name__ == "__main__":
    unittest.main()
