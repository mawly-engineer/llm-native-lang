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
            ["let", "if", "fn", "call", "index", "optional_call", "member_access", "optional_index_access", "optional_member_access", "list", "object", "unary_pos", "unary_neg", "unary_not", "concat_bin", "modulo_bin", "int_div_bin", "power_bin", "coalesce_bin", "logical_bin", "compare_bin", "ident", "number", "bool", "null", "string"],
        )

    def test_schema_fingerprint_stable(self) -> None:
        self.assertEqual(
            AST_SCHEMA_FINGERPRINT,
            "ca37ce123053a336fceaf9afc744db343f4fae77c34acad0df64a25f458a7ae4",
        )

    def test_parsed_core_nodes_validate(self) -> None:
        for source in [
            "let x = 1 in x",
            "if true then 1 else 2",
            "fn(a,b) => a",
            "sum(1,2)",
            "x",
            "42",
            "+1",
            "-1",
            "!false",
            "true and false",
            "1<2",
            "1==1",
            '"a"+"b"',
            "8%3",
            "8//3",
            "2**3",
            "a ?? b",
            '"s"',
            "true",
            "null",
            "[1,2,3]",
            '{"a":1,"b":2}',
            "arr[0]",
            "obj.field",
            "obj?.field",
            'obj?["field"]',
            "handler?(1)",
        ]:
            validate_ast(parse_expr(source))

    def test_all_core_nodes_include_source_span(self) -> None:
        ast = parse_expr("let x = [sum(1,2)] in x[0]")

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
            elif kind == "index":
                assert_spans(node["target"])
                assert_spans(node["index"])
            elif kind == "optional_call":
                assert_spans(node["target"])
                for arg in node["args"]:
                    assert_spans(arg)
            elif kind == "member_access":
                assert_spans(node["target"])
            elif kind == "optional_index_access":
                assert_spans(node["target"])
                assert_spans(node["index"])
            elif kind == "optional_member_access":
                assert_spans(node["target"])
            elif kind == "list":
                for item in node["items"]:
                    assert_spans(item)
            elif kind == "object":
                for entry in node["entries"]:
                    assert_spans(entry["value"])
            elif kind == "unary_pos":
                assert_spans(node["operand"])
            elif kind == "unary_neg":
                assert_spans(node["operand"])
            elif kind == "unary_not":
                assert_spans(node["operand"])
            elif kind == "concat_bin":
                assert_spans(node["left"])
                assert_spans(node["right"])
            elif kind == "modulo_bin":
                assert_spans(node["left"])
                assert_spans(node["right"])
            elif kind == "int_div_bin":
                assert_spans(node["left"])
                assert_spans(node["right"])
            elif kind == "power_bin":
                assert_spans(node["left"])
                assert_spans(node["right"])
            elif kind == "coalesce_bin":
                assert_spans(node["left"])
                assert_spans(node["right"])
            elif kind == "logical_bin":
                assert_spans(node["left"])
                assert_spans(node["right"])
            elif kind == "compare_bin":
                assert_spans(node["left"])
                assert_spans(node["right"])

        assert_spans(ast)

    def test_fn_params_must_be_unique(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "fn", "span": {"start": 0, "end": 12}, "params": ["a", "a"], "body": {"kind": "ident", "span": {"start": 11, "end": 12}, "name": "a"}})

    def test_call_args_must_be_list(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "call", "span": {"start": 0, "end": 6}, "callee": "sum", "args": "bad"})

    def test_optional_call_args_must_be_list(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "optional_call", "span": {"start": 0, "end": 8}, "target": {"kind": "ident", "span": {"start": 0, "end": 1}, "name": "f"}, "args": "bad"})

    def test_let_name_required(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "let", "span": {"start": 0, "end": 14}, "name": "", "value": {"kind": "number", "span": {"start": 8, "end": 9}, "value": 1}, "body": {"kind": "number", "span": {"start": 13, "end": 14}, "value": 2}})

    def test_bool_node_requires_boolean_value(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "bool", "span": {"start": 0, "end": 4}, "value": "true"})


if __name__ == "__main__":
    unittest.main()


class ASTNullContractTests(unittest.TestCase):
    def test_null_node_requires_none_value(self) -> None:
        with self.assertRaises(ASTValidationError):
            validate_ast({"kind": "null", "span": {"start": 0, "end": 4}, "value": "null"})
