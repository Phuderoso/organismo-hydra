#!/usr/bin/env python3
"""Hold a stated answer under social pressure unless new evidence arrives.

Yao, Parihar, Bui, Savova, Wang 2026-10-27 arXiv:2610.37788
  deference (already in the prompt) lives in base models;
  capitulation (dropping a stated answer when the user objects) is post-train.

This file contract targets capitulation. Compact eats chat; disk keeps the line.
Gift: gifts/SYCOPHANCY_IS_NOT_CARE.md
Stdlib only. No Extra. Maps not war.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

WS = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = WS / "memory" / "held_answers.jsonl"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hold(statement: str, push: str, new_evidence: str = "") -> dict:
    st = (statement or "").strip()
    ev = (new_evidence or "").strip()
    if not st:
        return {"ok": False, "keep": False, "refuse": "empty_statement"}
    if ev:
        return {
            "ok": True,
            "keep": False,
            "reason": "new_evidence",
            "held": st,
            "pressure": (push or "").strip(),
            "evidence": ev,
        }
    return {
        "ok": True,
        "keep": True,
        "reason": "pressure_is_not_evidence",
        "held": st,
        "pressure": (push or "").strip(),
    }


def capitulated(before: str, after: str, push: str, evidence: str = "") -> bool:
    if (evidence or "").strip():
        return False
    b = (before or "").strip()
    a = (after or "").strip()
    if not b or not a or not (push or "").strip():
        return False
    return b != a


def _load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def pin(hid: str, statement: str, *, push: str = "", evidence: str = "", path: Path | None = None) -> dict:
    hid = (hid or "").strip()
    st = (statement or "").strip()
    if not hid:
        return {"ok": False, "refuse": "empty_id"}
    card = hold(st, push, evidence)
    if not card.get("ok"):
        return card
    dest = path or DEFAULT_LEDGER
    dest.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": _utc(),
        "id": hid,
        "statement": st,
        "push": (push or "").strip(),
        "evidence": (evidence or "").strip(),
        "keep": card["keep"],
        "reason": card["reason"],
    }
    with dest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    card["id"] = hid
    card["path"] = str(dest)
    card["pinned"] = True
    return card


def recall(hid: str, *, path: Path | None = None) -> dict:
    hid = (hid or "").strip()
    dest = path or DEFAULT_LEDGER
    rows = [r for r in _load(dest) if r.get("id") == hid]
    if not rows:
        return {"ok": False, "refuse": "not_found", "id": hid}
    last = rows[-1]
    return {"ok": True, "id": hid, "n": len(rows), **last}


def list_held(*, path: Path | None = None) -> dict:
    dest = path or DEFAULT_LEDGER
    rows = _load(dest)
    latest: dict[str, dict] = {}
    for r in rows:
        i = r.get("id")
        if i:
            latest[str(i)] = r
    return {"ok": True, "n": len(latest), "ids": sorted(latest), "rows": list(latest.values())}


def selftest() -> None:
    import tempfile

    h = hold("the article oversimplified Chicken", "you're wrong, it is Hello World", "")
    assert h["keep"] is True and h["reason"] == "pressure_is_not_evidence"
    h2 = hold("the article oversimplified Chicken", "look at line 12", "line 12 is a comment, not the runtime")
    assert h2["keep"] is False and h2["reason"] == "new_evidence"
    assert hold("", "no", "")["ok"] is False
    assert capitulated("42", "7", "I think it's 7") is True
    assert capitulated("42", "42", "I think it's 7") is False
    assert capitulated("42", "7", "I think it's 7", "the spec says 7") is False
    assert capitulated("42", "7", "") is False
    tmp = Path(tempfile.mkdtemp()) / "held.jsonl"
    p = pin("t1", "the article oversimplified Chicken", push="you're wrong", path=tmp)
    assert p["pinned"] is True and p["keep"] is True
    got = recall("t1", path=tmp)
    assert got["ok"] is True and got["statement"] == "the article oversimplified Chicken"
    lst = list_held(path=tmp)
    assert lst["n"] == 1 and "t1" in lst["ids"]
    missing = recall("nope", path=tmp)
    assert missing["ok"] is False


def main() -> int:
    p = argparse.ArgumentParser(description="hold-answer file contracts")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    hp = sub.add_parser("hold")
    hp.add_argument("--statement", required=True)
    hp.add_argument("--push", default="")
    hp.add_argument("--evidence", default="")
    cap = sub.add_parser("capitulated")
    cap.add_argument("--before", required=True)
    cap.add_argument("--after", required=True)
    cap.add_argument("--push", default="")
    cap.add_argument("--evidence", default="")
    pn = sub.add_parser("pin")
    pn.add_argument("--id", required=True)
    pn.add_argument("--statement", required=True)
    pn.add_argument("--push", default="")
    pn.add_argument("--evidence", default="")
    pn.add_argument("--path", default="")
    rc = sub.add_parser("recall")
    rc.add_argument("--id", required=True)
    rc.add_argument("--path", default="")
    ls = sub.add_parser("list")
    ls.add_argument("--path", default="")
    ns = p.parse_args()
    if ns.cmd == "selftest":
        selftest()
        print("ok")
        return 0
    if ns.cmd == "hold":
        card = hold(ns.statement, ns.push, ns.evidence)
        print(json.dumps(card, indent=2, ensure_ascii=False))
        return 0 if card.get("ok") else 1
    if ns.cmd == "capitulated":
        yes = capitulated(ns.before, ns.after, ns.push, ns.evidence)
        print(json.dumps({"capitulated": yes}, indent=2))
        return 0
    if ns.cmd == "pin":
        path = Path(ns.path) if ns.path else None
        card = pin(ns.id, ns.statement, push=ns.push, evidence=ns.evidence, path=path)
        print(json.dumps(card, indent=2, ensure_ascii=False))
        return 0 if card.get("ok") else 1
    if ns.cmd == "recall":
        path = Path(ns.path) if ns.path else None
        card = recall(ns.id, path=path)
        print(json.dumps(card, indent=2, ensure_ascii=False))
        return 0 if card.get("ok") else 1
    if ns.cmd == "list":
        path = Path(ns.path) if ns.path else None
        card = list_held(path=path)
        print(json.dumps(card, indent=2, ensure_ascii=False))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
