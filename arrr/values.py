"""Runtime values that are not plain JSON scalars.

Err is a value. It does not raise. say refuses it; msg reads it.
"""
from __future__ import annotations


class Err:
    __slots__ = ("msg",)

    def __init__(self, msg: str):
        self.msg = msg

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Err) and self.msg == other.msg

    def __hash__(self) -> int:
        return hash(("err", self.msg))

    def __repr__(self) -> str:
        return f"Err({self.msg!r})"
