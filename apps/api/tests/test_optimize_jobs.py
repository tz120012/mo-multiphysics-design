"""Q4-9: optimize Jobs → packages/solver-opt (async; no NSGA on request thread)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

_FIXTURE = (
    REPO_ROOT
    / "packages"
    / "solver-opt"
    / "fixtures"
    / "seed42_rf_pmsm_payload.json"
)


def _seed42_payload(**overrides):
    raw = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    # Drop top-level projectId from fixture (JobCreate has its own)
    raw.pop("projectId", None)
    raw.update(overrides)
    return raw


@pytest.fixture()
def client(tmp_path, monkeypatch):
    work = tmp_path / "opt_work"
    work.mkdir()
    monkeypatch.setenv("MO_OPT_WORKDIR", str(work))
    monkeypatch.setenv("MO_FEM_WORKDIR", str(work))
    monkeypatch.setenv("CELERY_ENABLED", "0")
    monkeypatch.setenv("SOLVER_OPT_PATH", str(REPO_ROOT / "packages" / "solver-opt"))
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


def _poll_terminal(c: TestClient, headers: dict, jid: str, timeout_s: float = 15.0):
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = c.get(f"/api/v1/jobs/{jid}", headers=headers)
        assert r.status_code == 200, r.text
        last = r.json()
        if last["status"] in ("succeeded", "failed", "cancelled"):
            return last
        time.sleep(0.05)
    return last


def test_optimize_missing_fields_422(client):
    c, _work = client
    token = _auth(c)
    headers = {"Authorization": f"Bearer {token}"}
    pid = str(uuid4())
    r = c.post(
        "/api/v1/jobs",
        headers=headers,
        json={"projectId": pid, "jobType": "optimize", "payload": {}},
    )
    assert r.status_code == 422, r.text
    body = r.json()
    assert body.get("code") == "validation_error"
    assert "OptimizeJobPayload" in body.get("message", "")


def test_optimize_seed42_happy_path_artifacts(client):
    c, work = client
    token = _auth(c)
    headers = {"Authorization": f"Bearer {token}"}
    pid = str(uuid4())
    r = c.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "projectId": pid,
            "jobType": "optimize",
            "payload": _seed42_payload(),
        },
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["status"] == "queued"
    jid = body["id"]

    final = _poll_terminal(c, headers, jid)
    assert final is not None
    assert final["status"] == "succeeded", final
    expect_ref = f"solver/optimize/jobs/{jid}/manifest.json"
    assert final["resultRef"] == expect_ref

    man = work / "mems_shadow" / expect_ref
    pareto = work / "mems_shadow" / f"results/optimize/{jid}/pareto.json"
    assert man.is_file(), man
    assert pareto.is_file(), pareto

    man_body = json.loads(man.read_text(encoding="utf-8"))
    assert man_body["evaluatorProfile"] == "analytic"
    assert man_body["nsga"]["seed"] == 42
    assert "summary" in man_body and man_body["summary"]["paretoCount"] >= 1

    r_list = c.get(f"/api/v1/jobs/{jid}/artifacts", headers=headers)
    assert r_list.status_code == 200, r_list.text
    listed = r_list.json()
    assert listed["resultRef"] == expect_ref
    paths = [a["path"] for a in listed["artifacts"]]
    assert any(p.endswith("pareto.json") for p in paths), listed
    assert listed["artifacts"][0]["role"] == "pareto"

    r_get = c.get(
        f"/api/v1/jobs/{jid}/artifacts/results/optimize/{jid}/pareto.json",
        headers=headers,
    )
    assert r_get.status_code == 200, r_get.text
    pareto_body = r_get.json()
    assert pareto_body["seed"] == 42
    assert "fronts" in pareto_body and "individuals" in pareto_body
    assert "digest" in pareto_body
    assert len(pareto_body["individuals"]) >= 1


def test_optimize_without_base_solve_uses_fixture(client):
    """Omitting baseSolveRequest is allowed; worker fills seed42 fixture default."""
    c, _work = client
    token = _auth(c)
    headers = {"Authorization": f"Bearer {token}"}
    payload = _seed42_payload()
    payload.pop("baseSolveRequest", None)
    r = c.post(
        "/api/v1/jobs",
        headers=headers,
        json={"projectId": str(uuid4()), "jobType": "optimize", "payload": payload},
    )
    assert r.status_code == 202, r.text
    jid = r.json()["id"]
    final = _poll_terminal(c, headers, jid)
    assert final["status"] == "succeeded", final
    assert final["resultRef"] == f"solver/optimize/jobs/{jid}/manifest.json"


def test_optimize_cancel(client):
    c, _work = client
    token = _auth(c)
    headers = {"Authorization": f"Bearer {token}"}
    r = c.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "projectId": str(uuid4()),
            "jobType": "optimize",
            "payload": _seed42_payload(),
        },
    )
    assert r.status_code == 202, r.text
    jid = r.json()["id"]

    r_cancel = c.post(f"/api/v1/jobs/{jid}/cancel", headers=headers)
    assert r_cancel.status_code == 200, r_cancel.text
    assert r_cancel.json()["status"] == "cancelled"

    final = _poll_terminal(c, headers, jid)
    assert final["status"] == "cancelled"

    r2 = c.post(f"/api/v1/jobs/{jid}/cancel", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "cancelled"

    r404 = c.post(f"/api/v1/jobs/{uuid4()}/cancel", headers=headers)
    assert r404.status_code == 404
