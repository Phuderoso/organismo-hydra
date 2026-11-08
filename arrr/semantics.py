"""Interpret an AST. No network. Maps not war. Output lives on `out`.

`times` is the only repetition. Its count is an integer in 0..MAX_TIMES.
There are no functions and no recursive verbs, so evaluation terminates.
"""
from __future__ import annotations

import re
from typing import Any

from .errors import OverflowErr, SemError
from .limits import MAX_DEPTH, MAX_INT, MAX_TIMES
from .symbols import REFUSE, VERBS
from .values import Err

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


def _fit(n: int) -> int:
    if type(n) is not int or n < -MAX_INT or n > MAX_INT:
        raise OverflowErr("int bound", detail={"v": n})
    return n


def _truthy(v: Any) -> bool:
    if v is None or v is False:
        return False
    if v is True:
        return True
    if isinstance(v, Err):
        return True
    if isinstance(v, int) and type(v) is int:
        return v != 0
    if isinstance(v, str):
        return v != ""
    if isinstance(v, (bytes, bytearray, list, tuple, dict)):
        return len(v) != 0
    return True


def _eval_value(n: dict, _depth: int = 0) -> Any:
    op = n["op"]
    if op in ("str", "int"):
        return _s(n)
    if op == "bytes":
        return bytes.fromhex(str(n["args"][0]))
    if op == "kv":
        return (_eval_value(n["args"][0], _depth), _eval_value(n["args"][1], _depth))
    r = eval_ast(n, _depth=_depth + 1)
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
    raise SemError("len/nth needs str, list, or bytes")


def _key_str(v: Any) -> str:
    if isinstance(v, Err):
        raise SemError("key refuses error")
    if isinstance(v, (bytes, bytearray)):
        s = v.hex()
    elif isinstance(v, str) or type(v) is int:
        s = str(v)
    else:
        raise SemError("key needs str")
    if s.lower() in REFUSE:
        raise SemError(f"refused key {s}")
    return s


def _collect_out(r: dict) -> list[str]:
    outs: list[str] = []
    if r.get("op") == "say" and "out" in r:
        outs.append(str(r["out"]))
    elif r.get("op") == "times" and r.get("out"):
        outs.append(str(r["out"]))
    for s in r.get("steps") or []:
        if isinstance(s, dict):
            outs.extend(_collect_out(s))
    return outs


def _flatten(n: dict, _depth: int = 0) -> Any:
    op = n["op"]
    if op in ("str", "int"):
        return _s(n)
    if op == "bytes":
        return bytes.fromhex(str(n["args"][0]))
    if op in ("list", "seq"):
        return [_flatten(a, _depth + 1) for a in n.get("args") or []]
    if op == "map":
        return eval_ast(n, _depth=_depth + 1)["map"]
    if op == "err":
        return eval_ast(n, _depth=_depth + 1)["value"]
    r = eval_ast(n, _depth=_depth + 1)
    if "value" in r:
        return r["value"]
    return r


def eval_ast(ast: dict, _depth: int = 0) -> dict:
    if _depth > MAX_DEPTH:
        raise OverflowErr("eval depth", detail={"depth": _depth})
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
        url = _eval_value(args[0], _depth) if args else ""
        if not isinstance(url, str) or not _URL.match(url):
            raise SemError("fetch needs http(s) url")
        return {"ok": True, "op": "fetch", "url": url, "did_network": False}
    if op == "sha":
        hx = _eval_value(args[0], _depth) if args else ""
        if not isinstance(hx, str) or not _SHA.match(hx):
            raise SemError("sha needs hex digest")
        return {"ok": True, "op": "sha", "hex": hx.lower()}
    if op == "map":
        pairs = []
        for a in args:
            if a.get("op") == "kv":
                k = _key_str(_eval_value(a["args"][0], _depth))
                v = _flatten(a["args"][1], _depth)
                pairs.append((k, v))
            else:
                pairs.append(("item", _flatten(a, _depth)))
        return {"ok": True, "op": "map", "map": dict(pairs)}
    if op == "list":
        return {"ok": True, "op": "list", "value": [_flatten(a, _depth) for a in args]}
    if op == "bytes":
        return {"ok": True, "op": "bytes", "value": bytes.fromhex(str(args[0]))}
    if op == "seq":
        steps = [eval_ast(a, _depth=_depth + 1) for a in args]
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
        v = _eval_value(args[0], _depth)
        if isinstance(v, Err):
            raise SemError("say refuses an error value")
        text = v.hex() if isinstance(v, (bytes, bytearray)) else str(v)
        return {"ok": True, "op": "say", "out": text}
    if op == "cat":
        vals = [_eval_value(a, _depth) for a in args]
        if any(isinstance(v, Err) for v in vals):
            raise SemError("cat refuses error")
        if vals and all(isinstance(v, (bytes, bytearray)) for v in vals):
            return {"ok": True, "op": "cat", "value": b"".join(vals)}
        parts = []
        for v in vals:
            parts.append(v.hex() if isinstance(v, (bytes, bytearray)) else str(v))
        return {"ok": True, "op": "cat", "value": "".join(parts)}
    if op == "add":
        xs = [_eval_value(a, _depth) for a in args]
        if any(type(x) is not int for x in xs):
            raise SemError("add needs ints")
        return {"ok": True, "op": "add", "value": _fit(sum(xs))}
    if op == "sub":
        a, b = _eval_value(args[0], _depth), _eval_value(args[1], _depth)
        if type(a) is not int or type(b) is not int:
            raise SemError("sub needs ints")
        return {"ok": True, "op": "sub", "value": _fit(a - b)}
    if op == "eq":
        a, b = _eval_value(args[0], _depth), _eval_value(args[1], _depth)
        return {"ok": True, "op": "eq", "value": 1 if a == b else 0}
    if op == "not":
        v = _eval_value(args[0], _depth)
        return {"ok": True, "op": "not", "value": 0 if _truthy(v) else 1}
    if op == "if":
        cond = _truthy(_eval_value(args[0], _depth))
        pick = args[1] if cond else (args[2] if len(args) > 2 else {"op": "ok", "args": []})
        return eval_ast(pick, _depth=_depth + 1)
    if op == "len":
        inner = args[0]
        if inner["op"] in ("seq", "list", "map"):
            n = len(inner.get("args") or [])
        elif inner["op"] == "bytes":
            n = len(bytes.fromhex(str(inner["args"][0])))
        else:
            v = _eval_value(inner, _depth)
            if isinstance(v, (str, list, tuple, dict, bytes, bytearray)):
                n = len(v)
            else:
                raise SemError("len needs str, list, map, or bytes")
        return {"ok": True, "op": "len", "value": n}
    if op == "nth":
        inner, idx_n = args[0], args[1]
        i = _eval_value(idx_n, _depth)
        if type(i) is not int:
            raise SemError("nth index needs int")
        if inner["op"] in ("seq", "list"):
            xs = inner.get("args") or []
            if i < 0 or i >= len(xs):
                raise SemError("nth out of range")
            if xs[i]["op"] in VERBS:
                return eval_ast(xs[i], _depth=_depth + 1)
            return {"ok": True, "op": "nth", "value": _eval_value(xs[i], _depth)}
        v = _eval_value(inner, _depth)
        if isinstance(v, (bytes, bytearray)):
            if i < 0 or i >= len(v):
                raise SemError("nth out of range")
            return {"ok": True, "op": "nth", "value": v[i]}
        if isinstance(v, str):
            if i < 0 or i >= len(v):
                raise SemError("nth out of range")
            return {"ok": True, "op": "nth", "value": v[i]}
        seq = _as_seq(v)
        if i < 0 or i >= len(seq):
            raise SemError("nth out of range")
        return {"ok": True, "op": "nth", "value": seq[i]}
    if op == "err":
        msg = _eval_value(args[0], _depth)
        if not isinstance(msg, str):
            raise SemError("err needs str")
        return {"ok": True, "op": "err", "value": Err(msg)}
    if op == "iserr":
        v = _eval_value(args[0], _depth)
        return {"ok": True, "op": "iserr", "value": 1 if isinstance(v, Err) else 0}
    if op == "msg":
        v = _eval_value(args[0], _depth)
        if isinstance(v, Err):
            text = v.msg
        elif isinstance(v, str):
            text = v
        elif isinstance(v, (bytes, bytearray)):
            text = v.hex()
        else:
            raise SemError("msg needs err, str, or bytes")
        return {"ok": True, "op": "msg", "value": text}
    if op == "get":
        m = _eval_value(args[0], _depth)
        if not isinstance(m, dict):
            raise SemError("get needs map")
        k = _key_str(_eval_value(args[1], _depth))
        if k not in m:
            raise SemError("get missing key")
        return {"ok": True, "op": "get", "value": m[k]}
    if op == "has":
        m = _eval_value(args[0], _depth)
        if not isinstance(m, dict):
            raise SemError("has needs map")
        k = _key_str(_eval_value(args[1], _depth))
        return {"ok": True, "op": "has", "value": 1 if k in m else 0}
    if op == "keys":
        m = _eval_value(args[0], _depth)
        if not isinstance(m, dict):
            raise SemError("keys needs map")
        return {"ok": True, "op": "keys", "value": list(m.keys())}
    if op == "times":
        n = _eval_value(args[0], _depth)
        if type(n) is not int:
            raise SemError("times needs int")
        if n < 0 or n > MAX_TIMES:
            raise OverflowErr("times bound", detail={"n": n, "max": MAX_TIMES})
        outs: list[str] = []
        last: Any = 0
        for _ in range(n):
            step = eval_ast(args[1], _depth=_depth + 1)
            outs.extend(_collect_out(step))
            if "value" in step:
                last = step["value"]
            elif "out" in step:
                last = step["out"]
        result = {"ok": True, "op": "times", "n": n, "value": last}
        if outs:
            result["out"] = "\n".join(outs)
        return result
    raise SemError(f"unknown op {op}")
