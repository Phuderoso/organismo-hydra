#!/usr/bin/env python3
"""Arrr-bay CLI — the language, not the ten-line postcard.

  python3 arrr_bay.py parse 'fetch "https://taberna.limeprime.online/twelve"'
  python3 arrr_bay.py roundtrip 'seq sit ok'
  python3 arrr_bay.py send 'help' --codec pack | python3 arrr_bay.py recv
  python3 arrr_bay.py --selftest
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from arrr.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
