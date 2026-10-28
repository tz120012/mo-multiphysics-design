"""In-memory materials store (Q2-1 typed curves). Seed from JSON; structure ready for Postgres later."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from app.schemas.materials import MATERIALS_SCHEMA_VERSION

_lock = Lock()
_materials: dict[str, dict[str, Any]] = {}
_loaded = False

_SEED_PATH = Path(__file__).resolve().parent / "data" / "materials_seed.json"

_CATEGORY_CURVE_KEY = {
    "steel": "steel",
    "magnet": "magnet",
    "coil": "coil",
    "acim_bar": "acim_bar",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _lift_curves_from_meta(category: str, meta: dict[str, Any]) -> dict[str, Any] | None:
    """Best-effort adapter: old camelCase meta → typed curves (transition)."""
    cat = category.lower()
    if cat == "steel":
        steel: dict[str, Any] = {}
        bh = meta.get("bhCurve")
        if isinstance(bh, list) and len(bh) >= 2:
            steel["bh"] = {
                "xName": "H",
                "yName": "B",
                "xUnit": "A/m",
                "yUnit": "T",
                "points": [[float(p["hAPerM"]), float(p["bT"])] for p in bh],
            }
        bp = meta.get("bpPoints")
        if isinstance(bp, list) and len(bp) >= 2:
            steel["bp"] = {
                "xName": "B",
                "yName": "P",
                "xUnit": "T",
                "yUnit": "W/kg",
                "points": [[float(p["bT"]), float(p["pWPerKg"])] for p in bp],
            }
        if meta.get("ironLossCoeffs"):
            steel["lossCoefficients"] = dict(meta["ironLossCoeffs"])
        return {"steel": steel} if steel else None
    if cat == "magnet":
        br = meta.get("brT")
        demag = meta.get("demagCurve")
        hc = None
        if isinstance(demag, list) and demag:
            hs = [abs(float(p.get("hAPerM", 0))) for p in demag]
            hc = max(hs) if hs else None
        if br is None or hc is None:
            return None
        magnet: dict[str, Any] = {"br_t": float(br), "hc_a_per_m": float(hc)}
        if isinstance(demag, list) and demag:
            magnet["demag"] = [
                {
                    "temperature_c": 20.0,
                    "curve": {
                        "xName": "H",
                        "yName": "B",
                        "xUnit": "A/m",
                        "yUnit": "T",
                        "points": [[float(p["hAPerM"]), float(p["bT"])] for p in demag],
                    },
                }
            ]
        if meta.get("tempCoeffBr") is not None:
            magnet["alphaBr"] = float(meta["tempCoeffBr"])
        return {"magnet": magnet}
    if cat == "coil":
        rho = meta.get("resistivityOhmM")
        if rho is None and meta.get("conductivitySPerM"):
            rho = 1.0 / float(meta["conductivitySPerM"])
        if rho is None:
            return None
        return {"coil": {"resistivity_ohm_m": float(rho)}}
    if cat == "acim_bar":
        sigma = meta.get("conductivitySPerM")
        if sigma is None:
            return None
        return {"acim_bar": {"conductivity_s_per_m": float(sigma)}}
    return None


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    mid = str(row["id"])
    category = str(row["category"])
    meta = dict(row.get("meta") or {})
    # Strip promoted keys from meta if duplicated at top level
    for k in ("builtin", "materialsSchemaVersion"):
        meta.pop(k, None)

    curves = row.get("curves")
    if not curves:
        lifted = _lift_curves_from_meta(category, meta)
        curves = lifted

    builtin = bool(row.get("builtin", meta.get("builtin", False)))
    version = str(row.get("materialsSchemaVersion") or MATERIALS_SCHEMA_VERSION)

    item: dict[str, Any] = {
        "id": mid,
        "name": row["name"],
        "category": category,
        "builtin": builtin,
        "materialsSchemaVersion": version,
        "curves": deepcopy(curves) if curves else None,
        "meta": meta,
        "deletedAt": row.get("deletedAt"),
        "createdAt": row.get("createdAt"),
        "updatedAt": row.get("updatedAt"),
    }
    return item


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        if _SEED_PATH.is_file():
            raw = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
            for row in raw:
                item = _normalize_row(row)
                _materials[item["id"]] = item
        _loaded = True


def materials_list(
    *,
    category: str | None = None,
    include_deleted: bool = False,
) -> list[dict[str, Any]]:
    _ensure_loaded()
    with _lock:
        items = [deepcopy(m) for m in _materials.values()]
    if not include_deleted:
        items = [m for m in items if m.get("deletedAt") is None]
    if category:
        cat = category.strip().lower()
        items = [m for m in items if str(m.get("category", "")).lower() == cat]
    return sorted(items, key=lambda m: m["id"])


def materials_get(material_id: str, *, include_deleted: bool = False) -> dict[str, Any] | None:
    _ensure_loaded()
    with _lock:
        item = _materials.get(material_id)
        if item is None:
            return None
        if item.get("deletedAt") is not None and not include_deleted:
            return None
        return deepcopy(item)


def materials_create(
    *,
    name: str,
    category: str,
    curves: dict[str, Any],
    meta: dict[str, Any] | None = None,
    material_id: str | None = None,
) -> dict[str, Any]:
    """Create a custom (non-builtin) material. builtin always forced false."""
    _ensure_loaded()
    mid = (material_id or f"mat-custom-{uuid4().hex[:12]}").strip()
    now = _utc_now()
    item = {
        "id": mid,
        "name": name,
        "category": category,
        "builtin": False,
        "materialsSchemaVersion": MATERIALS_SCHEMA_VERSION,
        "curves": deepcopy(curves),
        "meta": dict(meta or {}),
        "deletedAt": None,
        "createdAt": now,
        "updatedAt": now,
    }
    with _lock:
        existing = _materials.get(mid)
        if existing is not None and existing.get("deletedAt") is None:
            raise ValueError(f"material id already exists: {mid}")
        _materials[mid] = item
        return deepcopy(item)


def materials_replace(
    material_id: str,
    *,
    name: str,
    category: str,
    curves: dict[str, Any],
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full replace custom material. Raises KeyError if missing; PermissionError if builtin."""
    _ensure_loaded()
    with _lock:
        existing = _materials.get(material_id)
        if existing is None or existing.get("deletedAt") is not None:
            raise KeyError(material_id)
        if existing.get("builtin"):
            raise PermissionError("builtin material is read-only")
        now = _utc_now()
        item = {
            "id": material_id,
            "name": name,
            "category": category,
            "builtin": False,
            "materialsSchemaVersion": MATERIALS_SCHEMA_VERSION,
            "curves": deepcopy(curves),
            "meta": dict(meta or {}),
            "deletedAt": None,
            "createdAt": existing.get("createdAt") or now,
            "updatedAt": now,
        }
        _materials[material_id] = item
        return deepcopy(item)


def materials_soft_delete(material_id: str) -> None:
    """Soft-delete custom material. Raises KeyError if missing; PermissionError if builtin."""
    _ensure_loaded()
    with _lock:
        existing = _materials.get(material_id)
        if existing is None or existing.get("deletedAt") is not None:
            raise KeyError(material_id)
        if existing.get("builtin"):
            raise PermissionError("builtin material is read-only")
        existing["deletedAt"] = _utc_now()
        existing["updatedAt"] = existing["deletedAt"]


def materials_count(*, include_deleted: bool = False) -> int:
    _ensure_loaded()
    with _lock:
        if include_deleted:
            return len(_materials)
        return sum(1 for m in _materials.values() if m.get("deletedAt") is None)
