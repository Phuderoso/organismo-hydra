#!/usr/bin/env python3
"""Hello World and the expression language. Sit is not a greeting."""
from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from arrr.cli import main
from arrr.core import compile, encode, decode, roundtrip, run
from arrr.errors import SemError
from arrr.parser import ParseError


class TestLang(unittest.TestCase):
    def test_hello_world(self):
        r = run('say "Hello World"')
        self.assertEqual(r["out"], "Hello World")
        self.assertTrue(r["ok"])

    def test_hello_world_cli_prints_text(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["run", 'say "Hello World"'])
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue(), "Hello World\n")

    def test_hello_via_cat(self):
        r = run('say cat "Hello" " " "World"')
        self.assertEqual(r["out"], "Hello World")

    def test_if_eq_branch(self):
        r = run('if eq 1 1 say "Hello World" say "no"')
        self.assertEqual(r["out"], "Hello World")
        r2 = run('if eq 1 0 say "Hello World" say "no"')
        self.assertEqual(r2["out"], "no")

    def test_add_sub_len_nth(self):
        self.assertEqual(run("add 2 3 5")["value"], 10)
        self.assertEqual(run("sub 10 3")["value"], 7)
        self.assertEqual(run('len "Hello"')["value"], 5)
        self.assertEqual(run('nth "Hello World" 0')["value"], "H")
        self.assertEqual(run('len ["a" "b" "c"]')["value"], 3)
        self.assertEqual(run('nth ["a" "b" "c"] 1')["value"], "b")

    def test_not_and_seq_outs(self):
        self.assertEqual(run("not 0")["value"], 1)
        r = run('seq say "Hello" say "World"')
        self.assertEqual(r["out"], "Hello\nWorld")

    def test_hello_roundtrip_all_codecs(self):
        src = 'say "Hello World"'
        ast = compile(src)
        for codec in ("pack", "json", "cbor"):
            rt = roundtrip(src, codec=codec)
            self.assertTrue(rt["ok"], codec)
            self.assertEqual(decode(encode(ast, codec), codec), ast)
            self.assertEqual(run(rt["readable"])["out"], "Hello World")

    def test_refuse_still_parse_error(self):
        with self.assertRaises(ParseError):
            compile("pin")
        with self.assertRaises(ParseError):
            compile('say "live-send"')

    def test_add_rejects_str(self):
        with self.assertRaises(SemError):
            run('add "a" 1')


if __name__ == "__main__":
    unittest.main(verbosity=2)
