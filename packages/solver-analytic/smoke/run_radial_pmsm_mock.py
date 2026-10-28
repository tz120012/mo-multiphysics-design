#!/usr/bin/env python3
"""Gate0 smoke: radial PMSM fake-data → numeric SolveResult (mock, no accuracy claim)."""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "radial_pmsm_request.json"


def mock_solve(req: dict) -> dict:
    if req.get("topology") != "RF" or req.get("machine_type") != "PMSM":
        raise SystemExit("Gate0 smoke only covers RF + PMSM")

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

    # Toy scaling only — placeholder until real MEC lands post-Gate0
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
        "schema_version": "0.0.0-gate0",
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


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else FIXTURE
    req = json.loads(path.read_text(encoding="utf-8"))
    t0 = time.perf_counter()
    out = mock_solve(req)
    out["meta"]["elapsed_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    assert isinstance(out["torque_nm"], (int, float))
    assert isinstance(out["back_emf_v_peak"], (int, float))
    assert out["losses_w"]["copper"] >= 0
    assert out["meta"]["mock"] is True
    print(
        f"\n# smoke OK RF/PMSM mock "
        f"T={out['torque_nm']} Nm  E={out['back_emf_v_peak']} V  "
        f"elapsed_ms={out['meta']['elapsed_ms']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
