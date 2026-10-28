"""In-memory materials store (Q2-1). Seed from JSON; structure ready for Postgres later."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

_lock = Lock()
_materials: dict[str, dict[str, Any]] = {}
_loaded = False

_SEED_PATH = Path(__file__).resolve().parent / "data" / "materials_seed.json"


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
                mid = str(row["id"])
                _materials[mid] = {
                    "id": mid,
                    "name": row["name"],
                    "category": row["category"],
                    "meta": dict(row.get("meta") or {}),
                }
        _loaded = True


def materials_list(*, category: str | None = None) -> list[dict[str, Any]]:
    _ensure_loaded()
    with _lock:
        items = list(_materials.values())
    if category:
        cat = category.strip().lower()
        items = [m for m in items if str(m.get("category", "")).lower() == cat]
    return sorted(items, key=lambda m: m["id"])


def materials_get(material_id: str) -> dict[str, Any] | None:
    _ensure_loaded()
    with _lock:
        item = _materials.get(material_id)
        return dict(item) if item else None


def materials_create(
    *,
    name: str,
    category: str,
    meta: dict[str, Any] | None = None,
    material_id: str | None = None,
) -> dict[str, Any]:
    """Create a custom (non-builtin) material. Optional explicit id."""
    _ensure_loaded()
    mid = (material_id or f"mat-custom-{uuid4().hex[:12]}").strip()
    meta_out = dict(meta or {})
    meta_out.setdefault("builtin", False)
    item = {
        "id": mid,
        "name": name,
        "category": category,
        "meta": meta_out,
    }
    with _lock:
        if mid in _materials:
            raise ValueError(f"material id already exists: {mid}")
        _materials[mid] = item
        return dict(item)


def materials_count() -> int:
    _ensure_loaded()
    with _lock:
        return len(_materials)
