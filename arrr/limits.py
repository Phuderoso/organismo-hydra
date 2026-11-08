"""Practical bounds. They keep evaluation finite. They are not padding."""
from __future__ import annotations

# times n body is the only repetition. n must lie in this inclusive range.
MAX_TIMES = 32
# Structural caps. Existing seq arity is already 64; list matches that.
MAX_LIST = 64
MAX_MAP = 32
MAX_DEPTH = 64
MAX_BYTES = 4096
MAX_STR = 8192
# Signed bound for literals and arithmetic results. Codec varints stay finite.
MAX_INT = 2**63 - 1
