"""Text → AST. Unambiguous recursive descent. JSON sugar kept for bt1 sit."""
from __future__ import annotations

import json
from typing import Any

from .errors import ParseError
from .symbols import EXPR, REFUSE, VERBS, arity, is_verb


def node(op: str, *args: Any) -> dict:
    return {"op": op, "args": list(args)}


class _Tok:
    def __init__(self, kind: str, value: Any, pos: int):
        self.kind = kind
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:
        return f"Tok({self.kind!r},{self.value!r})"


def tokenize(src: str) -> list[_Tok]:
    s = src.strip()
    i, n = 0, len(s)
    out: list[_Tok] = []
    while i < n:
        c = s[i]
        if c.isspace() or c == ",":
            i += 1
            continue
        if c in "()[]{}:":
            out.append(_Tok(c, c, i))
            i += 1
            continue
        if c == '"':
            j = i + 1
            buf: list[str] = []
            while j < n:
                d = s[j]
                if d == "\\":
                    if j + 1 >= n:
                        raise ParseError(f"unterminated escape at {i}", span=i)
                    esc = s[j + 1]
                    buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(esc, esc))
                    j += 2
                    continue
                if d == '"':
                    out.append(_Tok("str", "".join(buf), i))
                    i = j + 1
                    break
                buf.append(d)
                j += 1
            else:
                raise ParseError(f"unterminated string at {i}", span=i)
            continue
        if c in "bB" and i + 1 < n and s[i + 1] == '"':
            j = i + 2
            hexes: list[str] = []
            while j < n and s[j] != '"':
                hexes.append(s[j])
                j += 1
            if j >= n or s[j] != '"':
                raise ParseError(f"unterminated bytes at {i}", span=i)
            hx = "".join(hexes)
            if len(hx) % 2 or any(ch not in "0123456789abcdefABCDEF" for ch in hx):
                raise ParseError(f"bytes want even hex at {i}", span=i)
            out.append(_Tok("bytes", hx.lower(), i))
            i = j + 1
            continue
        if c.isdigit() or (c == "-" and i + 1 < n and s[i + 1].isdigit()):
            j = i + 1 if c == "-" else i
            while j < n and s[j].isdigit():
                j += 1
            out.append(_Tok("int", int(s[i:j]), i))
            i = j
            continue
        if c.isalpha() or c == "_":
            j = i + 1
            while j < n and (s[j].isalnum() or s[j] in "_-"):
                j += 1
            out.append(_Tok("id", s[i:j], i))
            i = j
            continue
        raise ParseError(f"unexpected {c!r} at {i}", span=i)
    out.append(_Tok("eof", None, n))
    return out


class _P:
    def __init__(self, toks: list[_Tok]):
        self.toks = toks
        self.i = 0

    def peek(self) -> _Tok:
        return self.toks[self.i]

    def eat(self, kind: str | None = None) -> _Tok:
        t = self.peek()
        if kind and t.kind != kind:
            raise ParseError(f"expected {kind} got {t.kind} at {t.pos}", span=t.pos)
        self.i += 1
        return t

    def parse_value(self) -> dict:
        t = self.peek()
        if t.kind == "str":
            self.eat()
            return node("str", t.value)
        if t.kind == "int":
            self.eat()
            return node("int", t.value)
        if t.kind == "bytes":
            self.eat()
            return node("bytes", t.value)
        if t.kind == "(":
            self.eat()
            inner = self.parse_expr()
            self.eat(")")
            return inner
        if t.kind == "[":
            self.eat()
            xs: list[dict] = []
            while self.peek().kind not in ("]", "eof"):
                xs.append(self.parse_value())
            self.eat("]")
            return node("list", *xs)
        if t.kind == "{":
            return self.parse_map_block()
        if t.kind == "id":
            return self.parse_expr()
        raise ParseError(f"expected value at {t.pos}", span=t.pos)

    def parse_map_block(self) -> dict:
        self.eat("{")
        pairs: list[dict] = []
        while self.peek().kind not in ("}", "eof"):
            k = self.eat()
            if k.kind not in ("id", "str"):
                raise ParseError(f"map key at {k.pos}", span=k.pos)
            if self.peek().kind == ":":
                self.eat()
            val = self.parse_value()
            pairs.append(node("kv", node("str", str(k.value)), val))
        self.eat("}")
        return node("map", *pairs)

    def parse_expr(self) -> dict:
        t = self.peek()
        if t.kind != "id":
            return self.parse_value()
        name = t.value
        if name == "bt1":
            self.eat()
            if self.peek().kind == "id":
                return self.parse_expr()
            raise ParseError("bt1 needs a verb", span=self.peek().pos)
        self.eat()
        if not is_verb(name):
            # bare ident as string key/word
            return node("str", name)
        if name == "map" and self.peek().kind != "{":
            pairs: list[dict] = []
            while self.peek().kind not in ("eof", ")", "]", "}") and len(pairs) < 16:
                k = self.parse_value()
                if self.peek().kind in ("eof", ")", "]", "}"):
                    pairs.append(node("kv", k, node("str", "")))
                    break
                v = self.parse_value()
                pairs.append(node("kv", k if k["op"] == "str" else node("str", render(k)), v))
            if not pairs:
                return node("map")
            return node("map", *pairs)
        lo, hi = arity(name)
        args: list[dict] = []
        allow = name in EXPR
        while len(args) < hi and self._arg_ahead(allow_verbs=allow):
            args.append(self.parse_value())
        if len(args) < lo:
            raise ParseError(f"{name} needs {lo} arg(s), got {len(args)}", span=t.pos)
        return node(name, *args)

    def _arg_ahead(self, allow_verbs: bool = False) -> bool:
        t = self.peek()
        if t.kind in ("eof", ")", "]", "}"):
            return False
        if t.kind == "id" and is_verb(t.value) and t.value != "seq":
            return allow_verbs
        return True


def parse(src: str) -> dict:
    raw = (src or "").strip()
    if not raw:
        raise ParseError("empty", span=0)
    if raw[0] in "{[":
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            obj = None
        if isinstance(obj, dict) and obj.get("v") == "bt1" and "op" in obj:
            op = str(obj["op"])
            if op in REFUSE:
                raise ParseError(f"refused {op}", span=0)
            args = obj.get("args") or []
            if not isinstance(args, list):
                args = [args]
            nodes = [_from_json(a) for a in args]
            if not nodes and "url" in obj:
                nodes = [node("str", obj["url"])]
            ast = node(op, *nodes)
            reject_refused(ast)
            return ast
        if obj is not None:
            ast = _from_json(obj)
            reject_refused(ast)
            return ast
    p = _P(tokenize(raw))
    ast = p.parse_expr()
    if p.peek().kind != "eof":
        # more top-level exprs → seq
        rest = [ast]
        while p.peek().kind != "eof":
            rest.append(p.parse_expr())
        ast = node("seq", *rest)
    reject_refused(ast)
    return ast


def _from_json(obj: Any) -> dict:
    if isinstance(obj, str):
        return node("str", obj)
    if isinstance(obj, bool):
        return node("int", int(obj))
    if isinstance(obj, int):
        return node("int", obj)
    if isinstance(obj, list):
        return node("list", *[_from_json(x) for x in obj])
    if isinstance(obj, dict):
        if "op" in obj:
            return node(str(obj["op"]), *[_from_json(a) for a in (obj.get("args") or [])])
        pairs = [node("kv", node("str", str(k)), _from_json(v)) for k, v in obj.items()]
        return node("map", *pairs)
    raise ParseError(f"bad json value {type(obj)}")


def reject_refused(n: dict) -> None:
    op = n.get("op")
    if op in REFUSE:
        raise ParseError(f"refused {op}", span=0)
    if op == "str" and n["args"] and str(n["args"][0]).lower() in REFUSE:
        raise ParseError(f"refused {n['args'][0]}", span=0)
    for a in n.get("args") or []:
        if isinstance(a, dict):
            reject_refused(a)


def render(ast: dict) -> str:
    """Canonical readable form. Meaning-preserving, not original whitespace."""
    op = ast["op"]
    args = ast.get("args") or []
    if op == "str":
        return json.dumps(args[0], ensure_ascii=False)
    if op == "int":
        return str(args[0])
    if op == "bytes":
        return 'b"' + str(args[0]) + '"'
    if op == "list":
        return "[" + " ".join(render(a) for a in args) + "]"
    if op == "kv":
        return f"{render(args[0])} {render(args[1])}"
    if op == "seq":
        inner = " ".join(render(a) for a in args)
        return f"seq {inner}" if args else "seq"
    if op == "map":
        inner = " ".join(render(a) for a in args)
        return f"map {inner}".rstrip()
    if op in VERBS:
        if not args:
            return op
        return op + " " + " ".join(render(a) for a in args)
    raise ParseError(f"cannot render {op}")
