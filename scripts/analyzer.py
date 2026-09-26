#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyzer Agent（基准分析脚本）

分析基准测试结果，发现模式和异常：
- 总是通过或失败的断言（无区分力）
- 高方差评估（测试不稳定）
- 时间和token的权衡
- 生成观察笔记，为人工审核提供参考

用法：
  python3 analyzer.py <benchmark_dir>
  python3 analyzer.py <benchmark_dir> --mode baseline  # 基准分析模式
  python3 analyzer.py <comparison_dir> --mode posthoc  # 事后分析模式
"""
import argparse
import json
import os
import sys
from pathlib import Path


def load_grading_files(benchmark_dir):
    """加载目录下所有grading.json"""
    gradings = []
    bench_path = Path(benchmark_dir)
    for g in bench_path.glob("**/grading.json"):
        with open(g, "r", encoding="utf-8") as f:
            grading = json.load(f)
            grading["file"] = str(g)
            gradings.append(grading)
    return gradings


def analyze_baseline(benchmark_dir):
    """基准分析模式：发现模式和异常"""
    gradings = load_grading_files(benchmark_dir)

    if not gradings:
        return {"error": "未找到grading.json文件"}

    # 收集所有断言
    all_expectations = {}
    for g in gradings:
        for r in g.get("results", []):
            text = r["text"]
            if text not in all_expectations:
                all_expectations[text] = {"total": 0, "passed": 0}
            all_expectations[text]["total"] += 1
            if r["passed"]:
                all_expectations[text]["passed"] += 1

    # 分析模式
    always_pass = []
    always_fail = []
    high_variance = []

    for text, stats in all_expectations.items():
        rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
        if rate == 1.0:
            always_pass.append({"expectation": text, "total": stats["total"]})
        elif rate == 0.0:
            always_fail.append({"expectation": text, "total": stats["total"]})
        elif 0.3 < rate < 0.7:
            high_variance.append({"expectation": text, "rate": round(rate, 2), "total": stats["total"]})

    # 计算总体统计
    total_passed = sum(g.get("passed", 0) for g in gradings)
    total_expectations = sum(g.get("total_expectations", 0) for g in gradings)
    overall_rate = total_passed / total_expectations if total_expectations > 0 else 0

    notes = []
    if always_pass:
        notes.append(f"⚠️ {len(always_pass)}个断言总是通过（无区分力），建议移除或改进")
    if always_fail:
        notes.append(f"🔴 {len(always_fail)}个断言总是失败，说明技能有根本性问题")
    if high_variance:
        notes.append(f"⚠️ {len(high_variance)}个断言高方差（30-70%通过率），测试不稳定")

    analysis = {
        "mode": "baseline",
        "total_runs": len(gradings),
        "overall_pass_rate": round(overall_rate, 2),
        "total_passed": total_passed,
        "total_expectations": total_expectations,
        "always_pass": always_pass,
        "always_fail": always_fail,
        "high_variance": high_variance,
        "notes": notes,
    }

    return analysis


def analyze_posthoc(comparison_dir):
    """事后分析模式：解盲分析，生成改进建议"""
    comparison_file = Path(comparison_dir) / "comparison.json"
    if not comparison_file.exists():
        return {"error": "未找到comparison.json"}

    with open(comparison_file, "r", encoding="utf-8") as f:
        comparison = json.load(f)

    winner = comparison.get("overall_winner", "tie")
    dimensions = comparison.get("dimensions", [])

    suggestions = []
    for dim in dimensions:
        if dim["winner"] == winner and winner != "tie":
            suggestions.append({
                "category": "strength",
                "dimension": dim["dimension"],
                "priority": "high",
                "message": f"{dim['dimension']}是优势，继续保持"
            })
        elif dim["winner"] != winner and winner != "tie":
            suggestions.append({
                "category": "improvement",
                "dimension": dim["dimension"],
                "priority": "medium",
                "message": f"{dim['dimension']}是劣势，需要改进"
            })

    analysis = {
        "mode": "posthoc",
        "winner": winner,
        "suggestions": suggestions,
        "summary": f"胜者是{winner}，建议{len(suggestions)}条"
    }

    return analysis


def main():
    parser = argparse.ArgumentParser(description="Analyzer Agent：基准分析")
    parser.add_argument("input_dir", help="输入目录（benchmark或comparison）")
    parser.add_argument("--mode", choices=["baseline", "posthoc"], default="baseline",
                        help="分析模式（默认baseline）")
    parser.add_argument("--output", help="输出analysis.json路径")
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"❌ 目录不存在: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    if args.mode == "baseline":
        analysis = analyze_baseline(args.input_dir)
    else:
        analysis = analyze_posthoc(args.input_dir)

    output_path = args.output or os.path.join(args.input_dir, "analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    print(f"✅ 分析完成（{args.mode}模式）")
    if "overall_pass_rate" in analysis:
        print(f"   总体通过率: {analysis['overall_pass_rate']*100:.0f}%")
    if "notes" in analysis:
        for note in analysis["notes"]:
            print(f"   {note}")
    print(f"   📄 结果已保存: {output_path}")


if __name__ == "__main__":
    main()
