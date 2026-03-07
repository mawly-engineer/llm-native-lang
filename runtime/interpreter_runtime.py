"""Deterministic core AST evaluator with lexical scope bindings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from runtime.ast_contract import ASTValidationError, validate_ast


class EvalError(ValueError):
    """Structured runtime error with machine-readable fields."""

    def __init__(self, code: str, message: str, location: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.location = location or {}
        super().__init__(self.__str__())

    def __str__(self) -> str:
        location_suffix = f" location={self.location}" if self.location else ""
        return f"[{self.code}] {self.message}{location_suffix}"


@dataclass(frozen=True)
class Closure:
    params: tuple[str, ...]
    body: dict[str, Any]
    env: "Env"


class Env:
    def __init__(self, parent: "Env | None" = None) -> None:
        self.parent = parent
        self.bindings: dict[str, Any] = {}

    def child(self) -> "Env":
        return Env(parent=self)

    def set(self, name: str, value: Any) -> None:
        self.bindings[name] = value

    def get(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise EvalError(
            code="E_RT_UNKNOWN_IDENTIFIER",
            message=f"unknown identifier '{name}'",
            location={"phase": "env_lookup", "identifier": name},
        )


def eval_expr(node: dict[str, Any], env: Mapping[str, Any] | None = None) -> Any:
    try:
        validate_ast(node)
    except ASTValidationError as exc:
        raise EvalError(
            code="E_RT_AST_INVALID",
            message=str(exc),
            location={"phase": "ast_validation"},
        ) from exc

    root = Env()
    root.set("false", False)
    root.set("true", True)
    if env:
        for key in sorted(env.keys()):
            root.set(key, env[key])

    return _eval(node, root)


def _eval(node: dict[str, Any], env: Env) -> Any:
    kind = node["kind"]

    if kind == "number":
        return node["value"]

    if kind == "ident":
        return env.get(node["name"])

    if kind == "unary_neg":
        value = _eval(node["operand"], env)
        if not isinstance(value, int):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"unary negation expects int, got {type(value).__name__}",
                location={"node_kind": "unary_neg"},
            )
        return -value

    if kind == "logical_bin":
        op = node["op"]
        if op not in {"and", "or"}:
            raise EvalError(
                code="E_RT_UNSUPPORTED_KIND",
                message=f"unsupported logical op '{op}'",
                location={"node_kind": "logical_bin", "op": op},
            )
        left = _eval(node["left"], env)
        if not isinstance(left, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"logical {op} expects bool left operand, got {type(left).__name__}",
                location={"node_kind": "logical_bin", "op": op, "side": "left"},
            )
        if op == "and":
            if not left:
                return False
            right = _eval(node["right"], env)
            if not isinstance(right, bool):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"logical and expects bool right operand, got {type(right).__name__}",
                    location={"node_kind": "logical_bin", "op": op, "side": "right"},
                )
            return right

        if left:
            return True
        right = _eval(node["right"], env)
        if not isinstance(right, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"logical or expects bool right operand, got {type(right).__name__}",
                location={"node_kind": "logical_bin", "op": op, "side": "right"},
            )
        return right

    if kind == "let":
        value = _eval(node["value"], env)
        scoped = env.child()
        scoped.set(node["name"], value)
        return _eval(node["body"], scoped)

    if kind == "if":
        cond = _eval(node["cond"], env)
        branch = node["then"] if bool(cond) else node["else"]
        return _eval(branch, env)

    if kind == "fn":
        return Closure(params=tuple(node["params"]), body=node["body"], env=env)

    if kind == "call":
        callee_name = node["callee"]
        callee = env.get(callee_name)
        args = [_eval(arg, env) for arg in node["args"]]

        if isinstance(callee, Closure):
            if len(args) != len(callee.params):
                raise EvalError(
                    code="E_RT_ARITY_MISMATCH",
                    message=(
                        f"arity mismatch for '{callee_name}': "
                        f"expected {len(callee.params)}, got {len(args)}"
                    ),
                    location={"node_kind": "call", "callee": callee_name},
                )
            call_env = callee.env.child()
            for param, value in zip(callee.params, args):
                call_env.set(param, value)
            return _eval(callee.body, call_env)

        if callable(callee):
            fn = callee
            try:
                return fn(*args)
            except TypeError as exc:
                raise EvalError(
                    code="E_RT_HOST_CALL_ARITY",
                    message=str(exc),
                    location={"node_kind": "call", "callee": callee_name},
                ) from exc

        raise EvalError(
            code="E_RT_NOT_CALLABLE",
            message=f"'{callee_name}' is not callable",
            location={"node_kind": "call", "callee": callee_name},
        )

    raise EvalError(
        code="E_RT_UNSUPPORTED_KIND",
        message=f"unsupported kind '{kind}'",
        location={"node_kind": kind},
    )
