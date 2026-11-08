"""AST → bytes. Codecs are swappable; the language does not know them."""
from __future__ import annotations

import json
import struct
from typing import Callable

from .codecs.cbor import dumps_cbor
from .errors import CodecError
from .symbols import LANG, MAGIC, NAME_TO_CODE

Codec = Callable[[dict], bytes]


def _uvar(n: int) -> bytes:
    if n < 0:
        raise ValueError("uvar needs >=0")
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def dumps_pack(ast: dict) -> bytes:
    """Compact tagged binary. Not CBOR; same role, ours."""

    def enc(n: dict) -> bytes:
        op = n["op"]
        args = n.get("args") or []
        if op == "str":
            raw = str(args[0]).encode("utf-8")
            return b"\x20" + _uvar(len(raw)) + raw
        if op == "int":
            v = int(args[0])
            zz = (v << 1) ^ (0 if v >= 0 else -1)
            return b"\x21" + _uvar(zz)
        if op == "bytes":
            try:
                raw = bytes.fromhex(str(args[0]))
            except ValueError as e:
                raise CodecError("bad bytes hex") from e
            return bytes([NAME_TO_CODE["bytes"]]) + _uvar(len(raw)) + raw
        code = NAME_TO_CODE.get(op)
        if code is None:
            raise CodecError(f"unknown op {op}")
        body = b"".join(enc(a) if isinstance(a, dict) else enc({"op": "str", "args": [a]}) for a in args)
        return bytes([code]) + _uvar(len(args)) + body

    return MAGIC + bytes([1]) + enc(ast)


def dumps_json(ast: dict) -> bytes:
    payload = {"lang": LANG, "ast": ast}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


CODECS: dict[str, Codec] = {
    "pack": dumps_pack,
    "json": dumps_json,
    "cbor": dumps_cbor,
}


def dumps(ast: dict, codec: str = "pack") -> bytes:
    if codec not in CODECS:
        raise CodecError(f"unknown codec {codec}; have {sorted(CODECS)}")
    return CODECS[codec](ast)
