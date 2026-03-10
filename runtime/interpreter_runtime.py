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


def _is_int(value: Any) -> bool:
    """Type predicate: returns true for integers (excluding bool)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_float(value: Any) -> bool:
    """Type predicate: returns true for floats."""
    return isinstance(value, float)


def _is_string(value: Any) -> bool:
    """Type predicate: returns true for strings."""
    return isinstance(value, str)


def _is_bool(value: Any) -> bool:
    """Type predicate: returns true for booleans."""
    return isinstance(value, bool)


def _is_list(value: Any) -> bool:
    """Type predicate: returns true for lists."""
    return isinstance(value, list)


def _is_object(value: Any) -> bool:
    """Type predicate: returns true for objects (dicts)."""
    return isinstance(value, dict)


def _is_null(value: Any) -> bool:
    """Type predicate: returns true for null."""
    return value is None


def _is_function(value: Any) -> bool:
    """Type predicate: returns true for functions/closures."""
    return isinstance(value, Closure) or callable(value)


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
    
    # Type predicate built-ins
    root.set("is_int", _is_int)
    root.set("is_float", _is_float)
    root.set("is_string", _is_string)
    root.set("is_bool", _is_bool)
    root.set("is_list", _is_list)
    root.set("is_object", _is_object)
    root.set("is_null", _is_null)
    root.set("is_function", _is_function)
    
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

    if kind == "slice":
        target = _eval(node["target"], env, context)

        if not isinstance(target, list):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"slice target must be list, got {type(target).__name__}",
                location={"node_kind": "slice", "field": "target"},
            )

        # Evaluate bounds
        def eval_bound(bound_node):
            if bound_node is None:
                return None
            value = _eval(bound_node, env, context)
            if not isinstance(value, int) or isinstance(value, bool):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"slice bounds must evaluate to int, got {type(value).__name__}",
                    location={"node_kind": "slice", "field": "bound"},
                )
            return value

        start = eval_bound(node.get("start"))
        end = eval_bound(node.get("end"))
        step = eval_bound(node.get("step"))

        # Default step is 1
        if step is None:
            step = 1

        if step == 0:
            raise EvalError(
                code="E_RT_SLICE_STEP_ZERO",
                message="slice step cannot be zero",
                location={"node_kind": "slice", "field": "step"},
            )

        # Normalize bounds similar to Python slicing
        length = len(target)

        def normalize_index(idx, default):
            if idx is None:
                return default
            if idx < 0:
                idx = length + idx
            return max(0, min(idx, length))

        if step > 0:
            start_idx = normalize_index(start, 0)
            end_idx = normalize_index(end, length)
        else:
            # Negative step: start from end, go backward
            start_idx = normalize_index(start, length - 1)
            if start_idx >= length:
                start_idx = length - 1
            end_idx = normalize_index(end, -1)

        # Build result by iterating
        result = []
        if step > 0:
            current = start_idx
            while current < end_idx:
                if 0 <= current < length:
                    result.append(target[current])
                current += step
        else:
            current = start_idx
            while current > end_idx:
                if 0 <= current < length:
                    result.append(target[current])
                current += step

        return result

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
            operand_type = type(operand).__name__
            raise EvalError(
                code="E_RT_TYPE",
                message=f"unary plus expects int operand, got {operand_type}",
                location={"node_kind": "unary_pos", "operand_type": operand_type},
            )
        return operand

    if kind == "unary_neg":
        value = _eval(node["operand"], env, context)
        if not isinstance(value, int) or isinstance(value, bool):
            operand_type = type(value).__name__
            raise EvalError(
                code="E_RT_TYPE",
                message=f"unary negation expects int, got {operand_type}",
                location={"node_kind": "unary_neg", "operand_type": operand_type},
            )
        return -value

    if kind == "unary_not":
        value = _eval(node["operand"], env, context)
        if not isinstance(value, bool):
            operand_type = type(value).__name__
            raise EvalError(
                code="E_RT_TYPE",
                message=f"unary logical-not expects bool, got {operand_type}",
                location={"node_kind": "unary_not", "operand_type": operand_type},
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
            left_type = type(left).__name__
            right_type = type(right).__name__
            raise EvalError(
                code="E_RT_TYPE",
                message=(
                    "plus expects both operands as int or both as string, "
                    f"got {left_type} and {right_type}"
                ),
                location={
                    "node_kind": "concat_bin",
                    "op": "+",
                    "left_type": left_type,
                    "right_type": right_type,
                },
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
        
        # Accept int or float for base (exclude bool)
        left_is_int = isinstance(left, int) and not isinstance(left, bool)
        left_is_float = isinstance(left, float)
        if not (left_is_int or left_is_float):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"exponentiation expects int or float left operand, got {type(left).__name__}",
                location={"node_kind": "power_bin", "side": "left"},
            )
        
        # Accept int or float for exponent (exclude bool)
        right_is_int = isinstance(right, int) and not isinstance(right, bool)
        right_is_float = isinstance(right, float)
        if not (right_is_int or right_is_float):
            raise EvalError(
                code="E_RT_TYPE",
                message=f"exponentiation expects int or float right operand, got {type(right).__name__}",
                location={"node_kind": "power_bin", "side": "right"},
            )
        
        # Compute power - Python's ** handles negative and fractional exponents
        result = left ** right
        
        # Return int if result is a whole number and inputs were ints
        # Otherwise return float
        if left_is_int and right_is_int and right >= 0:
            # Both inputs were positive ints, result is guaranteed int by Python
            return result
        
        # For mixed types or negative/fractional exponents, return float
        # but convert whole numbers to int for consistency
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result

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
            left_type = type(left).__name__
            raise EvalError(
                code="E_RT_TYPE",
                message=f"logical {op} expects bool left operand, got {left_type}",
                location={"node_kind": "logical_bin", "op": op, "side": "left", "operand_type": left_type},
            )
        if op == "and":
            if not left:
                return False
            right = _eval(node["right"], env, context)
            if not isinstance(right, bool):
                right_type = type(right).__name__
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"logical and expects bool right operand, got {right_type}",
                    location={"node_kind": "logical_bin", "op": op, "side": "right", "operand_type": right_type},
                )
            return right

        if left:
            return True
        right = _eval(node["right"], env, context)
        if not isinstance(right, bool):
            right_type = type(right).__name__
            raise EvalError(
                code="E_RT_TYPE",
                message=f"logical or expects bool right operand, got {right_type}",
                location={"node_kind": "logical_bin", "op": op, "side": "right", "operand_type": right_type},
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
            left_is_float = isinstance(left, float)
            right_is_float = isinstance(right, float)
            left_is_num = left_is_int or left_is_float
            right_is_num = right_is_int or right_is_float
            left_is_str = isinstance(left, str)
            right_is_str = isinstance(right, str)

            if left_is_num and right_is_num:
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
                    f"comparison {op} expects both operands as int, float, or both as string, "
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
                    "right_type": type(right).__name__,
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
        name = node["name"]
        is_recursive = node.get("recursive", False)
        
        if is_recursive:
            # For recursive let, we need fixpoint semantics
            # Create environment with placeholder binding first
            scoped = env.child()
            
            # Create a mutable cell that will hold the actual value
            # This allows the closure to capture a reference that gets updated
            recursive_cell = [None]
            
            # Create a proxy object that looks like the actual value
            # When called, it delegates to the cell contents
            class RecursiveProxy:
                def __init__(self, cell, proxy_name):
                    self._cell = cell
                    self._name = proxy_name
                
                def _get_value(self):
                    if self._cell[0] is None:
                        raise EvalError(
                            code="E_RT_RECURSION_LIMIT",
                            message=f"recursive binding '{self._name}' accessed before initialization",
                            location={"node_kind": "let", "name": self._name}
                        )
                    return self._cell[0]
                
                def __call__(self, *args):
                    val = self._get_value()
                    if isinstance(val, Closure):
                        if len(args) != len(val.params):
                            raise EvalError(
                                code="E_RT_ARITY_MISMATCH",
                                message=(
                                    f"arity mismatch: "
                                    f"expected {len(val.params)}, got {len(args)}"
                                ),
                                location={"node_kind": "let", "name": self._name},
                            )
                        call_env = val.env.child()
                        for param, arg_val in zip(val.params, args):
                            call_env.set(param, arg_val)
                        return _eval(val.body, call_env, context)
                    if callable(val):
                        return val(*args)
                    raise EvalError(
                        code="E_RT_NOT_CALLABLE",
                        message=f"recursive binding '{self._name}' is not callable",
                        location={"node_kind": "let", "name": self._name}
                    )
                
                # Proxy attribute access to the actual value
                def __getattr__(self, attr):
                    if attr.startswith('_'):
                        return object.__getattribute__(self, attr)
                    val = self._get_value()
                    return getattr(val, attr)
                
                # Proxy item access to the actual value
                def __getitem__(self, key):
                    val = self._get_value()
                    return val[key]
                
                def __repr__(self):
                    return f"<recursive {self._name}>"
            
            # Bind the proxy to the name before evaluating the value
            proxy = RecursiveProxy(recursive_cell, name)
            scoped.set(name, proxy)
            
            # Now evaluate the value with the name in scope
            # This allows the function definition to capture the recursive reference
            value = _eval(node["value"], scoped, context)
            
            # Update the cell with the actual value
            recursive_cell[0] = value
            
            # Bind the actual value (replacing the proxy) and evaluate body
            scoped.bindings[name] = value  # Replace proxy with actual value
            return _eval(node["body"], scoped, context)
        else:
            # Non-recursive let (existing behavior)
            value = _eval(node["value"], env, context)
            scoped = env.child()
            scoped.set(name, value)
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
        target = _eval(node["target"], env, context)
        args = [_eval(arg, env, context) for arg in node["args"]]

        if isinstance(target, Closure):
            if len(args) != len(target.params):
                raise EvalError(
                    code="E_RT_ARITY_MISMATCH",
                    message=(
                        f"arity mismatch: "
                        f"expected {len(target.params)}, got {len(args)}"
                    ),
                    location={"node_kind": "call"},
                )
            call_env = target.env.child()
            for param, value in zip(target.params, args):
                call_env.set(param, value)
            return _eval(target.body, call_env, context)

        if callable(target):
            fn = target
            try:
                return fn(*args)
            except TypeError as exc:
                raise EvalError(
                    code="E_RT_HOST_CALL_ARITY",
                    message=str(exc),
                    location={"node_kind": "call"},
                ) from exc

        raise EvalError(
            code="E_RT_NOT_CALLABLE",
            message=f"value is not callable: {type(target).__name__}",
            location={"node_kind": "call"},
        )

    if kind == "range_call":
        args = node["args"]
        evaluated_args = [_eval(arg, env, context) for arg in args]
        
        # Validate all arguments are integers
        for idx, val in enumerate(evaluated_args):
            if not isinstance(val, int) or isinstance(val, bool):
                raise EvalError(
                    code="E_RT_TYPE",
                    message=f"range argument {idx} must be int, got {type(val).__name__}",
                    location={"node_kind": "range_call", "arg_index": idx},
                )
        
        # Parse arguments based on count
        if len(evaluated_args) == 1:
            start, end, step = 0, evaluated_args[0], 1
        elif len(evaluated_args) == 2:
            start, end, step = evaluated_args[0], evaluated_args[1], 1
        else:  # 3 args
            start, end, step = evaluated_args[0], evaluated_args[1], evaluated_args[2]
        
        # Validate step is not zero
        if step == 0:
            raise EvalError(
                code="E_RT_RANGE_STEP_ZERO",
                message="range step cannot be zero",
                location={"node_kind": "range_call", "field": "step"},
            )
        
        # Generate range list
        result = []
        if step > 0:
            current = start
            while current < end:
                result.append(current)
                current += step
        else:
            current = start
            while current > end:
                result.append(current)
                current += step
        
        return result

    raise EvalError(
        code="E_RT_UNSUPPORTED_KIND",
        message=f"unsupported kind '{kind}'",
        location={"node_kind": kind},
    )
