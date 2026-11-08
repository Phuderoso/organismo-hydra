"""On-wire envelope. Body codec is a field, not the language."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .decoder import DecodeError, loads, sniff
from .encoder import dumps
from .symbols import LANG, MAGIC
from .version import check_protocol


def wrap(ast: dict, codec: str = "pack", meta: dict[str, Any] | None = None) -> bytes:
    body = dumps(ast, codec=codec)
    digest = hashlib.sha256(body).hexdigest()
    head = {
        "v": 1,
        "lang": LANG,
        "codec": codec,
        "sha256": digest,
        "meta": meta or {},
        "n": len(body),
    }
    head_bytes = json.dumps(head, separators=(",", ":"), sort_keys=True).encode("utf-8")
    # ENV1 + u32 head_len + head + body
    return b"ENV1" + len(head_bytes).to_bytes(4, "big") + head_bytes + body


def unwrap(blob: bytes) -> dict:
    if blob.startswith(b"ENV1"):
        n = int.from_bytes(blob[4:8], "big")
        head = json.loads(blob[8 : 8 + n].decode("utf-8"))
        body = blob[8 + n :]
        if head.get("n") != len(body):
            raise DecodeError("envelope length mismatch")
        got = hashlib.sha256(body).hexdigest()
        if head.get("sha256") != got:
            raise DecodeError("envelope sha mismatch")
        check_protocol(head.get("v"), where="env")
        ast = loads(body, codec=head.get("codec"))
        return {"head": head, "ast": ast}
    # bare codec
    ast = loads(blob)
    return {"head": {"codec": sniff(blob), "lang": LANG, "bare": True}, "ast": ast}


def recover(blob: bytes) -> dict:
    """Recipient path: bytes → AST. Exact vs sender AST."""
    return unwrap(blob)["ast"]
