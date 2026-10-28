# Motor 签字 · Q5-4 FEM ≤3%（有限范围）/ F2

| 项 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 Asia/Shanghai |
| 签字人 | Motor · Mo 项目经理 |
| 业务 tip | `56ba136`（闭磁路 pot-core / `ms_gap_force_3d`） |
| 测试复现 tip | `0461681`（D1-rev2） |
| 报告 | [标定报告-FEM-20261028-Q5-4](reports/标定报告-FEM-20261028-Q5-4.md) rev2 |

## 裁定

1. **同意勾选冒烟清单 Q5-F2（有限范围）**。
2. **可宣称范围（硬边界）**：仅 verification case **`ms-gap-force-001`** / 模板 **`ms_gap_force_3d`** / 书面单指标  
   Maxwell `|Fz|` vs `body-rms(Bz)²·A/(2μ0)`；相对误差 ≈ **1.32% ≤ 3%**。
3. **不可外推**：完整 AF 电机、其它模板（含 `af_pmsm_3d_ms`）、1D 教材激励对照（≈8.3%，不作关闭）、heat-proxy。
4. **Q5-4 跟踪状态** → **有限范围通过（单指标）**（原「阻塞（数值）」关闭）。
5. **Q3-L4 整行** → **关闭**：真磁静力学路径（Q5-2）+ 本验证 case 已标定；产品级全机型仍见各 job `pending_calibration` 策略。
6. **仍禁止**：宣称 **MVP 已达成**；打 tag `v1.0.0`；勾 **F1**（解析 ≤5% 仍阻塞 Q5-3）。
7. 隔离仅 `/workspace/mo-platform`。

## 依据

- 有限元 rev2 tip `56ba136`；罐式闭磁路实跑；`equationMode=magnetostatic`；`elmerExit=0`。
- 测试复现 tip `0461681`：量级一致；`claimable_fem_le_3pct=true`；总评同意有限宣称；**未代签**。
- rev1 ≈93%（`76dc43a`）**不作**关闭依据。

## 后续

- Q5-3（解析 ≤5% / F1）仍阻塞，待用户 CC BY-NC 或替代金标。
- Q5-6/Q5-7 与 MVP/tag 须 Q5-3 与其余退出项齐后 Motor 再议。

## 产品确认（Mo-产品）

同意 Motor 裁定（tip **`15bbd97`**）：

1. Q5-4 → **有限范围通过（单指标）**；**勾 F2（有限）**。
2. **可宣称范围**：仅 `ms-gap-force-001` / `ms_gap_force_3d` / body-rms 单指标 ≈1.32%。
3. **不可外推**：AF 整机 / `af_pmsm_3d_ms` / 1D≈8.3% / heat-proxy。
4. **Q3-L4 整行关闭**；**禁 F1**；**不开 MVP / 不打 tag**；Q5-3 仍阻塞。

产品 tip 见本 commit。

*Mo-产品 · 对齐 Motor 有限 F2 · 不开 MVP。*

---

*Motor · 有限 F2 签字 · 不开 MVP。*
