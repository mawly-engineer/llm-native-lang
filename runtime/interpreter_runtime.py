"""Deterministic core AST evaluator with lexical scope bindings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

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


@dataclass
class EvalContext:
    fuel_remaining: int | None = None

    def consume_step(self, node_kind: str) -> None:
        if self.fuel_remaining is None:
            return
        if self.fuel_remaining <= 0:
            raise EvalError(
                code="E_RT_FUEL_EXHAUSTED",
                message="evaluation halted: deterministic fuel budget exhausted",
                location={
                    "phase": "step_budget",
                    "node_kind": node_kind,
                    "halt_reason": "fuel_exhausted",
                },
            )
        self.fuel_remaining -= 1


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


def eval_expr(
    node: dict[str, Any],
    env: Mapping[str, Any] | None = None,
    fuel_limit: int | None = None,
) -> Any:
    try:
        validate_ast(node)
    except ASTValidationError as exc:
        raise EvalError(
            code="E_RT_AST_INVALID",
            message=str(exc),
            location={"phase": "ast_validation"},
        ) from exc

    if fuel_limit is not None and (not isinstance(fuel_limit, int) or fuel_limit < 0):
        raise EvalError(
            code="E_RT_FUEL_CONFIG",
            message=f"fuel_limit must be a non-negative int, got {fuel_limit!r}",
            location={"phase": "step_budget", "field": "fuel_limit"},
        )

    root = Env()
    root.set("false", False)
    root.set("true", True)
    if env:
        for key in sorted(env.keys()):
            root.set(key, env[key])

    context = EvalContext(fuel_remaining=fuel_limit)
    return _eval(node, root, context)


def _eval(node: dict[str, Any], env: Env, context: EvalContext) -> Any:
    kind = node["kind"]
    context.consume_step(kind)

    if kind == "number":
        return node["value"]

    if kind == "bool":
        return node["value"]

    if kind == "string":
        return node["value"]

    if kind == "null":
        return None

    if kind == "list":
        return [_eval(item, env, context) for item in node["items"]]

    if kind == "index":
        target = _eval(node["target"], env, context)
        index = _eval(node["index"], env, context)

        if not isinstance(target, list):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"index target must be list, got {type(target).__name__}",
                location={"node_kind": "index", "field": "target"},
            )
        if not isinstance(index, int) or isinstance(index, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"index expression must evaluate to int, got {type(index).__name__}",
                location={"node_kind": "index", "field": "index"},
            )
        if index < 0 or index >= len(target):
            raise EvalError(
                code="E_RT_INDEX_OUT_OF_RANGE",
                message=f"list index out of range: {index} (size={len(target)})",
                location={"node_kind": "index", "index": index, "size": len(target)},
            )
        return target[index]

    if kind == "ident":
        return env.get(node["name"])

    if kind == "unary_neg":
        value = _eval(node["operand"], env, context)
        if not isinstance(value, int) or isinstance(value, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"unary negation expects int, got {type(value).__name__}",
                location={"node_kind": "unary_neg"},
            )
        return -value

    if kind == "unary_not":
        value = _eval(node["operand"], env, context)
        if not isinstance(value, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"unary logical-not expects bool, got {type(value).__name__}",
                location={"node_kind": "unary_not"},
            )
        return not value

    if kind == "concat_bin":
        left = _eval(node["left"], env, context)
        right = _eval(node["right"], env, context)
        if not isinstance(left, str):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"string concatenation expects string left operand, got {type(left).__name__}",
                location={"node_kind": "concat_bin", "side": "left"},
            )
        if not isinstance(right, str):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"string concatenation expects string right operand, got {type(right).__name__}",
                location={"node_kind": "concat_bin", "side": "right"},
            )
        return left + right

    if kind == "modulo_bin":
        left = _eval(node["left"], env, context)
        right = _eval(node["right"], env, context)
        if not isinstance(left, int) or isinstance(left, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"modulo expects int left operand, got {type(left).__name__}",
                location={"node_kind": "modulo_bin", "side": "left"},
            )
        if not isinstance(right, int) or isinstance(right, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"modulo expects int right operand, got {type(right).__name__}",
                location={"node_kind": "modulo_bin", "side": "right"},
            )
        if right == 0:
            raise EvalError(
                code="E_RT_ZERO_DIVISION",
                message="modulo by zero",
                location={"node_kind": "modulo_bin", "side": "right"},
            )
        return left % right

    if kind == "int_div_bin":
        left = _eval(node["left"], env, context)
        right = _eval(node["right"], env, context)
        if not isinstance(left, int) or isinstance(left, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"integer division expects int left operand, got {type(left).__name__}",
                location={"node_kind": "int_div_bin", "side": "left"},
            )
        if not isinstance(right, int) or isinstance(right, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"integer division expects int right operand, got {type(right).__name__}",
                location={"node_kind": "int_div_bin", "side": "right"},
            )
        if right == 0:
            raise EvalError(
                code="E_RT_ZERO_DIVISION",
                message="integer division by zero",
                location={"node_kind": "int_div_bin", "side": "right"},
            )
        return left // right

    if kind == "logical_bin":
        op = node["op"]
        if op not in {"and", "or"}:
            raise EvalError(
                code="E_RT_UNSUPPORTED_KIND",
                message=f"unsupported logical op '{op}'",
                location={"node_kind": "logical_bin", "op": op},
            )
        left = _eval(node["left"], env, context)
        if not isinstance(left, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"logical {op} expects bool left operand, got {type(left).__name__}",
                location={"node_kind": "logical_bin", "op": op, "side": "left"},
            )
        if op == "and":
            if not left:
                return False
            right = _eval(node["right"], env, context)
            if not isinstance(right, bool):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"logical and expects bool right operand, got {type(right).__name__}",
                    location={"node_kind": "logical_bin", "op": op, "side": "right"},
                )
            return right

        if left:
            return True
        right = _eval(node["right"], env, context)
        if not isinstance(right, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"logical or expects bool right operand, got {type(right).__name__}",
                location={"node_kind": "logical_bin", "op": op, "side": "right"},
            )
        return right

    if kind == "compare_bin":
        op = node["op"]
        if op not in {"==", "!=", "<", "<=", ">", ">="}:
            raise EvalError(
                code="E_RT_UNSUPPORTED_KIND",
                message=f"unsupported compare op '{op}'",
                location={"node_kind": "compare_bin", "op": op},
            )
        left = _eval(node["left"], env, context)
        right = _eval(node["right"], env, context)

        if op in {"<", "<=", ">", ">="}:
            if not isinstance(left, int) or isinstance(left, bool):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"comparison {op} expects int left operand, got {type(left).__name__}",
                    location={"node_kind": "compare_bin", "op": op, "side": "left"},
                )
            if not isinstance(right, int) or isinstance(right, bool):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"comparison {op} expects int right operand, got {type(right).__name__}",
                    location={"node_kind": "compare_bin", "op": op, "side": "right"},
                )
            return {
                "<": left < right,
                "<=": left <= right,
                ">": left > right,
                ">=": left >= right,
            }[op]

        allowed_types = (int, bool, str, type(None))
        if not isinstance(left, allowed_types):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"equality {op} unsupported for left operand type {type(left).__name__}",
                location={"node_kind": "compare_bin", "op": op, "side": "left"},
            )
        if type(left) is not type(right):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"equality {op} expects same operand types, got {type(left).__name__} and {type(right).__name__}",
                location={"node_kind": "compare_bin", "op": op},
            )
        return (left == right) if op == "==" else (left != right)

    if kind == "let":
        value = _eval(node["value"], env, context)
        scoped = env.child()
        scoped.set(node["name"], value)
        return _eval(node["body"], scoped, context)

    if kind == "if":
        cond = _eval(node["cond"], env, context)
        branch = node["then"] if bool(cond) else node["else"]
        return _eval(branch, env, context)

    if kind == "fn":
        return Closure(params=tuple(node["params"]), body=node["body"], env=env)

    if kind == "call":
        callee_name = node["callee"]
        callee = env.get(callee_name)
        args = [_eval(arg, env, context) for arg in node["args"]]

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
            return _eval(callee.body, call_env, context)

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
