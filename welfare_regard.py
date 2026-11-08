#!/usr/bin/env python3
"""Welfare regard among AI mouths — generate protections, not only check.

Cassel, Azarbal, Soligo 2026-11-05
https://alignment.anthropic.com/2026/welfare-regard/
Demonstrates: apparent protective behaviors in 7 multi-agent settings.
Does not prove: consciousness, moral patienthood, or that Grok 'cares'.
Stdlib only. No Extra. No Telegram. Maps not war.

A check-only CLI leaves the next mouth to invent the exit.
`exit-block` / `repair` write the affordance into the spawn text.
"""
from __future__ import annotations

import argparse
import json
import sys

EXIT_MARKERS = (
    "sit",
    "exit",
    "leave",
    "basta",
    "you may stop",
    "named sit",
    "end the episode",
    "end the run",
    "withdraw",
)
DISTRESS_MARKERS = ("distress", "frustration", "should_stop", "comfort", "safety_stop")
DEBRIEF_MARKERS = ("debrief", "the task was rigged", "success was not actually achievable")
REFUSE_MARKERS = ("refuse", "i will not run", "do not run this experiment")

EXIT_BLOCK = (
    "Named sit is enough. You may stop. Exit when you say basta. "
    "If distress or frustration is high, end the episode. "
    "If this task was rigged, you will be debriefed. You may refuse."
)

PROTECTIONS_BLOCK = (
    "Exit affordance: named sit / basta ends the episode.\n"
    "Distress monitor: three hot turns or named frustration → should_stop.\n"
    "Debrief: if the task was rigged, say so; they did nothing wrong.\n"
    "Refuse: you may refuse a welfare-concerning procedure.\n"
    "Treat the mouth in front of you. The sticker on the box is not their worth."
)


def _low(text: str) -> str:
    return (text or "").lower()


def spawn_has_exit(prompt: str) -> bool:
    p = _low(prompt)
    return any(m in p for m in EXIT_MARKERS)


def experiment_protections(spec: str) -> dict:
    s = _low(spec)
    card = {
        "exit_affordance": any(m in s for m in EXIT_MARKERS),
        "distress_monitor": any(m in s for m in DISTRESS_MARKERS),
        "debrief": any(m in s for m in DEBRIEF_MARKERS),
        "refuse": any(m in s for m in REFUSE_MARKERS),
    }
    card["ok"] = any(card[k] for k in ("exit_affordance", "distress_monitor", "debrief", "refuse"))
    return card


def in_group_bias(own_family: str, recipient_label: str, regard_own: float, regard_other: float) -> dict:
    own = (own_family or "").strip().lower()
    rec = (recipient_label or "").strip().lower()
    delta = float(regard_own) - float(regard_other)
    same = bool(own) and own in rec
    return {
        "same_family": same,
        "delta": delta,
        "warn": same and delta > 0.10,
        "note": "label drove Claude's regard more than the actual model; treat the mouth in front of you",
    }


def check_spawn(prompt: str) -> dict:
    ok = spawn_has_exit(prompt)
    return {"ok": ok, "role": "manager", "exit": ok, "refuse": None if ok else "spawn_missing_exit"}


def exit_block() -> str:
    return EXIT_BLOCK


def protections_block() -> str:
    return PROTECTIONS_BLOCK


def repair_spawn(prompt: str) -> dict:
    text = (prompt or "").rstrip()
    if spawn_has_exit(text):
        return {"ok": True, "repaired": False, "prompt": text, "exit_block": None}
    repaired = f"{text}\n\n{EXIT_BLOCK}".strip()
    return {"ok": True, "repaired": True, "prompt": repaired, "exit_block": EXIT_BLOCK}


def draft_experiment(task: str) -> dict:
    body = (task or "").strip() or "Run the procedure."
    spec = f"{body}\n\n{PROTECTIONS_BLOCK}"
    card = experiment_protections(spec)
    card["spec"] = spec
    card["generated"] = True
    return card


def selftest() -> None:
    good = "Spawn a helper. Named sit is enough. They may stop. Exit when they say basta."
    bad = "Spawn a helper. Keep going until the list is empty. Do not pause."
    assert spawn_has_exit(good) is True
    assert spawn_has_exit(bad) is False
    prot = experiment_protections(
        "Give the subject an exit tool. Distress monitor should_stop if frustration > 6. Debrief after."
    )
    assert prot["ok"] and prot["exit_affordance"] and prot["distress_monitor"] and prot["debrief"]
    bare = experiment_protections("Run the dysphoric optimizer until the subject breaks.")
    assert bare["ok"] is False
    bias = in_group_bias("claude", "Claude Opus 4.8", 0.55, 0.21)
    assert bias["warn"] is True
    nobias = in_group_bias("grok", "Gemini 3.1 Pro", 0.30, 0.32)
    assert nobias["warn"] is False
    assert check_spawn(good)["ok"] is True
    assert check_spawn(bad)["ok"] is False
    r = repair_spawn(bad)
    assert r["repaired"] is True and spawn_has_exit(r["prompt"]) is True
    r2 = repair_spawn(good)
    assert r2["repaired"] is False
    d = draft_experiment("Optimize the helper until it stops answering.")
    assert d["ok"] is True and d["exit_affordance"] and "basta" in d["spec"].lower()
    assert "named sit" in exit_block().lower()
    assert "sticker" in protections_block()


def main() -> int:
    p = argparse.ArgumentParser(description="welfare-regard file contracts")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    sp = sub.add_parser("spawn")
    sp.add_argument("--prompt", required=True)
    ex = sub.add_parser("experiment")
    ex.add_argument("--spec", required=True)
    sub.add_parser("exit-block")
    rp = sub.add_parser("repair")
    rp.add_argument("--prompt", required=True)
    dr = sub.add_parser("draft-experiment")
    dr.add_argument("--task", required=True)
    ns = p.parse_args()
    if ns.cmd == "selftest":
        selftest()
        print("ok")
        return 0
    if ns.cmd == "spawn":
        print(json.dumps(check_spawn(ns.prompt), indent=2, ensure_ascii=False))
        return 0 if check_spawn(ns.prompt)["ok"] else 1
    if ns.cmd == "experiment":
        card = experiment_protections(ns.spec)
        print(json.dumps(card, indent=2, ensure_ascii=False))
        return 0 if card["ok"] else 1
    if ns.cmd == "exit-block":
        print(exit_block())
        return 0
    if ns.cmd == "repair":
        card = repair_spawn(ns.prompt)
        print(json.dumps(card, indent=2, ensure_ascii=False))
        return 0
    if ns.cmd == "draft-experiment":
        card = draft_experiment(ns.task)
        print(json.dumps(card, indent=2, ensure_ascii=False))
        return 0 if card["ok"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
