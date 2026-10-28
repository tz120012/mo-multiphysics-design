import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { fileURLToPath } from 'url'

const root = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(root, '../..')
const wasmPkg = path.resolve(repoRoot, 'packages/solver-analytic-wasm/pkg')

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(root, 'src'),
      // After `packages/solver-analytic-wasm/./build.sh`
      '@mo/solver-analytic-wasm': wasmPkg,
    },
  },
  assetsInclude: ['**/*.wasm'],
  server: {
    port: 5173,
    host: true,
    fs: {
      allow: [repoRoot],
    },
    proxy: {
      // 浏览器走同源 /api → FastAPI，规避 CORS
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  optimizeDeps: {
    exclude: ['@mo/solver-analytic-wasm'],
  },
})
