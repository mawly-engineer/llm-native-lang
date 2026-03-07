"""Type/check contracts for llm-native-lang core AST nodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class TypeSpec:
    kind: str
    args: tuple["TypeSpec", ...] = ()
    returns: "TypeSpec | None" = None

    def __str__(self) -> str:
        if self.kind != "fn":
            return self.kind
        args = ",".join(str(arg) for arg in self.args)
        out = "any" if self.returns is None else str(self.returns)
        return f"fn({args})->{out}"


TYPE_NUMBER = TypeSpec("number")
TYPE_BOOL = TypeSpec("bool")
TYPE_ANY = TypeSpec("any")


def fn_type(*args: TypeSpec, returns: TypeSpec = TYPE_ANY) -> TypeSpec:
    return TypeSpec("fn", args=args, returns=returns)


DEFAULT_TYPE_ENV: dict[str, TypeSpec] = {
    "true": TYPE_BOOL,
    "false": TYPE_BOOL,
}


class TypeCheckError(ValueError):
    """Raised when an AST node violates core type/check contracts."""


class _Ctx:
    def __init__(self, env: Mapping[str, TypeSpec] | None = None) -> None:
        self.env: dict[str, TypeSpec] = dict(DEFAULT_TYPE_ENV)
        if env:
            self.env.update(env)

    def child(self) -> "_Ctx":
        nxt = _Ctx()
        nxt.env = dict(self.env)
        return nxt


def check_expr(node: Any, env: Mapping[str, TypeSpec] | None = None) -> TypeSpec:
    """Return the inferred type for `node` or raise TypeCheckError."""

    return _check(node, _Ctx(env), path="expr")


def _check(node: Any, ctx: _Ctx, path: str) -> TypeSpec:
    if not isinstance(node, dict):
        raise TypeCheckError(f"{path}: node must be object")

    kind = node.get("kind")

    if kind == "number":
        value = node.get("value")
        if not isinstance(value, int):
            raise TypeCheckError(f"{path}.value: number literal must be int")
        return TYPE_NUMBER

    if kind == "ident":
        name = node.get("name")
        if not isinstance(name, str) or not name.strip():
            raise TypeCheckError(f"{path}.name: ident name must be non-empty string")
        if name not in ctx.env:
            raise TypeCheckError(f"{path}.name: unknown identifier '{name}'")
        return ctx.env[name]

    if kind == "let":
        name = node.get("name")
        if not isinstance(name, str) or not name.strip():
            raise TypeCheckError(f"{path}.name: let name must be non-empty string")

        value_ty = _check(node.get("value"), ctx, f"{path}.value")
        child = ctx.child()
        child.env[name] = value_ty
        return _check(node.get("body"), child, f"{path}.body")

    if kind == "if":
        cond_ty = _check(node.get("cond"), ctx, f"{path}.cond")
        if cond_ty != TYPE_BOOL:
            raise TypeCheckError(f"{path}.cond: expected bool, got {cond_ty}")

        then_ty = _check(node.get("then"), ctx, f"{path}.then")
        else_ty = _check(node.get("else"), ctx, f"{path}.else")
        if then_ty != else_ty:
            raise TypeCheckError(f"{path}: branch type mismatch ({then_ty} vs {else_ty})")
        return then_ty

    if kind == "fn":
        params = node.get("params")
        if not isinstance(params, list):
            raise TypeCheckError(f"{path}.params: fn params must be list")

        child = ctx.child()
        param_types: list[TypeSpec] = []
        for idx, param in enumerate(params):
            if not isinstance(param, str) or not param.strip():
                raise TypeCheckError(f"{path}.params[{idx}]: parameter must be non-empty string")
            child.env[param] = TYPE_ANY
            param_types.append(TYPE_ANY)

        body_ty = _check(node.get("body"), child, f"{path}.body")
        return fn_type(*param_types, returns=body_ty)

    if kind == "call":
        callee = node.get("callee")
        if not isinstance(callee, str) or not callee.strip():
            raise TypeCheckError(f"{path}.callee: callee must be non-empty string")
        if callee not in ctx.env:
            raise TypeCheckError(f"{path}.callee: unknown function '{callee}'")

        callee_ty = ctx.env[callee]
        if callee_ty.kind != "fn":
            raise TypeCheckError(f"{path}.callee: expected function, got {callee_ty}")

        args = node.get("args")
        if not isinstance(args, list):
            raise TypeCheckError(f"{path}.args: args must be list")
        if len(args) != len(callee_ty.args):
            raise TypeCheckError(
                f"{path}.args: arity mismatch, expected {len(callee_ty.args)}, got {len(args)}"
            )

        for idx, arg in enumerate(args):
            arg_ty = _check(arg, ctx, f"{path}.args[{idx}]")
            expected = callee_ty.args[idx]
            if expected != TYPE_ANY and arg_ty != expected:
                raise TypeCheckError(
                    f"{path}.args[{idx}]: expected {expected}, got {arg_ty}"
                )

        return TYPE_ANY if callee_ty.returns is None else callee_ty.returns

    raise TypeCheckError(f"{path}: unsupported kind '{kind}'")
