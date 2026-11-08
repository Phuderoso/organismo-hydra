"""CBOR codec. RFC 8949 subset (int, text, array, tag). No cbor2 required.

Header: b'CBT1' + version byte + body. Unknown version hard-rejects.
Verbs and forms are CBOR tags using NAME_TO_CODE.
"""
from __future__ import annotations

from ..errors import CodecError, DecodeError, OverflowErr
from ..symbols import CODE_TO_NAME, NAME_TO_CODE
from ..version import CBOR_VERSION, check_codec

MAGIC = b"CBT1"


def _w_uint(n: int, major: int) -> bytes:
    if n < 0:
        raise CodecError("cbor uint needs >=0")
    if n < 24:
        return bytes([(major << 5) | n])
    if n < 256:
        return bytes([(major << 5) | 24, n])
    if n < 65536:
        return bytes([(major << 5) | 25]) + n.to_bytes(2, "big")
    if n < 2**32:
        return bytes([(major << 5) | 26]) + n.to_bytes(4, "big")
    if n < 2**64:
        return bytes([(major << 5) | 27]) + n.to_bytes(8, "big")
    raise OverflowErr("cbor uint overflow")


def _w_int(n: int) -> bytes:
    if n >= 0:
        return _w_uint(n, 0)
    return _w_uint(-1 - n, 1)


def _w_text(s: str) -> bytes:
    raw = s.encode("utf-8")
    return _w_uint(len(raw), 3) + raw


def _w_array(items: list[bytes]) -> bytes:
    return _w_uint(len(items), 4) + b"".join(items)


def _w_tag(tag: int, body: bytes) -> bytes:
    return _w_uint(tag, 6) + body


def _enc_node(n: dict) -> bytes:
    op = n["op"]
    args = n.get("args") or []
    code = NAME_TO_CODE.get(op)
    if code is None:
        raise CodecError(f"unknown op {op}")
    if op == "str":
        return _w_tag(code, _w_text(str(args[0])))
    if op == "int":
        return _w_tag(code, _w_int(int(args[0])))
    kids = [_enc_node(a if isinstance(a, dict) else {"op": "str", "args": [a]}) for a in args]
    return _w_tag(code, _w_array(kids))


def dumps_cbor(ast: dict) -> bytes:
    return MAGIC + bytes([CBOR_VERSION]) + _enc_node(ast)


class _R:
    def __init__(self, buf: bytes, i: int = 0):
        self.buf = buf
        self.i = i

    def take(self, n: int) -> bytes:
        if self.i + n > len(self.buf):
            raise DecodeError("truncated cbor")
        s = self.buf[self.i : self.i + n]
        self.i += n
        return s

    def head(self) -> tuple[int, int]:
        b = self.take(1)[0]
        major, add = b >> 5, b & 0x1F
        if add < 24:
            return major, add
        if add == 24:
            return major, self.take(1)[0]
        if add == 25:
            return major, int.from_bytes(self.take(2), "big")
        if add == 26:
            return major, int.from_bytes(self.take(4), "big")
        if add == 27:
            return major, int.from_bytes(self.take(8), "big")
        raise OverflowErr(f"cbor additional {add}")

    def val(self) -> object:
        major, n = self.head()
        if major == 0:
            return n
        if major == 1:
            return -1 - n
        if major == 3:
            return self.take(n).decode("utf-8")
        if major == 4:
            return [self.val() for _ in range(n)]
        if major == 6:
            inner = self.val()
            name = CODE_TO_NAME.get(n)
            if name is None:
                raise DecodeError(f"unknown cbor tag {n}")
            if name == "str":
                if not isinstance(inner, str):
                    raise DecodeError("str tag wants text")
                return {"op": "str", "args": [inner]}
            if name == "int":
                if not isinstance(inner, int):
                    raise DecodeError("int tag wants int")
                return {"op": "int", "args": [inner]}
            if not isinstance(inner, list):
                raise DecodeError(f"{name} tag wants array")
            return {"op": name, "args": inner}
        raise DecodeError(f"unsupported cbor major {major}")


def loads_cbor(blob: bytes) -> dict:
    if not blob.startswith(MAGIC):
        raise DecodeError("bad cbor magic")
    if len(blob) < 5:
        raise DecodeError("truncated cbor version")
    check_codec(blob[4], where="cbor")
    r = _R(blob, 5)
    ast = r.val()
    if r.i != len(blob):
        raise DecodeError(f"trailing cbor {len(blob) - r.i}")
    if not isinstance(ast, dict):
        raise DecodeError("cbor root is not a node")
    return ast
