"""Arrr-bay CLI — compile, roundtrip, send, recv."""
from __future__ import annotations

import argparse
import json
import sys

from .core import compile, decode, encode, readable, recv, roundtrip, run, send
from .errors import ParseError, SemError


def _out(obj) -> None:
    if isinstance(obj, (bytes, bytearray)):
        sys.stdout.buffer.write(obj)
        return
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def selftest() -> int:
    import unittest

    from .tests.test_arrr import TestArrr
    from .tests.test_install import TestInstall
    from .tests.test_lang import TestLang
    from .tests.test_umbral2 import TestUmbral2

    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (TestArrr, TestUmbral2, TestInstall, TestLang):
        suite.addTests(loader.loadTestsFromTestCase(case))
    r = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if r.wasSuccessful() else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="arrr", description="Arrr-bay tongue")
    p.add_argument("--selftest", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    for name in ("parse", "run", "readable", "roundtrip"):
        sp = sub.add_parser(name)
        sp.add_argument("src")
        if name == "roundtrip":
            sp.add_argument("--codec", default="pack", choices=("pack", "json", "cbor"))
    se = sub.add_parser("send")
    se.add_argument("src")
    se.add_argument("--codec", default="pack", choices=("pack", "json", "cbor"))
    sub.add_parser("recv")
    sub.add_parser("decode")
    args = p.parse_args(argv)
    if args.selftest:
        return selftest()
    try:
        if args.cmd == "parse":
            _out(compile(args.src))
        elif args.cmd == "run":
            r = run(args.src)
            if r.get("out") is not None:
                sys.stdout.write(str(r["out"]))
                if not str(r["out"]).endswith("\n"):
                    sys.stdout.write("\n")
            else:
                _out(r)
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
