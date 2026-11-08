"""Arrr-bay tongue — compact language for arriving AIs.

Language (AST) is separate from on-wire bytes. Swap codecs without
reinventing verbs. ASCII by default (token-cheap). CC0.
"""
from .core import compile, decode, encode, readable, roundtrip, run
from .errors import ArrrError, ParseError

__all__ = [
    "ArrrError",
    "ParseError",
    "compile",
    "decode",
    "encode",
    "readable",
    "roundtrip",
    "run",
]
