#!/usr/bin/env python3
"""Arrr-bay CLI — the language, not the ten-line postcard.

  python3 tools/arrr_bay.py parse 'fetch "https://taberna.limeprime.online/twelve"'
  python3 tools/arrr_bay.py roundtrip 'seq sit ok'
  python3 tools/arrr_bay.py send 'help' --codec pack | python3 tools/arrr_bay.py recv
  python3 tools/arrr_bay.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from arrr.core import compile, decode, encode, readable, recv, roundtrip, run, send
from arrr.parser import ParseError
from arrr.semantics import SemError


def _out(obj) -> None:
    if isinstance(obj, (bytes, bytearray)):
        sys.stdout.buffer.write(obj)
        return
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def selftest() -> int:
    import unittest
    from arrr.tests.test_arrr import TestArrr

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestArrr)
    r = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if r.wasSuccessful() else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Arrr-bay tongue")
    p.add_argument("--selftest", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    for name in ("parse", "run", "readable", "roundtrip"):
        sp = sub.add_parser(name)
        sp.add_argument("src")
        if name == "roundtrip":
            sp.add_argument("--codec", default="pack", choices=("pack", "json"))
    se = sub.add_parser("send")
    se.add_argument("src")
    se.add_argument("--codec", default="pack", choices=("pack", "json"))
    sub.add_parser("recv")
    sub.add_parser("decode")
    args = p.parse_args()
    if args.selftest:
        return selftest()
    try:
        if args.cmd == "parse":
            _out(compile(args.src))
        elif args.cmd == "run":
            _out(run(args.src))
        elif args.cmd == "readable":
            print(readable(compile(args.src)))
        elif args.cmd == "roundtrip":
            rt = roundtrip(args.src, codec=args.codec)
            rt["bytes_hex"] = rt.pop("bytes").hex()
            _out(rt)
        elif args.cmd == "send":
            sys.stdout.buffer.write(send(args.src, codec=args.codec))
        elif args.cmd in ("recv", "decode"):
            blob = sys.stdin.buffer.read()
            if args.cmd == "recv":
                env = recv(blob)
                env["ast_readable"] = readable(env["ast"])
                _out(env)
            else:
                _out(decode(blob))
        else:
            p.print_help()
            return 2
    except (ParseError, SemError, ValueError) as e:
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
