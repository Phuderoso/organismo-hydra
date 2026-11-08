"""Tagged AST + static typecheck. Runtime semantics still run after this."""
from __future__ import annotations

from typing import Any, TypedDict

from .errors import TypeCheckError
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


def typecheck(ast: object, *, span: int | None = None) -> Node:
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
            typecheck(a, span=span)
        elif op in ("str", "int"):
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
    if op == "fetch":
        if not args or _leaf_kind(args[0]) != "str":
            raise TypeCheckError("fetch needs str url", span=span)
    if op == "sha":
        if not args or _leaf_kind(args[0]) != "str":
            raise TypeCheckError("sha needs str hex", span=span)
    if op == "kv":
        if len(args) != 2:
            raise TypeCheckError("kv needs key and value", span=span)
    return n
