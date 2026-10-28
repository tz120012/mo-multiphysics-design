#!/usr/bin/env python3
"""CLI wrapper: python packages/geometry/scripts/rebuild_examples.py"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is importable when run as a file from repo root / package root
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from mo_geometry.rebuild_examples import main

if __name__ == "__main__":
    raise SystemExit(main())
