#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
code-reviewer 示例技能：代码静态检查脚本

这是一个示例脚本，展示 Process 型技能如何用脚本做确定性检查。
实际使用时可替换为更专业的工具（pylint/flake8/sonar-scanner等）。

用法：
  python3 scripts/static_check.py <file-or-dir>
  python3 scripts/static_check.py my_project/ --json
"""
import argparse
import ast
import json
import os
import sys


def check_file(filepath):
    """检查单个Python文件的常见问题"""
    issues = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
    except Exception as e:
        return [{"file": filepath, "line": 0, "severity": "error", "message": f"无法读取文件: {e}"}]

    # 检查1：文件过长（>500行建议拆分）
    if len(lines) > 500:
        issues.append({
            "file": filepath, "line": 0, "severity": "warning",
            "message": f"文件过长（{len(lines)}行），建议拆分为多个模块"
        })

    # 检查2：函数过长（>50行建议拆分）
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = node.end_lineno - node.lineno + 1
                if func_lines > 50:
                    issues.append({
                        "file": filepath, "line": node.lineno, "severity": "warning",
                        "message": f"函数 '{node.name}' 过长（{func_lines}行），建议拆分"
                    })
                # 检查3：函数参数过多（>5个）
                args_count = len(node.args.args) + len(node.args.kwonlyargs)
                if args_count > 5:
                    issues.append({
                        "file": filepath, "line": node.lineno, "severity": "info",
                        "message": f"函数 '{node.name}' 参数过多（{args_count}个），考虑用配置对象"
                    })
    except SyntaxError as e:
        issues.append({
            "file": filepath, "line": e.lineno or 0, "severity": "error",
            "message": f"语法错误: {e.msg}"
        })

    # 检查4：硬编码凭据（简单模式匹配）
    for i, line in enumerate(lines, 1):
        if any(pattern in line.lower() for pattern in ["api_key =", "password =", "secret =", "token ="]):
            if "os.environ" not in line and "getenv" not in line:
                issues.append({
                    "file": filepath, "line": i, "severity": "high",
                    "message": "可能存在硬编码凭据，建议使用环境变量"
                })

    # 检查5：TODO/FIXME标记
    for i, line in enumerate(lines, 1):
        if "TODO" in line or "FIXME" in line:
            issues.append({
                "file": filepath, "line": i, "severity": "info",
                "message": f"待办标记: {line.strip()[:60]}"
            })

    return issues


def main():
    parser = argparse.ArgumentParser(description="代码静态检查（示例脚本）")
    parser.add_argument("path", help="文件或目录路径")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    all_issues = []

    if os.path.isfile(args.path):
        all_issues = check_file(args.path)
    elif os.path.isdir(args.path):
        for root, dirs, files in os.walk(args.path):
            # 跳过常见无关目录
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "venv", ".venv", "node_modules")]
            for f in files:
                if f.endswith(".py"):
                    filepath = os.path.join(root, f)
                    all_issues.extend(check_file(filepath))
    else:
        print(f"❌ 路径不存在: {args.path}", file=sys.stderr)
        sys.exit(1)

    # 统计
    high = sum(1 for i in all_issues if i["severity"] == "high")
    error = sum(1 for i in all_issues if i["severity"] == "error")
    warning = sum(1 for i in all_issues if i["severity"] == "warning")
    info = sum(1 for i in all_issues if i["severity"] == "info")

    if args.json:
        print(json.dumps({
            "total": len(all_issues),
            "high": high, "error": error, "warning": warning, "info": info,
            "issues": all_issues
        }, ensure_ascii=False, indent=2))
    else:
        print(f"📊 静态检查结果: {len(all_issues)} 个问题")
        print(f"  🔴 高危: {high}  ❌ 错误: {error}  🟡 警告: {warning}  ℹ️ 信息: {info}")
        print()
        for issue in all_issues:
            icon = {"high": "🔴", "error": "❌", "warning": "🟡", "info": "ℹ️"}.get(issue["severity"], "❓")
            line_info = f":{issue['line']}" if issue["line"] else ""
            print(f"  {icon} {issue['file']}{line_info}: {issue['message']}")

    # 有高危或错误时返回非0
    sys.exit(1 if high > 0 or error > 0 else 0)


if __name__ == "__main__":
    main()
