"""Deterministic core AST evaluator with lexical scope bindings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from runtime.ast_contract import validate_ast


class EvalError(ValueError):
    """Raised when evaluation fails."""


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
        raise EvalError(f"unknown identifier '{name}'")


def eval_expr(node: dict[str, Any], env: Mapping[str, Any] | None = None) -> Any:
    validate_ast(node)

    root = Env()
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
        callee = env.get(node["callee"])
        args = [_eval(arg, env) for arg in node["args"]]

        if isinstance(callee, Closure):
            if len(args) != len(callee.params):
                raise EvalError(
                    f"arity mismatch for '{node['callee']}': expected {len(callee.params)}, got {len(args)}"
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
                raise EvalError(str(exc)) from exc

        raise EvalError(f"'{node['callee']}' is not callable")

    raise EvalError(f"unsupported kind '{kind}'")
