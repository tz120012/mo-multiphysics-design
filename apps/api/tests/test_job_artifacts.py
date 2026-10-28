"""Smoke: GET /jobs/{id}/artifacts list + single-file (F1 / L4)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

# Ensure import path
import sys

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    work = tmp_path / "fem_work"
    work.mkdir()
    monkeypatch.setenv("MO_FEM_WORKDIR", str(work))
    # Avoid redis / celery side effects
    monkeypatch.setenv("CELERY_ENABLED", "0")
    from app.jobs_store import _jobs, _lock

    with _lock:
        _jobs.clear()
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c, work


def _auth(c: TestClient) -> str:
    r = c.post("/api/v1/auth/login", json={"username": "t", "password": "t"})
    assert r.status_code == 200, r.text
    return r.json()["accessToken"]


def test_list_and_get_from_mems_shadow(client):
    c, work = client
    token = _auth(c)
    headers = {"Authorization": f"Bearer {token}"}

    jid = uuid4()
    manifest = {
        "jobId": str(jid),
        "status": "succeeded",
        "solverKernel": "elmer",
        "topology": "RF",
        "machineType": "PMSM",
        "dim": "2d",
        "scalars": {"torqueNm": 0.0, "dryRun": True, "pending_calibration": True},
        "artifacts": [
            {
                "path": f"results/fem/{jid}/scalars.json",
                "role": "scalars",
                "format": "json",
                "bytes": 12,
            }
        ],
    }
    man_rel = f"solver/fem/jobs/{jid}/manifest.json"
    shadow_man = work / "mems_shadow" / man_rel
    shadow_man.parent.mkdir(parents=True, exist_ok=True)
    shadow_man.write_text(json.dumps(manifest), encoding="utf-8")

    scalars_rel = f"results/fem/{jid}/scalars.json"
    shadow_sc = work / "mems_shadow" / scalars_rel
    shadow_sc.parent.mkdir(parents=True, exist_ok=True)
    shadow_sc.write_text('{"ok":true}\n', encoding="utf-8")

    from app.jobs_store import job_create, job_update
    from datetime import datetime, timezone

    # Seed succeeded job with resultRef (no embedded manifest — disk wins)
    item = job_create(project_id=uuid4(), job_type="fem", payload={"input": {}}, status="queued")
    # Force known id by rewriting store entry
    from app.jobs_store import _jobs, _lock

    with _lock:
        old = _jobs.pop(item["id"])
        old["id"] = jid
        old["status"] = "succeeded"
        old["resultRef"] = man_rel
        old["updatedAt"] = datetime.now(timezone.utc)
        _jobs[jid] = old

    r = c.get(f"/api/v1/jobs/{jid}/artifacts", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["jobId"] == str(jid)
    assert body["resultRef"] == man_rel
    assert len(body["artifacts"]) == 1
    assert body["artifacts"][0]["role"] == "scalars"

    r2 = c.get(f"/api/v1/jobs/{jid}/artifacts/{scalars_rel}", headers=headers)
    assert r2.status_code == 200, r2.text
    assert r2.headers["content-type"].startswith("application/json")
    assert r2.json() == {"ok": True}

    r3 = c.get(f"/api/v1/jobs/{jid}/artifacts/{man_rel}", headers=headers)
    assert r3.status_code == 200
    assert r3.json()["jobId"] == str(jid)

    # Traversal rejected
    r4 = c.get(f"/api/v1/jobs/{jid}/artifacts/../etc/passwd", headers=headers)
    assert r4.status_code in (400, 404)


def test_list_from_embedded_manifest_empty_artifacts(client):
    c, work = client
    token = _auth(c)
    headers = {"Authorization": f"Bearer {token}"}
    # No files on disk; stub-like payload.manifest with artifacts=[]
    from app.jobs_store import job_create, job_update

    item = job_create(
        project_id=uuid4(),
        job_type="fem",
        payload={
            "manifest": {
                "jobId": "x",
                "status": "succeeded",
                "solverKernel": "elmer",
                "topology": "RF",
                "machineType": "PMSM",
                "dim": "2d",
                "scalars": {},
                "artifacts": [],
            }
        },
        status="queued",
    )
    job_update(item["id"], status="succeeded", resultRef=f"solver/fem/jobs/{item['id']}/manifest.json")

    r = c.get(f"/api/v1/jobs/{item['id']}/artifacts", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["artifacts"] == []

    # Single-file non-manifest without disk → 404
    r2 = c.get(
        f"/api/v1/jobs/{item['id']}/artifacts/results/fem/{item['id']}/scalars.json",
        headers=headers,
    )
    assert r2.status_code == 404


def test_job_missing_404(client):
    c, _ = client
    token = _auth(c)
    headers = {"Authorization": f"Bearer {token}"}
    missing = uuid4()
    r = c.get(f"/api/v1/jobs/{missing}/artifacts", headers=headers)
    assert r.status_code == 404
    assert r.json()["code"] == "not_found"


def test_work_roots_fallback_defaults(tmp_path, monkeypatch):
    """No MO_* env → work_roots includes writer defaults (/tmp/mo-opt, /tmp/mo-fem)."""
    monkeypatch.delenv("MO_OPT_WORKDIR", raising=False)
    monkeypatch.delenv("MO_FEM_WORKDIR", raising=False)
    from app import artifacts_resolve as ar

    opt = tmp_path / "mo-opt"
    fem = tmp_path / "mo-fem"
    monkeypatch.setattr(ar, "DEFAULT_OPT_WORKDIR", opt)
    monkeypatch.setattr(ar, "DEFAULT_FEM_WORKDIR", fem)

    roots = ar.work_roots()
    assert opt in roots
    assert fem in roots
    assert opt.is_dir()
    assert fem.is_dir()


def test_get_artifact_from_default_opt_workdir(tmp_path, monkeypatch):
    """In-process path: unset env, file under default opt workdir → GET 200."""
    monkeypatch.delenv("MO_OPT_WORKDIR", raising=False)
    monkeypatch.delenv("MO_FEM_WORKDIR", raising=False)
    monkeypatch.setenv("CELERY_ENABLED", "0")

    from app import artifacts_resolve as ar

    opt = tmp_path / "mo-opt"
    fem = tmp_path / "mo-fem"
    monkeypatch.setattr(ar, "DEFAULT_OPT_WORKDIR", opt)
    monkeypatch.setattr(ar, "DEFAULT_FEM_WORKDIR", fem)

    from app.jobs_store import _jobs, _lock

    with _lock:
        _jobs.clear()
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        token = _auth(c)
        headers = {"Authorization": f"Bearer {token}"}

        jid = uuid4()
        rel = f"results/optimize/{jid}/pareto.json"
        shadow = opt / "mems_shadow" / rel
        shadow.parent.mkdir(parents=True, exist_ok=True)
        shadow.write_text('{"front":[]}\n', encoding="utf-8")

        man_rel = f"solver/optimize/jobs/{jid}/manifest.json"
        manifest = {
            "jobId": str(jid),
            "status": "succeeded",
            "artifacts": [{"path": rel, "role": "pareto", "format": "json", "bytes": 12}],
        }
        man_path = opt / "mems_shadow" / man_rel
        man_path.parent.mkdir(parents=True, exist_ok=True)
        man_path.write_text(json.dumps(manifest), encoding="utf-8")

        from app.jobs_store import job_create
        from datetime import datetime, timezone

        item = job_create(
            project_id=uuid4(), job_type="optimize", payload={"input": {}}, status="queued"
        )
        with _lock:
            old = _jobs.pop(item["id"])
            old["id"] = jid
            old["status"] = "succeeded"
            old["resultRef"] = man_rel
            old["updatedAt"] = datetime.now(timezone.utc)
            _jobs[jid] = old

        r = c.get(f"/api/v1/jobs/{jid}/artifacts/{rel}", headers=headers)
        assert r.status_code == 200, r.text
        assert r.json() == {"front": []}


def test_get_artifact_from_mems_zip_member_when_disk_miss(client):
    """Q4+-3: disk miss → optional project .mems zip member serves artifacts GET."""
    import io
    import zipfile
    from datetime import datetime, timezone

    c, work = client
    token = _auth(c)
    headers = {"Authorization": f"Bearer {token}"}

    pid = uuid4()
    jid = uuid4()
    rel = f"results/fem/{jid}/scalars.json"
    man_rel = f"solver/fem/jobs/{jid}/manifest.json"
    payload_body = b'{"from":"zip","ok":true}\n'
    manifest = {
        "jobId": str(jid),
        "status": "succeeded",
        "solverKernel": "elmer",
        "topology": "RF",
        "machineType": "PMSM",
        "dim": "2d",
        "scalars": {"fromZip": True},
        "artifacts": [
            {"path": rel, "role": "scalars", "format": "json", "bytes": len(payload_body)}
        ],
    }

    # Build minimal .mems zip with project.json + artifact members (no disk copies).
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "project.json",
            json.dumps({"id": str(pid), "name": "zip-fallback"}),
        )
        zf.writestr(man_rel, json.dumps(manifest))
        zf.writestr(rel, payload_body)
    from app.mems_store import mems_put, mems_delete

    mems_put(pid, buf.getvalue())

    from app.jobs_store import job_create, _jobs, _lock

    item = job_create(project_id=pid, job_type="fem", payload={"input": {}}, status="queued")
    with _lock:
        old = _jobs.pop(item["id"])
        old["id"] = jid
        old["projectId"] = pid
        old["status"] = "succeeded"
        old["resultRef"] = man_rel
        old["updatedAt"] = datetime.now(timezone.utc)
        _jobs[jid] = old

    # Ensure workdir has no shadow copy of the scalars file (zip-only path).
    shadow = work / "mems_shadow" / rel
    assert not shadow.exists()

    r_list = c.get(f"/api/v1/jobs/{jid}/artifacts", headers=headers)
    assert r_list.status_code == 200, r_list.text
    listed = r_list.json()
    assert listed["resultRef"] == man_rel
    assert any(a["path"] == rel for a in listed["artifacts"])

    r_get = c.get(f"/api/v1/jobs/{jid}/artifacts/{rel}", headers=headers)
    assert r_get.status_code == 200, r_get.text
    assert r_get.json() == {"from": "zip", "ok": True}

    r_man = c.get(f"/api/v1/jobs/{jid}/artifacts/{man_rel}", headers=headers)
    assert r_man.status_code == 200, r_man.text
    assert r_man.json()["scalars"]["fromZip"] is True

    mems_delete(pid)
