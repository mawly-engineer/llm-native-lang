import unittest

from runtime.grammar_contract import (
    GRAMMAR_CONTRACT,
    GRAMMAR_FINGERPRINT,
    ParseError,
    parse_expr,
)


class GrammarContractTests(unittest.TestCase):
    def test_contract_freezes_required_nonterminals(self) -> None:
        self.assertEqual(
            GRAMMAR_CONTRACT["nonterminals"],
            ["expr", "let", "if", "fn", "coalesce", "logical_or", "logical_and", "equality", "comparison", "concat", "multiplicative", "power", "unary", "postfix", "atom"],
        )

    def test_contract_fingerprint_is_stable(self) -> None:
        self.assertEqual(
            GRAMMAR_FINGERPRINT,
            "3890fa88d09bada42a1eb4b72f35b7d8b865504b3aa9412a701273695f274cad",
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

    def test_parse_unary_logical_not_expression(self) -> None:
        ast = parse_expr("!true")
        self.assertEqual(ast["kind"], "unary_not")
        self.assertEqual(ast["operand"]["kind"], "bool")

    def test_unary_negation_wraps_call_for_precedence_safety(self) -> None:
        ast = parse_expr("-sum(1)")
        self.assertEqual(ast["kind"], "unary_neg")
        self.assertEqual(ast["operand"]["kind"], "call")
        self.assertEqual(ast["operand"]["callee"], "sum")

    def test_unary_logical_not_wraps_call_for_precedence_safety(self) -> None:
        ast = parse_expr("!flag()")
        self.assertEqual(ast["kind"], "unary_not")
        self.assertEqual(ast["operand"]["kind"], "call")
        self.assertEqual(ast["operand"]["callee"], "flag")

    def test_parse_bool_literals_as_literal_nodes(self) -> None:
        ast_true = parse_expr("true")
        ast_false = parse_expr("false")
        self.assertEqual(ast_true["kind"], "bool")
        self.assertTrue(ast_true["value"])
        self.assertEqual(ast_false["kind"], "bool")
        self.assertFalse(ast_false["value"])

    def test_parse_null_literal_as_literal_node(self) -> None:
        ast_null = parse_expr("null")
        self.assertEqual(ast_null["kind"], "null")
        self.assertIsNone(ast_null["value"])

    def test_parse_null_coalescing_right_associative_and_precedence(self) -> None:
        ast = parse_expr("a ?? b ?? c")
        self.assertEqual(ast["kind"], "coalesce_bin")
        self.assertEqual(ast["left"]["kind"], "ident")
        self.assertEqual(ast["right"]["kind"], "coalesce_bin")

    def test_null_coalescing_binds_looser_than_logical_or(self) -> None:
        ast = parse_expr("a or b ?? c")
        self.assertEqual(ast["kind"], "coalesce_bin")
        self.assertEqual(ast["left"]["kind"], "logical_bin")

    def test_parse_logical_and_or_with_precedence(self) -> None:
        ast = parse_expr("true or false and true")
        self.assertEqual(ast["kind"], "logical_bin")
        self.assertEqual(ast["op"], "or")
        self.assertEqual(ast["left"]["kind"], "bool")
        self.assertEqual(ast["right"]["kind"], "logical_bin")
        self.assertEqual(ast["right"]["op"], "and")

    def test_parse_equality_and_comparison_tiers_with_precedence(self) -> None:
        ast = parse_expr("1+2 < 4 == true")
        self.assertEqual(ast["kind"], "compare_bin")
        self.assertEqual(ast["op"], "==")
        self.assertEqual(ast["left"]["kind"], "compare_bin")
        self.assertEqual(ast["left"]["op"], "<")
        self.assertEqual(ast["left"]["left"]["kind"], "concat_bin")
        self.assertEqual(ast["right"]["kind"], "bool")

    def test_parse_string_literal(self) -> None:
        ast = parse_expr('"hi"')
        self.assertEqual(ast["kind"], "string")
        self.assertEqual(ast["value"], "hi")

    def test_parse_string_concatenation(self) -> None:
        ast = parse_expr('"a"+"b"+"c"')
        self.assertEqual(ast["kind"], "concat_bin")
        self.assertEqual(ast["op"], "+")
        self.assertEqual(ast["left"]["kind"], "concat_bin")
        self.assertEqual(ast["right"]["kind"], "string")

    def test_parse_subtraction_left_associative(self) -> None:
        ast = parse_expr("9-3-1")
        self.assertEqual(ast["kind"], "concat_bin")
        self.assertEqual(ast["op"], "-")
        self.assertEqual(ast["left"]["kind"], "concat_bin")
        self.assertEqual(ast["left"]["op"], "-")

    def test_parse_modulo_expression(self) -> None:
        ast = parse_expr("10%3%2")
        self.assertEqual(ast["kind"], "modulo_bin")
        self.assertEqual(ast["left"]["kind"], "modulo_bin")
        self.assertEqual(ast["right"]["kind"], "number")

    def test_parse_integer_division_expression(self) -> None:
        ast = parse_expr("20//5//2")
        self.assertEqual(ast["kind"], "int_div_bin")
        self.assertEqual(ast["left"]["kind"], "int_div_bin")
        self.assertEqual(ast["right"]["kind"], "number")

    def test_parse_exponentiation_expression_right_associative(self) -> None:
        ast = parse_expr("2**3**2")
        self.assertEqual(ast["kind"], "power_bin")
        self.assertEqual(ast["left"]["kind"], "number")
        self.assertEqual(ast["right"]["kind"], "power_bin")

    def test_exponentiation_has_higher_precedence_than_multiplicative(self) -> None:
        ast = parse_expr("2**3%3")
        self.assertEqual(ast["kind"], "modulo_bin")
        self.assertEqual(ast["left"]["kind"], "power_bin")

    def test_multiplicative_operators_share_precedence_left_associative(self) -> None:
        ast = parse_expr("20//5%3")
        self.assertEqual(ast["kind"], "modulo_bin")
        self.assertEqual(ast["left"]["kind"], "int_div_bin")

    def test_modulo_has_higher_precedence_than_concat(self) -> None:
        ast = parse_expr('"x"+8%3')
        self.assertEqual(ast["kind"], "concat_bin")
        self.assertEqual(ast["right"]["kind"], "modulo_bin")

    def test_parse_list_literal(self) -> None:
        ast = parse_expr("[1,2,3]")
        self.assertEqual(ast["kind"], "list")
        self.assertEqual(len(ast["items"]), 3)

    def test_parse_object_literal(self) -> None:
        ast = parse_expr('{"name":"Luis","age":1}')
        self.assertEqual(ast["kind"], "object")
        self.assertEqual(len(ast["entries"]), 2)
        self.assertEqual(ast["entries"][0]["key"], "name")

    def test_parse_trailing_commas_in_fn_call_list_and_object(self) -> None:
        fn_ast = parse_expr("fn(a,b,) => a")
        self.assertEqual(fn_ast["kind"], "fn")
        self.assertEqual(fn_ast["params"], ["a", "b"])

        call_ast = parse_expr("sum(1,2,)")
        self.assertEqual(call_ast["kind"], "call")
        self.assertEqual(len(call_ast["args"]), 2)

        list_ast = parse_expr("[1,2,]")
        self.assertEqual(list_ast["kind"], "list")
        self.assertEqual(len(list_ast["items"]), 2)

        object_ast = parse_expr('{"a":1,"b":2,}')
        self.assertEqual(object_ast["kind"], "object")
        self.assertEqual(len(object_ast["entries"]), 2)

    def test_parse_rejects_sparse_comma_sequences(self) -> None:
        with self.assertRaises(ParseError):
            parse_expr("sum(1,,2)")
        with self.assertRaises(ParseError):
            parse_expr("fn(a,,b)=>a")
        with self.assertRaises(ParseError):
            parse_expr("[1,,2]")
        with self.assertRaises(ParseError):
            parse_expr('{"a":1,,"b":2}')

    def test_parse_rejects_object_entry_without_colon(self) -> None:
        with self.assertRaises(ParseError):
            parse_expr('{"a" 1}')

    def test_parse_index_access(self) -> None:
        ast = parse_expr("arr[1]")
        self.assertEqual(ast["kind"], "index")
        self.assertEqual(ast["target"]["kind"], "ident")
        self.assertEqual(ast["index"]["kind"], "number")

    def test_parse_member_access(self) -> None:
        ast = parse_expr("user.profile")
        self.assertEqual(ast["kind"], "member_access")
        self.assertEqual(ast["target"]["kind"], "ident")
        self.assertEqual(ast["member"], "profile")

    def test_parse_optional_member_access(self) -> None:
        ast = parse_expr("user?.profile")
        self.assertEqual(ast["kind"], "optional_member_access")
        self.assertEqual(ast["target"]["kind"], "ident")
        self.assertEqual(ast["member"], "profile")

    def test_parse_optional_index_access(self) -> None:
        ast = parse_expr('user?["profile"]')
        self.assertEqual(ast["kind"], "optional_index_access")
        self.assertEqual(ast["target"]["kind"], "ident")
        self.assertEqual(ast["index"]["kind"], "string")

    def test_parse_optional_call_access(self) -> None:
        ast = parse_expr("handler?(1,2)")
        self.assertEqual(ast["kind"], "optional_call")
        self.assertEqual(ast["target"]["kind"], "ident")
        self.assertEqual(len(ast["args"]), 2)

    def test_optional_index_access_binds_tighter_than_coalesce(self) -> None:
        ast = parse_expr('user?["name"] ?? fallback')
        self.assertEqual(ast["kind"], "coalesce_bin")
        self.assertEqual(ast["left"]["kind"], "optional_index_access")

    def test_optional_call_binds_tighter_than_coalesce(self) -> None:
        ast = parse_expr("handler?(1) ?? fallback")
        self.assertEqual(ast["kind"], "coalesce_bin")
        self.assertEqual(ast["left"]["kind"], "optional_call")

    def test_member_access_binds_tighter_than_unary_and_coalesce(self) -> None:
        ast = parse_expr("a.b ?? c")
        self.assertEqual(ast["kind"], "coalesce_bin")
        self.assertEqual(ast["left"]["kind"], "member_access")

    def test_parser_emits_deterministic_source_spans(self) -> None:
        ast = parse_expr("let x = [1,2] in x[0]")
        self.assertEqual(ast["span"], {"start": 0, "end": 21})
        self.assertEqual(ast["value"]["span"], {"start": 8, "end": 13})
        self.assertEqual(ast["body"]["span"], {"start": 17, "end": 21})


if __name__ == "__main__":
    unittest.main()
