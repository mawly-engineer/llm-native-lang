"""Frozen minimal grammar contract for llm-native-lang.

Scope: expr, let, if, fn, call, unary negation/logical-not,
string literals, string concatenation, logical and/or, bool literals,
list literals, and index access.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, List

GRAMMAR_VERSION = "1.0.0"

# Machine-readable grammar contract (ordered for deterministic fingerprinting)
GRAMMAR_CONTRACT = {
    "version": GRAMMAR_VERSION,
    "start": "expr",
    "nonterminals": [
        "expr",
        "let",
        "if",
        "fn",
        "logical_or",
        "logical_and",
        "concat",
        "unary",
        "postfix",
        "atom",
    ],
    "productions": [
        "expr -> let | if | fn | logical_or",
        "let -> 'let' IDENT '=' expr 'in' expr",
        "if -> 'if' expr 'then' expr 'else' expr",
        "fn -> 'fn' '(' params? ')' '=>' expr",
        "logical_or -> logical_and ('or' logical_and)*",
        "logical_and -> concat ('and' concat)*",
        "concat -> unary ('+' unary)*",
        "unary -> '-' unary | '!' unary | postfix",
        "postfix -> atom (call_suffix | index_suffix)*",
        "call_suffix -> '(' args? ')'",
        "index_suffix -> '[' expr ']'",
        "atom -> 'true' | 'false' | STRING | IDENT | NUMBER | list | '(' expr ')'",
        "list -> '[' args? ']'",
        "params -> IDENT (',' IDENT)*",
        "args -> expr (',' expr)*",
    ],
}

GRAMMAR_FINGERPRINT = sha256(
    "\n".join(GRAMMAR_CONTRACT["productions"]).encode("utf-8")
).hexdigest()


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    start: int
    end: int


class ParseError(ValueError):
    pass


def _tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    while i < len(source):
        ch = source[i]
        if ch.isspace():
            i += 1
            continue
        if source.startswith("=>", i):
            tokens.append(Token("ARROW", "=>", i, i + 2))
            i += 2
            continue
        if ch == '"':
            start = i
            i += 1
            chars: list[str] = []
            while i < len(source):
                cur = source[i]
                if cur == '"':
                    i += 1
                    tokens.append(Token("STRING", "".join(chars), start, i))
                    break
                if cur == "\\":
                    if i + 1 >= len(source):
                        raise ParseError("unterminated string literal")
                    nxt = source[i + 1]
                    if nxt == '"':
                        chars.append('"')
                    elif nxt == "\\":
                        chars.append("\\")
                    elif nxt == "n":
                        chars.append("\n")
                    elif nxt == "t":
                        chars.append("\t")
                    else:
                        raise ParseError(f"unsupported string escape: \\{nxt}")
                    i += 2
                    continue
                chars.append(cur)
                i += 1
            else:
                raise ParseError("unterminated string literal")
            continue
        if ch in "()[],=-+!":
            tokens.append(Token(ch, ch, i, i + 1))
            i += 1
            continue
        if ch.isdigit():
            j = i + 1
            while j < len(source) and source[j].isdigit():
                j += 1
            tokens.append(Token("NUMBER", source[i:j], i, j))
            i = j
            continue
        if ch.isalpha() or ch == "_":
            j = i + 1
            while j < len(source) and (source[j].isalnum() or source[j] == "_"):
                j += 1
            ident = source[i:j]
            if ident in {"let", "in", "if", "then", "else", "fn", "and", "or", "true", "false"}:
                tokens.append(Token("KW", ident, i, j))
            else:
                tokens.append(Token("IDENT", ident, i, j))
            i = j
            continue
        raise ParseError(f"unexpected character: {ch}")

    tokens.append(Token("EOF", "", len(source), len(source)))
    return tokens


class _Parser:
    def __init__(self, source: str) -> None:
        self.tokens = _tokenize(source)
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _eat(self, kind: str, value: str | None = None) -> Token:
        tok = self._peek()
        if tok.kind != kind:
            raise ParseError(f"expected {kind}, got {tok.kind}:{tok.value}")
        if value is not None and tok.value != value:
            raise ParseError(f"expected {value}, got {tok.value}")
        self.pos += 1
        return tok

    @staticmethod
    def _with_span(kind: str, start: int, end: int, **fields: Any) -> dict[str, Any]:
        return {
            "kind": kind,
            "span": {"start": start, "end": end},
            **fields,
        }

    def parse(self) -> dict[str, Any]:
        node = self._expr()
        self._eat("EOF")
        return node

    def _expr(self) -> dict[str, Any]:
        tok = self._peek()
        if tok.kind == "KW" and tok.value == "let":
            return self._let()
        if tok.kind == "KW" and tok.value == "if":
            return self._if()
        if tok.kind == "KW" and tok.value == "fn":
            return self._fn()
        return self._logical_or()

    def _let(self) -> dict[str, Any]:
        start = self._eat("KW", "let").start
        name = self._eat("IDENT").value
        self._eat("=", "=")
        value = self._expr()
        self._eat("KW", "in")
        body = self._expr()
        return self._with_span("let", start, body["span"]["end"], name=name, value=value, body=body)

    def _if(self) -> dict[str, Any]:
        start = self._eat("KW", "if").start
        cond = self._expr()
        self._eat("KW", "then")
        then_node = self._expr()
        self._eat("KW", "else")
        else_node = self._expr()
        return self._with_span(
            "if",
            start,
            else_node["span"]["end"],
            cond=cond,
            then=then_node,
            **{"else": else_node},
        )

    def _fn(self) -> dict[str, Any]:
        start = self._eat("KW", "fn").start
        self._eat("(", "(")
        params: list[str] = []
        if self._peek().kind == "IDENT":
            params.append(self._eat("IDENT").value)
            while self._peek().kind == ",":
                self._eat(",", ",")
                params.append(self._eat("IDENT").value)
        self._eat(")", ")")
        self._eat("ARROW", "=>")
        body = self._expr()
        return self._with_span("fn", start, body["span"]["end"], params=params, body=body)

    def _logical_or(self) -> dict[str, Any]:
        node = self._logical_and()
        while self._peek().kind == "KW" and self._peek().value == "or":
            self._eat("KW", "or")
            right = self._logical_and()
            node = self._with_span(
                "logical_bin",
                node["span"]["start"],
                right["span"]["end"],
                op="or",
                left=node,
                right=right,
            )
        return node

    def _logical_and(self) -> dict[str, Any]:
        node = self._concat()
        while self._peek().kind == "KW" and self._peek().value == "and":
            self._eat("KW", "and")
            right = self._concat()
            node = self._with_span(
                "logical_bin",
                node["span"]["start"],
                right["span"]["end"],
                op="and",
                left=node,
                right=right,
            )
        return node

    def _concat(self) -> dict[str, Any]:
        node = self._unary()
        while self._peek().kind == "+":
            self._eat("+", "+")
            right = self._unary()
            node = self._with_span(
                "concat_bin",
                node["span"]["start"],
                right["span"]["end"],
                left=node,
                right=right,
            )
        return node

    def _unary(self) -> dict[str, Any]:
        tok = self._peek()
        if tok.kind == "-":
            minus = self._eat("-", "-")
            operand = self._unary()
            return self._with_span(
                "unary_neg",
                minus.start,
                operand["span"]["end"],
                operand=operand,
            )
        if tok.kind == "!":
            bang = self._eat("!", "!")
            operand = self._unary()
            return self._with_span(
                "unary_not",
                bang.start,
                operand["span"]["end"],
                operand=operand,
            )
        return self._postfix()

    def _postfix(self) -> dict[str, Any]:
        node = self._atom()
        while True:
            tok = self._peek()
            if tok.kind == "(" and node["kind"] == "ident":
                self._eat("(", "(")
                args: list[dict[str, Any]] = []
                if self._peek().kind != ")":
                    args.append(self._expr())
                    while self._peek().kind == ",":
                        self._eat(",", ",")
                        args.append(self._expr())
                close_tok = self._eat(")", ")")
                node = self._with_span(
                    "call",
                    node["span"]["start"],
                    close_tok.end,
                    callee=node["name"],
                    args=args,
                )
                continue
            if tok.kind == "[":
                self._eat("[", "[")
                index = self._expr()
                close_tok = self._eat("]", "]")
                node = self._with_span(
                    "index",
                    node["span"]["start"],
                    close_tok.end,
                    target=node,
                    index=index,
                )
                continue
            break
        return node

    def _atom(self) -> dict[str, Any]:
        tok = self._peek()
        if tok.kind == "KW" and tok.value in {"true", "false"}:
            boolean = self._eat("KW")
            return self._with_span("bool", boolean.start, boolean.end, value=boolean.value == "true")
        if tok.kind == "STRING":
            string = self._eat("STRING")
            return self._with_span("string", string.start, string.end, value=string.value)
        if tok.kind == "IDENT":
            ident = self._eat("IDENT")
            return self._with_span("ident", ident.start, ident.end, name=ident.value)
        if tok.kind == "NUMBER":
            number = self._eat("NUMBER")
            return self._with_span("number", number.start, number.end, value=int(number.value))
        if tok.kind == "[":
            open_tok = self._eat("[", "[")
            items: list[dict[str, Any]] = []
            if self._peek().kind != "]":
                items.append(self._expr())
                while self._peek().kind == ",":
                    self._eat(",", ",")
                    items.append(self._expr())
            close_tok = self._eat("]", "]")
            return self._with_span("list", open_tok.start, close_tok.end, items=items)
        if tok.kind == "(":
            self._eat("(", "(")
            node = self._expr()
            self._eat(")", ")")
            return node
        raise ParseError(f"expected atom, got {tok.kind}:{tok.value}")


def parse_expr(source: str) -> dict[str, Any]:
    return _Parser(source).parse()
