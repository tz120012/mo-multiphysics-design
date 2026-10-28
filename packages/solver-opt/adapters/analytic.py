"""Analytic objective adapter — calls packages/solver-analytic.solve.

MVP (F3 analytic-only):
  abs_torque         maximize  |torque_nm|
  copper_iron_loss   minimize  losses_w.copper + losses_w.iron

Does not own NSGA loop. Spot FEM = stretch (see fem_spot_hook.py).
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[3]
_ANALYTIC = _REPO / "packages" / "solver-analytic"
if str(_ANALYTIC) not in sys.path:
    sys.path.insert(0, str(_ANALYTIC))

from solve import solve  # noqa: E402


def _set_path(obj: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur: Any = obj
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


class AnalyticObjectives:
    """Map variable vector → SolveRequest knobs → objective vector f[]."""

    METRIC_ORDER = ("abs_torque", "copper_iron_loss")

    def __init__(
        self,
        base_request: dict[str, Any],
        variables: list[dict[str, Any]],
        *,
        solver: str = "mec",
    ) -> None:
        self.base = base_request
        self.variables = variables
        self.solver = solver

    def apply_x(self, x: list[float]) -> dict[str, Any]:
        req = copy.deepcopy(self.base)
        for var, val in zip(self.variables, x):
            path = var.get("path") or f"geometry.{var['id']}"
            vtype = var.get("type", "continuous")
            v = int(round(val)) if vtype == "integer" else float(val)
            _set_path(req, path, v)
        return req

    def objectives_from_result(self, result: dict[str, Any]) -> list[float]:
        torque = abs(float(result.get("torque_nm", 0.0)))
        losses = result.get("losses_w") or {}
        copper = float(losses.get("copper", 0.0))
        iron = float(losses.get("iron", 0.0))
        return [torque, copper + iron]

    def evaluate(self, x: list[float]) -> tuple[list[float], dict[str, Any]]:
        req = self.apply_x(x)
        result = solve(req, solver=self.solver)
        return self.objectives_from_result(result), result


def evaluate_individual(
    base_request: dict[str, Any],
    variables: list[dict[str, Any]],
    x: list[float],
    *,
    solver: str = "mec",
) -> list[float]:
    return AnalyticObjectives(base_request, variables, solver=solver).evaluate(x)[0]
