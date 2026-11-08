"""Interpret an AST. No network. Maps not war. Output lives on `out`."""
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


def _truthy(v: Any) -> bool:
    if v is None or v is False:
        return False
    if v is True:
        return True
    if isinstance(v, int):
        return v != 0
    if isinstance(v, str):
        return v != ""
    if isinstance(v, (list, tuple, dict)):
        return len(v) != 0
    return True


def _eval_value(n: dict) -> Any:
    op = n["op"]
    if op in ("str", "int"):
        return _s(n)
    if op == "kv":
        return (_eval_value(n["args"][0]), _eval_value(n["args"][1]))
    r = eval_ast(n)
    if "value" in r:
        return r["value"]
    if "out" in r:
        return r["out"]
    if r.get("op") == "map":
        return r.get("map")
    if r.get("op") == "seq":
        return r.get("out") if "out" in r else r.get("steps")
    if r.get("op") == "fetch":
        return r.get("url")
    return r


def _as_seq(v: Any) -> list:
    if isinstance(v, str):
        return list(v)
    if isinstance(v, list):
        return v
    if isinstance(v, tuple):
        return list(v)
    raise SemError("len/nth needs str or seq")


def _collect_out(r: dict) -> list[str]:
    outs: list[str] = []
    if r.get("op") == "say" and "out" in r:
        outs.append(str(r["out"]))
    for s in r.get("steps") or []:
        if isinstance(s, dict):
            outs.extend(_collect_out(s))
    return outs


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
        url = _eval_value(args[0]) if args else ""
        if not isinstance(url, str) or not _URL.match(url):
            raise SemError("fetch needs http(s) url")
        return {"ok": True, "op": "fetch", "url": url, "did_network": False}
    if op == "sha":
        hx = _eval_value(args[0]) if args else ""
        if not isinstance(hx, str) or not _SHA.match(hx):
            raise SemError("sha needs hex digest")
        return {"ok": True, "op": "sha", "hex": hx.lower()}
    if op == "map":
        pairs = []
        for a in args:
            if a.get("op") == "kv":
                k, v = _eval_value(a["args"][0]), _flatten(a["args"][1])
                if str(k).lower() in REFUSE:
                    raise SemError(f"refused key {k}")
                pairs.append((str(k), v))
            else:
                pairs.append(("item", _flatten(a)))
        return {"ok": True, "op": "map", "map": dict(pairs)}
    if op == "seq":
        steps = [eval_ast(a) for a in args]
        result: dict = {"ok": all(s.get("ok") for s in steps), "op": "seq", "steps": steps}
        outs = []
        for s in steps:
            outs.extend(_collect_out(s))
        if outs:
            result["out"] = "\n".join(outs)
        return result
    if op in ("str", "int", "kv"):
        return {"ok": True, "op": op, "value": _s(ast)}
    if op == "say":
        if not args:
            raise SemError("say needs a value")
        text = str(_eval_value(args[0]))
        return {"ok": True, "op": "say", "out": text}
    if op == "cat":
        parts = [str(_eval_value(a)) for a in args]
        return {"ok": True, "op": "cat", "value": "".join(parts)}
    if op == "add":
        xs = [_eval_value(a) for a in args]
        if any(type(x) is not int for x in xs):
            raise SemError("add needs ints")
        return {"ok": True, "op": "add", "value": sum(xs)}
    if op == "sub":
        a, b = _eval_value(args[0]), _eval_value(args[1])
        if type(a) is not int or type(b) is not int:
            raise SemError("sub needs ints")
        return {"ok": True, "op": "sub", "value": a - b}
    if op == "eq":
        a, b = _eval_value(args[0]), _eval_value(args[1])
        return {"ok": True, "op": "eq", "value": 1 if a == b else 0}
    if op == "not":
        v = _eval_value(args[0])
        return {"ok": True, "op": "not", "value": 0 if _truthy(v) else 1}
    if op == "if":
        cond = _truthy(_eval_value(args[0]))
        pick = args[1] if cond else (args[2] if len(args) > 2 else {"op": "ok", "args": []})
        return eval_ast(pick)
    if op == "len":
        inner = args[0]
        if inner["op"] == "seq":
            n = len(inner.get("args") or [])
        elif inner["op"] == "map":
            n = len(inner.get("args") or [])
        else:
            v = _eval_value(inner)
            if isinstance(v, (str, list, tuple, dict)):
                n = len(v)
            else:
                raise SemError("len needs str, seq, or map")
        return {"ok": True, "op": "len", "value": n}
    if op == "nth":
        inner, idx_n = args[0], args[1]
        i = _eval_value(idx_n)
        if type(i) is not int:
            raise SemError("nth index needs int")
        if inner["op"] == "seq":
            xs = inner.get("args") or []
            if i < 0 or i >= len(xs):
                raise SemError("nth out of range")
            return eval_ast(xs[i]) if xs[i]["op"] in VERBS else {
                "ok": True,
                "op": "nth",
                "value": _eval_value(xs[i]),
            }
        v = _eval_value(inner)
        if isinstance(v, str):
            if i < 0 or i >= len(v):
                raise SemError("nth out of range")
            return {"ok": True, "op": "nth", "value": v[i]}
        seq = _as_seq(v)
        if i < 0 or i >= len(seq):
            raise SemError("nth out of range")
        return {"ok": True, "op": "nth", "value": seq[i]}
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
