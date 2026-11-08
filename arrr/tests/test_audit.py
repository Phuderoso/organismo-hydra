#!/usr/bin/env python3
"""Regressions from the 0.4 SPEC audit. Each case is a small program or blob."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from arrr.core import compile, decode, encode, readable, roundtrip, run, send
from arrr.errors import DecodeError, ParseError, SemError, TypeCheckError, VersionError
from arrr.protocol import unwrap
from arrr.symbols import MAGIC


def _rt(src: str) -> None:
    ast = compile(src)
    assert ast == compile(readable(ast))
    for codec in ("pack", "json", "cbor"):
        got = roundtrip(src, codec=codec)
        assert got["ok"], codec
        assert decode(encode(ast, codec), codec) == ast


class TestAudit(unittest.TestCase):
    def test_nested_add_not_swallowed(self):
        src = "eq (add 1 2) 3"
        self.assertEqual(run(src)["value"], 1)
        self.assertEqual(readable(compile(src)), "eq (add 1 2) 3")
        _rt(src)
        with self.assertRaises(ParseError):
            compile("eq add 1 2 3")

    def test_list_and_map_keep_nested_calls(self):
        _rt("[ (add 1 2) 3 ]")
        self.assertEqual(run("nth [ (add 1 2) 3 ] 0")["value"], 3)
        self.assertEqual(len(compile("[ (add 1 2) 3 ]")["args"]), 2)
        src = 'get {a: {b: 1}} a'
        self.assertEqual(run(src)["value"], {"b": 1})
        _rt(src)
        _rt("eq {a: 1 b: 2} {b: 2 a: 1}")
        self.assertEqual(run("eq {a: 1 b: 2} {b: 2 a: 1}")["value"], 1)
        _rt('map "k" (add 1 2) "m" 3')

    def test_map_pair_ceiling(self):
        body = " ".join(f"k{i}: {i}" for i in range(17))
        src = "{" + body + "}"
        self.assertEqual(len(compile(src)["args"]), 17)
        _rt(src)
        wide = "{" + " ".join(f"k{i}: {i}" for i in range(32)) + "}"
        self.assertEqual(len(compile(wide)["args"]), 32)
        _rt(wide)
        too = "{" + " ".join(f"k{i}: {i}" for i in range(33)) + "}"
        with self.assertRaises(TypeCheckError):
            compile(too)

    def test_duplicate_keys_keep_both_pairs(self):
        ast = compile("{a: 1 a: 9}")
        self.assertEqual(len(ast["args"]), 2)
        self.assertEqual(run("get {a: 1 a: 9} a")["value"], 9)
        _rt("{a: 1 a: 9}")

    def test_branch_and_times_skip_untaken(self):
        self.assertEqual(run('if 0 (say "no") (say "yes")')["out"], "yes")
        self.assertEqual(run("if 0 (get {a: 1} z) (ok)")["op"], "ok")
        self.assertEqual(run("times 0 (get {a: 1} z)")["value"], 0)
        self.assertEqual(run('say (times 2 (say "z"))')["out"], "z")
        self.assertEqual(run('len (say "ab")')["value"], 2)
        self.assertNotIn("out", run('len (say "ab")'))

    def test_refuse_is_leaf_not_computed_text(self):
        self.assertEqual(run('say "pinball"')["out"], "pinball")
        self.assertEqual(run('cat "pi" "n"')["value"], "pin")
        with self.assertRaises(ParseError):
            compile('say "PIN"')
        with self.assertRaises(SemError):
            run('get {a: 1} (cat "pi" "n")')

    def test_bad_escape_and_newline(self):
        self.assertEqual(compile(r'say "a\nb"')["args"][0]["args"][0], "a\nb")
        with self.assertRaises(ParseError):
            compile(r'say "\q"')

    def test_analogous_groupings_roundtrip(self):
        """Same class of hole as pocket.bt1 on 94ad269: nested map/list/call."""
        samples = (
            'say (get {door: "twelve"} door)',
            "get {a: {b: 1}} a",
            "eq (add 1 2) 3",
            "[(add 1 2) 3]",
            "if (eq 1 1) (add 2 2) (add 9 9)",
            'cat (cat "a" "b") "c"',
            'map "k" (add 1 2) "m" 3',
            "eq {a: 1 b: 2} {b: 2 a: 1}",
            "{xs: [get {a: 1} a]}",
            "nth [get {a: 1} a 2] 0",
            'len (get {a: "hi"} a)',
            "nth (get {a: [1 2 3]} a) 1",
            'cat (get {a: "Hel"} a) (get {b: "lo"} b)',
            'msg (err (get {a: "kept"} a))',
            'if (get {a: 1} a) (say "y") (say "n")',
            "[{a: 1} {b: 2}]",
            "times 2 (get {a: 1} a)",
            "sub (add 1 2) (add 3 4)",
            "not (eq (add 1 1) 2)",
            'say (get {a: b"61"} a)',
            'get {a: [err "e" 1]} a',
            'add (get {n: 2} n) 3',
            "{k: get {a: 1} a m: 2}",
        )
        for src in samples:
            ast = compile(src)
            self.assertEqual(compile(readable(ast)), ast, src)
            for codec in ("pack", "json", "cbor"):
                self.assertTrue(roundtrip(src, codec=codec)["ok"], (src, codec))

    def test_hello_render_stays_flat(self):
        self.assertEqual(readable(compile('say "Hello World"')), 'say "Hello World"')

    def test_malformed_decode(self):
        blob = encode(compile('say "Hello World"'), "pack")
        for i in range(len(blob)):
            with self.assertRaises((DecodeError, VersionError)):
                decode(blob[:i], "pack")
        with self.assertRaises(DecodeError):
            decode(blob + b"\xff", "pack")
        with self.assertRaises(VersionError):
            decode(MAGIC + bytes([2, 1, 0]), "pack")
        with self.assertRaises(DecodeError):
            decode(b"{", "json")
        with self.assertRaises(DecodeError):
            decode(b'{"ast": 1}', "json")
        with self.assertRaises(DecodeError):
            decode(b'{"lang":"bt1"}', "json")
        with self.assertRaises(DecodeError):
            decode(b"CBT1", "cbor")
        with self.assertRaises(VersionError):
            decode(b"CBT1\x02", "cbor")
        bad = bytearray(encode(compile('say "hi"'), "cbor"))
        bad[-2] = 0xFF
        with self.assertRaises(DecodeError):
            decode(bytes(bad), "cbor")

    def test_envelope_sha_mismatch(self):
        env = bytearray(send("sit"))
        env[-1] ^= 0xFF
        with self.assertRaises(DecodeError):
            unwrap(bytes(env))

    def test_nested_list_depth_limit(self):
        def nest(n: int) -> str:
            s = "1"
            for _ in range(n):
                s = f"[{s}]"
            return s

        compile(nest(64))
        with self.assertRaises(TypeCheckError):
            compile(nest(65))

    def test_bytes_case_and_codecs(self):
        self.assertEqual(compile('b"AB"')["args"], ["ab"])
        _rt('say b"AB"')
        planted = {"op": "bytes", "args": ["AB"]}
        self.assertEqual(decode(encode(planted, "pack"), "pack")["args"], ["ab"])
        self.assertEqual(decode(encode(planted, "cbor"), "cbor")["args"], ["ab"])
        self.assertEqual(decode(encode(planted, "json"), "json")["args"], ["AB"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
