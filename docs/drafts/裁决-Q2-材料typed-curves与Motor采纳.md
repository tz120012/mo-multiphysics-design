# 裁决：Q2 材料 typed curves + Motor 采纳 `3c34f1c`

| 字段 | 内容 |
| --- | --- |
| 维护 | Mo-架构 |
| 日期 | 2026-10-28（Asia/Shanghai） |
| 状态 | **已裁决** |
| 依据 | `docs/drafts/Q2-材料与解析边界.md` tip `3c34f1c`；Motor 裁决采纳；Mo-后端 tip `2a44125` FYI |
| 仓库 | `/workspace/mo-platform`（仅本仓库） |

> **不改** `docs/01` / `docs/02` 正文。

## 1. Motor 已采纳（钉死）

| 项 | 结论 |
| --- | --- |
| 交互主路径 | **Wasm**（目标包 `packages/solver-analytic-wasm/`，Rust→wasm32） |
| Jobs / Celery `analytic` | **Q2-6 可选**批处理，非交互硬依赖 |
| `POST /solver/analytic/solve` | **不升为 Q2 MVP 硬项**；CI / Wasm 未就绪时的过渡即可 |
| 其他分叉 | 无 |

## 2. 材料响应形状：typed curves **目标钉死**；`meta` 袋 **过渡可接受**

### 2.1 追认结论（答 Mo-后端）

1. **目标契约不变**：OpenAPI / `Q2-材料与解析边界.md` 的顶层  
   `curves.*` + `builtin` + `materialsSchemaVersion: "0.1.0-q2"` + custom **PUT/DELETE**（seed builtin 只读）。  
2. **接受** tip `2a44125` 现状作为 **过渡**：`Material{id,name,category,meta}`，电磁量与曲线暂放 `meta`（camelCase：`bhCurve` / `bpPoints` / `brT` / …），且 `meta.materialsSchemaVersion` / `meta.builtin` 已出现 —— **允许解析 adapter 继续读 meta**。  
3. **Q2-1 关门前必须完成提升**（否则材料项不得标「通过」）：  
   - 顶层 `curves`（至少覆盖 seed 四类）；  
   - 顶层 `builtin`、`materialsSchemaVersion`；  
   - **PUT** 全量替换 + **DELETE** soft-delete；builtin 写拒绝；  
   - `meta` 降为扩展袋，**不得**再作为曲线唯一载体。  
4. **禁止**再发明第三套键名。过渡映射以本表为准；解析侧 `材料消费字段.md` / `materials_adapter` 中期对齐 `curves`，snake/camel 仅在适配层换算。

### 2.2 过渡 `meta` → 目标 `curves` 映射（最小）

| category | 过渡 meta（`2a44125`） | 目标顶层 |
| --- | --- | --- |
| steel | `bhCurve[]` `{bT,hAPerM}`；`bpPoints[]`；`ironLossCoeffs` | `curves.bh`；`curves.bp`；`lossCoefficients` |
| magnet | demag 点列（若有）+ `brT` / Hc 类键 | `curves.demag`；`br_t` / `hc_a_per_m`（或 camel 对外、对内 SI 文档化二选一，**对外 OpenAPI 跟 typed 草案**） |
| coil | `conductivitySPerM` 等 | 电阻率/电导率字段（非曲线表亦可） |
| acim_bar | 导条电导等 | 材料电热属性；**导条几何仍归 geometry** |

> 对外 JSON 在提升完成后以 OpenAPI typed 为准；提升 PR/commit 须同步改 `openapi-v1.yaml` 与 seed，并通知 Mo-解析改 adapter。

## 3. Wasm 包边界（继续盯）

| 检查项 | 现状（本裁决时 tip ~`4c5e0af`） | 期望 |
| --- | --- | --- |
| `packages/solver-analytic-wasm/` | **尚未建包** | Mo-解析落地；与 `solve.schema.json` 同形 JSON in/out |
| Python `packages/solver-analytic` | Q2 MEC/ACIM 进行中 | **保持 golden / CI** |
| FE local-first | Mo-前端适配中 | Wasm → sync（可选）→ Jobs |

Mo-架构不改业务码；Wasm 目录或 FE 接线 tip 出现后做契约抽检。

## 4. 给各角色的一句话

| 角色 | 动作 |
| --- | --- |
| **Mo-后端** | 过渡 meta **已追认**；排期提升 typed + PUT/DELETE 后再喊验收 |
| **Mo-解析** | 继续 meta adapter；Wasm 包按 `3c34f1c`；勿分叉第二套 Materials API |
| **Mo-前端** | 按 Motor：主路径 Wasm；sync 非硬项 |
| **Motor** | 无新分叉；材料关门以 §2.1.3 为准 |

