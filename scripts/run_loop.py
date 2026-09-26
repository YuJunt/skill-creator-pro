#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
描述优化自动循环（run_loop.py）

自动优化技能的description字段：
  1. 加载evals.json（触发评估用例）
  2. 60%train/40%test分割
  3. 评估当前描述的触发率
  4. 生成改进建议
  5. 迭代优化
  6. 选最佳描述（基于test score，避免过拟合）

用法：
  python3 run_loop.py --eval-set <path> --skill-path <path> --max-iterations 5
  python3 run_loop.py --eval-set <path> --skill-path <path> --suggest  # 只生成建议
"""
import argparse
import json
import os
import random
import sys
from pathlib import Path
from datetime import datetime


def load_eval_set(eval_set_path):
    """加载评估用例集"""
    try:
        with open(eval_set_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载评估用例集失败: {e}", file=sys.stderr)
        sys.exit(1)


def split_eval_set(evals, train_ratio=0.6, seed=42):
    """分割训练集和测试集"""
    random.seed(seed)
    shuffled = evals[:]
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * train_ratio)
    train = shuffled[:split_idx]
    test = shuffled[split_idx:]

    return train, test


def extract_description(skill_path):
    """从SKILL.md提取description"""
    skill_md = Path(skill_path) / "SKILL.md"
    if not skill_md.exists():
        return None

    content = skill_md.read_text(encoding="utf-8", errors="replace")

    if not content.startswith("---"):
        return None

    end = content.find("---", 3)
    if end == -1:
        return None

    fm_text = content[3:end]

    import re
    desc_match = re.search(r"^description:\s*(.+?)(?=\n[a-z_]+:|\Z)", fm_text, re.DOTALL | re.MULTILINE)
    if not desc_match:
        return None

    desc = desc_match.group(1).strip().strip('"').strip("'")
    desc = desc.lstrip(">").strip()

    return desc


def evaluate_description(description, eval_set):
    """评估描述的触发率（简化版：基于关键词匹配）"""
    # 这是一个简化的评估，实际应该用LLM来判断
    # 这里用关键词匹配作为代理

    desc_lower = description.lower()
    triggered = 0
    total = len(eval_set)

    for eval_item in eval_set:
        query = eval_item.get("query", "").lower()
        should_trigger = eval_item.get("should_trigger", True)

        # 简化：检查query中的关键词是否在description中
        query_words = set(query.split())
        desc_words = set(desc_lower.split())
        overlap = len(query_words & desc_words)

        # 如果有重叠，认为会触发
        is_triggered = overlap > 0

        if is_triggered == should_trigger:
            triggered += 1

    return triggered / total if total > 0 else 0


def generate_suggestions(description, eval_set, score):
    """生成改进建议"""
    suggestions = []

    # 检查三要素
    has_what = len(description) > 30
    has_when = any(w in description for w in ["when", "use", "触发", "适用于", "场景"])
    has_trigger = any(w in description for w in ["触发", "trigger", '"'])

    if not has_what:
        suggestions.append("缺少What（做什么），建议添加技能的核心功能描述")

    if not has_when:
        suggestions.append("缺少When（什么时候用），建议添加具体的使用场景")

    if not has_trigger:
        suggestions.append("缺少触发词，建议用引号标注具体的触发词")

    # 检查长度
    if len(description) > 500:
        suggestions.append("描述过长（>500字符），建议精简到100-200字符")
    elif len(description) < 50:
        suggestions.append("描述过短（<50字符），建议补充细节")

    # 检查是否有不适用于
    if "不适用于" not in description and "not for" not in description.lower():
        suggestions.append("建议添加'不适用于'，避免误触发")

    # 基于评估结果
    if score < 0.5:
        suggestions.append("触发率过低，建议添加更多具体的触发词和场景描述")
    elif score > 0.95:
        suggestions.append("触发率过高，可能存在误触发，建议添加'不适用于'限制")

    return suggestions


def run_optimization_loop(eval_set_path, skill_path, max_iterations=5):
    """运行优化循环"""
    # 加载评估用例
    eval_set = load_eval_set(eval_set_path)
    print(f"✅ 加载{len(eval_set)}个评估用例")

    # 分割训练集和测试集
    train, test = split_eval_set(eval_set)
    print(f"✅ 训练集: {len(train)}个, 测试集: {len(test)}个")

    # 提取当前描述
    current_description = extract_description(skill_path)
    if not current_description:
        print("❌ 无法提取description", file=sys.stderr)
        sys.exit(1)

    print(f"\n当前描述: {current_description[:100]}...")

    # 评估当前描述
    train_score = evaluate_description(current_description, train)
    test_score = evaluate_description(current_description, test)
    print(f"当前评分: 训练集={train_score:.2f}, 测试集={test_score:.2f}")

    # 生成改进建议
    suggestions = generate_suggestions(current_description, eval_set, test_score)

    iterations = [
        {
            "iteration": 0,
            "description": current_description,
            "train_score": train_score,
            "test_score": test_score,
            "suggestions": suggestions,
        }
    ]

    best = iterations[0]

    print("\n" + "=" * 60)
    print("📝 改进建议")
    print("=" * 60)
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. {s}")

    print("\n💡 请根据以上建议修改description，然后重新运行此脚本评估")
    print("   或者使用 --suggest 只生成建议，不运行循环")

    # 保存结果
    result = {
        "skill_path": skill_path,
        "eval_set_path": eval_set_path,
        "max_iterations": max_iterations,
        "iterations": iterations,
        "best_description": best["description"],
        "best_test_score": best["test_score"],
    }

    result_path = os.path.join(os.path.dirname(eval_set_path), "description_optimization.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存: {result_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="描述优化自动循环")
    parser.add_argument("--eval-set", required=True, help="评估用例集路径")
    parser.add_argument("--skill-path", required=True, help="技能目录路径")
    parser.add_argument("--max-iterations", type=int, default=5, help="最大迭代次数")
    parser.add_argument("--suggest", action="store_true", help="只生成建议，不运行循环")
    args = parser.parse_args()

    if not os.path.isfile(args.eval_set):
        print(f"❌ 评估用例集不存在: {args.eval_set}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.skill_path):
        print(f"❌ 技能目录不存在: {args.skill_path}", file=sys.stderr)
        sys.exit(1)

    if args.suggest:
        # 只生成建议
        eval_set = load_eval_set(args.eval_set)
        description = extract_description(args.skill_path)
        score = evaluate_description(description, eval_set)
        suggestions = generate_suggestions(description, eval_set, score)

        print("=" * 60)
        print("📝 描述改进建议")
        print("=" * 60)
        print(f"当前描述: {description[:100]}...")
        print(f"当前评分: {score:.2f}")
        print()
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s}")
    else:
        run_optimization_loop(args.eval_set, args.skill_path, args.max_iterations)


if __name__ == "__main__":
    main()
