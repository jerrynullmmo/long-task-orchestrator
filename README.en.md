---
title: Long Task Orchestrator Skill
created: 2026-06-17
tags: [long-task, skill, agent-orchestration]
---

# Long Task Orchestrator Skill

English | [中文](README.md)

`long-task-orchestrator` is an agent skill for Codex-first workflows, with Claude Code compatibility notes. It turns long, drift-prone work into a controlled orchestration loop led by the main thread.

It is not a tool for “letting an agent run forever.” It is a protocol for how the main thread delegates work, limits write scope, reads machine-readable receipts, checks monitor state, and decides whether a stage can pass the gate.

## What It Improves

| Problem | With this skill |
|---|---|
| The main thread reads materials, edits artifacts, and decides release at the same time | The main thread keeps only goals, state, authorization, and gate decisions |
| Subagents or new windows receive too much context and expand scope | Each execution unit receives only a bounded task package, required files, and authorized paths |
| An execution unit says “done,” but there is no auditable evidence | Completion must be written as a machine-readable receipt plus monitor state |
| A lightweight subagent edits high-risk artifacts directly | High-risk artifacts default to an isolated thread or an equivalent isolated carrier |
| After multiple retries, nobody knows whether the stage can advance | A gate script checks structural evidence before the main thread makes the final decision |

For tasks longer than 2 hours, this protocol can significantly improve the output stability and auditable quality of Codex 5.5 xhigh model runs. It reduces context drift, unauthorized writes, and evidence-free release decisions. It does not replace final business review.

## When To Use It

- A task is expected to take more than 2 hours and needs multiple execution units.
- The main thread is likely to be overloaded by long files, debugging, rendering, building, or audit work.
- Some artifacts are high risk and need authorized paths, forbidden paths, and an independent receipt.
- You need to normalize subagents, new threads, command tasks, or manual execution as execution units.
- You want the worker to return structured evidence instead of forcing the main thread to read the entire work transcript.

## When Not To Use It

- One-off small edits, tiny file changes, or single-command work.
- Full task platforms, queue systems, remote schedulers, permission centers, or dashboards.
- Simple session progress notes that do not need task packages, receipts, monitor state, or gate release.

## Repository Layout

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

## Installation

With GitHub CLI:

```bash
gh skill install jerrynullmmo/long-task-orchestrator
```

You can also copy `long-task-orchestrator/` into a project-level skill directory. Codex reads `long-task-orchestrator/SKILL.md` first. Claude Code users can copy the same directory to `.claude/skills/long-task-orchestrator/`, then follow `references/Claude-Code适配.md` for thread creation and receipt monitoring adjustments.

## Minimal Workflow

### Step 1: Decide Whether To Delegate

The main thread first decides whether the task should be delegated. Delegate when any of these is true:

- The task is long enough that doing it in the main thread would crowd the context.
- The task needs an isolated window, subagent, command task, or manual confirmation.
- The artifact is high risk and needs explicit authorization and a receipt.
- The stage needs review, critique, or evidence gathering.

If you choose not to delegate, still write the reason into the dispatch record, such as “read-only explanation,” “tiny edit,” or “an execution unit is already waiting to return a receipt.”

### Step 2: Create A State Package Directory

Create these files in the target project. See `examples/最小闭环示例/状态包/` for a complete example:

```text
状态包/
  当前状态.json
  调度记录.json
  任务包/
  回执/
  监控/
```

These files keep stage state outside the chat transcript.

### Step 3: Copy The Task Package Template

Copy `templates/任务包.template.json` into the target project’s `状态包/任务包/`, then fill the minimum fields:

| Field | Purpose |
|---|---|
| `任务包ID` | Binds the task package, receipt, and monitor state |
| `执行单元类型` | Marks `subagent`, `独立线程`, `命令任务`, or `人工执行` |
| `上游状态版本` | Prevents delivery against stale upstream state |
| `必读文件` | Limits the materials the worker must read |
| `允许写入路径` | Limits where the worker may write |
| `授权产物路径` | Defines the expected artifacts |
| `禁止触碰路径` | Defines paths that must not be touched |
| `回执监控路径` | Defines where the worker writes the receipt |
| `监控器状态路径` | Defines where the main thread or automation checks monitor state |
| `验收标准` | Defines how the main thread decides whether to enter the gate |

High-risk artifacts should only be authorized to `独立线程` or to an equivalent isolated carrier explicitly accepted by the user.

### Step 4: Send The Task Package To The Execution Unit

Send only the necessary context:

1. The full task package.
2. Required file paths.
3. Allowed write paths and forbidden paths.
4. Receipt path.
5. A stop condition: after completion, write the receipt and do not start the next stage.

The point is to provide narrow but complete context. Do not hand the entire main-thread context to the execution unit.

### Step 5: Require A Receipt

After completion, the execution unit copies `templates/回执.template.json` and writes it to the receipt path required by the task package.

The main thread accepts only machine-readable receipts, not natural-language completion claims. A receipt must answer:

- Which `任务包ID` was used.
- Whether the input version equals the task package’s `上游状态版本`.
- Which files were read.
- Which artifacts were written.
- Whether there are failures, blockers, or open questions.
- What the gate result says.

### Step 6: Read Monitor State

Monitor state may be written by automation, or by the main thread after checking the receipt file. See `templates/监控状态.template.json`.

The main thread continues to gate evaluation only when `监控状态` is `已收到回执`, and `任务包ID`, `回执路径`, and `状态路径` all match.

### Step 7: Run The Gate Script

From the repository root:

```bash
python3 long-task-orchestrator/scripts/validate_orchestrator.py \
  --project long-task-orchestrator/examples/最小闭环示例
```

Expected output includes:

```text
结果: 通过
```

Passing this script only means the evidence structure is valid. The main thread still makes the final business decision against the acceptance criteria.

## Complete Example

The minimal closed-loop example lives in `long-task-orchestrator/examples/最小闭环示例/`.

It shows a documentation task moving through the loop:

1. The main thread writes `当前状态.json` and `调度记录.json`.
2. The main thread creates `任务包/文档整理任务.json`.
3. The isolated execution unit writes `回执/文档整理任务回执.json`.
4. Monitor state is written to `监控/文档整理任务监控.json`.
5. The main thread runs the validation script and decides whether to release the stage.

Run it directly:

```bash
cd long-task-orchestrator/examples/最小闭环示例
python3 ../../scripts/validate_orchestrator.py --project .
```

## Redaction Check

Before publishing, use a local private keyword list. Create `.redaction-keywords` in the repository root, one sensitive literal per line. Prefix a line with `re:` when you need a regular expression. Then run:

```bash
python3 long-task-orchestrator/scripts/check_redaction.py --keywords .redaction-keywords .
```

`.redaction-keywords` is ignored by Git. Do not commit private keywords or private regular expressions to a public repository.

## Boundaries

- Projects like `long-task-harness` focus on session continuity and progress logs.
- Projects like `context-packet` focus on context packets and dependency graph parsing.
- `superpowers` focuses on software development discipline and subagent execution patterns.
- `agent-teams` focuses on multi-agent task decomposition and team coordination.
- This skill focuses only on the long-task delivery protocol: task packages, isolated execution, machine receipts, monitor state, and main-thread gate release.

## Questions

### Does passing validation mean the task is done?

No. The validator only checks whether task package, receipt, monitor state, and authorization paths are structurally consistent. Business quality is still judged by the main thread.

### Must I always create a new thread?

No. Read-only review, evidence gathering, and non-high-risk analysis can use `subagent`. Formal artifacts, high-risk artifacts, pre-release review, and major rework should default to an isolated thread.

### Is this a task platform?

No. This skill does not provide queues, remote execution, account permissions, dashboards, or background services. It provides a file-based, agent-readable, script-checkable delivery protocol.

### Why not use natural-language receipts?

Natural-language completion claims are hard to verify consistently and often omit input versions, authorized paths, or failures. Machine-readable receipts let the main thread run structural checks before making a business decision.
