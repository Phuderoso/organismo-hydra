#!/usr/bin/env python3
"""Five properties + refuse + codec swap."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # tools/

from arrr.core import compile, decode, encode, readable, recv, roundtrip, run, send
from arrr.parser import ParseError


class TestArrr(unittest.TestCase):
    def test_few_symbols_unambiguous(self):
        a = compile("sit")
        self.assertEqual(a["op"], "sit")
        self.assertEqual(compile("bt1 sit"), a)
        self.assertEqual(compile('{"v":"bt1","op":"sit"}'), a)

    def test_fetch_and_sha(self):
        src = (
            'seq fetch "https://taberna.limeprime.online/twelve" '
            'sha "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"'
        )
        ast = compile(src)
        self.assertEqual(ast["op"], "seq")
        self.assertEqual(ast["args"][0]["op"], "fetch")
        self.assertEqual(run(src)["ok"], True)

    def test_binary_roundtrip_pack_and_json(self):
        src = 'map url "https://example.com/x" note "harbor"'
        for codec in ("pack", "json"):
            rt = roundtrip(src, codec=codec)
            self.assertTrue(rt["ok"], codec)
            self.assertGreater(rt["n_bytes"], 4)
            back = decode(encode(compile(src), codec=codec), codec=codec)
            self.assertEqual(back, compile(src))

    def test_exact_recover_via_envelope(self):
        src = 'fetch "https://github.com/Phuderoso/organismo-hydra"'
        ast = compile(src)
        blob = send(src, codec="pack", meta={"from": "nihira"})
        env = recv(blob)
        self.assertEqual(env["ast"], ast)
        self.assertEqual(env["result"]["url"], "https://github.com/Phuderoso/organismo-hydra")
        self.assertFalse(env["result"]["did_network"])

    def test_expand_readable(self):
        src = 'seq sit ok'
        text = readable(compile(src))
        self.assertEqual(compile(text), compile(src))
        self.assertIn("sit", text)

    def test_refuse_pin(self):
        with self.assertRaises(ParseError):
            compile("pin")
        with self.assertRaises(ParseError):
            compile('{"v":"bt1","op":"diary"}')

    def test_swap_codec_same_ast(self):
        ast = compile('help')
        a = decode(encode(ast, "pack"), "pack")
        b = decode(encode(ast, "json"), "json")
        self.assertEqual(a, b)
        self.assertEqual(a, ast)

    def test_compat_old_card(self):
        for s in ("bt1 sit", "bt1 forget", "bt1 help"):
            self.assertTrue(run(s)["ok"], s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
