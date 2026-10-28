from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))

from pmsm_foc import solve_pmsm_foc  # noqa: E402


def test_pmsm_foc_id_iq():
    r = solve_pmsm_foc(
        {
            "machineType": "PMSM",
            "operatingPoint": {"speedRpm": 4000, "idA": 0.0, "iqA": 12.0, "tempC": 80},
            "plant": {"Rs": 0.04, "Ld": 1e-3, "Lq": 1.2e-3, "psi_f": 0.07, "p": 5},
            "nSamples": 72,
        }
    )
    assert r["mode"] == "pmsm_foc"
    assert r["currentsA"]["iq"] == pytest_approx(12.0)
    assert r["lossesW"]["copper"] > 0
    assert r["lossesW"]["magnetEddy"] is not None
    assert abs(r["metrics"]["torqueAvgNm"] - r["operatingPoint"]["torqueNm"]) < 1e-6


def pytest_approx(x, rel=1e-3):
    class A:
        def __eq__(self, other):
            return abs(float(other) - x) <= rel * max(abs(x), 1.0)
    return A()
