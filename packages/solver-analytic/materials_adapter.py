"""Resolve SolveRequest materials from inline fields, catalog ids, or engineering defaults.

Priority (bfd27ab / materialsSchemaVersion=0.1.0-q2): **inline → curves → meta → default**.

Target ``curves`` (preferred):
  steel: bh/bp CurveTable2D points=[[H,B]]/[[B,P]], lossCoefficients
  magnet: br_t, hc_a_per_m, demag[]{temperature_c,curve}, alphaBr/alphaHc
  coil: resistivity_ohm_m, fillFactor, skin
  acim_bar: conductivity_s_per_m, skin

Transitional camelCase ``meta`` still accepted:
  steel: bhCurve/bpPoints/ironLossCoeffs/bsT/muR
  magnet: brT/demagCurve/muRec/tempCoeffBr
  coil: resistivityOhmM/conductivitySPerM
  acim_bar: conductivitySPerM/role/materialRef

Legacy snake_case inline / meta keys remain for fixtures.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_SEED = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "app"
    / "data"
    / "materials_seed.json"
)

# Engineering defaults when nothing else is available
_DEFAULT_BR_T = 1.2
_DEFAULT_MUR_PM = 1.05
_DEFAULT_SIGMA_CU = 5.8e7
_DEFAULT_SIGMA_BAR = 3.5e7  # cast Al class
_DEFAULT_BS_T = 1.70
_DEFAULT_MUR0 = 5000.0


def _load_backend_seed() -> dict[str, dict[str, Any]]:
    """Prefer live backend seed file; fall back to embedded camelCase catalog."""
    out: dict[str, dict[str, Any]] = {}
    if _REPO_SEED.is_file():
        try:
            raw = json.loads(_REPO_SEED.read_text(encoding="utf-8"))
            for row in raw:
                if isinstance(row, dict) and row.get("id"):
                    out[str(row["id"])] = row
            return out
        except (OSError, json.JSONDecodeError):
            pass
    return dict(_EMBEDDED_CATALOG)


# Embedded mirror of apps/api seed (used when seed file not on path / Wasm sidecar).
_EMBEDDED_CATALOG: dict[str, dict[str, Any]] = {
    "mat-steel-m19": {
        "id": "mat-steel-m19",
        "name": "M19 Steel",
        "category": "steel",
        "meta": {
            "builtin": True,
            "grade": "M19",
            "bhCurve": [
                {"bT": 0.0, "hAPerM": 0.0},
                {"bT": 0.5, "hAPerM": 80.0},
                {"bT": 1.0, "hAPerM": 200.0},
                {"bT": 1.5, "hAPerM": 1200.0},
                {"bT": 1.8, "hAPerM": 8000.0},
            ],
            "ironLossCoeffs": {"kH": 0.02, "kE": 0.0001, "kExc": 0.001, "freqHz": 60.0},
            "materialsSchemaVersion": "0.1.0-q2",
        },
    },
    "mat-ndfeb-n42": {
        "id": "mat-ndfeb-n42",
        "name": "NdFeB N42",
        "category": "magnet",
        "meta": {
            "builtin": True,
            "grade": "N42",
            "brT": 1.28,
            "muRec": 1.05,
            "tempCoeffBr": -0.0012,
            "materialsSchemaVersion": "0.1.0-q2",
        },
    },
    "mat-copper": {
        "id": "mat-copper",
        "name": "Copper",
        "category": "coil",
        "meta": {
            "builtin": True,
            "resistivityOhmM": 1.72e-08,
            "conductivitySPerM": 5.8e7,
            "materialsSchemaVersion": "0.1.0-q2",
        },
    },
    "mat-acim-bar-al": {
        "id": "mat-acim-bar-al",
        "name": "ACIM Bar Aluminum",
        "category": "acim_bar",
        "meta": {
            "builtin": True,
            "role": "bar",
            "conductivitySPerM": 3.5e7,
            "materialsSchemaVersion": "0.1.0-q2",
        },
    },
    "mat-acim-bar-cu": {
        "id": "mat-acim-bar-cu",
        "name": "ACIM Bar Copper",
        "category": "acim_bar",
        "meta": {"builtin": True, "role": "bar", "conductivitySPerM": 5.8e7},
    },
    "mat-acim-endring-al": {
        "id": "mat-acim-endring-al",
        "name": "ACIM End-Ring Aluminum",
        "category": "acim_bar",
        "meta": {"builtin": True, "role": "endring", "conductivitySPerM": 3.5e7},
    },
    # Demo aliases (fixtures)
    "demo-steel": {
        "id": "demo-steel",
        "name": "Demo steel",
        "category": "steel",
        "meta": {"bsT": 1.70, "muR": 5000.0},
    },
    "demo-N35": {
        "id": "demo-N35",
        "name": "Demo NdFeB N35",
        "category": "magnet",
        "meta": {"brT": 1.2, "muRec": 1.05},
    },
    "Cu": {
        "id": "Cu",
        "name": "Copper",
        "category": "coil",
        "meta": {"conductivitySPerM": 5.8e7},
    },
    "mat-al-bar": {
        "id": "mat-al-bar",
        "name": "Aluminum rotor bar (legacy alias)",
        "category": "acim_bar",
        "meta": {"conductivitySPerM": 3.5e7},
    },
}

DEFAULT_MATERIALS_CATALOG: dict[str, dict[str, Any]] = _load_backend_seed()
# Ensure demo aliases always present even when backend seed loads
for _k, _v in _EMBEDDED_CATALOG.items():
    DEFAULT_MATERIALS_CATALOG.setdefault(_k, _v)


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
    temp_coeff_br: float | None = None
    notes: list[str] = field(default_factory=list)
    sources: dict[str, str] = field(default_factory=dict)
    # Raw camelCase blobs retained for advanced consumers (BH curve, demag, …)
    steel_bh_curve: list[dict[str, float]] | None = None
    steel_bp_points: list[dict[str, float]] | None = None
    magnet_demag_curve: list[dict[str, float]] | None = None
    iron_loss_coeffs: dict[str, float] | None = None


def _catalog_lookup(
    catalog: dict[str, dict[str, Any]],
    mid: str | None,
) -> dict[str, Any] | None:
    if not mid:
        return None
    return catalog.get(mid)


def _meta(item: dict[str, Any] | None) -> dict[str, Any]:
    if not item:
        return {}
    m = item.get("meta")
    return m if isinstance(m, dict) else {}


def _curves_bucket(item: dict[str, Any] | None, category: str) -> dict[str, Any]:
    """Return typed curves for category (curves.<cat> or flat curves)."""
    if not item:
        return {}
    c = item.get("curves")
    if not isinstance(c, dict):
        return {}
    nested = c.get(category)
    if isinstance(nested, dict):
        return nested
    # Flat layout (keys already at curves root) — rare
    return c if category in ("steel", "magnet", "coil", "acim_bar") and any(
        k in c for k in ("bh", "bp", "br_t", "resistivity_ohm_m", "conductivity_s_per_m", "lossCoefficients")
    ) else {}


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


def _bs_mur_from_bh_meta(curve: Any) -> tuple[float | None, float | None]:
    """Estimate bsT / muR0 from meta bhCurve[{bT,hAPerM}]."""
    if not isinstance(curve, list) or not curve:
        return None, None
    pts: list[tuple[float, float]] = []
    for p in curve:
        if not isinstance(p, dict):
            continue
        try:
            b = float(p.get("bT", p.get("b_t")))
            h = float(p.get("hAPerM", p.get("h_a_per_m")))
        except (TypeError, ValueError):
            continue
        pts.append((b, h))
    if not pts:
        return None, None
    pts.sort(key=lambda t: t[0])
    return _bs_mur_from_hb_points([(h, b) for b, h in pts])


def _bs_mur_from_hb_points(pts_hb: list[tuple[float, float]]) -> tuple[float | None, float | None]:
    """pts as (H, B)."""
    if not pts_hb:
        return None, None
    pts = sorted(pts_hb, key=lambda t: t[1])  # by B
    bs = pts[-1][1]
    mu0 = 4.0e-7 * 3.141592653589793
    mur0 = None
    for h, b in sorted(pts_hb, key=lambda t: t[0]):
        if b > 0.05 and h > 1.0:
            mur0 = b / (mu0 * h)
            break
    return bs, mur0


def _bs_mur_from_curves_bh(bh: Any) -> tuple[float | None, float | None]:
    """curves.steel.bh CurveTable2D: points=[[H,B], ...]."""
    if not isinstance(bh, dict):
        return None, None
    points = bh.get("points")
    if not isinstance(points, list):
        return None, None
    pts: list[tuple[float, float]] = []
    for p in points:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            try:
                pts.append((float(p[0]), float(p[1])))
            except (TypeError, ValueError):
                continue
    return _bs_mur_from_hb_points(pts)


def _sigma_from_resistivity(rho: Any) -> float | None:
    try:
        r = float(rho)
    except (TypeError, ValueError):
        return None
    if r <= 0.0:
        return None
    return 1.0 / r


def resolve_materials(
    materials: dict[str, Any] | None,
    *,
    materials_catalog: dict[str, dict[str, Any]] | list[dict[str, Any]] | None = None,
    need_magnet: bool = True,
    need_bar: bool = False,
) -> ResolvedMaterials:
    """Build ResolvedMaterials from request materials + optional catalog.

    Precedence per property (do not invent a third key set):
      1. Inline on ``materials`` (snake or camel)
      2. Catalog item ``curves.*`` (typed target, bfd27ab)
      3. Catalog item ``meta`` (camelCase transitional + legacy snake)
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
            if "items" in materials_catalog and isinstance(materials_catalog["items"], list):
                for it in materials_catalog["items"]:
                    if isinstance(it, dict) and it.get("id"):
                        catalog[str(it["id"])] = it
            else:
                catalog.update(materials_catalog)

    steel_item = _catalog_lookup(catalog, mats.get("steel_id"))
    magnet_item = _catalog_lookup(catalog, mats.get("magnet_id"))
    coil_item = _catalog_lookup(
        catalog, mats.get("conductor_id") or mats.get("coil_id")
    )
    bar_item = _catalog_lookup(
        catalog, mats.get("bar_id") or mats.get("rotor_bar_id")
    )

    steel_c = _curves_bucket(steel_item, "steel")
    magnet_c = _curves_bucket(magnet_item, "magnet")
    coil_c = _curves_bucket(coil_item, "coil")
    bar_c = _curves_bucket(bar_item, "acim_bar")

    steel_m = _meta(steel_item)
    magnet_m = _meta(magnet_item)
    coil_m = _meta(coil_item)
    bar_m = _meta(bar_item)

    out = ResolvedMaterials(notes=notes, sources=sources)

    # --- magnet: inline → curves.br_t → meta.brT ---
    br, found = _pick_num(
        mats.get("br_t"),
        mats.get("brT"),
        magnet_c.get("br_t"),
        magnet_m.get("brT"),
        magnet_m.get("br_t"),
        default=_DEFAULT_BR_T,
    )
    out.br_t = br
    if found:
        if mats.get("br_t") is not None or mats.get("brT") is not None:
            sources["br_t"] = "inline"
        elif magnet_c.get("br_t") is not None:
            sources["br_t"] = f"curves:{mats.get('magnet_id')}"
        else:
            sources["br_t"] = f"meta:{mats.get('magnet_id')}"
    elif need_magnet:
        notes.append(f"br_t defaulted to {br} T")
        sources["br_t"] = "default"

    mur, found = _pick_num(
        mats.get("mur_pm"),
        mats.get("muRec"),
        magnet_m.get("muRec"),
        magnet_m.get("mur_pm"),
        default=_DEFAULT_MUR_PM,
    )
    out.mur_pm = mur
    if found:
        sources["mur_pm"] = (
            "inline"
            if mats.get("mur_pm") is not None or mats.get("muRec") is not None
            else f"meta:{mats.get('magnet_id')}"
        )
    else:
        notes.append(f"mur_pm/muRec defaulted to {mur}")
        sources["mur_pm"] = "default"

    tcb, t_found = _pick_num(
        mats.get("tempCoeffBr"),
        mats.get("alphaBr"),
        magnet_c.get("alphaBr"),
        magnet_m.get("tempCoeffBr"),
        default=0.0,
    )
    if t_found:
        out.temp_coeff_br = tcb
        sources["tempCoeffBr"] = "inline/curves/meta"

    # demag: prefer curves.magnet.demag, else meta.demagCurve
    demag_c = magnet_c.get("demag")
    demag_m = magnet_m.get("demagCurve") or mats.get("demagCurve")
    if isinstance(demag_c, list):
        out.magnet_demag_curve = demag_c  # type: ignore[assignment]
        sources["demag"] = "curves"
    elif isinstance(demag_m, list):
        out.magnet_demag_curve = demag_m  # type: ignore[assignment]
        sources["demag"] = "meta"

    # --- coil: inline → curves.resistivity_ohm_m → meta ---
    sig_from_curves = _sigma_from_resistivity(coil_c.get("resistivity_ohm_m"))
    sig_from_meta_rho = _sigma_from_resistivity(
        mats.get("resistivityOhmM") or coil_m.get("resistivityOhmM")
    )
    sig_cu, found = _pick_num(
        mats.get("sigma_copper"),
        mats.get("sigma"),
        mats.get("conductivitySPerM"),
        sig_from_curves,
        coil_m.get("conductivitySPerM"),
        coil_m.get("sigma_copper"),
        coil_m.get("sigma"),
        sig_from_meta_rho,
        default=_DEFAULT_SIGMA_CU,
    )
    out.sigma_copper = sig_cu
    if found:
        if any(
            mats.get(k) is not None
            for k in ("sigma_copper", "sigma", "conductivitySPerM", "resistivityOhmM")
        ):
            sources["sigma_copper"] = "inline"
        elif sig_from_curves is not None:
            sources["sigma_copper"] = f"curves:{mats.get('conductor_id') or mats.get('coil_id')}"
        else:
            sources["sigma_copper"] = f"meta:{mats.get('conductor_id') or mats.get('coil_id')}"
    else:
        notes.append(f"sigma_copper defaulted to {sig_cu:g} S/m")
        sources["sigma_copper"] = "default"

    # --- acim_bar: inline → curves.conductivity_s_per_m → meta ---
    bar_rho = _sigma_from_resistivity(bar_m.get("resistivityOhmM"))
    sig_bar, found = _pick_num(
        mats.get("sigma_bar"),
        mats.get("conductivitySPerM_bar"),
        bar_c.get("conductivity_s_per_m"),
        bar_m.get("conductivitySPerM"),
        bar_m.get("sigma_bar"),
        bar_m.get("sigma"),
        bar_rho,
        default=_DEFAULT_SIGMA_BAR,
    )
    out.sigma_bar = sig_bar
    if found:
        if mats.get("sigma_bar") is not None or mats.get("conductivitySPerM_bar") is not None:
            sources["sigma_bar"] = "inline"
        elif bar_c.get("conductivity_s_per_m") is not None:
            sources["sigma_bar"] = f"curves:{mats.get('bar_id') or mats.get('rotor_bar_id')}"
        else:
            sources["sigma_bar"] = f"meta:{mats.get('bar_id') or mats.get('rotor_bar_id')}"
    elif need_bar:
        notes.append(f"sigma_bar defaulted to {sig_bar:g} S/m (cast-Al class)")
        sources["sigma_bar"] = "default"
    else:
        sources["sigma_bar"] = "default"

    # --- steel: inline → curves.bh / lossCoefficients → meta bhCurve / bsT / ironLossCoeffs ---
    bs_from_curves, mur_from_curves = _bs_mur_from_curves_bh(steel_c.get("bh"))
    bh_meta = steel_m.get("bhCurve") or mats.get("bhCurve")
    bs_from_bh, mur_from_bh = (None, None)
    if isinstance(bh_meta, list):
        out.steel_bh_curve = bh_meta  # type: ignore[assignment]
        bs_from_bh, mur_from_bh = _bs_mur_from_bh_meta(bh_meta)
    elif isinstance(steel_c.get("bh"), dict):
        # retain points for advanced consumers as list of {bT,hAPerM}
        pts = steel_c["bh"].get("points") if isinstance(steel_c.get("bh"), dict) else None
        if isinstance(pts, list):
            out.steel_bh_curve = [
                {"bT": float(p[1]), "hAPerM": float(p[0])}
                for p in pts
                if isinstance(p, (list, tuple)) and len(p) >= 2
            ]

    # bpPoints / curves.bp — retain for loss consumers
    bp_meta = steel_m.get("bpPoints") or mats.get("bpPoints")
    if isinstance(bp_meta, list):
        out.steel_bp_points = bp_meta  # type: ignore[assignment]
    elif isinstance(steel_c.get("bp"), dict):
        pts = steel_c["bp"].get("points")
        if isinstance(pts, list):
            out.steel_bp_points = [
                {"bT": float(p[0]), "pWPerKg": float(p[1])}
                for p in pts
                if isinstance(p, (list, tuple)) and len(p) >= 2
            ]

    bs, found = _pick_num(
        mats.get("bs_t"),
        mats.get("bsT"),
        bs_from_curves,
        steel_m.get("bsT"),
        steel_m.get("bs_t"),
        bs_from_bh,
        default=_DEFAULT_BS_T,
    )
    out.bs_t = bs
    if found:
        if mats.get("bs_t") is not None or mats.get("bsT") is not None:
            sources["bs_t"] = "inline"
        elif bs_from_curves is not None:
            sources["bs_t"] = "curves.bh"
        else:
            sources["bs_t"] = "meta"
    else:
        sources["bs_t"] = "default"

    mur0, found = _pick_num(
        mats.get("mur0"),
        mats.get("muR"),
        mur_from_curves,
        steel_m.get("muR"),
        steel_m.get("mur0"),
        mur_from_bh,
        default=_DEFAULT_MUR0,
    )
    out.mur0 = mur0
    sources["mur0"] = "inline/curves/meta" if found else "default"

    # loss coeffs: curves.lossCoefficients then meta.ironLossCoeffs
    ilc = None
    ilc_src = None
    if isinstance(steel_c.get("lossCoefficients"), dict):
        ilc = steel_c["lossCoefficients"]
        ilc_src = "curves"
    elif isinstance(steel_m.get("ironLossCoeffs"), dict):
        ilc = steel_m["ironLossCoeffs"]
        ilc_src = "meta"
    elif isinstance(mats.get("ironLossCoeffs"), dict):
        ilc = mats["ironLossCoeffs"]
        ilc_src = "inline"

    if isinstance(ilc, dict):
        out.iron_loss_coeffs = {str(k): float(v) for k, v in ilc.items() if _is_num(v)}
        kh_seed, kh_ok = _pick_num(ilc.get("kH"), default=0.02)
        ke_seed, ke_ok = _pick_num(ilc.get("kE"), default=0.0001)
        if kh_ok:
            out.steel_kh = max(kh_seed * 5000.0, 50.0)
            sources["steel_kh"] = f"{ilc_src}.kH"
        if ke_ok:
            out.steel_ke = max(ke_seed * 5000.0, 0.1)
            sources["steel_ke"] = f"{ilc_src}.kE"

    kh, _ = _pick_num(mats.get("kh"), steel_m.get("kh"), default=out.steel_kh)
    ke, _ = _pick_num(mats.get("ke"), steel_m.get("ke"), default=out.steel_ke)
    alpha, _ = _pick_num(mats.get("alpha"), steel_m.get("alpha"), default=1.8)
    out.steel_kh, out.steel_ke, out.steel_alpha = kh, ke, alpha

    if steel_item is None and mats.get("steel_id"):
        notes.append(f"steel_id {mats.get('steel_id')!r} not in catalog; steel defaults used")
    if (
        need_magnet
        and magnet_item is None
        and mats.get("magnet_id")
        and mats.get("br_t") is None
        and mats.get("brT") is None
    ):
        notes.append(f"magnet_id {mats.get('magnet_id')!r} not in catalog; magnet defaults used")

    return out



def _is_num(v: Any) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def resolve_from_request(
    request: dict[str, Any], *, need_magnet: bool = True, need_bar: bool = False
) -> ResolvedMaterials:
    """Convenience: pull materials + optional top-level materials_catalog from SolveRequest."""
    return resolve_materials(
        request.get("materials"),
        materials_catalog=request.get("materials_catalog"),
        need_magnet=need_magnet,
        need_bar=need_bar,
    )
