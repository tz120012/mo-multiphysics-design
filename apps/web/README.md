# Mo Web（`apps/web`）

Vue 3 + TypeScript + Vite + Element Plus + Vue Router + Pinia 工程壳（Q1-3）。

深色工程软件风：石墨黑底、细分割线、青绿 / 琥珀点缀。暂未接入 Three.js（见 Q1-4/5 工作区预留）。

## 环境

- Node.js ≥ 20
- 包管理：优先 **pnpm**（已锁定 `packageManager`）

## 安装

```bash
cd apps/web
pnpm install
```

可选：复制环境变量示例

```bash
cp .env.example .env
# VITE_API_BASE=http://localhost:8000
```

## 开发

```bash
pnpm dev
```

默认 http://localhost:5173 。

### 冒烟步骤

1. 打开浏览器访问开发地址，未登录会跳转到 `/login`
2. 输入任意账号 / 密码，点击「登录」（假登录，token 写入 `localStorage`）
3. 自动进入 `/projects` 工程列表（3 条示例假数据）
4. 可点「新建工程」打开对话框占位（仅本地 store，不调真实 API）
5. 清除 `localStorage` 的 `mo_token` 或点「退出」后，访问 `/projects` 应回到 `/login`

## 构建

```bash
pnpm build
```

产物在 `dist/`。预览：

```bash
pnpm preview
```

## 目录要点

| 路径 | 说明 |
| --- | --- |
| `src/styles/tokens.css` | 色板 / 字体设计令牌 |
| `src/router/index.ts` | 路由 + 鉴权守卫 |
| `src/stores/auth.ts` | 假登录 / token |
| `src/stores/projects.ts` | 工程列表假数据 |
| `src/api/client.ts` | axios 封装，`baseURL` ← `VITE_API_BASE` |
| `src/layouts/AppLayout.vue` | 顶栏布局（含工作区路由注释占位） |

## 已知限制

- 鉴权为 localStorage 占位，无真实后端校验
- 工程 CRUD 不调 API
- 工作区 / Three.js 未实现（路由注释预留）
