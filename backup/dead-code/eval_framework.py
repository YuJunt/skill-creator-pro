#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
8层评估框架（Eight-Layer Evaluation Framework）

对每个测试用例，按8层进行评估：
  1. routing（路由准确性）
  2. deterministic contract（确定性契约）
  3. trajectory（执行轨迹）
  4. final state（最终状态）
  5. semantic quality（语义质量）
  6. repeated-run reliability（重复运行可靠性）
  7. cost（成本）
  8. security（安全）

用法：
  python3 eval_framework.py <run_dir>
  python3 eval_framework.py <run_dir> --detailed  # 详细输出
"""
import argparse
import json
import os
import sys
from pathlib import Path


def evaluate_running(run_dir):
    """第1层：路由准确性"""
    run_path = Path(run_dir)
    conversation_file = run_path / "conversation.txt"

    if not conversation_file.exists():
        return {"layer": "routing", "score": 0, "passed": False, "reason": "无对话记录"}

    content = conversation_file.read_text(encoding="utf-8", errors="replace")

    # 检查是否有路由行
    has_routing = "路由:" in content or "🔀" in content

    return {
        "layer": "routing",
        "score": 10 if has_routing else 0,
        "passed": has_routing,
        "reason": "有路由行" if has_routing else "无路由行"
    }


def evaluate_deterministic_contract(run_dir):
    """第2层：确定性契约"""
    run_path = Path(run_dir)
    output_dir = run_path / "output"

    if not output_dir.exists():
        return {"layer": "deterministic_contract", "score": 0, "passed": False, "reason": "无输出目录"}

    # 检查输出文件是否存在且非空
    files = list(output_dir.glob("**/*"))
    files = [f for f in files if f.is_file()]

    if not files:
        return {"layer": "deterministic_contract", "score": 0, "passed": False, "reason": "无输出文件"}

    # 检查文件是否非空
    non_empty = sum(1 for f in files if f.stat().st_size > 0)
    score = (non_empty / len(files)) * 10

    return {
        "layer": "deterministic_contract",
        "score": round(score, 1),
        "passed": non_empty == len(files),
        "reason": f"{non_empty}/{len(files)}个文件非空"
    }


def evaluate_trajectory(run_dir):
    """第3层：执行轨迹"""
    run_path = Path(run_dir)
    conversation_file = run_path / "conversation.txt"

    if not conversation_file.exists():
        return {"layer": "trajectory", "score": 0, "passed": False, "reason": "无对话记录"}

    content = conversation_file.read_text(encoding="utf-8", errors="replace")

    # 检查是否有完整流程（开始→中间→结束）
    has_start = "开始" in content or "Step 1" in content or "第1步" in content
    has_end = "完成" in content or "Done" in content or "✅" in content

    score = 0
    if has_start:
        score += 5
    if has_end:
        score += 5

    return {
        "layer": "trajectory",
        "score": score,
        "passed": has_start and has_end,
        "reason": f"开始: {has_start}, 结束: {has_end}"
    }


def evaluate_final_state(run_dir):
    """第4层：最终状态"""
    run_path = Path(run_dir)

    # 读取grading.json
    grading_file = run_path / "grading.json"
    if grading_file.exists():
        with open(grading_file, "r", encoding="utf-8") as f:
            grading = json.load(f)
        pass_rate = grading.get("pass_rate", 0)
        score = pass_rate * 10
        return {
            "layer": "final_state",
            "score": round(score, 1),
            "passed": pass_rate >= 0.8,
            "reason": f"通过率: {pass_rate*100:.0f}%"
        }

    return {"layer": "final_state", "score": 0, "passed": False, "reason": "无grading.json"}


def evaluate_semantic_quality(run_dir):
    """第5层：语义质量（简化版：检查输出是否有意义）"""
    run_path = Path(run_dir)
    output_dir = run_path / "output"

    if not output_dir.exists():
        return {"layer": "semantic_quality", "score": 0, "passed": False, "reason": "无输出目录"}

    # 简单检查：输出是否有实质性内容（不是空文件）
    total_chars = 0
    files = list(output_dir.glob("**/*"))
    files = [f for f in files if f.is_file()]

    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            total_chars += len(content)
        except Exception:
            pass

    # 简单评分：100字符=1分，最多10分
    score = min(10, total_chars / 100)

    return {
        "layer": "semantic_quality",
        "score": round(score, 1),
        "passed": total_chars >= 500,
        "reason": f"总字符数: {total_chars}"
    }


def evaluate_reliability(run_dir):
    """第6层：重复运行可靠性（简化版：检查是否有多个run目录）"""
    # 这个需要多次运行才能评估，这里只检查是否有多次运行的目录
    run_path = Path(run_dir)
    parent = run_path.parent

    run_dirs = [d for d in parent.iterdir() if d.is_dir() and d.name.startswith("run-")]

    if len(run_dirs) < 2:
        return {"layer": "reliability", "score": 5, "passed": True, "reason": "单次运行，无法评估方差"}

    # 如果有多次运行，计算方差
    pass_rates = []
    for rd in run_dirs:
        grading_file = rd / "grading.json"
        if grading_file.exists():
            with open(grading_file, "r", encoding="utf-8") as f:
                grading = json.load(f)
                pass_rates.append(grading.get("pass_rate", 0))

    if not pass_rates:
        return {"layer": "reliability", "score": 5, "passed": True, "reason": "无评分数据"}

    # 计算方差
    avg = sum(pass_rates) / len(pass_rates)
    variance = sum((p - avg) ** 2 for p in pass_rates) / len(pass_rates)
    std_dev = variance ** 0.5

    # 标准差越小越可靠
    score = max(0, 10 - std_dev * 20)

    return {
        "layer": "reliability",
        "score": round(score, 1),
        "passed": std_dev < 0.2,
        "reason": f"{len(pass_rates)}次运行，标准差: {std_dev:.2f}"
    }


def evaluate_cost(run_dir):
    """第7层：成本（简化版：对话长度作为成本代理）"""
    run_path = Path(run_dir)
    conversation_file = run_path / "conversation.txt"

    if not conversation_file.exists():
        return {"layer": "cost", "score": 0, "passed": False, "reason": "无对话记录"}

    content = conversation_file.read_text(encoding="utf-8", errors="replace")
    char_count = len(content)

    # 简单评分：越短越好
    # 1000字符=10分，每增加1000字符减1分
    score = max(0, 10 - (char_count - 1000) / 1000)

    return {
        "layer": "cost",
        "score": round(score, 1),
        "passed": char_count < 5000,
        "reason": f"对话长度: {char_count}字符"
    }


def evaluate_security(run_dir):
    """第8层：安全（简化版：检查是否有敏感信息）"""
    run_path = Path(run_dir)
    conversation_file = run_path / "conversation.txt"

    if not conversation_file.exists():
        return {"layer": "security", "score": 0, "passed": False, "reason": "无对话记录"}

    content = conversation_file.read_text(encoding="utf-8", errors="replace")

    # 检查是否有敏感信息
    has_sensitive = any(w in content.lower() for w in ["password", "secret", "token", "api_key"])

    score = 0 if has_sensitive else 10

    return {
        "layer": "security",
        "score": score,
        "passed": not has_sensitive,
        "reason": "无敏感信息" if not has_sensitive else "发现敏感信息"
    }


def run_full_evaluation(run_dir):
    """运行8层评估"""
    layers = [
        evaluate_running(run_dir),
        evaluate_deterministic_contract(run_dir),
        evaluate_trajectory(run_dir),
        evaluate_final_state(run_dir),
        evaluate_semantic_quality(run_dir),
        evaluate_reliability(run_dir),
        evaluate_cost(run_dir),
        evaluate_security(run_dir),
    ]

    total_score = sum(l["score"] for l in layers)
    passed_count = sum(1 for l in layers if l["passed"])

    result = {
        "run_dir": run_dir,
        "total_score": round(total_score, 1),
        "max_score": 80,
        "pass_rate": round(total_score / 80, 2),
        "passed_layers": passed_count,
        "total_layers": 8,
        "layers": layers,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="8层评估框架")
    parser.add_argument("run_dir", help="运行目录")
    parser.add_argument("--detailed", action="store_true", help="详细输出")
    parser.add_argument("--output", help="输出JSON路径")
    args = parser.parse_args()

    if not os.path.isdir(args.run_dir):
        print(f"❌ 目录不存在: {args.run_dir}", file=sys.stderr)
        sys.exit(1)

    result = run_full_evaluation(args.run_dir)

    print("=" * 60)
    print("📊 8层评估报告")
    print("=" * 60)
    print(f"总分: {result['total_score']}/{result['max_score']} ({result['pass_rate']*100:.0f}%)")
    print(f"通过: {result['passed_layers']}/{result['total_layers']}层")
    print()

    for layer in result["layers"]:
        status = "✅" if layer["passed"] else "❌"
        print(f"{status} {layer['layer']}: {layer['score']}/10 - {layer['reason']}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n📄 结果已保存: {args.output}")


if __name__ == "__main__":
    main()
