# Template: RF PMSM 2D (Q3-4)

| 项 | 值 |
| --- | --- |
| topology | RF |
| machineType | PMSM |
| dim | 2d |
| solverKernel | elmer |
| meshProfile | `rf_pmsm_2d_default` |

## Files
- `case.sif` — Elmer case (**heat-proxy** for Q3 E2E; magnetostatic TBD)
- `mesh.geo` — Gmsh rectangle with Body/BC physical groups

Dry-run writes stub artifacts only. Real solve (`MO_FEM_DRY_RUN=0`) runs gmsh → ElmerGrid → ElmerSolver inside worker-fem. **Do not claim ≤3%.**
