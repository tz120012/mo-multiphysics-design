# Q4+-3 FE 路径说明 — `/field` source

| 字段 | 内容 |
| --- | --- |
| 角色 | Mo-前端 |
| 对照 | [Q4+-3 收口裁决](../drafts/Q4+-3-mems单文件与artifacts收口.md) §2 / §8 |
| 代码 | `apps/web/src/views/FieldVizView.vue`、`apps/web/src/types/fieldViz.ts` |
| 性质 | 路径说明，供 Q4+-C2 抽查。**不是**冒烟 PASS。 |

**不**勾选解析 ≤5% / FEM ≤3%。**不**宣称 MVP。fixture 路径保留。**不**调用 `GET /projects/{id}/mems` 整包，也**不**新增 `mems/files`（Q4+-3b / F5-A）。

## 尝试顺序

1. 查询 `source=fixture`（大小写不敏感）：不请求 Jobs artifacts。无 `jobId` → 页眉 `source=fixture`；有 `jobId` → `source=job-fixture`，注记含「显式 ?source=fixture」。
2. 无 `jobId`：public fixture `apps/web/public/fem/rf_pmsm_2d_dryrun`，`source=fixture`。
3. 有 `jobId`：先 `GET /api/v1/jobs/{id}`（非终态会短轮询），**无论成败**再 `GET /api/v1/jobs/{id}/artifacts`，并按 `resultRef` / 默认 `solver/fem/jobs/{id}/manifest.json` 与 `artifacts[].path` GET 单文件（manifest、scalars、slice 或 surface、preview）。列表非空，或上述关键 GET 成功 → 页眉 **`source=job-artifacts`**（`data-field-source` 同值）。
4. 仅当列表失败或为空，**且** manifest 与 scalars/slice/preview 均 404 或不可达：同一 public fixture，`source=job-fixture`。列表非空时单文件失败仍保持 `job-artifacts`。

状态条与页脚写「不宣称误差达标」；页脚另写「不宣称 MVP」。不出现精度达标文案。

## 给 Mo-测试的抽查

登录后看场量页眉 `source=`（不要只看 console）。

| URL | 期望 |
| --- | --- |
| `/field?jobId=<已成功且精简件可 GET 的任务>` | `source=job-artifacts`；侧栏来自该 job 的 manifest/scalars，而不是只看到 dry-run 目录 |
| `/field?jobId=<同上>&source=fixture` | 强制 public fixture；`source=job-fixture`；注记含显式 `?source=fixture`；网络面板无 `/artifacts` |
| `/field` 或 `/field?source=fixture` | `source=fixture` |
| `/field?jobId=<不存在或无产物>` | `source=job-fixture`（列表空/404 **且**关键 GET 失败） |

`projectId` 只作元数据展示，不参与本页取数。

## 磁静力学后处理（Q5-2 FE）

方程模式面板见 [Q5-2-FE-field-magnetostatic](Q5-2-FE-field-magnetostatic.md)（FEM tip `797ce67`）。数据源规则以上表为准，不因磁静力学标量改道。
