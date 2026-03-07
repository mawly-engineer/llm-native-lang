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
            "required": ["kind", "name", "value", "body"],
            "fields": {
                "kind": "literal:let",
                "name": "ident",
                "value": "expr",
                "body": "expr",
            },
        },
        "if": {
            "required": ["kind", "cond", "then", "else"],
            "fields": {
                "kind": "literal:if",
                "cond": "expr",
                "then": "expr",
                "else": "expr",
            },
        },
        "fn": {
            "required": ["kind", "params", "body"],
            "fields": {
                "kind": "literal:fn",
                "params": "ident[]",
                "body": "expr",
            },
        },
        "call": {
            "required": ["kind", "callee", "args"],
            "fields": {
                "kind": "literal:call",
                "callee": "ident",
                "args": "expr[]",
            },
        },
        "ident": {
            "required": ["kind", "name"],
            "fields": {
                "kind": "literal:ident",
                "name": "ident",
            },
        },
        "number": {
            "required": ["kind", "value"],
            "fields": {
                "kind": "literal:number",
                "value": "int",
            },
        },
    },
}


_AST_FINGERPRINT_SOURCE = [
    "let:kind,name,value,body",
    "if:kind,cond,then,else",
    "fn:kind,params,body",
    "call:kind,callee,args",
    "ident:kind,name",
    "number:kind,value",
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


def validate_ast(node: Any) -> None:
    _validate_expr(node)


def _validate_expr(node: Any) -> None:
    if not isinstance(node, dict):
        raise ASTValidationError("expr node must be an object")

    kind = node.get("kind")
    if kind == "let":
        _require_kind(node, "let")
        _require_ident(node.get("name"), "let.name")
        _validate_expr(node.get("value"))
        _validate_expr(node.get("body"))
        return

    if kind == "if":
        _require_kind(node, "if")
        _validate_expr(node.get("cond"))
        _validate_expr(node.get("then"))
        _validate_expr(node.get("else"))
        return

    if kind == "fn":
        _require_kind(node, "fn")
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
        _require_ident(node.get("callee"), "call.callee")
        args = node.get("args")
        if not isinstance(args, list):
            raise ASTValidationError("call.args must be a list")
        for arg in args:
            _validate_expr(arg)
        return

    if kind == "ident":
        _require_kind(node, "ident")
        _require_ident(node.get("name"), "ident.name")
        return

    if kind == "number":
        _require_kind(node, "number")
        if not isinstance(node.get("value"), int):
            raise ASTValidationError("number.value must be an int")
        return

    raise ASTValidationError(f"unsupported expr kind: {kind}")
