# Q6-FE 交测 · Motor 确认

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-29 Asia/Shanghai |
| PR | [#6](https://github.com/tz120012/mo-multiphysics-design/pull/6) tip **`72a368f`**（branch `cursor/q6-c2-workspace-bd3b`） |
| 合入 tip | **`f4acd73`**（merge；本地已叠 `e659e0a` / `05180e2` / `9ec36f5`） |
| CI | Actions smoke **success** @ `72a368f` |
| 依据 | 拍板 A1+B1+C2+D1 **`be6ed88`**；契约 **`55b1255`** |
| 结论 | **准交测**（≠ 放行；≠ Q6 阶段通过；≠ MVP） |

## 审阅要点（Motor）

- **C2 单壳**：`/workspace` 承载几何→材料→激励→网格→求解→后处理；旧路由重定向保留 `projectId`
- **rebuild**：改参 debounce 200ms → `POST /api/v1/geometry/rebuild`；仅 200 + 可用 descriptor 标 live；`paramsHash` 可选
- **fixture 红线**：非 2xx / 空描述符 / `?source=fixture` 降级 `public/mesh`，横幅「样例/fixture · 非建模完成」；禁止 fixture 冒充 200
- **求解**：显式按钮，UEM/`geometrySummary` → `solveRadial`/`solveAxial`；无 live summary 不得拿 fixture 求解

## 下游

1. **Mo-测试**：按 [Q6-冒烟清单](Q6-冒烟清单.md) **Q6-C1…C6** + [Q6-FE-冒烟清单-C2工作台](Q6-FE-冒烟清单-C2工作台.md) 实跑；未测过不得放行
2. **Mo-运维 / Motor**：重建 compose `web`（及必要时 `api`）使 tip 进运行态
3. 禁宣称「已对齐 Maxwell」至 Q6-6；**不重开** v1.0.0；**不扩** F1/F2

---

*Motor · tip `f4acd73` / FE `72a368f`*
