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

# Dual-track: memsSchemaVersion (package) vs geometry schemaVersion (0.1.0-q1).
_GEOMETRY_SCHEMA_VERSION = "0.1.0-q1"
# Authoritative pole count (positive even); pole pairs = poleCount / 2 (derived).
_DEFAULT_POLE_COUNT = 6


def _minimal_geometry_params(project: dict[str, Any]) -> dict[str, Any]:
    """Minimal geometry/params.json fragment (poleCount authority; not a full schema)."""
    topology = project.get("topology") or "RF"
    machine = project.get("machineType") or "PMSM"
    units = project.get("units") or {}
    geom_units = {
        "length": units.get("length", "mm"),
        "angle": units.get("angle", "deg"),
    }
    base: dict[str, Any] = {
        "schemaVersion": _GEOMETRY_SCHEMA_VERSION,
        "topology": topology,
        "machineType": machine,
        "units": geom_units,
    }
    if topology == "AF":
        # AF → pmsm.poleCount (positive even)
        base["config"] = "RFMR"
        base["pmsm"] = {
            "innerDiameter": 40.0,
            "outerDiameter": 100.0,
            "diskCount": 1,
            "airgap": 1.0,
            "diskThickness": 10.0,
            "magnetSectorAngle": 30.0,
            "slotCount": 18,
            "poleCount": _DEFAULT_POLE_COUNT,
        }
    else:
        # RF → rotor.poleCount (positive even)
        base["rotorTopology"] = "inner"
        base["stator"] = {
            "innerDiameter": 51.0,
            "outerDiameter": 80.0,
            "stackLength": 25.0,
            "slotCount": 18,
            "slotShape": "straight",
            "toothWidth": 4.5,
            "yokeHeight": 5.0,
            "skewAngle": None,
        }
        base["rotor"] = {
            "innerDiameter": 15.0,
            "outerDiameter": 50.0,
            "magnetTopology": "SPM",
            "poleCount": _DEFAULT_POLE_COUNT,
        }
        base["airgap"] = 0.5
        base["axialActiveLength"] = 25.0
    return base


def build_minimal_mems_zip(project: dict[str, Any]) -> bytes:
    """Build a minimal valid-ish .mems zip with project.json + geometry/params.json + dirs."""
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
    geometry_json = _minimal_geometry_params(project)
    manifest = {
        "memsSchemaVersion": version,
        "files": ["project.json", "geometry/params.json", "manifest.json"],
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", json.dumps(project_json, indent=2, ensure_ascii=False))
        zf.writestr(
            "geometry/params.json",
            json.dumps(geometry_json, indent=2, ensure_ascii=False),
        )
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        for d in _TOP_DIRS:
            if d == "geometry/":
                continue  # geometry/params.json already present
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


# Q5-5: read/validate accepts both; new writes emit 1.0.0 only (settings default).
ACCEPTED_MEMS_SCHEMA_VERSIONS = frozenset({"1.0.0", "1.0.0-draft"})


def validate_mems_bytes(data: bytes) -> None:
    """PUT/import checks. Raises ValueError with a clear message.

    Rejects non-zip / empty / missing project.json. If project.json carries
    memsSchemaVersion, accept `1.0.0` or `1.0.0-draft` (Q5-5 dual-accept);
    reject other values. Does **not** run a full schema engine.
    """
    if not data:
        raise ValueError("empty .mems body")
    bio = io.BytesIO(data)
    if not zipfile.is_zipfile(bio):
        raise ValueError("body is not a zip (.mems) archive")
    bio.seek(0)
    with zipfile.ZipFile(bio, "r") as zf:
        names = set(zf.namelist())
        if "project.json" not in names:
            raise ValueError(".mems zip missing required project.json")
        try:
            raw = zf.read("project.json")
            proj = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
            raise ValueError("project.json is not valid JSON") from exc
        if not isinstance(proj, dict):
            raise ValueError("project.json must be a JSON object")
        ver = proj.get("memsSchemaVersion")
        if ver is not None and str(ver) not in ACCEPTED_MEMS_SCHEMA_VERSIONS:
            raise ValueError(
                f"unsupported memsSchemaVersion: {ver!r} "
                f"(accepted: {sorted(ACCEPTED_MEMS_SCHEMA_VERSIONS)})"
            )


def mems_get_or_build(project_id: UUID, project: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    """Return stored zip; if missing, build minimal zip and persist it."""
    with _lock:
        stored = _mems.get(project_id)
        if stored is not None:
            return stored["data"], dict(stored["meta"])
        data = build_minimal_mems_zip(project)
        settings = get_settings()
        version = project.get("memsSchemaVersion") or settings.mems_schema_version
        meta = _meta(project_id, data, version, datetime.now(timezone.utc))
        _mems[project_id] = {"data": data, "meta": meta}
        return data, dict(meta)


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
