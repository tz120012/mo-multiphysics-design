"""In-memory jobs store with optional Redis mirror (Q2-6 Celery workers)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import UUID, uuid4

_lock = Lock()
_jobs: dict[UUID, dict[str, Any]] = {}

_REDIS_KEY_PREFIX = "mo:job:"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    out["id"] = str(out["id"])
    out["projectId"] = str(out["projectId"])
    for key in ("createdAt", "updatedAt"):
        val = out.get(key)
        if isinstance(val, datetime):
            out[key] = val.isoformat()
    return out


def _deserialize(raw: dict[str, Any]) -> dict[str, Any]:
    item = dict(raw)
    item["id"] = UUID(str(item["id"]))
    item["projectId"] = UUID(str(item["projectId"]))
    for key in ("createdAt", "updatedAt"):
        val = item.get(key)
        if isinstance(val, str):
            item[key] = datetime.fromisoformat(val.replace("Z", "+00:00"))
    return item


def _redis_client():
    try:
        import redis
    except ImportError:
        return None
    from app.config import get_settings

    url = get_settings().redis_url
    try:
        client = redis.Redis.from_url(url, socket_connect_timeout=0.5, socket_timeout=0.5)
        if not client.ping():
            client.close()
            return None
        return client
    except Exception:  # noqa: BLE001
        return None


def _redis_set(item: dict[str, Any]) -> None:
    client = _redis_client()
    if client is None:
        return
    try:
        key = f"{_REDIS_KEY_PREFIX}{item['id']}"
        client.set(key, json.dumps(_serialize(item), default=str), ex=86400)
    except Exception:  # noqa: BLE001
        pass
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass


def _redis_get(job_id: UUID) -> dict[str, Any] | None:
    client = _redis_client()
    if client is None:
        return None
    try:
        raw = client.get(f"{_REDIS_KEY_PREFIX}{job_id}")
        if not raw:
            return None
        return _deserialize(json.loads(raw))
    except Exception:  # noqa: BLE001
        return None
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass


def redis_available() -> bool:
    client = _redis_client()
    if client is None:
        return False
    try:
        client.close()
    except Exception:  # noqa: BLE001
        pass
    return True


def job_create(
    *,
    project_id: UUID,
    job_type: str,
    payload: dict[str, Any] | None = None,
    status: str = "queued",
) -> dict[str, Any]:
    now = _now()
    jid = uuid4()
    item = {
        "id": jid,
        "projectId": project_id,
        "jobType": job_type,
        "status": status,
        "resultRef": None,
        "error": None,
        "createdAt": now,
        "updatedAt": now,
        "payload": payload,
    }
    with _lock:
        _jobs[jid] = item
        out = dict(item)
    _redis_set(out)
    return out


def job_get(job_id: UUID) -> dict[str, Any] | None:
    """Prefer Redis mirror when present (Celery worker updates), else memory."""
    remote = _redis_get(job_id)
    if remote is not None:
        with _lock:
            _jobs[job_id] = remote
        return dict(remote)
    with _lock:
        item = _jobs.get(job_id)
        return dict(item) if item else None


def job_update(job_id: UUID | str, **fields: Any) -> dict[str, Any] | None:
    jid = job_id if isinstance(job_id, UUID) else UUID(str(job_id))
    with _lock:
        item = _jobs.get(jid)
        if item is None:
            remote = _redis_get(jid)
            if remote is None:
                return None
            _jobs[jid] = remote
            item = remote
        for key, val in fields.items():
            if key in ("status", "resultRef", "error", "payload"):
                item[key] = val
        item["updatedAt"] = _now()
        out = dict(item)
    _redis_set(out)
    return out
