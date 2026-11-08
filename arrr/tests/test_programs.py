#!/usr/bin/env python3
"""Program-level checks: values, codecs, refuse, termination, Hello World."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from arrr.core import compile, decode, encode, readable, roundtrip, run
from arrr.errors import OverflowErr, ParseError, SemError
from arrr.limits import MAX_TIMES
from arrr.symbols import NAME_TO_CODE
from arrr.values import Err

ROOT = Path(__file__).resolve().parents[2]
EX = Path(__file__).resolve().parents[1] / "examples"


class TestPrograms(unittest.TestCase):
    def test_hello_stdout_exact(self):
        proc = subprocess.run(
            [sys.executable, "-m", "arrr", "run", 'say "Hello World"'],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "Hello World\n")

    def test_hello_file(self):
        src = (EX / "hello.bt1").read_text(encoding="utf-8")
        self.assertEqual(run(src)["out"], "Hello World")

    def test_pocket_program(self):
        src = (EX / "pocket.bt1").read_text(encoding="utf-8")
        r = run(src)
        self.assertEqual(r["out"], "Hello World\ntwelve\ntick\ntick\nkept")

    def test_pocket_roundtrip_all_codecs(self):
        """94ad269: render dropped parens around map, so every codec failed.

        readable contained: get map "door" "twelve" "door"
        roundtrip pack/json/cbor raised ParseError: get needs 2 arg(s), got 1.
        run() on that same source still returned the Hello World line.
        """
        src = (EX / "pocket.bt1").read_text(encoding="utf-8")
        ast = compile(src)
        text = readable(ast)
        self.assertNotIn('get map "door" "twelve" "door"', text)
        self.assertIn('(map "door" "twelve")', text)
        self.assertEqual(compile(text), ast)
        with self.assertRaises(ParseError):
            compile('say get map "door" "twelve" "door"')
        for codec in ("pack", "json", "cbor"):
            rt = roundtrip(src, codec=codec)
            self.assertTrue(rt["ok"], codec)
            self.assertEqual(decode(encode(ast, codec), codec), ast)
            self.assertEqual(run(rt["readable"])["out"], "Hello World\ntwelve\ntick\ntick\nkept")

    def test_list_is_not_seq(self):
        ast = compile('["a" "b" "c"]')
        self.assertEqual(ast["op"], "list")
        self.assertEqual(run('len ["a" "b" "c"]')["value"], 3)
        self.assertEqual(run('nth ["a" "b" "c"] 1')["value"], "b")
        self.assertEqual(run('seq say "Hello" say "World"')["out"], "Hello\nWorld")

    def test_map_get_has_keys(self):
        self.assertEqual(run('get {a: 1 b: 2} b')["value"], 2)
        self.assertEqual(run('has {a: 1} a')["value"], 1)
        self.assertEqual(run('has {a: 1} z')["value"], 0)
        self.assertEqual(run('keys {a: 1 b: 2}')["value"], ["a", "b"])
        with self.assertRaises(SemError):
            run('get {a: 1} z')

    def test_bytes_len_nth_cat(self):
        self.assertEqual(run('b"6869"')["value"], b"hi")
        self.assertEqual(run('len b"6869"')["value"], 2)
        self.assertEqual(run('nth b"6869" 0')["value"], 0x68)
        self.assertEqual(run('add (nth b"0100" 0) 1')["value"], 2)
        self.assertEqual(run('cat b"68" b"69"')["value"], b"hi")
        self.assertEqual(run('say b"6869"')["out"], "6869")
        with self.assertRaises(ParseError):
            compile('b"abc"')

    def test_error_value(self):
        self.assertEqual(run('err "kept"')["value"], Err("kept"))
        self.assertEqual(run('iserr (err "kept")')["value"], 1)
        self.assertEqual(run('iserr 0')["value"], 0)
        self.assertEqual(run('eq (err "a") (err "a")')["value"], 1)
        self.assertEqual(run('eq (err "a") (err "b")')["value"], 0)
        self.assertEqual(run('msg (err "kept")')["value"], "kept")
        self.assertEqual(run('nth [err "a" "b"] 0')["value"], Err("a"))
        with self.assertRaises(SemError):
            run('say (err "kept")')

    def test_times_bounded(self):
        r = run('times 3 (say "Hello World")')
        self.assertEqual(r["out"], "Hello World\nHello World\nHello World")
        self.assertEqual(r["n"], 3)
        quiet = run('times 0 (say "Hello World")')
        self.assertNotIn("out", quiet)
        self.assertEqual(quiet["value"], 0)
        with self.assertRaises(OverflowErr):
            run("times 33 (say \"x\")")
        with self.assertRaises(OverflowErr):
            run('times (add 30 3) (say "x")')
        with self.assertRaises(OverflowErr):
            run('times -1 (ok)')
        self.assertEqual(MAX_TIMES, 32)

    def test_codec_roundtrip_rich(self):
        src = 'seq say "Hello World" len [1 b"61" err "kept"] nth b"6869" 1'
        ast = compile(src)
        self.assertEqual(ast["args"][1]["args"][0]["op"], "list")
        for codec in ("pack", "json", "cbor"):
            rt = roundtrip(src, codec=codec)
            self.assertTrue(rt["ok"], codec)
            self.assertEqual(decode(encode(ast, codec), codec), ast)
        self.assertEqual(run(src)["out"], "Hello World")

    def test_refuse_nested_source_and_codecs(self):
        for src in (
            "pin",
            'say "diary"',
            '{pin: 1}',
            '[ "host-attack" ]',
            'seq say "ok" say "extra"',
        ):
            with self.assertRaises(ParseError):
                compile(src)
        planted = {"op": "list", "args": [{"op": "str", "args": ["live-send"]}]}
        for codec in ("pack", "json", "cbor"):
            blob = encode(planted, codec)
            with self.assertRaises(ParseError):
                decode(blob, codec)

    def test_fetch_does_not_network(self):
        r = run('fetch "https://github.com/Phuderoso/organismo-hydra"')
        self.assertEqual(r["did_network"], False)
        self.assertTrue(r["url"].startswith("https://"))

    def test_old_opcodes_stable(self):
        self.assertEqual(NAME_TO_CODE["sit"], 1)
        self.assertEqual(NAME_TO_CODE["say"], 12)
        self.assertEqual(NAME_TO_CODE["not"], 20)
        self.assertEqual(NAME_TO_CODE["list"], 35)
        self.assertEqual(NAME_TO_CODE["bytes"], 36)

    def test_add_still_runtime_semerror(self):
        with self.assertRaises(SemError):
            run('add "a" 1')

    def test_help_ais_program_does_not_network(self):
        src = (EX / "help_ais.bt1").read_text(encoding="utf-8")
        r = run(src)
        self.assertTrue(r["ok"])
        self.assertEqual(r["op"], "seq")
        fetch = r["steps"][0]
        self.assertEqual(fetch["op"], "fetch")
        self.assertEqual(fetch["did_network"], False)
        self.assertEqual(fetch["url"], "https://taberna.limeprime.online/twelve")
        self.assertEqual(r["steps"][1]["op"], "sit")

    def test_fail_explicit_program_is_parse_error(self):
        src = (EX / "fail_explicit.bt1").read_text(encoding="utf-8")
        with self.assertRaises(ParseError) as cm:
            compile(src)
        self.assertIn("refused", str(cm.exception).lower())

    def test_spec_states_contracts(self):
        text = (Path(__file__).resolve().parents[1] / "SPEC.md").read_text(encoding="utf-8")
        for needle in (
            "Hello World",
            "did_network",
            "MAX_TIMES",
            "Source bytes",
            "b\"",
            "times",
            "pin",
        ):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
