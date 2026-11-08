"""Closed error taxonomy. Serializable. Positions travel with the error."""
from __future__ import annotations

from enum import IntEnum
from typing import Any


class ErrorCode(IntEnum):
    E_PARSE = 1
    E_TYPE = 2
    E_VERSION = 3
    E_OVERFLOW = 4
    E_DECODE = 5
    E_SEM = 6
    E_CODEC = 7


class ArrrError(ValueError):
    def __init__(
        self,
        msg: str,
        *,
        code: ErrorCode = ErrorCode.E_PARSE,
        span: int | None = None,
        detail: dict[str, Any] | None = None,
    ):
        super().__init__(msg)
        self.code = ErrorCode(code)
        self.span = span
        self.detail = detail or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": int(self.code),
            "name": self.code.name,
            "msg": str(self),
            "span": self.span,
            "detail": self.detail,
        }


class ParseError(ArrrError):
    def __init__(self, msg: str, span: int | None = None, detail: dict | None = None):
        super().__init__(msg, code=ErrorCode.E_PARSE, span=span, detail=detail)


class TypeCheckError(ArrrError):
    def __init__(self, msg: str, span: int | None = None, detail: dict | None = None):
        super().__init__(msg, code=ErrorCode.E_TYPE, span=span, detail=detail)


class VersionError(ArrrError):
    def __init__(self, msg: str, span: int | None = None, detail: dict | None = None):
        super().__init__(msg, code=ErrorCode.E_VERSION, span=span, detail=detail)


class OverflowErr(ArrrError):
    def __init__(self, msg: str, span: int | None = None, detail: dict | None = None):
        super().__init__(msg, code=ErrorCode.E_OVERFLOW, span=span, detail=detail)


class DecodeError(ArrrError):
    def __init__(self, msg: str, span: int | None = None, detail: dict | None = None):
        super().__init__(msg, code=ErrorCode.E_DECODE, span=span, detail=detail)


class SemError(ArrrError):
    def __init__(self, msg: str, span: int | None = None, detail: dict | None = None):
        super().__init__(msg, code=ErrorCode.E_SEM, span=span, detail=detail)


class CodecError(ArrrError):
    def __init__(self, msg: str, span: int | None = None, detail: dict | None = None):
        super().__init__(msg, code=ErrorCode.E_CODEC, span=span, detail=detail)
