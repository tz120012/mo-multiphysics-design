#!/usr/bin/env python3
"""Q4-6 smoke: PM demag margin → demagMargin + workingPoint (pending_calibration)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thermal import evaluate_demag_pm  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "demag_pm_request.json"


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else FIXTURE
    req = json.loads(path.read_text(encoding="utf-8"))
    out = evaluate_demag_pm(req)
    print(json.dumps(out, ensure_ascii=False, indent=2))

    assert out["meta"]["solver"] == "demag_pm"
    assert out["meta"]["pending_calibration"] is True
    assert out["pending_calibration"] is True
    assert out["meta"]["mock"] is False
    assert out["meta"]["source"] in ("analytic", "drive", "fem")
    assert math.isfinite(out["demagMargin"])
    assert "workingPoint" in out
    assert math.isfinite(out["workingPoint"]["b_t"])
    assert math.isfinite(out["workingPoint"]["h_a_per_m"])
    assert out["demag"]["demag_margin"] == out["demagMargin"]

    print(
        f"\n# smoke OK demag_pm demagMargin={out['demagMargin']:.4g} "
        f"B={out['workingPoint']['b_t']:.4g} T  source={out['meta']['source']} "
        f"elapsed_ms={out['meta']['elapsed_ms']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
