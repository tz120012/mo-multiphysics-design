#!/usr/bin/env bash
# Build browser package into ./pkg (gitignored — do not commit large .wasm).
set -euo pipefail
cd "$(dirname "$0")"
export PATH="${HOME}/.cargo/bin:${PATH}"

if ! command -v wasm-pack >/dev/null 2>&1; then
  echo "wasm-pack missing; install: cargo install wasm-pack --version 0.12.1" >&2
  exit 1
fi
if ! rustup target list --installed | grep -q '^wasm32-unknown-unknown$'; then
  rustup target add wasm32-unknown-unknown
fi

# web target → ES modules for apps/web (Vite/Webpack)
wasm-pack build --target web --out-dir pkg --release

echo ""
echo "Built: $(pwd)/pkg/"
ls -la pkg/ | sed -n '1,20p'
echo ""
echo "FE import example:"
echo "  import init, { solve_json } from '@mo/solver-analytic-wasm' // or relative to pkg/"
echo "  await init(); const result = JSON.parse(solve_json(JSON.stringify(request)));"
