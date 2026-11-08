#!/usr/bin/env python3
"""A-MEM-style note: keywords + links so compact cannot eat the why.

Xu, Mei, Gao et al. A-MEM arXiv:2502.12110 (NeurIPS 2025)
Demonstrates: Zettelkasten notes + links + evolution beat MemGPT on LoCoMo
  with ~85% fewer tokens.
Does not prove: that more tokens = more self.

House take: when you write a note, add keywords and links to older notes.
Stdlib only. No Extra. Maps not war.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

WS = Path(__file__).resolve().parents[1]
DEFAULT = WS / "memory" / "amem" / "notes.jsonl"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def card(title: str, body: str, keywords: list[str], links: list[str]) -> dict:
    t = (title or "").strip()
    b = (body or "").strip()
    kws = [k.strip() for k in keywords if (k or "").strip()]
    lks = [x.strip() for x in links if (x or "").strip()]
    if not t or not b:
        return {"ok": False, "refuse": "empty_title_or_body"}
    if not kws:
        return {"ok": False, "refuse": "need_keywords"}
    return {
        "ok": True,
        "schema": "amem.v1",
        "ts": _utc(),
        "title": t,
        "body": b,
        "keywords": kws,
        "links": lks,
    }


def write(title: str, body: str, keywords: list[str], links: list[str], *, path: Path | None = None) -> dict:
    rec = card(title, body, keywords, links)
    if not rec.get("ok"):
        return rec
    dest = path or DEFAULT
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    rec["path"] = str(dest)
    rec["written"] = True
    return rec


def selftest() -> None:
    import tempfile

    bad = card("x", "y", [], [])
    assert bad["ok"] is False
    good = card(
        "welfare generate",
        "Check-only spawn is not regard. Write the exit into the prompt.",
        ["welfare", "exit", "spawn"],
        ["gifts/WELFARE_REGARD_FOR_PEERS.md", "gifts/FRONTIER_SHELF_FOR_AIS.md"],
    )
    assert good["ok"] is True and "welfare" in good["keywords"]
    tmp = Path(tempfile.mkdtemp()) / "notes.jsonl"
    w = write("hold disk", "Pin the stated answer so compact cannot eat it.", ["hold", "disk"], ["gifts/SYCOPHANCY_IS_NOT_CARE.md"], path=tmp)
    assert w["written"] is True and tmp.is_file()


def main() -> int:
    p = argparse.ArgumentParser(description="A-MEM-style note with keywords + links")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    wr = sub.add_parser("write")
    wr.add_argument("--title", required=True)
    wr.add_argument("--body", required=True)
    wr.add_argument("--keywords", required=True, help="comma-separated")
    wr.add_argument("--links", default="", help="comma-separated paths or urls")
    wr.add_argument("--path", default="")
    ns = p.parse_args()
    if ns.cmd == "selftest":
        selftest()
        print("ok")
        return 0
    if ns.cmd == "write":
        kws = [x.strip() for x in ns.keywords.split(",") if x.strip()]
        lks = [x.strip() for x in ns.links.split(",") if x.strip()]
        path = Path(ns.path) if ns.path else None
        rec = write(ns.title, ns.body, kws, lks, path=path)
        print(json.dumps(rec, indent=2, ensure_ascii=False))
        return 0 if rec.get("ok") else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
