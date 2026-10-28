#!/usr/bin/env python3
"""Q4-7 smoke: LPTN thermal loop → thermal-loop-iter-v0 + meta.converged."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thermal import evaluate_lptn_loop  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "lptn_loop_request.json"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else FIXTURE
    req = json.loads(path.read_text(encoding="utf-8"))
    out = evaluate_lptn_loop(req)
    print(json.dumps(out, ensure_ascii=False, indent=2))

    assert out["schemaVersion"] == "thermal-loop-iter-v0"
    assert out["pending_calibration"] is True
    assert out["meta"]["solver"] == "lptn_loop"
    assert out["meta"]["pending_calibration"] is True
    assert out["meta"]["source"] in ("analytic", "drive", "fem")
    assert out["source"] in ("analytic", "drive", "fem")
    assert isinstance(out["iters"], list) and len(out["iters"]) >= 1
    last = out["iters"][-1]
    assert "lossesIn" in last and "lossesW" in last["lossesIn"]
    assert "tempsOut" in last
    for k in ("windingC", "magnetC", "ambientC"):
        assert k in last["tempsOut"]
        assert last["tempsOut"][k] is None or math.isfinite(last["tempsOut"][k])
    assert "materialUpdate" in last
    assert "BrFactor" in last["materialUpdate"]
    assert "resistivityFactor" in last["materialUpdate"]
    assert "residual" in last
    assert "lossesW" in out
    for k in ("iron", "copper", "pmEddy", "rotorBar", "endRing"):
        assert k in out["lossesW"]
    assert out.get("fem_compare_hook") is None
    # Convergence expected on demo fixture
    assert out["meta"]["converged"] is True

    print(
        f"\n# smoke OK lptn_loop iters={len(out['iters'])} converged={out['meta']['converged']} "
        f"Tw={last['tempsOut']['windingC']:.4g}C Tm={last['tempsOut']['magnetC']:.4g}C "
        f"BrFactor={last['materialUpdate']['BrFactor']:.4g} "
        f"elapsed_ms={out['meta']['elapsed_ms']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
