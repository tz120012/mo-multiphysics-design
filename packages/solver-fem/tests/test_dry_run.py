"""Dry-run smoke without Elmer on host."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))

from run_job import run_job  # noqa: E402


class DryRunTests(unittest.TestCase):
    def test_rf_pmsm_2d_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = run_job(
                "11111111-1111-4111-8111-111111111111",
                {
                    "topology": "RF",
                    "machineType": "PMSM",
                    "dim": "2d",
                    "solverKernel": "elmer",
                    "meshProfile": "rf_pmsm_2d_default",
                    "operatingPoint": {"rpm": 3000},
                    "materials": {"magnet": "N42"},
                },
                Path(td),
                dry_run=True,
            )
            self.assertTrue(out["dryRun"])
            self.assertEqual(
                out["resultRef"],
                "solver/fem/jobs/11111111-1111-4111-8111-111111111111/manifest.json",
            )
            man = Path(out["manifestPath"])
            self.assertTrue(man.is_file())
            data = json.loads(man.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "succeeded")
            self.assertEqual(data["topology"], "RF")
            roles = {a["role"] for a in data["artifacts"]}
            self.assertIn("scalars", roles)
            self.assertIn("slice", roles)

    def test_magnetostatic_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = run_job(
                "22222222-2222-4222-8222-222222222222",
                {
                    "templateId": "af_pmsm_3d_ms",
                    "equationMode": "magnetostatic",
                    "topology": "AF",
                    "machineType": "PMSM",
                    "dim": "3d",
                    "solverKernel": "elmer",
                },
                Path(td),
                dry_run=True,
            )
            self.assertTrue(out["dryRun"])
            self.assertEqual(out["equationMode"], "magnetostatic")
            self.assertTrue(out.get("magnetostaticPathReady"))
            man = Path(out["manifestPath"])
            data = json.loads(man.read_text(encoding="utf-8"))
            sc = data["scalars"]
            self.assertEqual(sc.get("equationMode"), "magnetostatic")
            self.assertTrue(sc.get("pending_calibration"))
            self.assertTrue(sc.get("magnetostaticPathReady"))


if __name__ == "__main__":
    unittest.main()
