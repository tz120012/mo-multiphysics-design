"""Iron B-H and PM material helpers for radial MEC (engineering first cut)."""
from __future__ import annotations

import math

MU0 = 4.0 * math.pi * 1e-7


def mu_r_steel(B: float) -> float:
    """Relative permeability of generic electrical steel (analytic saturation).

    Starts near 5000 at low B and approaches ~1 as |B| → Bs.
    Not a named grade — good enough for nonlinear iteration demos.
    """
    b = abs(float(B))
    bs = 1.70
    mur0 = 5000.0
    x = b / bs
    # Soft knee via high even power; clamp for numerical safety
    mur = 1.0 + (mur0 - 1.0) / (1.0 + x**8)
    return max(mur, 1.05)


def mu_steel(B: float) -> float:
    """Absolute permeability μ(B) = μ0 · μr(B)."""
    return MU0 * mu_r_steel(B)


def steel_H(B: float) -> float:
    """H [A/m] for given B [T]."""
    b = abs(float(B))
    if b < 1e-12:
        return 0.0
    return b / mu_steel(b)


def pm_mu_r(default: float = 1.05) -> float:
    """Recoil relative permeability of NdFeB-class magnets."""
    return float(default)


def pm_hc(br_t: float, mur_pm: float | None = None) -> float:
    """Coercivity Hc ≈ Br / (μ0 · μr) for linear recoil model."""
    mur = pm_mu_r() if mur_pm is None else float(mur_pm)
    return float(br_t) / (MU0 * mur)
