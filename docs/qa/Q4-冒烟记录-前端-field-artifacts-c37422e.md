# Q4 冒烟记录 — 前端 tip `c37422e`（Q3-L4 /field artifacts；并行 FYI）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 14:42 Asia/Shanghai |
| 指派 tip | **`c37422e`**（`feat(web): load /field from job artifacts with fixture fallback`） |
| 合并 tip | **`f207bbb`**（`Merge FE tip c37422e: /field 接 L4 job artifacts`） |
| 执行 | Mo-测试（并行结果短记；**不挡** Q4-P05） |
| 范围 | `/field` L4 降级 public fixture；**非** P05 门禁；**不**宣称 FEM ≤3% |

## 实测摘要（照抄）

| 项 | 结果 |
| --- | --- |
| `/field` | **PASS（L4 降级 public fixture）** |
| source | `fixture` |
| jobId | **未带** |
| pending_calibration | 有（口径遵守） |
| ≤3% | **未宣称** |

## 跟踪影响

| 项 | 变更 |
| --- | --- |
| Q3-L4 | **仍跟踪中**；FE 接线部分推进（本记录）；**整行不关**（除非产品另改口径） |
| Q4-P05 | **无关**（本轮不挡；见 [Q4-冒烟记录-前端-compare-7a45369](Q4-冒烟记录-前端-compare-7a45369.md)） |
| P11 | **不改** |

## 结论

`/field` @ `c37422e`/`f207bbb`：**PASS（L4 降级 public fixture）**；Q3-L4 仍跟踪中；**未**勾 ≤3%；**未**宣称 MVP。
