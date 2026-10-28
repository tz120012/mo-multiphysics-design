# Q1-P04 Undo/Redo 冒烟（bf0a810）

| 字段 | 内容 |
| --- | --- |
| 日期 | 2026-10-28 12:12 Asia/Shanghai |
| 前端 tip | **`bf0a810`**（history 契约 `f43bcd7`） |
| 环境 | `127.0.0.1:5173` + API `:8000`；workspace `projectId=d10456b3-…`；RF-ACIM |
| 范围 | Local-first；**未测** POST history；Linux Ctrl（未测 Cmd） |

## 结果

| 项 | 判定 | 证据 |
| --- | --- | --- |
| 改导条 width 入栈 | PASS | 4→9 后历史 `1/1`，撤销可用 |
| 撤销恢复 | PASS | Ctrl+Z：9→4，历史 `0/1`；按钮同样有效 |
| 重做再应用 | PASS | Ctrl+Shift+Z / Ctrl+Y / 按钮均生效 |
| redo 尾截断 | PASS | Undo 后改 height→历史 `1/1`（非 1/2），width 保持 4 未恢复 9 |
| 快捷键 | PASS | Ctrl+Z、Ctrl+Shift+Z、Ctrl+Y |

## 结论

**P04 → 通过**。仅 ACIM 可编辑字段入栈（已知）。
