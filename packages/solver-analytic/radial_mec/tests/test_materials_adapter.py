#!/usr/bin/env python3
"""materials_adapter: inline / curves / meta / default precedence."""
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
    assert "curves" in r.sources["br_t"] or "meta" in r.sources["br_t"] or "catalog" in r.sources["br_t"]


def test_curves_before_meta():
    """curves.br_t wins over conflicting meta.brT when both present."""
    catalog = {
        "mat-x": {
            "id": "mat-x",
            "category": "magnet",
            "curves": {"magnet": {"br_t": 1.33, "hc_a_per_m": 900000.0}},
            "meta": {"brT": 0.5, "muRec": 1.05},
        }
    }
    r = resolve_materials({"magnet_id": "mat-x"}, materials_catalog=catalog, need_magnet=True)
    assert abs(r.br_t - 1.33) < 1e-12
    assert r.sources["br_t"].startswith("curves")


def test_meta_camel_fallback():
    catalog = {
        "mat-y": {
            "id": "mat-y",
            "category": "magnet",
            "meta": {"brT": 1.11, "muRec": 1.08},
        }
    }
    r = resolve_materials({"magnet_id": "mat-y"}, materials_catalog=catalog, need_magnet=True)
    assert abs(r.br_t - 1.11) < 1e-12
    assert abs(r.mur_pm - 1.08) < 1e-12


def test_coil_curves_resistivity():
    catalog = {
        "mat-c": {
            "id": "mat-c",
            "category": "coil",
            "curves": {"coil": {"resistivity_ohm_m": 2.0e-8}},
            "meta": {"conductivitySPerM": 1.0e6},  # should lose to curves
        }
    }
    r = resolve_materials({"conductor_id": "mat-c"}, materials_catalog=catalog)
    assert abs(r.sigma_copper - 5.0e7) < 1.0  # 1/2e-8
    assert "curves" in r.sources["sigma_copper"]


def test_acim_bar_curves():
    catalog = {
        "mat-b": {
            "id": "mat-b",
            "category": "acim_bar",
            "curves": {"acim_bar": {"conductivity_s_per_m": 4.2e7}},
            "meta": {"conductivitySPerM": 1.0e6},
        }
    }
    r = resolve_materials({"bar_id": "mat-b"}, materials_catalog=catalog, need_bar=True)
    assert abs(r.sigma_bar - 4.2e7) < 1.0
    assert "curves" in r.sources["sigma_bar"]


def test_default_note():
    r = resolve_materials({}, need_magnet=True, need_bar=True)
    assert any("br_t defaulted" in n for n in r.notes)
    assert any("sigma_bar defaulted" in n for n in r.notes)


def main() -> int:
    test_inline_wins()
    test_catalog_seed_id()
    test_curves_before_meta()
    test_meta_camel_fallback()
    test_coil_curves_resistivity()
    test_acim_bar_curves()
    test_default_note()
    print("OK materials_adapter tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
