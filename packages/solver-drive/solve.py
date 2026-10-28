"""Unified drive entry: run_drive_case / run_efficiency_map."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

_PKG = Path(__file__).resolve().parent
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from acim_vf_foc import solve_acim_foc, solve_acim_vf  # noqa: E402
from bldc_square import solve_bldc_square  # noqa: E402
from efficiency_map import run_map  # noqa: E402
from pmsm_foc import solve_pmsm_foc  # noqa: E402
from pwm_deadtime import apply_corrections, parse_pwm  # noqa: E402

SINGLE_MODES = frozenset({"bldc_square", "pmsm_foc", "acim_vf", "acim_foc"})
ALL_MODES = SINGLE_MODES | frozenset({"efficiency_map"})


def _normalize_mode(cfg: dict[str, Any]) -> str:
    raw = str(cfg.get("mode") or cfg.get("driveMode") or cfg.get("drive_mode") or "").strip().lower()
    aliases = {
        "bldc": "bldc_square",
        "square": "bldc_square",
        "foc": "pmsm_foc",
        "pmsm": "pmsm_foc",
        "vf": "acim_vf",
        "v/f": "acim_vf",
        "acim": "acim_vf",
        "induction_foc": "acim_foc",
        "map": "efficiency_map",
        "efficiency": "efficiency_map",
    }
    mode = aliases.get(raw, raw)
    if mode not in ALL_MODES:
        raise ValueError(
            f"Unknown drive mode {raw!r}; expected one of "
            f"{sorted(ALL_MODES)}"
        )
    return mode


def _dispatch_single(cfg: dict[str, Any], mode: str) -> dict[str, Any]:
    if mode == "bldc_square":
        return solve_bldc_square(cfg)
    if mode == "pmsm_foc":
        return solve_pmsm_foc(cfg)
    if mode == "acim_vf":
        return solve_acim_vf(cfg)
    if mode == "acim_foc":
        return solve_acim_foc(cfg)
    raise ValueError(f"Not a single-case mode: {mode}")


def run_drive_case(config: dict[str, Any]) -> dict[str, Any]:
    """Run one drive operating point (not efficiency_map).

    Returns result with public fields lossesW / currentsA / operatingPoint.
    Applies PWM/dead-time corrections when pwm or deadTime present.
    """
    cfg = dict(config or {})
    mode = _normalize_mode(cfg)
    if mode == "efficiency_map":
        raise ValueError("efficiency_map requires run_efficiency_map(); use Jobs for maps")
    t0 = time.perf_counter()
    result = _dispatch_single(cfg, mode)
    # Apply PWM/deadtime if configured (or always attach defaults summary)
    has_pwm = isinstance(cfg.get("pwm"), dict) or isinstance(
        cfg.get("deadTime") or cfg.get("dead_time"), dict
    )
    if has_pwm:
        result = apply_corrections(result, cfg)
    else:
        result["pwm"] = parse_pwm(cfg)
    elapsed = (time.perf_counter() - t0) * 1000.0
    meta = dict(result.get("meta") or {})
    meta["elapsed_ms"] = round(elapsed, 3)
    result["meta"] = meta
    # Objective-export aliases (drive owns Map/ripple/loss measures; not NSGA core)
    metrics = dict(result.get("metrics") or {})
    if "torqueRipplePpNm" in metrics and "ripplePpNm" not in metrics:
        metrics["ripplePpNm"] = metrics["torqueRipplePpNm"]
    result["metrics"] = metrics
    result.setdefault("source", "drive")
    return result


def run_efficiency_map(config: dict[str, Any]) -> dict[str, Any]:
    """Scan torque–speed grid. Prefer Jobs enqueue at API layer (never block browser)."""
    cfg = dict(config or {})
    # Allow mode=efficiency_map with mapMode, or mode=pmsm_foc with mapGrid
    mode = str(cfg.get("mode") or "").strip().lower()
    if mode in ("efficiency_map", "map", "efficiency", ""):
        drive_mode = str(
            cfg.get("mapMode") or cfg.get("driveMode") or cfg.get("drive_mode") or "pmsm_foc"
        ).strip().lower()
        aliases = {
            "bldc": "bldc_square",
            "foc": "pmsm_foc",
            "pmsm": "pmsm_foc",
            "vf": "acim_vf",
            "induction_foc": "acim_foc",
        }
        drive_mode = aliases.get(drive_mode, drive_mode)
        if drive_mode not in SINGLE_MODES:
            drive_mode = "pmsm_foc"
        cfg = {**cfg, "mode": drive_mode}
    else:
        drive_mode = _normalize_mode(cfg)
        if drive_mode == "efficiency_map":
            drive_mode = "pmsm_foc"
        cfg = {**cfg, "mode": drive_mode}

    t0 = time.perf_counter()

    def _case(point_cfg: dict[str, Any]) -> dict[str, Any]:
        # Skip PWM on every map cell by default for speed; optional flag
        pc = dict(point_cfg)
        if not cfg.get("mapApplyPwm"):
            pc.pop("pwm", None)
            pc.pop("deadTime", None)
            pc.pop("dead_time", None)
        return run_drive_case(pc)

    out = run_map(cfg, _case)
    out["meta"]["elapsed_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mo solver-drive CLI")
    parser.add_argument("config_json", nargs="?", help="Path to config JSON")
    parser.add_argument("--map", action="store_true", help="Run efficiency map")
    args = parser.parse_args(argv)
    if not args.config_json:
        parser.print_help()
        return 2
    cfg = json.loads(Path(args.config_json).read_text(encoding="utf-8"))
    if args.map or str(cfg.get("mode", "")).lower() in ("efficiency_map", "map"):
        out = run_efficiency_map(cfg)
    else:
        out = run_drive_case(cfg)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
