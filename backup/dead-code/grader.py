#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grader Agent（评分脚本）

读取执行记录和输出文件，对每个断言进行PASS/FAIL评分，生成grading.json。

用法：
  python3 grader.py <run_dir> --expectations expectations.json
  python3 grader.py <run_dir> --auto  # 自动从输出文件提取断言
"""
import argparse
import json
import os
import sys
from pathlib import Path


def load_run_outputs(run_dir):
    """加载运行目录下的所有输出文件"""
    outputs = {}
    run_path = Path(run_dir)
    if not run_path.exists():
        return outputs

    # 读取对话记录
    conversation = run_path / "conversation.txt"
    if conversation.exists():
        outputs["conversation"] = conversation.read_text(encoding="utf-8", errors="replace")

    # 读取输出文件
    output_dir = run_path / "output"
    if output_dir.exists():
        for f in output_dir.glob("**/*"):
            if f.is_file():
                rel_path = str(f.relative_to(output_dir))
                try:
                    outputs[f"output:{rel_path}"] = f.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    outputs[f"output:{rel_path}"] = f"[binary file: {rel_path}]"

    return outputs


def evaluate_expectation(expectation, outputs):
    """评估单个断言"""
    text = expectation.get("text", "")
    check_type = expectation.get("type", "contains")

    # 合并所有输出用于搜索
    all_content = "\n".join(outputs.values())

    if check_type == "contains":
        # 检查是否包含关键词
        keywords = expectation.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [keywords]
        found = all(kw in all_content for kw in keywords)
        return {
            "text": text,
            "passed": found,
            "evidence": f"检查关键词: {keywords}",
            "type": "contains"
        }

    elif check_type == "file_exists":
        # 检查文件是否存在
        filename = expectation.get("filename", "")
        file_key = f"output:{filename}"
        exists = file_key in outputs
        return {
            "text": text,
            "passed": exists,
            "evidence": f"文件 {filename} {'存在' if exists else '不存在'}",
            "type": "file_exists"
        }

    elif check_type == "file_not_empty":
        # 检查文件是否非空
        filename = expectation.get("filename", "")
        file_key = f"output:{filename}"
        content = outputs.get(file_key, "")
        not_empty = len(content.strip()) > 0
        return {
            "text": text,
            "passed": not_empty,
            "evidence": f"文件 {filename} 长度: {len(content)} 字符",
            "type": "file_not_empty"
        }

    elif check_type == "not_contains":
        # 检查不包含敏感词
        forbidden = expectation.get("keywords", [])
        if isinstance(forbidden, str):
            forbidden = [forbidden]
        not_found = all(kw not in all_content for kw in forbidden)
        return {
            "text": text,
            "passed": not_found,
            "evidence": f"检查禁用词: {forbidden}",
            "type": "not_contains"
        }

    elif check_type == "execution":
        # 检查是否执行了正确的动作（官方4种断言之一）
        # 检查输出中是否包含特定的命令/脚本执行痕迹
        actions = expectation.get("actions", [])
        if isinstance(actions, str):
            actions = [actions]
        # 支持多种执行痕迹：命令行调用、脚本名、特定输出标记
        executed = all(
            any(action in content for content in outputs.values())
            for action in actions
        )
        return {
            "text": text,
            "passed": executed,
            "evidence": f"检查执行动作: {actions}",
            "type": "execution"
        }

    elif check_type == "output_quality":
        # 检查输出质量（官方4种断言之一，contains的别名）
        # 检查输出是否包含期望的数据/结构
        requirements = expectation.get("requirements", [])
        if isinstance(requirements, str):
            requirements = [requirements]
        quality_ok = all(req in all_content for req in requirements)
        return {
            "text": text,
            "passed": quality_ok,
            "evidence": f"检查输出质量要求: {requirements}",
            "type": "output_quality"
        }

    else:
        return {
            "text": text,
            "passed": False,
            "evidence": f"未知检查类型: {check_type}",
            "type": "unknown"
        }


def grade_run(run_dir, expectations=None):
    """对单次运行进行评分"""
    outputs = load_run_outputs(run_dir)

    if expectations is None:
        # 自动模式：基本检查
        expectations = [
            {"text": "对话记录存在", "type": "file_exists", "filename": "conversation.txt"},
            {"text": "有输出文件", "type": "contains", "keywords": ["output:"]},
        ]

    results = []
    passed_count = 0
    for exp in expectations:
        result = evaluate_expectation(exp, outputs)
        results.append(result)
        if result["passed"]:
            passed_count += 1

    total = len(results)
    pass_rate = passed_count / total if total > 0 else 0

    grading = {
        "run_dir": str(run_dir),
        "total_expectations": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "pass_rate": round(pass_rate, 2),
        "results": results,
    }

    return grading


def main():
    parser = argparse.ArgumentParser(description="Grader Agent：评分脚本")
    parser.add_argument("run_dir", help="运行目录路径")
    parser.add_argument("--expectations", help="期望断言JSON文件路径")
    parser.add_argument("--auto", action="store_true", help="自动模式（基本检查）")
    parser.add_argument("--output", help="输出grading.json的路径")
    args = parser.parse_args()

    if not os.path.isdir(args.run_dir):
        print(f"❌ 运行目录不存在: {args.run_dir}", file=sys.stderr)
        sys.exit(1)

    expectations = None
    if args.expectations:
        with open(args.expectations, "r", encoding="utf-8") as f:
            expectations = json.load(f)

    grading = grade_run(args.run_dir, expectations)

    output_path = args.output or os.path.join(args.run_dir, "grading.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(grading, f, ensure_ascii=False, indent=2)

    print(f"✅ 评分完成: {grading['passed']}/{grading['total_expectations']} 通过 ({grading['pass_rate']*100:.0f}%)")
    print(f"📄 结果已保存: {output_path}")

    # 输出失败项
    failed = [r for r in grading["results"] if not r["passed"]]
    if failed:
        print("\n❌ 未通过的断言:")
        for r in failed:
            print(f"  - {r['text']}: {r['evidence']}")


if __name__ == "__main__":
    main()
