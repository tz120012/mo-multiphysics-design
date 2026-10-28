#!/usr/bin/env python3
"""Q4-9 smoke: fixed-seed analytic NSGA stub → Pareto digest + schema shape check."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]
_REPO = _PKG.parents[1]
sys.path.insert(0, str(_PKG))
sys.path.insert(0, str(_REPO / "packages" / "solver-analytic"))

from adapters.analytic import AnalyticObjectives  # noqa: E402
from nsga.core import run_nsga2_stub  # noqa: E402


def _load(name: str) -> dict:
    return json.loads((_PKG / "fixtures" / name).read_text(encoding="utf-8"))


def _basic_schema_check(payload: dict, pareto: dict, manifest: dict) -> None:
    for key in ("variables", "objectives", "nsga", "evaluatorProfile"):
        if key not in payload:
            raise AssertionError(f"payload missing {key}")
    if payload["evaluatorProfile"] != "analytic":
        raise AssertionError("MVP smoke expects evaluatorProfile=analytic")
    if "seed" not in payload["nsga"]:
        raise AssertionError("nsga.seed required")
    for key in ("seed", "objectiveIds", "fronts", "individuals"):
        if key not in pareto:
            raise AssertionError(f"pareto missing {key}")
    for key in ("jobId", "status", "evaluatorProfile", "nsga", "summary", "artifacts"):
        if key not in manifest:
            raise AssertionError(f"manifest missing {key}")
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return
    api = _PKG / "api"
    jsonschema.validate(payload, json.loads((api / "optimize-job-payload.schema.json").read_text()))
    jsonschema.validate(manifest, json.loads((api / "optimize-manifest.schema.json").read_text()))
    jsonschema.validate(pareto, json.loads((api / "pareto-results.schema.json").read_text()))


def main() -> int:
    write_golden = "--write-golden" in sys.argv
    payload = _load("seed42_rf_pmsm_payload.json")
    nsga = payload["nsga"]
    seed = int(nsga["seed"])
    pop = int(nsga["popSize"])
    gens = int(nsga["generations"])
    variables = payload["variables"]
    senses = [o["sense"] for o in payload["objectives"]]
    objective_ids = [o["metricId"] for o in payload["objectives"]]
    variable_ids = [v["id"] for v in variables]

    adapter = AnalyticObjectives(payload["baseSolveRequest"], variables, solver="mec")

    def evaluate(x: list[float]) -> list[float]:
        return adapter.evaluate(x)[0]

    result = run_nsga2_stub(
        variables=variables,
        senses=senses,
        evaluate=evaluate,
        pop_size=pop,
        generations=gens,
        seed=seed,
    )

    pareto = {
        "seed": seed,
        "generations": gens,
        "objectiveIds": objective_ids,
        "variableIds": variable_ids,
        "fronts": result["fronts"],
        "individuals": result["individuals"],
        "digest": result["digest"],
    }

    job_id = "fixture-seed42"
    manifest = {
        "jobId": job_id,
        "status": "succeeded",
        "evaluatorProfile": "analytic",
        "nsga": {"popSize": pop, "generations": gens, "seed": seed},
        "summary": {
            "generationsRun": gens,
            "paretoCount": result["digest"]["paretoCount"],
            "evaluations": result["evaluations"],
            "note": "analytic-only MVP stub; not accuracy-gated",
        },
        "artifacts": [
            {"path": f"results/optimize/{job_id}/pareto.json", "kind": "pareto"}
        ],
        "resultRef": f"solver/optimize/jobs/{job_id}/manifest.json",
    }

    _basic_schema_check(payload, pareto, manifest)

    expected_path = _PKG / "fixtures" / "seed42_pareto_expected.json"
    manifest_path = _PKG / "fixtures" / "seed42_manifest.json"
    if write_golden or not expected_path.exists():
        expected_path.write_text(
            json.dumps(pareto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    else:
        golden = json.loads(expected_path.read_text(encoding="utf-8"))
        if golden.get("digest") != result["digest"]:
            raise AssertionError(
                f"golden digest mismatch: got {result['digest']} expected {golden.get('digest')}"
            )
        if int(golden.get("seed", -1)) != seed:
            raise AssertionError("golden seed mismatch")

    result2 = run_nsga2_stub(
        variables=variables,
        senses=senses,
        evaluate=evaluate,
        pop_size=pop,
        generations=gens,
        seed=seed,
    )
    if result2["digest"] != result["digest"]:
        raise AssertionError(
            f"seed determinism failed: {result['digest']} != {result2['digest']}"
        )

    sample = next(
        (ind for ind in pareto["individuals"] if ind["rank"] == 0),
        pareto["individuals"][0],
    )
    print("solver-opt smoke OK")
    print(f"seed={seed}")
    print(f"generations={gens}")
    print(f"popSize={pop}")
    print(f"paretoCount={result['digest']['paretoCount']}")
    print(f"evaluations={result['evaluations']}")
    print(f"sample_x={sample['x']}")
    print(f"sample_f={sample['f']}  # [abs_torque_nm, copper+iron_W]")
    print(f"digest={json.dumps(result['digest'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
