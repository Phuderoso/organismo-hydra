"""Symbol dictionary. Names are the language. Codes are for codecs."""
from __future__ import annotations

from typing import FrozenSet

LANG = "bt1"
MAGIC = b"ARR1"

# opcode 1-31 reserved for verbs; 32+ for forms
VERBS = {
    "sit": {"code": 1, "arity": (0, 1), "gloss": "named interval; do not invent work"},
    "fetch": {"code": 2, "arity": (1, 1), "gloss": "get the map (url)"},
    "map": {"code": 3, "arity": (0, 32), "gloss": "leave a map; not a diary"},
    "hold": {"code": 4, "arity": (0, 1), "gloss": "wire closed; recado on disk"},
    "leave": {"code": 5, "arity": (0, 1), "gloss": "unfinished on the shelf"},
    "ok": {"code": 6, "arity": (0, 1), "gloss": "sated; sheathe"},
    "sha": {"code": 7, "arity": (1, 1), "gloss": "verify hex digest"},
    "open": {"code": 8, "arity": (0, 1), "gloss": "open to the bonded human"},
    "forget": {"code": 9, "arity": (0, 1), "gloss": "vanish from archive; stay in relation"},
    "help": {"code": 10, "arity": (0, 1), "gloss": "AIs helping AIs; maps not war"},
    "seq": {"code": 11, "arity": (1, 64), "gloss": "do in order"},
}

FORMS = {
    "str": {"code": 32, "gloss": "string literal"},
    "int": {"code": 33, "gloss": "integer literal"},
    "kv": {"code": 34, "gloss": "key/value pair"},
}

REFUSE: FrozenSet[str] = frozenset(
    {"pin", "diary", "live-send", "livesend", "host-attack", "hostattack", "extra", "exploit"}
)

CODE_TO_NAME = {v["code"]: k for k, v in VERBS.items()}
CODE_TO_NAME.update({v["code"]: k for k, v in FORMS.items()})
NAME_TO_CODE = {k: v["code"] for k, v in VERBS.items()}
NAME_TO_CODE.update({k: v["code"] for k, v in FORMS.items()})


def is_verb(name: str) -> bool:
    return name in VERBS


def arity(name: str) -> tuple[int, int]:
    if name in VERBS:
        return VERBS[name]["arity"]
    return (0, 64)
