"""Unit tests for Maxwell SaveScalars parser (no Elmer required)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))

from postprocess_ms import parse_elmer_scalars_dat  # noqa: E402


class PostprocessMsTests(unittest.TestCase):
    def test_parse_force3_as_axial(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dat = root / "scalars.dat"
            names = root / "scalars.dat.names"
            dat.write_text(
                "   0.0   9.236521314775E-005   3.377E-006  -1.103E-005  -2.726E-003\n",
                encoding="utf-8",
            )
            names.write_text(
                "\n".join(
                    [
                        "Variables in columns of matrix:",
                        "   1: res: eddy current power",
                        "   2: res: electromagnetic field energy",
                        "   3: component 1: res: magnetic force 1",
                        "   4: component 1: res: magnetic force 2",
                        "   5: component 1: res: magnetic force 3",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            out = parse_elmer_scalars_dat(dat, names)
            self.assertEqual(out["postprocess"], "maxwell")
            self.assertAlmostEqual(out["axialForceN"], -2.726e-3, places=8)
            self.assertAlmostEqual(out["forceXN"], 3.377e-6, places=10)
            self.assertAlmostEqual(out["magneticEnergyJ"], 9.236521314775e-5, places=12)
            self.assertIn("uncalibrated", out["notes"])


if __name__ == "__main__":
    unittest.main()
