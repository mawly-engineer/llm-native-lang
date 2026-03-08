"""Deterministic core AST evaluator with lexical scope bindings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from collections.abc import Mapping as MappingABC

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
    trace_counter: int = 0
    trace_ids: list[str] | None = None

    def next_trace_id(self, node_kind: str) -> str:
        self.trace_counter += 1
        return f"n-{self.trace_counter:06d}:{node_kind}"

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


def _prepare_eval(node: dict[str, Any], env: Mapping[str, Any] | None, fuel_limit: int | None) -> tuple[Env, EvalContext]:
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

    return root, EvalContext(fuel_remaining=fuel_limit)


def eval_expr(
    node: dict[str, Any],
    env: Mapping[str, Any] | None = None,
    fuel_limit: int | None = None,
) -> Any:
    root, context = _prepare_eval(node=node, env=env, fuel_limit=fuel_limit)
    return _eval(node, root, context)


def eval_expr_with_trace(
    node: dict[str, Any],
    env: Mapping[str, Any] | None = None,
    fuel_limit: int | None = None,
) -> tuple[Any, list[str]]:
    root, context = _prepare_eval(node=node, env=env, fuel_limit=fuel_limit)
    context.trace_ids = []
    result = _eval(node, root, context)
    return result, context.trace_ids


def _eval(node: dict[str, Any], env: Env, context: EvalContext) -> Any:
    kind = node["kind"]
    trace_id = context.next_trace_id(kind)
    if context.trace_ids is not None:
        context.trace_ids.append(trace_id)
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

    if kind == "object":
        out: dict[str, Any] = {}
        for entry in node["entries"]:
            out[entry["key"]] = _eval(entry["value"], env, context)
        return out

    if kind == "index":
        target = _eval(node["target"], env, context)
        index = _eval(node["index"], env, context)

        if isinstance(target, list):
            if not isinstance(index, int) or isinstance(index, bool):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"list index expression must evaluate to int, got {type(index).__name__}",
                    location={"node_kind": "index", "field": "index", "target_kind": "list"},
                )
            if index < 0 or index >= len(target):
                raise EvalError(
                    code="E_RT_INDEX_OUT_OF_RANGE",
                    message=f"list index out of range: {index} (size={len(target)})",
                    location={"node_kind": "index", "index": index, "size": len(target), "target_kind": "list"},
                )
            return target[index]

        if isinstance(target, MappingABC):
            if not isinstance(index, str):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"object index expression must evaluate to string, got {type(index).__name__}",
                    location={"node_kind": "index", "field": "index", "target_kind": "object"},
                )
            if index not in target:
                raise EvalError(
                    code="E_RT_MISSING_MEMBER",
                    message=f"object member not found: {index}",
                    location={"node_kind": "index", "member": index, "target_kind": "object"},
                )
            return target[index]

        raise EvalError(
            code="E_RT_TYPE",
            message=f"index target must be list or object, got {type(target).__name__}",
            location={"node_kind": "index", "field": "target"},
        )

    if kind == "member_access":
        target = _eval(node["target"], env, context)
        member = node["member"]

        if not isinstance(target, MappingABC):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"member access target must be object, got {type(target).__name__}",
                location={"node_kind": "member_access", "field": "target"},
            )
        if member not in target:
            raise EvalError(
                code="E_RT_MISSING_MEMBER",
                message=f"object member not found: {member}",
                location={"node_kind": "member_access", "member": member},
            )
        return target[member]

    if kind == "optional_index_access":
        target = _eval(node["target"], env, context)

        if target is None:
            return None

        index = _eval(node["index"], env, context)

        if isinstance(target, list):
            if not isinstance(index, int) or isinstance(index, bool):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"optional index list index expression must evaluate to int, got {type(index).__name__}",
                    location={"node_kind": "optional_index_access", "field": "index", "target_kind": "list"},
                )
            if index < 0 or index >= len(target):
                raise EvalError(
                    code="E_RT_INDEX_OUT_OF_RANGE",
                    message=f"optional index list index out of range: {index} (size={len(target)})",
                    location={"node_kind": "optional_index_access", "index": index, "size": len(target), "target_kind": "list"},
                )
            return target[index]

        if isinstance(target, MappingABC):
            if not isinstance(index, str):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"optional index object key expression must evaluate to string, got {type(index).__name__}",
                    location={"node_kind": "optional_index_access", "field": "index", "target_kind": "object"},
                )
            if index not in target:
                raise EvalError(
                    code="E_RT_MISSING_MEMBER",
                    message=f"object member not found: {index}",
                    location={"node_kind": "optional_index_access", "member": index, "target_kind": "object"},
                )
            return target[index]

        raise EvalError(
            code="E_RT_TYPE",
            message=f"optional index target must be list|object|null, got {type(target).__name__}",
            location={"node_kind": "optional_index_access", "field": "target"},
        )

    if kind == "optional_member_access":
        target = _eval(node["target"], env, context)
        member = node["member"]

        if target is None:
            return None
        if not isinstance(target, MappingABC):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"optional member access target must be object|null, got {type(target).__name__}",
                location={"node_kind": "optional_member_access", "field": "target"},
            )
        if member not in target:
            raise EvalError(
                code="E_RT_MISSING_MEMBER",
                message=f"object member not found: {member}",
                location={"node_kind": "optional_member_access", "member": member},
            )
        return target[member]

    if kind == "optional_call":
        target = _eval(node["target"], env, context)

        if target is None:
            return None

        args = [_eval(arg, env, context) for arg in node["args"]]

        if isinstance(target, Closure):
            if len(args) != len(target.params):
                raise EvalError(
                    code="E_RT_ARITY_MISMATCH",
                    message=(
                        f"optional call arity mismatch: expected {len(target.params)}, got {len(args)}"
                    ),
                    location={"node_kind": "optional_call"},
                )
            call_env = target.env.child()
            for param, value in zip(target.params, args):
                call_env.set(param, value)
            return _eval(target.body, call_env, context)

        if callable(target):
            try:
                return target(*args)
            except TypeError as exc:
                raise EvalError(
                    code="E_RT_HOST_CALL_ARITY",
                    message=str(exc),
                    location={"node_kind": "optional_call"},
                ) from exc

        raise EvalError(
            code="E_RT_NOT_CALLABLE",
            message=f"optional call target is not callable: {type(target).__name__}",
            location={"node_kind": "optional_call"},
        )

    if kind == "ident":
        return env.get(node["name"])

    if kind == "unary_pos":
        operand = _eval(node["operand"], env, context)
        if not isinstance(operand, int) or isinstance(operand, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"unary plus expects int operand, got {type(operand).__name__}",
                location={"node_kind": "unary_pos"},
            )
        return operand

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
        op = node.get("op")
        if op not in {"+", "-"}:
            raise EvalError(
                code="E_RT_UNSUPPORTED_KIND",
                message=f"unsupported additive op '{op}'",
                location={"node_kind": "concat_bin", "op": op},
            )

        left = _eval(node["left"], env, context)
        right = _eval(node["right"], env, context)

        left_is_int = isinstance(left, int) and not isinstance(left, bool)
        right_is_int = isinstance(right, int) and not isinstance(right, bool)

        if op == "+":
            if left_is_int and right_is_int:
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            raise EvalError(
                code="E_RT_TYPE",
                message=(
                    "plus expects both operands as int or both as string, "
                    f"got {type(left).__name__} and {type(right).__name__}"
                ),
                location={"node_kind": "concat_bin", "op": "+"},
            )

        if left_is_int and right_is_int:
            return left - right

        raise EvalError(
            code="E_RT_TYPE",
            message=(
                "minus expects both operands as int, "
                f"got {type(left).__name__} and {type(right).__name__}"
            ),
            location={"node_kind": "concat_bin", "op": "-"},
        )

    if kind == "mul_bin":
        left = _eval(node["left"], env, context)
        right = _eval(node["right"], env, context)
        if not isinstance(left, int) or isinstance(left, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"multiplication expects int left operand, got {type(left).__name__}",
                location={"node_kind": "mul_bin", "side": "left"},
            )
        if not isinstance(right, int) or isinstance(right, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"multiplication expects int right operand, got {type(right).__name__}",
                location={"node_kind": "mul_bin", "side": "right"},
            )
        return left * right

    if kind == "exact_div_bin":
        left = _eval(node["left"], env, context)
        right = _eval(node["right"], env, context)
        if not isinstance(left, int) or isinstance(left, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"exact division expects int left operand, got {type(left).__name__}",
                location={"node_kind": "exact_div_bin", "side": "left"},
            )
        if not isinstance(right, int) or isinstance(right, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"exact division expects int right operand, got {type(right).__name__}",
                location={"node_kind": "exact_div_bin", "side": "right"},
            )
        if right == 0:
            raise EvalError(
                code="E_RT_ZERO_DIVISION",
                message="exact division by zero",
                location={"node_kind": "exact_div_bin", "side": "right"},
            )
        if left % right != 0:
            raise EvalError(
                code="E_RT_DOMAIN",
                message=f"exact division requires divisible operands, got {left} and {right}",
                location={"node_kind": "exact_div_bin", "left": left, "right": right},
            )
        return left // right

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

    if kind == "power_bin":
        left = _eval(node["left"], env, context)
        right = _eval(node["right"], env, context)
        if not isinstance(left, int) or isinstance(left, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"exponentiation expects int left operand, got {type(left).__name__}",
                location={"node_kind": "power_bin", "side": "left"},
            )
        if not isinstance(right, int) or isinstance(right, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"exponentiation expects int right operand, got {type(right).__name__}",
                location={"node_kind": "power_bin", "side": "right"},
            )
        if right < 0:
            raise EvalError(
                code="E_RT_DOMAIN",
                message="exponentiation exponent must be non-negative",
                location={"node_kind": "power_bin", "side": "right"},
            )
        return left ** right

    if kind == "coalesce_bin":
        left = _eval(node["left"], env, context)
        if left is not None:
            return left
        return _eval(node["right"], env, context)

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
            left_is_int = isinstance(left, int) and not isinstance(left, bool)
            right_is_int = isinstance(right, int) and not isinstance(right, bool)
            left_is_str = isinstance(left, str)
            right_is_str = isinstance(right, str)

            if left_is_int and right_is_int:
                return {
                    "<": left < right,
                    "<=": left <= right,
                    ">": left > right,
                    ">=": left >= right,
                }[op]

            if left_is_str and right_is_str:
                return {
                    "<": left < right,
                    "<=": left <= right,
                    ">": left > right,
                    ">=": left >= right,
                }[op]

            raise EvalError(
                code="E_RT_TYPE",
                message=(
                    f"comparison {op} expects both operands as int or both as string, "
                    f"got {type(left).__name__} and {type(right).__name__}"
                ),
                location={
                    "node_kind": "compare_bin",
                    "op": op,
                    "left_type": type(left).__name__,
                    "right_type": type(right).__name__,
                },
            )

        allowed_types = (int, bool, str, type(None))
        if not isinstance(left, allowed_types):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"equality {op} unsupported for left operand type {type(left).__name__}",
                location={
                    "node_kind": "compare_bin",
                    "op": op,
                    "side": "left",
                    "left_type": type(left).__name__,
                },
            )
        if type(left) is not type(right):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"equality {op} expects same operand types, got {type(left).__name__} and {type(right).__name__}",
                location={
                    "node_kind": "compare_bin",
                    "op": op,
                    "left_type": type(left).__name__,
                    "right_type": type(right).__name__,
                },
            )
        return (left == right) if op == "==" else (left != right)

    if kind == "let":
        value = _eval(node["value"], env, context)
        scoped = env.child()
        scoped.set(node["name"], value)
        return _eval(node["body"], scoped, context)

    if kind == "if":
        cond = _eval(node["cond"], env, context)
        if not isinstance(cond, bool):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"if condition must evaluate to bool, got {type(cond).__name__}",
                location={"node_kind": "if", "field": "cond"},
            )
        branch = node["then"] if cond else node["else"]
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
