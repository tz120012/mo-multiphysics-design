from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))

from solve import run_drive_case, run_efficiency_map  # noqa: E402


def test_pwm_deadtime_reduces_torque():
    base = run_drive_case(
        {
            "mode": "pmsm_foc",
            "machineType": "PMSM",
            "operatingPoint": {"speedRpm": 3000, "iqA": 10.0},
            "plant": {"psi_f": 0.08, "p": 4, "Rs": 0.05},
        }
    )
    with_dt = run_drive_case(
        {
            "mode": "pmsm_foc",
            "machineType": "PMSM",
            "operatingPoint": {"speedRpm": 3000, "iqA": 10.0},
            "plant": {"psi_f": 0.08, "p": 4, "Rs": 0.05},
            "pwm": {"carrierHz": 20000, "modIndex": 0.9, "scheme": "svpwm"},
            "deadTime": {"tdeadUs": 2.0},
        }
    )
    assert with_dt["metrics"]["torqueAvgNm"] <= base["metrics"]["torqueAvgNm"] + 1e-9
    assert with_dt["pwm"]["scheme"] == "svpwm"
    assert "deadTimeDistortion" in with_dt["metrics"]


def test_efficiency_map_3x3():
    m = run_efficiency_map(
        {
            "mode": "efficiency_map",
            "mapMode": "pmsm_foc",
            "machineType": "PMSM",
            "mapGrid": {
                "nx": 3,
                "ny": 3,
                "speedRpmMin": 1000,
                "speedRpmMax": 3000,
                "torqueNmMin": 1,
                "torqueNmMax": 5,
            },
            "plant": {"psi_f": 0.08, "p": 4, "Rs": 0.05, "Ld": 1e-3, "Lq": 1.2e-3},
        }
    )
    assert m["mode"] == "efficiency_map"
    assert len(m["axes"]["speedRpm"]) == 3
    assert len(m["axes"]["torqueNm"]) == 3
    assert len(m["efficiency"]) == 3
    assert len(m["efficiency"][0]) == 3
    assert m["meta"]["validCells"] >= 1


def test_run_drive_case_rejects_map_mode():
    import pytest

    with pytest.raises(ValueError, match="efficiency_map"):
        run_drive_case({"mode": "efficiency_map", "machineType": "PMSM"})
