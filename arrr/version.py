"""Protocol and codec version. Unknown versions hard-reject. No soft fallback."""
from __future__ import annotations

from .errors import VersionError

PROTOCOL_VERSION = 1
PACK_VERSION = 1
CBOR_VERSION = 1
SUPPORTED = frozenset({1})


def check_protocol(v: object, *, where: str = "protocol") -> int:
    try:
        n = int(v)  # type: ignore[arg-type]
    except (TypeError, ValueError) as e:
        raise VersionError(f"{where}: missing version", detail={"where": where, "v": v}) from e
    if n not in SUPPORTED:
        raise VersionError(
            f"{where}: unsupported version {n}",
            detail={"where": where, "v": n, "supported": sorted(SUPPORTED)},
        )
    return n


def check_codec(v: object, *, where: str = "codec") -> int:
    return check_protocol(v, where=where)
