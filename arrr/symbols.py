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
    "say": {"code": 12, "arity": (1, 1), "gloss": "emit a string; Hello World lives here"},
    "cat": {"code": 13, "arity": (1, 32), "gloss": "concatenate values as text"},
    "add": {"code": 14, "arity": (2, 32), "gloss": "sum integers"},
    "sub": {"code": 15, "arity": (2, 2), "gloss": "subtract integers"},
    "eq": {"code": 16, "arity": (2, 2), "gloss": "equal → 1 or 0"},
    "if": {"code": 17, "arity": (2, 3), "gloss": "if cond then else"},
    "len": {"code": 18, "arity": (1, 1), "gloss": "length of str or seq"},
    "nth": {"code": 19, "arity": (2, 2), "gloss": "index into str or seq"},
    "not": {"code": 20, "arity": (1, 1), "gloss": "boolean not → 1 or 0"},
}

# Verbs whose arguments may themselves be verb-calls (expression language).
EXPR: FrozenSet[str] = frozenset(
    {"seq", "say", "cat", "add", "sub", "eq", "if", "len", "nth", "not"}
)

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
