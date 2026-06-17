#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用本地私有清单检查仓库脱敏情况。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Pattern


跳过目录 = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
文本后缀 = {
    ".md",
    ".json",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".sh",
}


def 读取规则(路径: Path) -> tuple[list[str], list[Pattern[str]]]:
    if not 路径.exists():
        raise ValueError(f"关键词清单不存在：{路径}")
    关键词: list[str] = []
    正则: list[Pattern[str]] = []
    for 行 in 路径.read_text(encoding="utf-8").splitlines():
        值 = 行.strip()
        if not 值 or 值.startswith("#"):
            continue
        if 值.startswith("re:"):
            表达式 = 值.removeprefix("re:").strip()
            if not 表达式:
                raise ValueError(f"正则规则为空：{路径}")
            try:
                正则.append(re.compile(表达式))
            except re.error as 错误:
                raise ValueError(f"正则规则无效：{表达式}：{错误}") from 错误
        else:
            关键词.append(值)
    if not 关键词 and not 正则:
        raise ValueError(f"关键词清单为空：{路径}")
    return 关键词, 正则


def 可检查文件(路径: Path) -> bool:
    if any(部分 in 跳过目录 for 部分 in 路径.parts):
        return False
    if 路径.name == ".redaction-keywords":
        return False
    return 路径.is_file() and 路径.suffix.lower() in 文本后缀


def 扫描(根目录: Path, 关键词: list[str], 正则: list[Pattern[str]]) -> list[str]:
    问题: list[str] = []
    for 路径 in sorted(根目录.rglob("*")):
        if not 可检查文件(路径):
            continue
        try:
            内容 = 路径.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for 行号, 行 in enumerate(内容.splitlines(), start=1):
            for 词 in 关键词:
                if 词 in 行:
                    相对路径 = 路径.relative_to(根目录)
                    问题.append(f"{相对路径}:{行号}: 命中本地敏感片段")
                    break
            else:
                for 表达式 in 正则:
                    if 表达式.search(行):
                        相对路径 = 路径.relative_to(根目录)
                        问题.append(f"{相对路径}:{行号}: 命中本地敏感规则")
                        break
    return 问题


def main() -> int:
    解析器 = argparse.ArgumentParser(description="用本地私有清单检查仓库脱敏情况")
    解析器.add_argument("path", nargs="?", default=".", help="要检查的目录")
    解析器.add_argument("--keywords", required=True, help="本地关键词清单路径，不要提交")
    参数 = 解析器.parse_args()

    根目录 = Path(参数.path).resolve()
    try:
        关键词, 正则 = 读取规则(Path(参数.keywords).resolve())
    except ValueError as 错误:
        print("结果: 阻断")
        print(f"- {错误}")
        return 2

    问题 = 扫描(根目录, 关键词, 正则)
    if 问题:
        print("结果: 阻断")
        for 项 in 问题:
            print(f"- {项}")
        return 2

    print("结果: 通过")
    print(f"项目: {根目录}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
