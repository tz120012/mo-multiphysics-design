"""In-memory .mems zip store + minimal zip builder (Q1 shell)."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import UUID

from app.config import get_settings

_lock = Lock()
# project_id -> {bytes, meta fields}
_mems: dict[UUID, dict[str, Any]] = {}

_TOP_DIRS = (
    "geometry/",
    "materials/",
    "solver/analytic/",
    "solver/fem/",
    "drive/",
    "results/",
    "history/",
)


def build_minimal_mems_zip(project: dict[str, Any]) -> bytes:
    """Build a minimal valid-ish .mems zip with project.json + placeholder dirs."""
    settings = get_settings()
    version = project.get("memsSchemaVersion") or settings.mems_schema_version
    project_json = {
        "id": str(project["id"]),
        "name": project["name"],
        "memsSchemaVersion": version,
        "topology": project["topology"],
        "machineType": project["machineType"],
        "units": project.get("units") or {},
        "createdAt": _iso(project.get("createdAt")),
        "updatedAt": _iso(project.get("updatedAt")),
    }
    manifest = {
        "memsSchemaVersion": version,
        "files": ["project.json", "manifest.json"],
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", json.dumps(project_json, indent=2, ensure_ascii=False))
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        for d in _TOP_DIRS:
            zf.writestr(d + ".gitkeep", "")
    return buf.getvalue()


def _iso(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _meta(project_id: UUID, data: bytes, version: str, updated_at: datetime) -> dict[str, Any]:
    return {
        "projectId": project_id,
        "memsSchemaVersion": version,
        "sizeBytes": len(data),
        "checksumSha256": hashlib.sha256(data).hexdigest(),
        "updatedAt": updated_at,
    }


def mems_get_or_build(project_id: UUID, project: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    """Return stored zip or build a minimal one on the fly (does not persist)."""
    with _lock:
        stored = _mems.get(project_id)
        if stored is not None:
            return stored["data"], dict(stored["meta"])
    data = build_minimal_mems_zip(project)
    settings = get_settings()
    version = project.get("memsSchemaVersion") or settings.mems_schema_version
    meta = _meta(project_id, data, version, datetime.now(timezone.utc))
    return data, meta


def mems_put(project_id: UUID, data: bytes, version: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    ver = version or settings.mems_schema_version
    now = datetime.now(timezone.utc)
    meta = _meta(project_id, data, ver, now)
    with _lock:
        _mems[project_id] = {"data": data, "meta": meta}
        return dict(meta)


def mems_delete(project_id: UUID) -> None:
    with _lock:
        _mems.pop(project_id, None)
