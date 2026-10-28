from __future__ import annotations

import sys
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))

from bldc_square import solve_bldc_square  # noqa: E402


def test_bldc_square_waveforms_and_losses():
    r = solve_bldc_square(
        {
            "machineType": "BLDC",
            "operatingPoint": {"speedRpm": 3000, "torqueNm": 2.0, "tempC": 75},
            "plant": {"Rs": 0.05, "psi_f": 0.08, "p": 4, "Vdc": 48},
            "nSamples": 72,
        }
    )
    assert r["mode"] == "bldc_square"
    assert "lossesW" in r and r["lossesW"]["copper"] is not None
    assert r["lossesW"]["bar"] is None
    assert "currentsA" in r and r["currentsA"]["rmsPhase"] > 0
    assert r["operatingPoint"]["speedRpm"] == 3000
    wf = r["waveforms"]
    assert len(wf["ia"]) == len(wf["t_s"]) == len(wf["torque_nm"])
    assert r["metrics"]["torqueAvgNm"] > 0
    assert r["metrics"]["torqueRipplePpNm"] >= 0
