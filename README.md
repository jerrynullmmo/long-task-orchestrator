---
title: 长任务编排技能
created: 2026-06-16
tags: [长任务, 技能, 代理编排]
---

# 长任务编排技能

`long-task-orchestrator` 是一个面向 Codex 优先、兼容 Claude Code 的代理技能，用来把容易漂移的长任务拆成可控的主线程编排流程。

它解决的不是“如何让代理一直跑”，而是“主线程如何可靠地分派任务、限制执行范围、读取机器回执，并用监控状态和闸门证据决定是否放行”。

## 适用场景

- 一个任务预计超过 15 分钟，且需要多个执行单元分工。
- 主线程上下文容易被长材料、排障、渲染、构建或审计过程塞满。
- 某些产物风险高，需要授权路径、禁止触碰路径和独立回执。
- 需要把子代理、新线程、命令任务或人工执行统一成“独立执行单元”。
- 希望执行方只回传结构化证据，而不是让主线程持续读取完整过程。

## 不适用场景

- 一次性小修、小文件编辑或单命令执行。
- 需要完整任务平台、队列系统、远程调度器或权限中心。
- 只想记录会话进度，而不需要任务包、回执、监控状态和闸门放行。

## 仓库结构

```text
long-task-orchestrator/
  SKILL.md
  references/
  templates/
  scripts/
  examples/
  evals/
docs/plans/
```

## 快速校验

```bash
python3 long-task-orchestrator/scripts/validate_orchestrator.py \
  --project long-task-orchestrator/examples/最小闭环示例
```

预期输出包含 `结果: 通过`。

发布前可用本地私有清单做脱敏自查。先创建不入库的 `.redaction-keywords`，每行写一个敏感片段；需要正则时给该行加 `re:` 前缀。然后运行：

```bash
python3 long-task-orchestrator/scripts/check_redaction.py --keywords .redaction-keywords .
```

## 安装方式

首版按代理技能目录结构发布。支持代理技能规范的工具可以把 `long-task-orchestrator/` 作为技能目录安装或复制到项目级技能目录。

Codex 优先读取 `long-task-orchestrator/SKILL.md`。Claude Code 用户可以复制同一目录到 `.claude/skills/long-task-orchestrator/`，再按本仓库 `references/Claude-Code适配.md` 调整线程创建和回执监控方式。

## 与相邻项目的边界

- `long-task-harness` 类项目偏会话连续性和进度日志。
- `context-packet` 类项目偏上下文包和依赖图解析。
- `superpowers` 偏软件开发方法和子代理执行纪律。
- `agent-teams` 偏多代理任务拆分和团队协作模式。
- 本技能只聚焦长任务交付协议：任务包、隔离执行、机器回执、监控状态和主线程放行。
