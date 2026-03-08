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
        "list": {
            "required": ["kind", "span", "items"],
            "fields": {"kind": "literal:list", "span": "span", "items": "expr[]"},
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
            "required": ["kind", "span", "left", "right"],
            "fields": {"kind": "literal:concat_bin", "span": "span", "left": "expr", "right": "expr"},
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
    "list:kind,span,items",
    "unary_neg:kind,span,operand",
    "unary_not:kind,span,operand",
    "concat_bin:kind,span,left,right",
    "logical_bin:kind,span,op,left,right",
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

    if kind == "list":
        _require_kind(node, "list")
        _require_span(node, "list")
        items = node.get("items")
        if not isinstance(items, list):
            raise ASTValidationError("list.items must be a list")
        for item in items:
            _validate_expr(item)
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
