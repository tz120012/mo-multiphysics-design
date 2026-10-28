#!/usr/bin/env bash
# Print toolchain versions then exec CMD (default: sleep infinity for compose).
set -euo pipefail
echo "[mo-fem] toolchain:"
command -v ElmerSolver && ElmerSolver 2>&1 | head -n 2 || true
command -v ElmerGrid && ElmerGrid 2>&1 | head -n 1 || true
command -v gmsh && gmsh -version 2>&1 | head -n 3 || true
command -v getdp && getdp -version 2>&1 | head -n 2 || echo "[mo-fem] getdp: not installed (F2 stub OK)"
mkdir -p "${MO_FEM_WORKDIR:-/var/mo/fem}"
exec "$@"
