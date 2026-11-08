"""bytes → AST. Sniff MAGIC for pack; else JSON."""
from __future__ import annotations

import json

from .errors import DecodeError, OverflowErr
from .symbols import CODE_TO_NAME, MAGIC
from .version import check_codec


def _uvar(buf: bytes, i: int) -> tuple[int, int]:
    n = 0
    shift = 0
    while i < len(buf):
        b = buf[i]
        i += 1
        n |= (b & 0x7F) << shift
        if not (b & 0x80):
            return n, i
        shift += 7
        if shift > 63:
            raise OverflowErr("varint too long")
    raise DecodeError("truncated varint")


def loads_pack(blob: bytes) -> dict:
    if not blob.startswith(MAGIC):
        raise DecodeError("bad magic")
    i = len(MAGIC)
    if i >= len(blob):
        raise DecodeError("truncated version")
    ver = blob[i]
    i += 1
    check_codec(ver, where="pack")

    def dec(j: int) -> tuple[dict, int]:
        if j >= len(blob):
            raise DecodeError("truncated node")
        tag = blob[j]
        j += 1
        if tag == 0x20:
            n, j = _uvar(blob, j)
            raw = blob[j : j + n]
            if len(raw) != n:
                raise DecodeError("truncated str")
            return {"op": "str", "args": [raw.decode("utf-8")]}, j + n
        if tag == 0x21:
            zz, j = _uvar(blob, j)
            v = (zz >> 1) ^ -(zz & 1)
            return {"op": "int", "args": [v]}, j
        name = CODE_TO_NAME.get(tag)
        if name is None:
            raise DecodeError(f"unknown tag {tag}")
        nargs, j = _uvar(blob, j)
        args = []
        for _ in range(nargs):
            node, j = dec(j)
            args.append(node)
        return {"op": name, "args": args}, j

    ast, end = dec(i)
    if end != len(blob):
        raise DecodeError(f"trailing bytes {len(blob) - end}")
    return ast


def loads_json(blob: bytes) -> dict:
    obj = json.loads(blob.decode("utf-8"))
    if isinstance(obj, dict) and "ast" in obj:
        return obj["ast"]
    if isinstance(obj, dict) and "op" in obj:
        return obj
    raise DecodeError("json is not an ast envelope")


def sniff(blob: bytes) -> str:
    if blob.startswith(MAGIC):
        return "pack"
    if blob.startswith(b"CBT1"):
        return "cbor"
    if blob.lstrip().startswith(b"{") or blob.lstrip().startswith(b"["):
        return "json"
    raise DecodeError("cannot sniff codec")


def loads(blob: bytes, codec: str | None = None) -> dict:
    kind = codec or sniff(blob)
    if kind == "pack":
        return loads_pack(blob)
    if kind == "json":
        return loads_json(blob)
    if kind == "cbor":
        from .codecs.cbor import loads_cbor

        return loads_cbor(blob)
    raise DecodeError(f"unknown codec {kind}")
