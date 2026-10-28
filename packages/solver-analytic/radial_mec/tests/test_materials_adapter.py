#!/usr/bin/env python3
"""materials_adapter: inline / catalog / default precedence."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from materials_adapter import resolve_materials  # noqa: E402


def test_inline_wins():
    r = resolve_materials({"br_t": 1.35, "magnet_id": "mat-ndfeb-n42"}, need_magnet=True)
    assert abs(r.br_t - 1.35) < 1e-15
    assert r.sources["br_t"] == "inline"


def test_catalog_seed_id():
    r = resolve_materials({"magnet_id": "mat-ndfeb-n42"}, need_magnet=True)
    assert abs(r.br_t - 1.28) < 1e-12
    assert "catalog" in r.sources["br_t"]


def test_default_note():
    r = resolve_materials({}, need_magnet=True, need_bar=True)
    assert any("br_t defaulted" in n for n in r.notes)
    assert any("sigma_bar defaulted" in n for n in r.notes)


def main() -> int:
    test_inline_wins()
    test_catalog_seed_id()
    test_default_note()
    print("OK materials_adapter tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
