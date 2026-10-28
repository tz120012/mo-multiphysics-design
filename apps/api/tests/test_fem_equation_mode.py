"""Q5-2: FemJobPayload equationMode + magnetostatic stub honesty."""

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
def client(tmp_path, monkeypatch):
    work = tmp_path / "fem_work"
    work.mkdir()
    monkeypatch.setenv("MO_FEM_WORKDIR", str(work))
    monkeypatch.setenv("CELERY_ENABLED", "0")
    # Default dry-run stub path
    monkeypatch.setenv("MO_FEM_DRY_RUN", "1")
    from app.jobs_store import _jobs, _lock

    with _lock:
        _jobs.clear()
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c, work


def _auth(c: TestClient) -> dict[str, str]:
    r = c.post("/api/v1/auth/login", json={"username": "t", "password": "t"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}


def _fem_payload(**extra):
    base = {
        "topology": "AF",
        "machineType": "PMSM",
        "dim": "3d",
        "solverKernel": "elmer",
        "meshProfile": "af_pmsm_3d_min",
        "operatingPoint": {"rpm": 1000},
        "materials": {"magnet": "N35"},
    }
    base.update(extra)
    return base


def _poll(c, headers, jid, timeout_s=5.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = c.get(f"/api/v1/jobs/{jid}", headers=headers)
        assert r.status_code == 200, r.text
        body = r.json()
        if body["status"] in ("succeeded", "failed", "cancelled"):
            return body
        time.sleep(0.05)
    raise AssertionError(f"job {jid} not terminal")


def test_magnetostatic_stub_honesty(client):
    c, work = client
    headers = _auth(c)
    r = c.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "projectId": str(uuid4()),
            "jobType": "fem",
            "payload": _fem_payload(equationMode="magnetostatic"),
        },
    )
    assert r.status_code == 202, r.text
    jid = r.json()["id"]
    job = _poll(c, headers, jid)
    assert job["status"] == "succeeded"
    assert job["resultRef"] == f"solver/fem/jobs/{jid}/manifest.json"

    # Embedded / disk manifest scalars
    from app.jobs_store import job_get
    from uuid import UUID

    stored = job_get(UUID(jid))
    assert stored is not None
    man = (stored.get("payload") or {}).get("manifest") or {}
    sc = man.get("scalars") or {}
    assert sc.get("equationMode") == "magnetostatic"
    assert sc.get("pending_calibration") is True
    assert sc.get("dryRun") is True
    assert sc.get("magnetostaticPathReady") is False
    assert sc.get("axialForceN") is None
    # Must not invent a real force from heat-proxy
    assert sc.get("torqueNm") is None


def test_template_af_pmsm_3d_ms_implies_magnetostatic(client):
    c, _work = client
    headers = _auth(c)
    r = c.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "projectId": str(uuid4()),
            "jobType": "fem",
            "payload": _fem_payload(templateId="af_pmsm_3d_ms"),
        },
    )
    assert r.status_code == 202, r.text
    jid = r.json()["id"]
    job = _poll(c, headers, jid)
    assert job["status"] == "succeeded"
    from app.jobs_store import job_get
    from uuid import UUID

    man = (job_get(UUID(jid)).get("payload") or {}).get("manifest") or {}
    sc = man.get("scalars") or {}
    assert sc.get("equationMode") == "magnetostatic"
    assert sc.get("magnetostaticPathReady") is False


def test_heat_proxy_default_compat(client):
    c, _work = client
    headers = _auth(c)
    r = c.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "projectId": str(uuid4()),
            "jobType": "fem",
            "payload": _fem_payload(),  # no equationMode
        },
    )
    assert r.status_code == 202, r.text
    jid = r.json()["id"]
    _poll(c, headers, jid)
    from app.jobs_store import job_get
    from uuid import UUID

    sc = ((job_get(UUID(jid)).get("payload") or {}).get("manifest") or {}).get("scalars") or {}
    assert sc.get("equationMode") == "heat_proxy"
    assert sc.get("pending_calibration") is True
    assert sc.get("axialForceN") is None


def test_invalid_equation_mode_422(client):
    c, _work = client
    headers = _auth(c)
    r = c.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "projectId": str(uuid4()),
            "jobType": "fem",
            "payload": _fem_payload(equationMode="magic"),
        },
    )
    assert r.status_code == 422, r.text


def test_build_stub_manifest_unit():
    from app.tasks.fem import build_stub_manifest, resolve_equation_mode

    assert resolve_equation_mode({"equationMode": "magnetostatic"}, dry_run=True) == "magnetostatic"
    assert resolve_equation_mode({"templateId": "af_pmsm_3d_ms"}, dry_run=False) == "magnetostatic"
    assert resolve_equation_mode({}, dry_run=False) == "heat_proxy"
    man = build_stub_manifest("jid", {"equationMode": "magnetostatic", "topology": "AF"})
    assert man["scalars"]["magnetostaticPathReady"] is False
    assert man["scalars"]["axialForceN"] is None
