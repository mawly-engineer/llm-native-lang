"""AST schema contract and invariants for llm-native-lang core expressions."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

AST_SCHEMA_VERSION = "1.0.0"

AST_SCHEMA = {
    "version": AST_SCHEMA_VERSION,
    "root": "expr",
    "nodes": {
        "let": {
            "required": ["kind", "span", "name", "value", "body"],
            "fields": {"kind": "literal:let", "span": "span", "name": "ident", "value": "expr", "body": "expr"},
        },
        "if": {
            "required": ["kind", "span", "cond", "then", "else"],
            "fields": {"kind": "literal:if", "span": "span", "cond": "expr", "then": "expr", "else": "expr"},
        },
        "fn": {
            "required": ["kind", "span", "params", "body"],
            "fields": {"kind": "literal:fn", "span": "span", "params": "ident[]", "body": "expr"},
        },
        "call": {
            "required": ["kind", "span", "callee", "args"],
            "fields": {"kind": "literal:call", "span": "span", "callee": "ident", "args": "expr[]"},
        },
        "index": {
            "required": ["kind", "span", "target", "index"],
            "fields": {"kind": "literal:index", "span": "span", "target": "expr", "index": "expr"},
        },
        "optional_call": {
            "required": ["kind", "span", "target", "args"],
            "fields": {"kind": "literal:optional_call", "span": "span", "target": "expr", "args": "expr[]"},
        },
        "member_access": {
            "required": ["kind", "span", "target", "member"],
            "fields": {"kind": "literal:member_access", "span": "span", "target": "expr", "member": "ident"},
        },
        "optional_index_access": {
            "required": ["kind", "span", "target", "index"],
            "fields": {"kind": "literal:optional_index_access", "span": "span", "target": "expr", "index": "expr"},
        },
        "optional_member_access": {
            "required": ["kind", "span", "target", "member"],
            "fields": {"kind": "literal:optional_member_access", "span": "span", "target": "expr", "member": "ident"},
        },
        "list": {
            "required": ["kind", "span", "items"],
            "fields": {"kind": "literal:list", "span": "span", "items": "expr[]"},
        },
        "object": {
            "required": ["kind", "span", "entries"],
            "fields": {"kind": "literal:object", "span": "span", "entries": "object_entry[]"},
        },
        "unary_pos": {
            "required": ["kind", "span", "operand"],
            "fields": {"kind": "literal:unary_pos", "span": "span", "operand": "expr"},
        },
        "unary_neg": {
            "required": ["kind", "span", "operand"],
            "fields": {"kind": "literal:unary_neg", "span": "span", "operand": "expr"},
        },
        "unary_not": {
            "required": ["kind", "span", "operand"],
            "fields": {"kind": "literal:unary_not", "span": "span", "operand": "expr"},
        },
        "concat_bin": {
            "required": ["kind", "span", "op", "left", "right"],
            "fields": {
                "kind": "literal:concat_bin",
                "span": "span",
                "op": "literal:+|-",
                "left": "expr",
                "right": "expr",
            },
        },
        "mul_bin": {
            "required": ["kind", "span", "left", "right"],
            "fields": {"kind": "literal:mul_bin", "span": "span", "left": "expr", "right": "expr"},
        },
        "modulo_bin": {
            "required": ["kind", "span", "left", "right"],
            "fields": {"kind": "literal:modulo_bin", "span": "span", "left": "expr", "right": "expr"},
        },
        "int_div_bin": {
            "required": ["kind", "span", "left", "right"],
            "fields": {"kind": "literal:int_div_bin", "span": "span", "left": "expr", "right": "expr"},
        },
        "power_bin": {
            "required": ["kind", "span", "left", "right"],
            "fields": {"kind": "literal:power_bin", "span": "span", "left": "expr", "right": "expr"},
        },
        "coalesce_bin": {
            "required": ["kind", "span", "left", "right"],
            "fields": {"kind": "literal:coalesce_bin", "span": "span", "left": "expr", "right": "expr"},
        },
        "logical_bin": {
            "required": ["kind", "span", "op", "left", "right"],
            "fields": {
                "kind": "literal:logical_bin",
                "span": "span",
                "op": "literal:and|or",
                "left": "expr",
                "right": "expr",
            },
        },
        "compare_bin": {
            "required": ["kind", "span", "op", "left", "right"],
            "fields": {
                "kind": "literal:compare_bin",
                "span": "span",
                "op": "literal:==|!=|<|<=|>|>=",
                "left": "expr",
                "right": "expr",
            },
        },
        "ident": {
            "required": ["kind", "span", "name"],
            "fields": {"kind": "literal:ident", "span": "span", "name": "ident"},
        },
        "number": {
            "required": ["kind", "span", "value"],
            "fields": {"kind": "literal:number", "span": "span", "value": "int"},
        },
        "bool": {
            "required": ["kind", "span", "value"],
            "fields": {"kind": "literal:bool", "span": "span", "value": "bool"},
        },
        "null": {
            "required": ["kind", "span", "value"],
            "fields": {"kind": "literal:null", "span": "span", "value": "null"},
        },
        "string": {
            "required": ["kind", "span", "value"],
            "fields": {"kind": "literal:string", "span": "span", "value": "string"},
        },
    },
}


_AST_FINGERPRINT_SOURCE = [
    "let:kind,span,name,value,body",
    "if:kind,span,cond,then,else",
    "fn:kind,span,params,body",
    "call:kind,span,callee,args",
    "index:kind,span,target,index",
    "optional_call:kind,span,target,args",
    "member_access:kind,span,target,member",
    "optional_index_access:kind,span,target,index",
    "optional_member_access:kind,span,target,member",
    "list:kind,span,items",
    "object:kind,span,entries",
    "unary_pos:kind,span,operand",
    "unary_neg:kind,span,operand",
    "unary_not:kind,span,operand",
    "concat_bin:kind,span,op,left,right",
    "mul_bin:kind,span,left,right",
    "modulo_bin:kind,span,left,right",
    "int_div_bin:kind,span,left,right",
    "power_bin:kind,span,left,right",
    "coalesce_bin:kind,span,left,right",
    "logical_bin:kind,span,op,left,right",
    "compare_bin:kind,span,op,left,right",
    "ident:kind,span,name",
    "number:kind,span,value",
    "bool:kind,span,value",
    "null:kind,span,value",
    "string:kind,span,value",
]

AST_SCHEMA_FINGERPRINT = sha256("\n".join(_AST_FINGERPRINT_SOURCE).encode("utf-8")).hexdigest()


class ASTValidationError(ValueError):
    """Raised when an AST node violates schema shape or invariants."""


def _require_ident(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ASTValidationError(f"{field} must be a non-empty identifier string")
    return value


def _require_kind(node: dict[str, Any], expected: str) -> None:
    actual = node.get("kind")
    if actual != expected:
        raise ASTValidationError(f"expected kind={expected}, got {actual}")


def _require_span(node: dict[str, Any], label: str) -> None:
    span = node.get("span")
    if not isinstance(span, dict):
        raise ASTValidationError(f"{label}.span must be an object")
    start = span.get("start")
    end = span.get("end")
    if not isinstance(start, int) or not isinstance(end, int):
        raise ASTValidationError(f"{label}.span.start and {label}.span.end must be ints")
    if start < 0 or end < start:
        raise ASTValidationError(f"{label}.span must satisfy 0 <= start <= end")


def validate_ast(node: Any) -> None:
    _validate_expr(node)


def _validate_expr(node: Any) -> None:
    if not isinstance(node, dict):
        raise ASTValidationError("expr node must be an object")

    kind = node.get("kind")
    if kind == "let":
        _require_kind(node, "let")
        _require_span(node, "let")
        _require_ident(node.get("name"), "let.name")
        _validate_expr(node.get("value"))
        _validate_expr(node.get("body"))
        return

    if kind == "if":
        _require_kind(node, "if")
        _require_span(node, "if")
        _validate_expr(node.get("cond"))
        _validate_expr(node.get("then"))
        _validate_expr(node.get("else"))
        return

    if kind == "fn":
        _require_kind(node, "fn")
        _require_span(node, "fn")
        params = node.get("params")
        if not isinstance(params, list):
            raise ASTValidationError("fn.params must be a list")

        seen = set()
        for idx, param in enumerate(params):
            ident = _require_ident(param, f"fn.params[{idx}]")
            if ident in seen:
                raise ASTValidationError(f"fn.params contains duplicate identifier: {ident}")
            seen.add(ident)

        _validate_expr(node.get("body"))
        return

    if kind == "call":
        _require_kind(node, "call")
        _require_span(node, "call")
        _require_ident(node.get("callee"), "call.callee")
        args = node.get("args")
        if not isinstance(args, list):
            raise ASTValidationError("call.args must be a list")
        for arg in args:
            _validate_expr(arg)
        return

    if kind == "index":
        _require_kind(node, "index")
        _require_span(node, "index")
        _validate_expr(node.get("target"))
        _validate_expr(node.get("index"))
        return

    if kind == "optional_call":
        _require_kind(node, "optional_call")
        _require_span(node, "optional_call")
        _validate_expr(node.get("target"))
        args = node.get("args")
        if not isinstance(args, list):
            raise ASTValidationError("optional_call.args must be a list")
        for arg in args:
            _validate_expr(arg)
        return

    if kind == "member_access":
        _require_kind(node, "member_access")
        _require_span(node, "member_access")
        _validate_expr(node.get("target"))
        _require_ident(node.get("member"), "member_access.member")
        return

    if kind == "optional_index_access":
        _require_kind(node, "optional_index_access")
        _require_span(node, "optional_index_access")
        _validate_expr(node.get("target"))
        _validate_expr(node.get("index"))
        return

    if kind == "optional_member_access":
        _require_kind(node, "optional_member_access")
        _require_span(node, "optional_member_access")
        _validate_expr(node.get("target"))
        _require_ident(node.get("member"), "optional_member_access.member")
        return

    if kind == "list":
        _require_kind(node, "list")
        _require_span(node, "list")
        items = node.get("items")
        if not isinstance(items, list):
            raise ASTValidationError("list.items must be a list")
        for item in items:
            _validate_expr(item)
        return

    if kind == "object":
        _require_kind(node, "object")
        _require_span(node, "object")
        entries = node.get("entries")
        if not isinstance(entries, list):
            raise ASTValidationError("object.entries must be a list")
        seen: set[str] = set()
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ASTValidationError(f"object.entries[{idx}] must be an object")
            key = entry.get("key")
            if not isinstance(key, str):
                raise ASTValidationError(f"object.entries[{idx}].key must be a string")
            if key in seen:
                raise ASTValidationError(f"object.entries[{idx}].key duplicates key: {key}")
            seen.add(key)
            _validate_expr(entry.get("value"))
        return

    if kind == "unary_pos":
        _require_kind(node, "unary_pos")
        _require_span(node, "unary_pos")
        _validate_expr(node.get("operand"))
        return

    if kind == "unary_neg":
        _require_kind(node, "unary_neg")
        _require_span(node, "unary_neg")
        _validate_expr(node.get("operand"))
        return

    if kind == "unary_not":
        _require_kind(node, "unary_not")
        _require_span(node, "unary_not")
        _validate_expr(node.get("operand"))
        return

    if kind == "concat_bin":
        _require_kind(node, "concat_bin")
        _require_span(node, "concat_bin")
        op = node.get("op")
        if op not in {"+", "-"}:
            raise ASTValidationError("concat_bin.op must be '+' or '-'")
        _validate_expr(node.get("left"))
        _validate_expr(node.get("right"))
        return

    if kind == "mul_bin":
        _require_kind(node, "mul_bin")
        _require_span(node, "mul_bin")
        _validate_expr(node.get("left"))
        _validate_expr(node.get("right"))
        return

    if kind == "modulo_bin":
        _require_kind(node, "modulo_bin")
        _require_span(node, "modulo_bin")
        _validate_expr(node.get("left"))
        _validate_expr(node.get("right"))
        return

    if kind == "int_div_bin":
        _require_kind(node, "int_div_bin")
        _require_span(node, "int_div_bin")
        _validate_expr(node.get("left"))
        _validate_expr(node.get("right"))
        return

    if kind == "power_bin":
        _require_kind(node, "power_bin")
        _require_span(node, "power_bin")
        _validate_expr(node.get("left"))
        _validate_expr(node.get("right"))
        return

    if kind == "coalesce_bin":
        _require_kind(node, "coalesce_bin")
        _require_span(node, "coalesce_bin")
        _validate_expr(node.get("left"))
        _validate_expr(node.get("right"))
        return

    if kind == "logical_bin":
        _require_kind(node, "logical_bin")
        _require_span(node, "logical_bin")
        op = node.get("op")
        if op not in {"and", "or"}:
            raise ASTValidationError("logical_bin.op must be 'and' or 'or'")
        _validate_expr(node.get("left"))
        _validate_expr(node.get("right"))
        return

    if kind == "compare_bin":
        _require_kind(node, "compare_bin")
        _require_span(node, "compare_bin")
        op = node.get("op")
        if op not in {"==", "!=", "<", "<=", ">", ">="}:
            raise ASTValidationError("compare_bin.op must be one of '==', '!=', '<', '<=', '>', '>='")
        _validate_expr(node.get("left"))
        _validate_expr(node.get("right"))
        return

    if kind == "ident":
        _require_kind(node, "ident")
        _require_span(node, "ident")
        _require_ident(node.get("name"), "ident.name")
        return

    if kind == "number":
        _require_kind(node, "number")
        _require_span(node, "number")
        if not isinstance(node.get("value"), int):
            raise ASTValidationError("number.value must be an int")
        return

    if kind == "bool":
        _require_kind(node, "bool")
        _require_span(node, "bool")
        if not isinstance(node.get("value"), bool):
            raise ASTValidationError("bool.value must be a bool")
        return

    if kind == "null":
        _require_kind(node, "null")
        _require_span(node, "null")
        if node.get("value") is not None:
            raise ASTValidationError("null.value must be None")
        return

    if kind == "string":
        _require_kind(node, "string")
        _require_span(node, "string")
        if not isinstance(node.get("value"), str):
            raise ASTValidationError("string.value must be a string")
        return

    raise ASTValidationError(f"unsupported expr kind: {kind}")
