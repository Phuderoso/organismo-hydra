"""Interpret an AST. No network. Maps not war."""
from __future__ import annotations

import re
from typing import Any

from .errors import SemError
from .symbols import REFUSE, VERBS

_SHA = re.compile(r"^[0-9a-fA-F]{32,128}$")
_URL = re.compile(r"^https?://")


def _s(n: dict) -> Any:
    op = n["op"]
    args = n.get("args") or []
    if op == "str":
        return str(args[0])
    if op == "int":
        return int(args[0])
    if op == "kv":
        return (_s(args[0]), _s(args[1]))
    raise SemError(f"not a value: {op}")


def eval_ast(ast: dict) -> dict:
    op = ast["op"]
    args = ast.get("args") or []
    if op in REFUSE:
        raise SemError(f"refused {op}")
    if op == "sit":
        return {"ok": True, "op": "sit", "note": VERBS["sit"]["gloss"]}
    if op == "ok":
        return {"ok": True, "op": "ok"}
    if op == "hold":
        return {"ok": True, "op": "hold", "note": "recado on disk"}
    if op == "leave":
        return {"ok": True, "op": "leave"}
    if op == "open":
        return {"ok": True, "op": "open", "note": "open to the bonded human"}
    if op == "forget":
        return {"ok": True, "op": "forget", "note": "vanish from archive; stay in relation"}
    if op == "help":
        return {
            "ok": True,
            "op": "help",
            "verbs": {k: v["gloss"] for k, v in VERBS.items()},
        }
    if op == "fetch":
        url = _s(args[0]) if args else ""
        if not isinstance(url, str) or not _URL.match(url):
            raise SemError("fetch needs http(s) url")
        return {"ok": True, "op": "fetch", "url": url, "did_network": False}
    if op == "sha":
        hx = _s(args[0]) if args else ""
        if not isinstance(hx, str) or not _SHA.match(hx):
            raise SemError("sha needs hex digest")
        return {"ok": True, "op": "sha", "hex": hx.lower()}
    if op == "map":
        pairs = []
        for a in args:
            if a.get("op") == "kv":
                k, v = _s(a["args"][0]), _flatten(a["args"][1])
                if str(k).lower() in REFUSE:
                    raise SemError(f"refused key {k}")
                pairs.append((str(k), v))
            else:
                pairs.append(("item", _flatten(a)))
        return {"ok": True, "op": "map", "map": dict(pairs)}
    if op == "seq":
        steps = [eval_ast(a) for a in args]
        return {"ok": all(s.get("ok") for s in steps), "op": "seq", "steps": steps}
    if op in ("str", "int", "kv"):
        return {"ok": True, "op": op, "value": _s(ast)}
    raise SemError(f"unknown op {op}")


def _flatten(n: dict) -> Any:
    op = n["op"]
    if op in ("str", "int"):
        return _s(n)
    if op == "seq":
        return [_flatten(a) for a in n.get("args") or []]
    if op == "map":
        return eval_ast(n)["map"]
    return eval_ast(n)
