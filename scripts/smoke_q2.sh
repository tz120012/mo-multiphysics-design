#!/usr/bin/env bash
# Q2 smoke entry — does NOT fail CI (always exit 0).
# P07: prints evidence pointers; does not run ≤5% golden compare.
# See docs/qa/Q2-冒烟清单.md / docs/qa/Q2-P07-签字包.md
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

tip="$(git rev-parse --short HEAD 2>/dev/null || echo 'NO-GIT')"
echo "=== Q2 smoke @ ${tip} ==="
echo "cwd: $ROOT"
echo
echo "INFO  P01 materials / P02–P04 analytic+Wasm / P05 Benchmark framework / P06 optional — evidence in docs/qa/"
echo "INFO  清单: docs/qa/Q2-冒烟清单.md"
echo "INFO  签字包: docs/qa/Q2-P07-签字包.md"
echo "INFO  阶段汇总: docs/qa/Q2-冒烟记录-P07-阶段汇总.md"
echo "INFO  Benchmark: docs/qa/Q2-Benchmark说明.md"
echo
echo "SKIP  Q2-R4 ≤5% 数值比对未启用（pending_calibration；不宣称达标）"
echo "SKIP  Q2-S1/S2 几何可读 / 材料 UI 引用（遗留，见签字包）"
echo "SKIP  Q2-R5 回归可重复（无比对脚本）"
echo
if [[ -d tests/benchmark/cases ]] && ls tests/benchmark/cases/*/case.json >/dev/null 2>&1; then
  n="$(ls -d tests/benchmark/cases/*/ 2>/dev/null | wc -l | tr -d ' ')"
  echo "OK    Benchmark cases present (n=${n})"
else
  echo "WARN  Benchmark cases missing"
fi
if [[ -d tests/benchmark/golden ]] && ls tests/benchmark/golden/*.json >/dev/null 2>&1; then
  echo "OK    Benchmark golden placeholders present"
else
  echo "WARN  Benchmark golden missing"
fi
echo
echo "RESULT  Q2 smoke entry OK (exit 0; 正式验收以签字包+Motor 签字为准)"
exit 0
