"""Tiny deterministic NSGA-II-flavoured stub for seed fixtures.

Pure Python + stdlib random. Not research-grade; stretch = pymoo in worker.
Same (seed, pop, gen, evaluator) → same Pareto digest.
"""
from __future__ import annotations

import math
import random
from typing import Any, Callable


def _dominates(fa: list[float], fb: list[float], senses: list[str]) -> bool:
    better = False
    for a, b, s in zip(fa, fb, senses):
        aa = -a if s == "maximize" else a
        bb = -b if s == "maximize" else b
        if aa > bb:
            return False
        if aa < bb:
            better = True
    return better


def non_dominated_rank(F: list[list[float]], senses: list[str]) -> list[int]:
    n = len(F)
    ranks = [0] * n
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if _dominates(F[j], F[i], senses):
                ranks[i] += 1
    levels = sorted(set(ranks))
    level_map = {lv: k for k, lv in enumerate(levels)}
    return [level_map[r] for r in ranks]


def _sample_x(rng: random.Random, variables: list[dict[str, Any]]) -> list[float]:
    x: list[float] = []
    for var in variables:
        lo, hi = float(var["bounds"][0]), float(var["bounds"][1])
        if var.get("type") == "integer":
            x.append(float(rng.randint(int(math.ceil(lo)), int(math.floor(hi)))))
        else:
            x.append(rng.uniform(lo, hi))
    return x


def _mutate(
    rng: random.Random,
    x: list[float],
    variables: list[dict[str, Any]],
    *,
    rate: float = 0.3,
) -> list[float]:
    y = list(x)
    for i, var in enumerate(variables):
        if rng.random() > rate:
            continue
        lo, hi = float(var["bounds"][0]), float(var["bounds"][1])
        if var.get("type") == "integer":
            y[i] = float(rng.randint(int(math.ceil(lo)), int(math.floor(hi))))
        else:
            span = hi - lo
            y[i] = min(hi, max(lo, y[i] + rng.uniform(-0.15 * span, 0.15 * span)))
    return y


def run_nsga2_stub(
    *,
    variables: list[dict[str, Any]],
    senses: list[str],
    evaluate: Callable[[list[float]], list[float]],
    pop_size: int,
    generations: int,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    pop = [_sample_x(rng, variables) for _ in range(pop_size)]
    F = [evaluate(x) for x in pop]
    evals = pop_size

    for _gen in range(generations):
        offspring = [_mutate(rng, pop[rng.randrange(pop_size)], variables) for _ in range(pop_size)]
        F_off = [evaluate(x) for x in offspring]
        evals += pop_size
        pool_x = pop + offspring
        pool_f = F + F_off
        ranks = non_dominated_rank(pool_f, senses)
        order = sorted(range(len(pool_x)), key=lambda i: (ranks[i], pool_f[i][0]))
        selected = order[:pop_size]
        pop = [pool_x[i] for i in selected]
        F = [pool_f[i] for i in selected]

    ranks = non_dominated_rank(F, senses)
    front0 = [i for i, r in enumerate(ranks) if r == 0]
    individuals = []
    for i, (x, f) in enumerate(zip(pop, F)):
        xs: list[Any] = []
        for j, var in enumerate(variables):
            if var.get("type") == "integer":
                xs.append(int(round(float(x[j]))))
            else:
                xs.append(round(float(x[j]), 9))
        individuals.append(
            {
                "id": f"ind-{i}",
                "x": xs,
                "f": [round(v, 6) for v in f],
                "rank": ranks[i],
                "feasible": True,
            }
        )

    f0 = [individuals[i]["f"] for i in front0] or [ind["f"] for ind in individuals]
    cols = list(zip(*f0)) if f0 else []
    digest = {
        "paretoCount": len(front0),
        "fMin": [round(min(c), 6) for c in cols] if cols else [],
        "fMax": [round(max(c), 6) for c in cols] if cols else [],
    }
    return {
        "seed": seed,
        "generations": generations,
        "evaluations": evals,
        "fronts": [{"rank": 0, "indices": front0}],
        "individuals": individuals,
        "digest": digest,
    }
