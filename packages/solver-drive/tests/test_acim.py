from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))

from acim_vf_foc import solve_acim_foc, solve_acim_vf  # noqa: E402


def test_acim_vf_has_bar_endring():
    r = solve_acim_vf(
        {
            "machineType": "ACIM",
            "operatingPoint": {"speedRpm": 1450, "slip": 0.03, "tempC": 90},
            "plant": {"Rs": 0.5, "Rr": 0.4, "Lm": 0.08, "Lsigma": 0.005, "p": 2, "Vdc": 540},
            "nSamples": 72,
        }
    )
    assert r["mode"] == "acim_vf"
    assert r["lossesW"]["bar"] is not None and r["lossesW"]["bar"] >= 0
    assert r["lossesW"]["endRing"] is not None
    assert r["lossesW"]["magnetEddy"] is None
    assert "slip" in r["operatingPoint"]


def test_acim_foc_currents():
    r = solve_acim_foc(
        {
            "machineType": "ACIM",
            "operatingPoint": {"speedRpm": 1400, "torqueNm": 10.0, "tempC": 85},
            "plant": {"Rs": 0.5, "Rr": 0.4, "Lm": 0.08, "Lsigma": 0.005, "p": 2},
            "nSamples": 72,
        }
    )
    assert r["mode"] == "acim_foc"
    assert r["currentsA"]["id"] is not None and r["currentsA"]["iq"] is not None
    assert abs(r["metrics"]["torqueAvgNm"] - 10.0) < 1.5  # engineering tolerance
