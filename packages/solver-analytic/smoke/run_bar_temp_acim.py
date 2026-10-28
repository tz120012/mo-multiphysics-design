#!/usr/bin/env python3
"""Q4-6 smoke: ACIM bar/end-ring ΔT (pending_calibration)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thermal import evaluate_bar_temp_acim  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bar_temp_acim_request.json"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else FIXTURE
    req = json.loads(path.read_text(encoding="utf-8"))
    out = evaluate_bar_temp_acim(req)
    print(json.dumps(out, ensure_ascii=False, indent=2))

    assert out["meta"]["solver"] == "bar_temp_acim"
    assert out["meta"]["pending_calibration"] is True
    assert out["pending_calibration"] is True
    assert out["meta"]["source"] in ("analytic", "drive", "fem")
    assert math.isfinite(out["barDeltaT_K"])
    assert math.isfinite(out["endRingDeltaT_K"])
    assert out["barDeltaT_K"] >= 0.0
    assert out["endRingDeltaT_K"] >= 0.0
    assert "rotorBar" in out["bar_temp"]["lossesW"]

    print(
        f"\n# smoke OK bar_temp_acim barΔT={out['barDeltaT_K']:.4g} K "
        f"endRingΔT={out['endRingDeltaT_K']:.4g} K  "
        f"elapsed_ms={out['meta']['elapsed_ms']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
