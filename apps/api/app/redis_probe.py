"""Optional Redis probe for /health (failures must not fail the health main path)."""

from __future__ import annotations

from typing import Any

from app.config import get_settings


def probe_redis() -> dict[str, Any]:
    try:
        import redis  # lazy: optional at runtime if package missing
    except ImportError:
        return {"ok": False, "error": "redis package not installed"}

    url = get_settings().redis_url
    try:
        client = redis.Redis.from_url(url, socket_connect_timeout=0.5, socket_timeout=0.5)
        pong = client.ping()
        client.close()
        return {"ok": bool(pong)}
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "url_host_hint": "127.0.0.1:6380 (host) or redis:6379 (compose)",
        }
