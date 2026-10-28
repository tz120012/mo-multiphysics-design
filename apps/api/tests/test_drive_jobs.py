"""Drive jobs: payload validation + in-process success path (Q4)."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("CELERY_ENABLED", "0")
    from app.config import get_settings
    from app.jobs_store import _jobs, _lock

    get_settings.cache_clear()
    with _lock:
        _jobs.clear()
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


def _auth(c: TestClient) -> dict[str, str]:
    r = c.post("/api/v1/auth/login", json={"username": "t", "password": "t"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}


def test_drive_payload_validation_missing_mode(client):
    c = client
    h = _auth(c)
    r = c.post(
        "/api/v1/jobs",
        headers=h,
        json={
            "projectId": str(uuid4()),
            "jobType": "drive",
            "payload": {"machineType": "PMSM", "operatingPoint": {"speedRpm": 1000}},
        },
    )
    assert r.status_code == 422, r.text
    body = r.json()
    assert body.get("code") == "validation_error"


def test_drive_job_in_process_succeeds(client):
    c = client
    h = _auth(c)
    r = c.post(
        "/api/v1/jobs",
        headers=h,
        json={
            "projectId": str(uuid4()),
            "jobType": "drive",
            "payload": {
                "mode": "pmsm_foc",
                "machineType": "PMSM",
                "operatingPoint": {"speedRpm": 3000, "iqA": 8.0, "tempC": 80},
                "plant": {"Rs": 0.05, "psi_f": 0.08, "p": 4},
                "pwm": {"carrierHz": 10000, "modIndex": 0.9, "scheme": "svpwm"},
                "deadTime": {"tdeadUs": 1.0},
            },
        },
    )
    assert r.status_code == 202, r.text
    job = r.json()
    jid = job["id"]
    assert job["jobType"] == "drive"
    assert job["status"] in ("queued", "running", "succeeded")

    final = None
    for _ in range(50):
        g = c.get(f"/api/v1/jobs/{jid}", headers=h)
        assert g.status_code == 200
        final = g.json()
        if final["status"] in ("succeeded", "failed", "cancelled"):
            break
        time.sleep(0.05)
    assert final is not None
    assert final["status"] == "succeeded", final
    assert final.get("resultRef", "").startswith("drive://jobs/")
    payload = final.get("payload") or {}
    result = payload.get("result") or {}
    assert "lossesW" in result
    assert "currentsA" in result
    assert result["lossesW"]["copper"] is not None
    assert "waveforms" in result


def test_drive_sync_solve_rejects_map(client):
    c = client
    h = _auth(c)
    # Pydantic pattern on DriveSolveRequest rejects efficiency_map at 422
    r = c.post(
        "/api/v1/drive/solve",
        headers=h,
        json={
            "mode": "efficiency_map",
            "machineType": "PMSM",
            "operatingPoint": {"speedRpm": 1000},
        },
    )
    assert r.status_code == 422, r.text


def test_drive_sync_solve_ok(client):
    c = client
    h = _auth(c)
    r = c.post(
        "/api/v1/drive/solve",
        headers=h,
        json={
            "mode": "bldc_square",
            "machineType": "BLDC",
            "operatingPoint": {"speedRpm": 2000, "torqueNm": 1.5},
            "plant": {"psi_f": 0.08, "p": 4, "Rs": 0.05},
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mode"] == "bldc_square"
    assert "lossesW" in body and "currentsA" in body


def test_efficiency_map_job(client):
    c = client
    h = _auth(c)
    r = c.post(
        "/api/v1/jobs",
        headers=h,
        json={
            "projectId": str(uuid4()),
            "jobType": "drive",
            "payload": {
                "mode": "efficiency_map",
                "mapMode": "pmsm_foc",
                "machineType": "PMSM",
                "operatingPoint": {"tempC": 80},
                "mapGrid": {
                    "nx": 3,
                    "ny": 3,
                    "speedRpmMin": 1000,
                    "speedRpmMax": 3000,
                    "torqueNmMin": 1,
                    "torqueNmMax": 4,
                },
                "plant": {"psi_f": 0.08, "p": 4, "Rs": 0.05},
            },
        },
    )
    assert r.status_code == 202, r.text
    jid = r.json()["id"]
    final = None
    for _ in range(80):
        g = c.get(f"/api/v1/jobs/{jid}", headers=h)
        final = g.json()
        if final["status"] in ("succeeded", "failed", "cancelled"):
            break
        time.sleep(0.05)
    assert final["status"] == "succeeded", final
    result = (final.get("payload") or {}).get("result") or {}
    assert result.get("mode") == "efficiency_map"
    assert len(result["efficiency"]) == 3
