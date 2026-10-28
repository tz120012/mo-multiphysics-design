# Q2 冒烟记录 — P01 材料库 typed tip `bfd27ab`（正式关门）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:27 Asia/Shanghai |
| 正式关门 tip | **`bfd27ab`**（`feat(api): Q2 materials typed curves CRUD + analytic solve 501 stub`） |
| 仓库 HEAD（实测时） | `0b83912`（含 `bfd27ab` 祖先） |
| 执行 | Mo-测试执行员 |
| 性质 | **正式关门冒烟**；过程 tip `2a44125` **不作**关门依据 |

## 环境

- `git merge-base --is-ancestor bfd27ab HEAD` → 通过。
- 实测前 compose `:8000` 容器仍为旧镜像（无 `app.schemas.materials`）；`sudo docker compose … up -d --build api`（box overlay）重建后加载 tip 代码。
- Health：`GET /api/v1/health` → `status=ok`，db/redis `ok=true`（box：host.docker.internal:5433/6380）。
- Auth：`POST /api/v1/auth/login` demo → Bearer。

## Motor 硬口径（须全部 PASS 才关 P01）

| # | 硬口径 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | list **9** / 四类 steel·magnet·coil·acim_bar | n=9；steel2 / magnet2 / coil2 / acim_bar3；`?category=` 四类过滤均正确 | **PASS** |
| 2 | 响应含 typed `curves.*` + `materialsSchemaVersion=0.1.0-q2` + builtin 标记/种子 | 列表 9/9 均有 `curves.<category>`；schema=`0.1.0-q2`；builtin=true×9；GET `mat-steel-m19` / `mat-ndfeb-n42` / `mat-copper` / `mat-acim-bar-al` 分支齐全；未知 id → 404 | **PASS** |
| 3 | POST custom + PUT custom 成功 | POST 201 `mat-custom-1f907c53cd27` steel，`builtin=false`，含 `curves.steel`；PUT 200 改名+曲线成功 | **PASS** |
| 4 | builtin 的 PUT / DELETE → **403** | PUT/DELETE `mat-steel-m19` → 403 `forbidden` / `builtin material is read-only` | **PASS** |
| 5 | DELETE custom 后 GET → **404** | DELETE custom → 204；随后 GET → 404 `not_found` | **PASS** |

## 产品关门四条对照

| 条件 | 判定 |
| --- | --- |
| 1. typed `curves.*` | **PASS** |
| 2. builtin 材料种子齐全 | **PASS**（9×builtin / 四类） |
| 3. `materialsSchemaVersion=0.1.0-q2` | **PASS** |
| 4. PUT / DELETE 可用 | **PASS**（custom 可写可删；builtin 只读 403） |

## 种子 ID（实测）

`mat-steel-m19`、`mat-steel-50ww470`、`mat-ndfeb-n42`、`mat-ndfeb-n35`、`mat-copper`、`mat-coil-al`、`mat-acim-bar-al`、`mat-acim-bar-cu`、`mat-acim-endring-al`

## 未动项

- **未**改 Q2-P04 / Q2-P06 状态（仍通过）。
- **未**改业务代码；仅 `docs/qa`。
- 未以 tip `2a44125` 作为关门依据。

## 结论

| 项 | 结论 |
| --- | --- |
| 硬口径 1–5 | 全部 **PASS** |
| 产品关门四条 | 全部 **PASS** |
| Q2-P01 | **通过 / 关项** |
