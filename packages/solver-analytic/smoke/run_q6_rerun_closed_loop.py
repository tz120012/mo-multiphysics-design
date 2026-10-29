#!/usr/bin/env python3
"""Q6 smoke: same-entry re-solve after geometry param change (analytic closed-loop).

Proves packages/solver-analytic ``compose_solve_request`` + ``solve()`` can be
re-triggered with a new GeometrySummary slice without a second geometry truth.
Does **not** claim Maxwell UI closed-loop; FE/UEM wiring is out of scope.
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
_ROOT = _PKG.parent.parent
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))
if str(_PKG / "api") not in sys.path:
    sys.path.insert(0, str(_PKG / "api"))

from compose_request import compose_solve_request  # noqa: E402
from solve import solve  # noqa: E402

FIX = _PKG / "smoke" / "fixtures" / "radial_pmsm_request.json"


def main() -> int:
    base = json.loads(FIX.read_text(encoding="utf-8"))
    req1 = compose_solve_request(
        topology=base["topology"],
        machine_type=base["machine_type"],
        geometry=base["geometry"],
        materials=base["materials"],
        operating_point=base["operating_point"],
        schema_version=base["schema_version"],
    )
    r1 = solve(req1, solver="mec")

    geom2 = deepcopy(base["geometry"])
    geom2["airgap_m"] = float(geom2["airgap_m"]) * 1.25
    req2 = compose_solve_request(
        topology=base["topology"],
        machine_type=base["machine_type"],
        geometry=geom2,
        materials=base["materials"],
        operating_point=base["operating_point"],
        schema_version=base["schema_version"],
    )
    r2 = solve(req2, solver="mec")

    t1 = float(r1["torque_nm"])
    t2 = float(r2["torque_nm"])
    if t1 == t2:
        print("FAIL: torque unchanged after airgap change", t1, t2)
        return 1
    if r1.get("meta", {}).get("solver") != "mec":
        print("FAIL: expected meta.solver=mec", r1.get("meta"))
        return 1

    print("PASS Q6 analytic re-solve closed-loop (same entry)")
    print(f"  airgap_m {base['geometry']['airgap_m']} → {geom2['airgap_m']}")
    print(f"  torque_nm {t1} → {t2} (delta={t2 - t1})")
    print(f"  entry=solve(compose_solve_request(...), solver=mec)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
