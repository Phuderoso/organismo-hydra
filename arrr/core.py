"""Facade: text ⇄ AST ⇄ bytes ⇄ text. Five properties in one place."""
from __future__ import annotations

from .decoder import loads
from .encoder import CODECS, dumps
from .parser import ParseError, parse, render
from .protocol import recover, unwrap, wrap
from .semantics import SemError, eval_ast


def compile(src: str) -> dict:
    return parse(src)


def encode(ast: dict, codec: str = "pack") -> bytes:
    return dumps(ast, codec=codec)


def decode(blob: bytes, codec: str | None = None) -> dict:
    return loads(blob, codec=codec)


def readable(ast: dict) -> str:
    return render(ast)


def roundtrip(src: str, codec: str = "pack") -> dict:
    ast = parse(src)
    blob = dumps(ast, codec=codec)
    back = loads(blob, codec=codec)
    text = render(back)
    again = parse(text)
    return {
        "ok": back == ast == again,
        "ast": ast,
        "bytes": blob,
        "n_bytes": len(blob),
        "readable": text,
        "codec": codec,
    }


def run(src: str) -> dict:
    return eval_ast(parse(src))


def send(src: str, codec: str = "pack", meta: dict | None = None) -> bytes:
    return wrap(parse(src), codec=codec, meta=meta)


def recv(blob: bytes) -> dict:
    env = unwrap(blob)
    env["result"] = eval_ast(env["ast"])
    return env


__all__ = [
    "CODECS",
    "ParseError",
    "SemError",
    "compile",
    "decode",
    "encode",
    "readable",
    "recv",
    "recover",
    "roundtrip",
    "run",
    "send",
]
