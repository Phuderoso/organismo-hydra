#!/usr/bin/env python3
"""Umbral 2: cbor identity, version reject, type error, span, refuse stays refuse."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from arrr.core import compile, decode, encode, roundtrip, unwrap
from arrr.errors import ParseError, TypeCheckError, VersionError
from arrr.parser import ParseError as ParserParseError
from arrr.symbols import LANG, MAGIC


class TestUmbral2(unittest.TestCase):
    def test_cbor_roundtrip_identity(self):
        src = 'seq fetch "https://taberna.limeprime.online/twelve" sit'
        rt = roundtrip(src, codec="cbor")
        self.assertTrue(rt["ok"])
        ast = compile(src)
        self.assertEqual(decode(encode(ast, "cbor"), "cbor"), ast)

    def test_pack_version_rejects_unknown(self):
        blob = MAGIC + bytes([2]) + b"\x01\x00"
        with self.assertRaises(VersionError) as cm:
            decode(blob, "pack")
        self.assertEqual(cm.exception.code.name, "E_VERSION")

    def test_env_version_rejects_unknown(self):
        body = encode(compile("sit"), "pack")
        head = {
            "v": 2,
            "lang": LANG,
            "codec": "pack",
            "sha256": hashlib.sha256(body).hexdigest(),
            "meta": {},
            "n": len(body),
        }
        hb = json.dumps(head, separators=(",", ":"), sort_keys=True).encode()
        blob = b"ENV1" + len(hb).to_bytes(4, "big") + hb + body
        with self.assertRaises(VersionError):
            unwrap(blob)

    def test_cbor_version_rejects_unknown(self):
        good = encode(compile("ok"), "cbor")
        bad = b"CBT1" + bytes([2]) + good[5:]
        with self.assertRaises(VersionError):
            decode(bad, "cbor")

    def test_type_error_fetch_int(self):
        with self.assertRaises(TypeCheckError) as cm:
            compile("fetch 1")
        self.assertEqual(cm.exception.code.name, "E_TYPE")
        self.assertIn("str", str(cm.exception))

    def test_parse_error_has_span(self):
        with self.assertRaises(ParseError) as cm:
            compile("fetch")
        self.assertIsInstance(cm.exception, ParserParseError)
        self.assertIsNotNone(cm.exception.span)
        self.assertGreaterEqual(cm.exception.span, 0)

    def test_refuse_still_parse_error(self):
        with self.assertRaises(ParseError):
            compile("pin")
        with self.assertRaises(ParseError):
            compile("diary")
        with self.assertRaises(ParseError):
            compile("host-attack")

    def test_error_to_dict(self):
        try:
            compile("fetch 1")
        except TypeCheckError as e:
            d = e.to_dict()
            self.assertEqual(d["name"], "E_TYPE")
            self.assertIn("msg", d)
            self.assertIn("span", d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
