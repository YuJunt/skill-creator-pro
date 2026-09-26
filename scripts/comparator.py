#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparator Agent（盲A/B比较脚本）

比较两个运行结果（A和B），不知道哪个用了技能，哪个是基线。
输出comparison.json，包含每个维度的评分和胜者。

用法：
  python3 comparator.py <run_a> <run_b>
  python3 comparator.py <run_a> <run_b> --criteria criteria.json
"""
import argparse
import json
import os
import sys
from pathlib import Path


def load_run_summary(run_dir):
    """加载运行摘要"""
    run_path = Path(run_dir)

    # 读取grading.json
    grading_file = run_path / "grading.json"
    if grading_file.exists():
        with open(grading_file, "r", encoding="utf-8") as f:
            grading = json.load(f)
    else:
        grading = {"pass_rate": 0, "passed": 0, "total_expectations": 0}

    # 读取对话记录长度（作为成本代理）
    conversation_file = run_path / "conversation.txt"
    conv_length = 0
    if conversation_file.exists():
        conv_length = len(conversation_file.read_text(encoding="utf-8", errors="replace"))

    return {
        "run_dir": str(run_dir),
        "pass_rate": grading.get("pass_rate", 0),
        "passed": grading.get("passed", 0),
        "total_expectations": grading.get("total_expectations", 0),
        "conversation_length": conv_length,
    }


def compare_runs(run_a_dir, run_b_dir, criteria=None):
    """比较两个运行"""
    a = load_run_summary(run_a_dir)
    b = load_run_summary(run_b_dir)

    # 默认评分维度
    if criteria is None:
        criteria = [
            {"name": "通过率", "weight": 0.6, "higher_better": True},
            {"name": "对话长度", "weight": 0.2, "higher_better": False},  # 越短越好
            {"name": "完成度", "weight": 0.2, "higher_better": True},
        ]

    scores = {"A": 0, "B": 0}
    dimensions = []

    for crit in criteria:
        name = crit["name"]
        weight = crit["weight"]
        higher_better = crit["higher_better"]

        if name == "通过率":
            a_val = a["pass_rate"]
            b_val = b["pass_rate"]
        elif name == "对话长度":
            a_val = a["conversation_length"]
            b_val = b["conversation_length"]
        elif name == "完成度":
            a_val = a["passed"] / a["total_expectations"] if a["total_expectations"] > 0 else 0
            b_val = b["passed"] / b["total_expectations"] if b["total_expectations"] > 0 else 0
        else:
            continue

        # 评分
        if higher_better:
            if a_val > b_val:
                winner = "A"
            elif b_val > a_val:
                winner = "B"
            else:
                winner = "tie"
        else:
            if a_val < b_val:
                winner = "A"
            elif b_val < a_val:
                winner = "B"
            else:
                winner = "tie"

        dimensions.append({
            "dimension": name,
            "weight": weight,
            "A": a_val,
            "B": b_val,
            "winner": winner,
        })

        if winner == "A":
            scores["A"] += weight
        elif winner == "B":
            scores["B"] += weight

    # 决定胜者
    if scores["A"] > scores["B"]:
        overall_winner = "A"
    elif scores["B"] > scores["A"]:
        overall_winner = "B"
    else:
        overall_winner = "tie"

    comparison = {
        "run_a": str(run_a_dir),
        "run_b": str(run_b_dir),
        "scores": scores,
        "dimensions": dimensions,
        "overall_winner": overall_winner,
        "note": "盲比较：比较器不知道哪个运行用了技能，只看输出质量"
    }

    return comparison


def main():
    parser = argparse.ArgumentParser(description="Comparator Agent：盲A/B比较")
    parser.add_argument("run_a", help="运行A目录")
    parser.add_argument("run_b", help="运行B目录")
    parser.add_argument("--criteria", help="比较标准JSON文件")
    parser.add_argument("--output", help="输出comparison.json路径")
    args = parser.parse_args()

    if not os.path.isdir(args.run_a) or not os.path.isdir(args.run_b):
        print("❌ 运行目录不存在", file=sys.stderr)
        sys.exit(1)

    criteria = None
    if args.criteria:
        with open(args.criteria, "r", encoding="utf-8") as f:
            criteria = json.load(f)

    comparison = compare_runs(args.run_a, args.run_b, criteria)

    output_path = args.output or os.path.join(args.run_a, "comparison.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    print(f"✅ 比较完成")
    print(f"   A得分: {comparison['scores']['A']:.2f}")
    print(f"   B得分: {comparison['scores']['B']:.2f}")
    print(f"   胜者: {comparison['overall_winner']}")
    print(f"   📄 结果已保存: {output_path}")


if __name__ == "__main__":
    main()
