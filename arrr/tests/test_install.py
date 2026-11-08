#!/usr/bin/env python3
"""Package surface: exports, CLI, pip install into a fresh venv."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2]


class TestInstall(unittest.TestCase):
    def test_public_exports(self):
        import arrr

        for name in ("compile", "encode", "decode", "roundtrip", "readable", "run"):
            self.assertTrue(callable(getattr(arrr, name)), name)
        ast = arrr.compile("sit")
        self.assertEqual(ast["op"], "sit")
        self.assertEqual(arrr.decode(arrr.encode(ast, "cbor")), ast)

    def test_cli_parse(self):
        import io
        from contextlib import redirect_stdout

        from arrr.cli import main

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["parse", "sit"])
        self.assertEqual(rc, 0)
        self.assertIn('"op"', buf.getvalue())

    def test_pip_install_fresh_venv(self):
        pyproject = TOOLS / "pyproject.toml"
        if not pyproject.is_file():
            self.skipTest("source tree only")
        with tempfile.TemporaryDirectory() as td:
            venv = Path(td) / "v"
            subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
            pip = venv / "bin" / "pip"
            py = venv / "bin" / "python"
            if not pip.is_file():
                pip = venv / "Scripts" / "pip.exe"
                py = venv / "Scripts" / "python.exe"
            subprocess.check_call(
                [str(pip), "install", "-q", str(TOOLS)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            code = (
                "from arrr import compile, encode, decode; "
                "a=compile('sit'); assert decode(encode(a,'pack'))==a"
            )
            subprocess.check_call([str(py), "-c", code])
            subprocess.check_call([str(py), "-m", "arrr", "parse", "ok"], stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
