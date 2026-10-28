#!/usr/bin/env python3
"""materials_adapter: inline / catalog camelCase+curves / default precedence."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from materials_adapter import (  # noqa: E402
    DEFAULT_MATERIALS_CATALOG,
    resolve_materials,
)


def test_inline_wins():
    r = resolve_materials({"br_t": 1.35, "magnet_id": "mat-ndfeb-n42"}, need_magnet=True)
    assert abs(r.br_t - 1.35) < 1e-15
    assert r.sources["br_t"] == "inline"


def test_inline_camel_brT():
    r = resolve_materials({"brT": 1.33, "muRec": 1.08}, need_magnet=True)
    assert abs(r.br_t - 1.33) < 1e-15
    assert abs(r.mur_pm - 1.08) < 1e-15
    assert r.sources["br_t"] == "inline"


def test_catalog_seed_id():
    r = resolve_materials({"magnet_id": "mat-ndfeb-n42"}, need_magnet=True)
    assert abs(r.br_t - 1.28) < 1e-12
    src = r.sources["br_t"]
    assert src.startswith("curves:") or src.startswith("meta:") or "catalog" in src


def test_q2_steel_bh_bp_iron_loss():
    r = resolve_materials({"steel_id": "mat-steel-m19"}, need_magnet=False)
    assert r.steel_bh_curve and len(r.steel_bh_curve) >= 3
    assert r.iron_loss_coeffs and "kH" in r.iron_loss_coeffs
    meta = (DEFAULT_MATERIALS_CATALOG.get("mat-steel-m19") or {}).get("meta") or {}
    curves = (DEFAULT_MATERIALS_CATALOG.get("mat-steel-m19") or {}).get("curves") or {}
    if meta.get("bpPoints") or (isinstance(curves.get("steel"), dict) and curves["steel"].get("bp")) or (
        isinstance(curves.get("bp"), dict)
    ):
        assert r.steel_bp_points and len(r.steel_bp_points) >= 1


def test_q2_coil_and_bars():
    r = resolve_materials(
        {"conductor_id": "mat-copper", "bar_id": "mat-acim-bar-al"},
        need_magnet=False,
        need_bar=True,
    )
    assert abs(r.sigma_copper - 5.8e7) / 5.8e7 < 0.01  # curves rho or meta sigma
    assert abs(r.sigma_bar - 3.5e7) / 3.5e7 < 0.01
    r2 = resolve_materials({"bar_id": "mat-acim-bar-cu"}, need_magnet=False, need_bar=True)
    assert abs(r2.sigma_bar - 5.8e7) / 5.8e7 < 0.01
    assert "mat-acim-endring-al" in DEFAULT_MATERIALS_CATALOG


def test_default_note():
    r = resolve_materials({}, need_magnet=True, need_bar=True)
    assert any("br_t defaulted" in n for n in r.notes)
    assert any("sigma_bar defaulted" in n for n in r.notes)


def main() -> int:
    test_inline_wins()
    test_inline_camel_brT()
    test_catalog_seed_id()
    test_q2_steel_bh_bp_iron_loss()
    test_q2_coil_and_bars()
    test_default_note()
    print("OK materials_adapter tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
