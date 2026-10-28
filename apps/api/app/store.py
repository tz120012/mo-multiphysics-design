"""In-memory project store used when Postgres is unavailable."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import UUID, uuid4

_lock = Lock()
_projects: dict[UUID, dict[str, Any]] = {}


def mem_list() -> list[dict[str, Any]]:
    with _lock:
        return sorted(_projects.values(), key=lambda p: p["createdAt"])


def mem_get(project_id: UUID) -> dict[str, Any] | None:
    with _lock:
        item = _projects.get(project_id)
        return dict(item) if item else None


def mem_create(
    *,
    name: str,
    topology: str,
    machine_type: str,
    mems_schema_version: str,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    pid = uuid4()
    item = {
        "id": pid,
        "name": name,
        "topology": topology,
        "machineType": machine_type,
        "memsSchemaVersion": mems_schema_version,
        "createdAt": now,
        "updatedAt": now,
    }
    with _lock:
        _projects[pid] = item
        return dict(item)


def mem_update(project_id: UUID, fields: dict[str, Any]) -> dict[str, Any] | None:
    with _lock:
        item = _projects.get(project_id)
        if item is None:
            return None
        for key in ("name", "topology", "machineType", "memsSchemaVersion"):
            if key in fields and fields[key] is not None:
                item[key] = fields[key]
        item["updatedAt"] = datetime.now(timezone.utc)
        return dict(item)


def mem_delete(project_id: UUID) -> bool:
    with _lock:
        if project_id not in _projects:
            return False
        del _projects[project_id]
        return True
