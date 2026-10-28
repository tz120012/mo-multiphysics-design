"""Resolve SolveRequest materials from inline fields, catalog ids, or engineering defaults.

Backend Q2-1 may still stub materials as id/name/category/meta only.
This adapter accepts:
  - inline overrides on ``materials`` (br_t, mur_pm, sigma_copper, sigma_bar, …)
  - material ids + optional ``materials_catalog`` (simulates GET /materials items)
  - local seed for known stub ids when catalog omitted

Never raises solely for missing EM properties — defaults + notes instead.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Local seed mirroring apps/api stub ids, with the meta keys we hope backend grows.
DEFAULT_MATERIALS_CATALOG: dict[str, dict[str, Any]] = {
    "mat-steel-m19": {
        "id": "mat-steel-m19",
        "name": "M19 Steel",
        "category": "steel",
        "meta": {
            "grade": "M19",
            "bs_t": 1.70,
            "mur0": 5000.0,
            "kh": 150.0,
            "ke": 0.8,
            "alpha": 1.8,
        },
    },
    "mat-ndfeb-n42": {
        "id": "mat-ndfeb-n42",
        "name": "NdFeB N42",
        "category": "magnet",
        "meta": {"grade": "N42", "br_t": 1.28, "mur_pm": 1.05},
    },
    "mat-copper": {
        "id": "mat-copper",
        "name": "Copper",
        "category": "coil",
        "meta": {"sigma": 5.8e7, "sigma_copper": 5.8e7},
    },
    # Alias commonly used in fixtures / demos
    "demo-steel": {
        "id": "demo-steel",
        "name": "Demo steel",
        "category": "steel",
        "meta": {"bs_t": 1.70, "mur0": 5000.0},
    },
    "demo-N35": {
        "id": "demo-N35",
        "name": "Demo NdFeB N35",
        "category": "magnet",
        "meta": {"br_t": 1.2, "mur_pm": 1.05},
    },
    "Cu": {
        "id": "Cu",
        "name": "Copper",
        "category": "coil",
        "meta": {"sigma": 5.8e7, "sigma_copper": 5.8e7},
    },
    "mat-al-bar": {
        "id": "mat-al-bar",
        "name": "Aluminum rotor bar",
        "category": "bar",
        "meta": {"sigma_bar": 3.5e7, "sigma": 3.5e7},
    },
}

# Engineering defaults when nothing else is available
_DEFAULT_BR_T = 1.2
_DEFAULT_MUR_PM = 1.05
_DEFAULT_SIGMA_CU = 5.8e7
_DEFAULT_SIGMA_BAR = 3.5e7  # cast Al class
_DEFAULT_BS_T = 1.70
_DEFAULT_MUR0 = 5000.0


@dataclass
class ResolvedMaterials:
    """Numeric EM properties consumed by MEC / ACIM solvers."""

    br_t: float = _DEFAULT_BR_T
    mur_pm: float = _DEFAULT_MUR_PM
    sigma_copper: float = _DEFAULT_SIGMA_CU
    sigma_bar: float = _DEFAULT_SIGMA_BAR
    bs_t: float = _DEFAULT_BS_T
    mur0: float = _DEFAULT_MUR0
    steel_kh: float = 150.0
    steel_ke: float = 0.8
    steel_alpha: float = 1.8
    notes: list[str] = field(default_factory=list)
    sources: dict[str, str] = field(default_factory=dict)


def _catalog_lookup(
    catalog: dict[str, dict[str, Any]],
    mid: str | None,
) -> dict[str, Any] | None:
    if not mid:
        return None
    item = catalog.get(mid)
    if item is None:
        return None
    return item


def _meta(item: dict[str, Any] | None) -> dict[str, Any]:
    if not item:
        return {}
    m = item.get("meta")
    return m if isinstance(m, dict) else {}


def _pick_num(*candidates: Any, default: float) -> tuple[float, bool]:
    """Return (value, found). First non-None numeric wins."""
    for c in candidates:
        if c is None:
            continue
        try:
            return float(c), True
        except (TypeError, ValueError):
            continue
    return float(default), False


def resolve_materials(
    materials: dict[str, Any] | None,
    *,
    materials_catalog: dict[str, dict[str, Any]] | list[dict[str, Any]] | None = None,
    need_magnet: bool = True,
    need_bar: bool = False,
) -> ResolvedMaterials:
    """Build ResolvedMaterials from request materials + optional catalog.

    Precedence per property:
      1. Inline field on ``materials`` (br_t, mur_pm, sigma_copper, sigma_bar, …)
      2. ``materials_catalog`` entry meta for the corresponding id
      3. Built-in DEFAULT_MATERIALS_CATALOG for known ids
      4. Engineering default + note
    """
    mats = dict(materials or {})
    notes: list[str] = []
    sources: dict[str, str] = {}

    catalog: dict[str, dict[str, Any]] = dict(DEFAULT_MATERIALS_CATALOG)
    if materials_catalog is not None:
        if isinstance(materials_catalog, list):
            for it in materials_catalog:
                if isinstance(it, dict) and it.get("id"):
                    catalog[str(it["id"])] = it
        elif isinstance(materials_catalog, dict):
            # either id→item map, or a wrapper {"items": [...]}
            if "items" in materials_catalog and isinstance(materials_catalog["items"], list):
                for it in materials_catalog["items"]:
                    if isinstance(it, dict) and it.get("id"):
                        catalog[str(it["id"])] = it
            else:
                catalog.update(materials_catalog)

    steel_item = _catalog_lookup(catalog, mats.get("steel_id"))
    magnet_item = _catalog_lookup(catalog, mats.get("magnet_id"))
    coil_item = _catalog_lookup(catalog, mats.get("conductor_id") or mats.get("coil_id"))
    bar_item = _catalog_lookup(catalog, mats.get("bar_id") or mats.get("rotor_bar_id"))

    steel_m = _meta(steel_item)
    magnet_m = _meta(magnet_item)
    coil_m = _meta(coil_item)
    bar_m = _meta(bar_item)

    out = ResolvedMaterials(notes=notes, sources=sources)

    # --- magnet ---
    br, found = _pick_num(
        mats.get("br_t"),
        magnet_m.get("br_t"),
        default=_DEFAULT_BR_T,
    )
    out.br_t = br
    if found:
        sources["br_t"] = "inline" if mats.get("br_t") is not None else f"catalog:{mats.get('magnet_id')}"
    elif need_magnet:
        notes.append(f"br_t defaulted to {br} T")
        sources["br_t"] = "default"

    mur, found = _pick_num(
        mats.get("mur_pm"),
        magnet_m.get("mur_pm"),
        default=_DEFAULT_MUR_PM,
    )
    out.mur_pm = mur
    if found:
        sources["mur_pm"] = "inline" if mats.get("mur_pm") is not None else f"catalog:{mats.get('magnet_id')}"
    else:
        notes.append(f"mur_pm defaulted to {mur}")
        sources["mur_pm"] = "default"

    # --- copper / coil ---
    sig_cu, found = _pick_num(
        mats.get("sigma_copper"),
        mats.get("sigma"),
        coil_m.get("sigma_copper"),
        coil_m.get("sigma"),
        default=_DEFAULT_SIGMA_CU,
    )
    out.sigma_copper = sig_cu
    if found:
        sources["sigma_copper"] = (
            "inline"
            if mats.get("sigma_copper") is not None or mats.get("sigma") is not None
            else f"catalog:{mats.get('conductor_id') or mats.get('coil_id')}"
        )
    else:
        notes.append(f"sigma_copper defaulted to {sig_cu:g} S/m")
        sources["sigma_copper"] = "default"

    # --- rotor bar (ACIM) ---
    sig_bar, found = _pick_num(
        mats.get("sigma_bar"),
        bar_m.get("sigma_bar"),
        bar_m.get("sigma"),
        default=_DEFAULT_SIGMA_BAR,
    )
    out.sigma_bar = sig_bar
    if found:
        sources["sigma_bar"] = (
            "inline"
            if mats.get("sigma_bar") is not None
            else f"catalog:{mats.get('bar_id') or mats.get('rotor_bar_id')}"
        )
    elif need_bar:
        notes.append(f"sigma_bar defaulted to {sig_bar:g} S/m (cast-Al class)")
        sources["sigma_bar"] = "default"
    else:
        sources["sigma_bar"] = "default"

    # --- steel BH / loss coeffs (optional for MEC; defaults match materials.py) ---
    bs, found = _pick_num(mats.get("bs_t"), steel_m.get("bs_t"), default=_DEFAULT_BS_T)
    out.bs_t = bs
    sources["bs_t"] = "inline/catalog" if found else "default"

    mur0, found = _pick_num(mats.get("mur0"), steel_m.get("mur0"), default=_DEFAULT_MUR0)
    out.mur0 = mur0
    sources["mur0"] = "inline/catalog" if found else "default"

    kh, _ = _pick_num(mats.get("kh"), steel_m.get("kh"), default=150.0)
    ke, _ = _pick_num(mats.get("ke"), steel_m.get("ke"), default=0.8)
    alpha, _ = _pick_num(mats.get("alpha"), steel_m.get("alpha"), default=1.8)
    out.steel_kh, out.steel_ke, out.steel_alpha = kh, ke, alpha

    if steel_item is None and mats.get("steel_id"):
        notes.append(f"steel_id {mats.get('steel_id')!r} not in catalog; steel defaults used")
    if need_magnet and magnet_item is None and mats.get("magnet_id") and mats.get("br_t") is None:
        notes.append(f"magnet_id {mats.get('magnet_id')!r} not in catalog; magnet defaults used")

    return out


def resolve_from_request(request: dict[str, Any], *, need_magnet: bool = True, need_bar: bool = False) -> ResolvedMaterials:
    """Convenience: pull materials + optional top-level materials_catalog from SolveRequest."""
    return resolve_materials(
        request.get("materials"),
        materials_catalog=request.get("materials_catalog"),
        need_magnet=need_magnet,
        need_bar=need_bar,
    )
