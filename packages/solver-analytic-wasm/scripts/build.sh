#!/usr/bin/env bash
# Build browser Wasm package for apps/web.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="${HOME}/.cargo/bin:${PATH}"
cd "$ROOT"
if ! command -v wasm-pack >/dev/null 2>&1; then
  echo "blocker: wasm-pack not found. Install: cargo install wasm-pack" >&2
  exit 1
fi
if ! rustup target list --installed 2>/dev/null | grep -q wasm32-unknown-unknown; then
  rustup target add wasm32-unknown-unknown
fi
wasm-pack build --target web --out-dir pkg --release
echo "OK: pkg/ ready (solver_analytic_wasm.js + .wasm)"
