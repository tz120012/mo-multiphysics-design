#!/usr/bin/env bash
# Q2 smoke placeholder — framework only; does NOT fail CI.
# Q2 analytic / materials / MEC / ACIM not ready: skip and exit 0.
# See docs/qa/Q2-冒烟清单.md and docs/qa/Q2-Benchmark说明.md.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

tip="$(git rev-parse --short HEAD 2>/dev/null || echo 'NO-GIT')"
echo "=== Q2 smoke placeholder @ ${tip} ==="
echo "cwd: $ROOT"
echo
echo "SKIP  Q2 未就绪：无材料库/MEC/ACIM/解析 UI 实跑"
echo "SKIP  Benchmark 比对未启用（tests/benchmark 仅为骨架）"
echo "INFO  清单: docs/qa/Q2-冒烟清单.md"
echo "INFO  Benchmark: docs/qa/Q2-Benchmark说明.md"
echo "INFO  跟踪: docs/qa/Q2-验收跟踪.md"
echo
echo "RESULT  placeholder OK (exit 0; 不挡解析/后端开工，勿作正式验收)"
exit 0
