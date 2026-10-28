#!/usr/bin/env python3
"""Q2 smoke: radial ACIM steady equivalent circuit → numeric SolveResult (mock=false)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from solve import solve  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "radial_acim_request.json"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else FIXTURE
    req = json.loads(path.read_text(encoding="utf-8"))
    out = solve(req, solver="mec")

    print(json.dumps(out, ensure_ascii=False, indent=2))

    assert out["meta"]["solver"] == "acim_equiv"
    assert out["meta"]["mock"] is False
    assert isinstance(out["meta"]["elapsed_ms"], (int, float))
    assert out["meta"]["elapsed_ms"] >= 0
    assert math.isfinite(out["torque_nm"])
    assert math.isfinite(out["back_emf_v_peak"])
    assert "rotor_bar" in out["losses_w"]
    assert math.isfinite(out["losses_w"]["rotor_bar"])
    assert out["losses_w"]["copper"] >= 0.0
    assert out["losses_w"]["iron"] >= 0.0
    assert out["losses_w"]["rotor_bar"] >= 0.0
    # Finite and typically motoring torque at slip ~0.03
    assert abs(out["torque_nm"]) < 1e6

    print(
        f"\n# smoke OK RF/ACIM acim_equiv "
        f"T={out['torque_nm']:.6g} Nm  E_ag={out['back_emf_v_peak']:.6g} V  "
        f"Pcu={out['losses_w']['copper']:.6g} W  "
        f"Protor={out['losses_w']['rotor_bar']:.6g} W  "
        f"Pfe={out['losses_w']['iron']:.6g} W  "
        f"slip={out['meta'].get('acim', {}).get('slip')}  "
        f"elapsed_ms={out['meta']['elapsed_ms']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
