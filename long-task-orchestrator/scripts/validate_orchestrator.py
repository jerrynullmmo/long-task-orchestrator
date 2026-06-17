#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""长任务编排最小结构校验。"""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
from typing import Any


高风险后缀 = {".html", ".htm", ".css", ".js", ".mjs", ".jsx", ".ts", ".tsx", ".py", ".sh", ".mp4", ".mov", ".webm"}
允许执行单元 = {"subagent", "独立线程", "命令任务", "人工执行"}


def 读_json(路径: Path) -> dict[str, Any]:
    if not 路径.exists():
        raise ValueError(f"文件不存在：{路径}")
    try:
        数据 = json.loads(路径.read_text(encoding="utf-8"))
    except json.JSONDecodeError as 错误:
        raise ValueError(f"JSON 解析失败：{路径}：{错误}") from 错误
    if not isinstance(数据, dict):
        raise ValueError(f"根节点必须是对象：{路径}")
    return 数据


def 有值(值: Any) -> bool:
    if 值 is None:
        return False
    if isinstance(值, str):
        return bool(值.strip())
    if isinstance(值, list):
        return bool(值)
    return True


def 要求字段(数据: dict[str, Any], 字段: list[str], 名称: str) -> list[str]:
    问题: list[str] = []
    for 项 in 字段:
        if not 有值(数据.get(项)):
            问题.append(f"{名称} 缺少字段：{项}")
    return 问题


def 标准化路径(路径: str) -> str:
    return 路径.replace("\\", "/").lstrip("./")


def 模式匹配(路径: str, 模式: str) -> bool:
    路径 = 标准化路径(路径)
    模式 = 标准化路径(模式)
    if any(符号 in 模式 for 符号 in "*?[]"):
        return fnmatch.fnmatch(路径, 模式)
    if 模式.endswith("/"):
        return 路径.startswith(模式)
    return 路径 == 模式 or 路径.startswith(模式.rstrip("/") + "/")


def 匹配任一(路径: str, 模式列表: list[str]) -> bool:
    return any(模式匹配(路径, 模式) for 模式 in 模式列表)


def 是高风险产物(路径: str) -> bool:
    if 标准化路径(路径).startswith("状态包/"):
        return False
    return Path(路径).suffix.lower() in 高风险后缀


def 找任务包(项目: Path) -> tuple[Path, dict[str, Any]]:
    目录 = 项目 / "状态包" / "任务包"
    if not 目录.exists():
        raise ValueError(f"缺少任务包目录：{目录}")
    候选 = sorted(目录.glob("*.json"))
    if not 候选:
        raise ValueError(f"任务包目录为空：{目录}")
    if len(候选) > 1:
        raise ValueError("示例校验一次只接受一个任务包：" + "、".join(路径.name for 路径 in 候选))
    return 候选[0], 读_json(候选[0])


def 校验项目(项目: Path) -> list[str]:
    问题: list[str] = []
    状态 = 读_json(项目 / "状态包" / "当前状态.json")
    调度 = 读_json(项目 / "状态包" / "调度记录.json")
    任务包路径, 任务包 = 找任务包(项目)

    问题.extend(要求字段(状态, ["项目", "当前阶段", "状态版本", "阶段状态"], "当前状态"))
    问题.extend(要求字段(调度, ["项目", "当前阶段", "调度结论", "任务包路径", "执行单元类型"], "调度记录"))
    问题.extend(
        要求字段(
            任务包,
            [
                "任务包ID",
                "阶段",
                "任务名",
                "任务目标",
                "执行单元类型",
                "上游状态版本",
                "必读文件",
                "允许写入路径",
                "授权产物路径",
                "禁止触碰路径",
                "回执监控路径",
                "监控器状态路径",
                "验收标准",
                "回传格式",
            ],
            "任务包",
        )
    )

    执行单元类型 = str(任务包.get("执行单元类型", ""))
    if 执行单元类型 not in 允许执行单元:
        问题.append(f"任务包 执行单元类型非法：{执行单元类型}")

    授权路径 = [str(项) for 项 in 任务包.get("授权产物路径", [])]
    允许路径 = [str(项) for 项 in 任务包.get("允许写入路径", [])]
    禁止路径 = [str(项) for 项 in 任务包.get("禁止触碰路径", [])]

    for 路径 in 授权路径:
        if not 匹配任一(路径, 允许路径):
            问题.append(f"授权产物未包含在允许写入路径内：{路径}")
        if 匹配任一(路径, 禁止路径):
            问题.append(f"授权产物命中禁止触碰路径：{路径}")

    if any(是高风险产物(路径) for 路径 in 授权路径) and 执行单元类型 != "独立线程":
        问题.append("高风险产物必须由 独立线程 执行")

    回执相对路径 = 标准化路径(str(任务包.get("回执监控路径", "")))
    监控相对路径 = 标准化路径(str(任务包.get("监控器状态路径", "")))
    回执 = 读_json(项目 / 回执相对路径)
    监控 = 读_json(项目 / 监控相对路径)

    问题.extend(要求字段(回执, ["任务包ID", "执行单元类型", "输入版本", "结果", "读取文件清单", "产物路径", "闸门结果"], "回执"))
    问题.extend(要求字段(监控, ["监控状态", "任务包ID", "回执路径", "状态路径"], "监控状态"))

    if 回执.get("任务包ID") != 任务包.get("任务包ID"):
        问题.append("回执 任务包ID 与任务包不匹配")
    if 回执.get("输入版本") != 任务包.get("上游状态版本"):
        问题.append("回执 输入版本 与任务包上游状态版本不匹配")
    if 回执.get("执行单元类型") != 任务包.get("执行单元类型"):
        问题.append("回执 执行单元类型 与任务包不匹配")
    if 回执.get("结果") != "通过":
        问题.append("回执结果不是通过")

    for 字段 in ["失败项", "阻塞问题"]:
        值 = 回执.get(字段, [])
        if 值:
            问题.append(f"回执存在{字段}：{值}")

    for 路径 in [str(项) for 项 in 回执.get("产物路径", [])]:
        if not 匹配任一(路径, 授权路径):
            问题.append(f"回执产物不在授权产物路径内：{路径}")
        if 匹配任一(路径, 禁止路径):
            问题.append(f"回执产物命中禁止触碰路径：{路径}")

    if 监控.get("监控状态") != "已收到回执":
        问题.append("监控状态不是 已收到回执")
    if 监控.get("任务包ID") != 任务包.get("任务包ID"):
        问题.append("监控状态 任务包ID 与任务包不匹配")
    if 标准化路径(str(监控.get("回执路径", ""))) != 回执相对路径:
        问题.append("监控状态 回执路径 与任务包不匹配")
    if 标准化路径(str(监控.get("状态路径", ""))) != 监控相对路径:
        问题.append("监控状态 状态路径 与任务包不匹配")

    if 标准化路径(str(调度.get("任务包路径", ""))) != 标准化路径(任务包路径.relative_to(项目).as_posix()):
        问题.append("调度记录 任务包路径 与实际任务包不匹配")
    if 调度.get("执行单元类型") != 任务包.get("执行单元类型"):
        问题.append("调度记录 执行单元类型 与任务包不匹配")

    return 问题


def main() -> int:
    解析器 = argparse.ArgumentParser(description="校验长任务编排状态包最小闭环")
    解析器.add_argument("--project", required=True, help="包含 状态包/ 的项目目录")
    参数 = 解析器.parse_args()

    项目 = Path(参数.project).resolve()
    try:
        问题 = 校验项目(项目)
    except ValueError as 错误:
        print("结果: 阻断")
        print(f"- {错误}")
        return 2

    if 问题:
        print("结果: 阻断")
        for 项 in 问题:
            print(f"- {项}")
        return 2

    print("结果: 通过")
    print(f"项目: {项目}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
