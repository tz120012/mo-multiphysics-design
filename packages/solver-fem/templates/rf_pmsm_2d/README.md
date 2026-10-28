# Template: RF PMSM 2D (Q3-4 first sample)

| 项 | 值 |
| --- | --- |
| topology | RF |
| machineType | PMSM |
| dim | 2d |
| solverKernel | elmer (primary) |
| meshProfile | `rf_pmsm_2d_default` |

## Files
- `case.sif` — Elmer case stub (placeholders for geometry/BC/materials)
- `mesh.geo` — Gmsh script stub (container-only)

Dry-run does not invoke Elmer; real solve runs inside `apps/fem` image.
