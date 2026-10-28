"""Unified SolveRequest → SolveResult entry for solver-analytic.

``solver`` query: \"mec\" (default) | \"mock\".
RF+PMSM/BLDC → MEC (BLDC = same path + square-wave coeff approx);
RF+ACIM → steady equivalent circuit (``meta.solver=acim_equiv``).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

# Allow `python3 packages/solver-analytic/solve.py` from repo root
_PKG = Path(__file__).resolve().parent
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from axial_planes import solve_axial_pmsm_planes  # noqa: E402
from machines.acim_equiv import solve_radial_acim_equiv  # noqa: E402
from radial_mec import solve_radial_pmsm_mec  # noqa: E402


def mock_solve_radial_pmsm(req: dict[str, Any]) -> dict[str, Any]:
    """Gate0 regression mock (toy scaling). Kept for CI / smoke."""
    import math

    if req.get("topology") != "RF" or req.get("machine_type") != "PMSM":
        raise ValueError("mock path only covers RF + PMSM")

    g = req["geometry"]
    m = req["materials"]
    op = req["operating_point"]

    poles = float(g["poles"])
    length = float(g["stack_length_m"])
    rod = float(g["rotor_od_m"])
    turns = float(g.get("turns_per_phase", 1))
    br = float(m.get("br_t", 1.0))
    i_pk = float(op.get("current_a_peak", 0.0))
    n_rpm = float(op["speed_rpm"])
    gamma = math.radians(float(op.get("gamma_deg", 0.0)))

    flux_per_pole = br * (rod**2) * length / max(poles, 1.0)
    ke = turns * poles * flux_per_pole * 0.5
    omega = n_rpm * 2.0 * math.pi / 60.0
    back_emf = ke * omega
    torque = ke * i_pk * math.cos(gamma)
    copper = 1.5 * (i_pk / math.sqrt(2.0)) ** 2 * 0.05
    iron = 0.02 * abs(n_rpm) * (br**2) * length * 1000.0
    magnet_eddy = 0.005 * abs(n_rpm) * (br**2)
    ld = 1e-3 * turns**2 * length / max(poles, 1.0)
    lq = ld * 0.85

    return {
        "schema_version": req.get("schema_version", "0.0.0-gate0"),
        "meta": {
            "solver": "mock",
            "elapsed_ms": 0,
            "mock": True,
            "note": "Gate0 radial PMSM mock — not for accuracy benchmarking",
        },
        "torque_nm": round(torque, 6),
        "back_emf_v_peak": round(back_emf, 6),
        "losses_w": {
            "copper": round(copper, 6),
            "iron": round(iron, 6),
            "magnet_eddy": round(magnet_eddy, 6),
        },
        "inductance_h": {"ld": round(ld, 9), "lq": round(lq, 9)},
    }


def solve(request: dict[str, Any], *, solver: str | None = None) -> dict[str, Any]:
    """Dispatch SolveRequest.

    Parameters
    ----------
    request:
        Dict matching ``api/solve.schema.json`` SolveRequest.
    solver:
        ``\"mec\"`` (default) or ``\"mock\"``. Also read from ``request[\"solver\"]``
        if this argument is omitted. ACIM always uses the equivalent-circuit path
        when ``solver=mec`` (result ``meta.solver=acim_equiv``).
    """
    kind = (solver or request.get("solver") or "mec").strip().lower()
    topo = request.get("topology")
    mtype = request.get("machine_type")

    if kind == "mock":
        if topo == "RF" and mtype == "PMSM":
            t0 = time.perf_counter()
            out = mock_solve_radial_pmsm(request)
            out["meta"]["elapsed_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
            return out
        raise ValueError(f"mock solver has no path for topology={topo!r} machine_type={mtype!r}")

    if kind == "mec":
        if topo == "AF" and mtype == "PMSM":
            return solve_axial_pmsm_planes(request)
        if topo == "AF" and mtype in ("BLDC", "ACIM"):
            raise ValueError(
                f"AF+{mtype} not implemented yet (Q3 MVP is AF+PMSM only); "
                "see packages/solver-analytic/axial_planes/README.md"
            )
        if topo == "AF":
            raise ValueError(f"unsupported AF machine_type={mtype!r}")
        if topo == "RF" and mtype == "PMSM":
            return solve_radial_pmsm_mec(request)
        if topo == "RF" and mtype == "BLDC":
            return solve_radial_pmsm_mec(request)
        if topo == "RF" and mtype == "ACIM":
            return solve_radial_acim_equiv(request)
        if mtype == "ACIM":
            raise NotImplementedError(
                f"ACIM equivalent-circuit solve requires topology=RF; got topology={topo!r}"
            )
        raise ValueError(f"unsupported combination topology={topo!r} machine_type={mtype!r}")

    raise ValueError(f"unknown solver={kind!r}; expected 'mec' or 'mock'")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    solver = "mec"
    path = None
    for a in argv:
        if a.startswith("--solver="):
            solver = a.split("=", 1)[1]
        elif a in ("-h", "--help"):
            print(
                "usage: solve.py [--solver=mec|mock] [request.json]\n"
                "  RF+PMSM/BLDC → MEC; RF+ACIM → acim_equiv; AF+PMSM → axial_planes",
                file=sys.stderr,
            )
            return 0
        else:
            path = a
    if path is None:
        path = str(_PKG / "smoke" / "fixtures" / "radial_pmsm_request.json")
    req = json.loads(Path(path).read_text(encoding="utf-8"))
    out = solve(req, solver=solver)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
