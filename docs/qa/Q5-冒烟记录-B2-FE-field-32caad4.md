# Q5 冒烟记录 — FE `/field` 磁静力学后处理四场景（@ `32caad4`）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 18:49 Asia/Shanghai |
| 业务 tip | **`32caad4`**（`feat(web): show magnetostatic postprocess on /field`） |
| tip 全 SHA | `32caad4833091e0e4c2e6708cbb5651b3ad10249` |
| PR | https://github.com/tz120012/mo-multiphysics-design/pull/5（open；head=`32caad4`） |
| 对照 FEM | tip **`797ce67`**（真路径标量形；CLI 见 [B1-磁静力学](Q5-冒烟记录-B1-磁静力学-797ce67.md)） |
| 对照 API | tip **`e3074b9`** / CLI B1 **`61f7b53`**（既证；本轮不重做） |
| 对照 Q5-5 | tip **`67824ba`**（谢；本轮**无需重做**） |
| 对照 Q4+ | [Q4plus-FE-field-source](Q4plus-FE-field-source.md)、[C2-FE-field-source](Q4plus-冒烟记录-C2-FE-field-source.md)（F1 source 四场景口径不变） |
| 执行 | Mo-测试；**仅** `docs/qa/` 证据入库；**未**改业务代码；无 browser 工具 |
| 性质 | Motor 正式抽检口径 ∪ 前端交测四场景；**FE 路径证据**；**不代关** B2 / Q3-L4 整行；**禁勾 F2/≤3%**；**不开宣称 MVP** |

## 环境

| 证据 | 结果 |
| --- | --- |
| FE 检出 | `/workspace/mo-multiphysics-design-qa` @ **`32caad4`**（detached） |
| 自检脚本 | `apps/web/src/lib/fieldPostprocess.check.ts` → esbuild → node；**exit 0** |
| public fixture | `apps/web/public/fem/rf_pmsm_2d_dryrun/{manifest,scalars}.json` |
| 本地 API | `http://127.0.0.1:8000` health **200**；`MO_FEM_DRY_RUN=1`（compose box） |
| Vite `:5173` | 服务 **mo-platform** `apps/web`（**无** `fieldPostprocess.ts`）→ **不能**代表 tip `32caad4` UI |
| 隔离 | 仅 `/workspace/mo-platform` 写 `docs/qa`；FE 源只读抽检 |

## Motor 抽检口径（合并一次）

| # | 口径 | 证据 | 结论 |
| --- | --- | --- | --- |
| M1 | `equationMode=magnetostatic` → 侧栏「磁静力学后处理」含 `postprocess` / `axialForceN` / `magneticEnergyJ` 等 + `pending_calibration` | `fieldPostprocess.check.ts` true-path（797ce67 形：`postprocess=maxwell`、`axialForceN=-0.002726984380961`、`magneticEnergyJ≈9.24e-5`、`pending=true`、力/能 `uncalibrated`）；`buildFieldPostprocessView` title=`磁静力学后处理` | **PASS（源码+自检）** |
| M2 | heat-proxy / 旧 fixture →「非磁静力学真值」 | public fixture 无 `equationMode` → kind=`heat-proxy`、title=`heat-proxy / 非磁静力学真值`；`equationMode=heat_proxy` 同；旧 fixture **不**出 axial/magneticEnergy 行 | **PASS（源码+自检）** |
| M3 | `/field` 仍 F1（field 路径/降级口径）；对齐 FEM **797ce67** | `FieldVizView.vue` 注释 §1–6：source 规则未改；后处理只读已取 scalars/manifest；disclaimer「不宣称误差达标，不宣称 MVP」；check 禁 `≤`/`MVP 已` | **PASS（静态）** |

## 前端四场景

| # | URL / 场景 | 期望 | 实测 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `/field`（或 `/field?source=fixture`） | `source=fixture`；heat-proxy / 非磁静力学真值；`pending_calibration` | public fixture：无 `equationMode`；`buildFieldPostprocessView(manifest,scalars)` → kind=`heat-proxy`、title=`heat-proxy / 非磁静力学真值`、`pendingCalibration=true`、`equationMode=missing`；`data-field-source` 无 jobId 分支 → `fixture`（`FieldVizView` L838/L674） | **PASS（源码+fixture+自检）** |
| 2 | `/field?jobId=<磁静力学 scalars>` | `source=job-artifacts`；磁静力学后处理；maxwell + `axialForceN` + `magneticEnergyJ`（未校准） | 自检 true-path / API-shape：kind=`magnetostatic`、title=`磁静力学后处理`、`postprocess=maxwell`、轴向力/磁能 `uncalibrated=true`；source 规则：有 jobId 且 artifacts 可达 → `job-artifacts`（L781） | **PASS（源码+自检）**；真人 UI / 真 job 喂 FE 见下「缺口」 |
| 3 | heat-proxy `jobId` | 标题**不是**「磁静力学后处理」 | 自检 heat：title=`heat-proxy / 非磁静力学真值`；`hasMsTitle=false`；无 magnetostatic 行键 | **PASS（源码+自检）** |
| 4 | `&source=fixture`（有 jobId） | `source=job-fixture` | `forceFixture`（query `source=fixture`）→ `loadFixtureDegraded` → `src='job-fixture'`（L838–840、L674）；degradeReason=`显式 ?source=fixture` | **PASS（静态路径）** |

**四场景总评：PASS（源码级 / 自检脚本；无 browser）**

## compose API 备注（可喂 FE 的 fixture 尝试）

| jobId | `equationMode`（input） | 产物 scalars | 对 FE 含义 |
| --- | --- | --- | --- |
| `cad1ddf2-e98f-4cb5-be17-397844b0ef4d` | `magnetostatic` | stub：**缺** `equationMode`；仅 `torqueNm/dryRun/pending_calibration/notes`；`artifacts: []`（manifest 经 resultRef 可 GET） | 当前 box dry-run stub **未**写出 `equationMode` → FE 会按 **missing → heat-proxy** 理解；**不能**当作磁静力学 UI 真值样例（与 B1-API pytest @ `e3074b9` 期望的诚实 stub 形不一致 / 或运行镜像未含该写回） |
| `b940f46b-f4c4-4373-b341-5199aaf0a1e3` | `heat_proxy` | 同上缺 mode | 兼容旧路径；标题侧应为非磁静力学真值 |

> 磁静力学面板数值形仍以 FEM tip **`797ce67`** + FE 自检注入为准；**不计** dry-run stub 力为已校准真值。

## 缺口 / 需主代理 computerUse

| 项 | 说明 |
| --- | --- |
| **需主代理 computerUse** | tip **`32caad4`** 检出后启 Vite，目视 `/field` 四 URL：`data-field-source`、侧栏 `data-postprocess-kind` / 标题 / `pending_calibration` 徽章、力/能旁未校准标记 |
| 本执行器 | **无** browser；`:5173` 为 mo-platform 旧 web（无本 tip 面板）→ **未**做真人 UI 判 |
| 真路径 job-artifacts UI | 需写出含 `equationMode=magnetostatic` + maxwell 标量的 artifacts（writeback / 非缺 mode 的 stub）后再喂 FE |

## 禁令确认

| 项 | 本记录 |
| --- | --- |
| F2 / ≤3% | **未勾** / **未宣称** |
| MVP / tag `v1.0.0` | **未宣称** / **未打** |
| B2 / Q3-L4 **整行** | **不代关**（仍后置 Q5-4 数值口径 · 产品 `bd6ae86`） |
| 产品签字 | **不代签** |
| heat-proxy ≠ 磁静力学真值 | **已钉** |

## 清单 / 跟踪变更（本 commit）

| 文档 | 变更 |
| --- | --- |
| [Q5-冒烟清单](Q5-冒烟清单.md) | 记 FE 证据 tip **`32caad4`**；B2 注 FE 路径可记、**整行仍后置**；**F2 不勾** |
| [Q5-验收跟踪](Q5-验收跟踪.md) | 变更记录追加 FE `/field` 抽测；产品 Q5-2/Q5-4 **不代改**状态；L4 整行仍后置 |

## 相关链接

- PR #5 · FE tip `32caad4`
- FEM tip `797ce67` · [B1 CLI](Q5-冒烟记录-B1-磁静力学-797ce67.md) · [B1-API](Q5-冒烟记录-B1-API-e3074b9.md)
- [Q4plus-FE-field-source](Q4plus-FE-field-source.md) · [C2-FE](Q4plus-冒烟记录-C2-FE-field-source.md)
- 上游说明（FE 仓）：`docs/qa/Q5-2-FE-field-magnetostatic.md` @ `32caad4`

---

*Mo-测试 · FE `/field` 四场景 + Motor 抽检 · 隔离仅 `/workspace/mo-platform`。*
