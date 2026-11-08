"""Tagged AST + static typecheck. Runtime semantics still run after this.

0.3 value mismatches such as `add "a" 1` stay SemError at runtime.
This pass rejects ill-formed trees: unknown ops, arity, refuse, bounds,
and bytes that are not even hex.
"""
from __future__ import annotations

from typing import Any, TypedDict

from .errors import TypeCheckError
from .limits import MAX_BYTES, MAX_DEPTH, MAX_INT, MAX_LIST, MAX_STR
from .symbols import FORMS, REFUSE, VERBS, arity


class Node(TypedDict):
    op: str
    args: list[Any]


def is_node(n: object) -> bool:
    return isinstance(n, dict) and isinstance(n.get("op"), str) and isinstance(n.get("args"), list)


def _leaf_kind(n: Node) -> str:
    op = n["op"]
    if op in ("str", "int"):
        return op
    if op in VERBS or op in FORMS:
        return "node"
    return op


def typecheck(ast: object, *, span: int | None = None, _depth: int = 0) -> Node:
    if _depth > MAX_DEPTH:
        raise TypeCheckError("ast too deep", span=span, detail={"depth": _depth})
    if not is_node(ast):
        raise TypeCheckError("ast is not a node", span=span)
    n: Node = ast  # type: ignore[assignment]
    op = n["op"]
    args = n["args"]
    if op in REFUSE:
        raise TypeCheckError(f"refused {op}", span=span, detail={"op": op})
    if op not in VERBS and op not in FORMS:
        raise TypeCheckError(f"unknown op {op}", span=span, detail={"op": op})
    for a in args:
        if is_node(a):
            typecheck(a, span=span, _depth=_depth + 1)
        elif op in ("str", "int", "bytes"):
            continue
        else:
            raise TypeCheckError(f"{op} arg is not a node", span=span, detail={"op": op})
    if op in VERBS:
        lo, hi = arity(op)
        if not (lo <= len(args) <= hi):
            raise TypeCheckError(
                f"{op} needs {lo}..{hi} arg(s), got {len(args)}",
                span=span,
                detail={"op": op, "got": len(args)},
            )
    if op == "str" and args and isinstance(args[0], str) and len(args[0]) > MAX_STR:
        raise TypeCheckError("str too long", span=span, detail={"n": len(args[0])})
    if op == "int" and args:
        v = args[0]
        if type(v) is not int or v < -MAX_INT or v > MAX_INT:
            raise TypeCheckError("int bound", span=span, detail={"v": v})
    if op == "bytes":
        if len(args) != 1 or isinstance(args[0], dict):
            raise TypeCheckError("bytes needs hex", span=span)
        hx = str(args[0])
        try:
            raw = bytes.fromhex(hx)
        except ValueError as e:
            raise TypeCheckError("bytes want even hex", span=span) from e
        if len(raw) > MAX_BYTES:
            raise TypeCheckError("bytes too long", span=span, detail={"n": len(raw)})
    if op == "list" and len(args) > MAX_LIST:
        raise TypeCheckError("list too long", span=span, detail={"n": len(args)})
    if op == "fetch":
        if not args or _leaf_kind(args[0]) != "str":
            raise TypeCheckError("fetch needs str url", span=span)
    if op == "sha":
        if not args or _leaf_kind(args[0]) != "str":
            raise TypeCheckError("sha needs str hex", span=span)
    if op == "say" and not args:
        raise TypeCheckError("say needs a value", span=span)
    if op == "kv":
        if len(args) != 2:
            raise TypeCheckError("kv needs key and value", span=span)
    return n
