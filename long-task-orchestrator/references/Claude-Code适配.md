---
title: Claude Code 适配
created: 2026-06-16
tags: [Claude-Code, 长任务, 适配]
---

# Claude Code 适配

## 推荐载体

- `subagent`：Claude Code 子代理，适合独立阅读、复核、测试和非高风险分析。
- `独立线程`：新 Claude Code 会话、新终端窗口或明确隔离的工作区。
- `命令任务`：普通终端脚本、测试或构建命令。

## 使用方式

把 `long-task-orchestrator/` 复制到项目级 `.claude/skills/long-task-orchestrator/` 或用户级技能目录后，在长任务开始时显式调用本技能。

Claude Code 用户可以把任务包路径直接传给子代理。若子代理无法写回文件，主线程必须要求它输出同结构 JSON，再由主线程写入回执文件。

## 兼容边界

不同工具的新窗口、子代理和权限不同。只要满足以下条件，就视为兼容：

- 执行单元拿到明确任务包。
- 执行单元的写入范围被限制。
- 完成状态能落为机器可读回执。
- 主线程能读取监控状态并独立放行。
