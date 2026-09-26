#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description Optimizer（自动描述改进脚本）

分析SKILL.md的description字段，给出改进建议：
- 检查三要素（What/When/Differentiator）
- 检查触发词是否明确
- 检查长度是否合适（100-200词最佳）
- 给出改进后的description建议

用法：
  python3 description_optimizer.py <skill_dir>
  python3 description_optimizer.py <skill_dir> --auto  # 自动改进
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path


def extract_description(skill_md_path):
    """从SKILL.md提取description"""
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取frontmatter
        if not content.startswith("---"):
            return None, "没有frontmatter"

        end = content.find("---", 3)
        if end == -1:
            return None, "frontmatter未闭合"

        fm_text = content[3:end]

        # 提取description
        desc_match = re.search(r"^description:\s*(.+?)(?=\n[a-z_]+:|\Z)", fm_text, re.DOTALL | re.MULTILINE)
        if not desc_match:
            return None, "缺少description字段"

        desc = desc_match.group(1).strip().strip('"').strip("'")
        # 去除折叠符号 >
        desc = desc.lstrip(">").strip()

        return desc, None
    except Exception as e:
        return None, f"读取失败: {e}"


def analyze_description(desc):
    """分析description质量"""
    issues = []
    suggestions = []
    score = 100

    # 1. 长度检查
    word_count = len(desc.split())
    char_count = len(desc)

    if char_count > 1024:
        issues.append(f"过长: {char_count}字符（max 1024）")
        score -= 20
    elif char_count < 50:
        issues.append(f"过短: {char_count}字符（建议100-200词）")
        score -= 15
    elif 100 <= word_count <= 200:
        suggestions.append(f"✅ 长度合适: {word_count}词")
    else:
        suggestions.append(f"⚠️ 长度: {word_count}词（建议100-200词）")

    # 2. 三要素检查
    has_what = len(desc) > 30
    has_when = any(w in desc for w in ["when", "use", "触发", "适用于", "场景", "当"])
    has_trigger = any(w in desc for w in ["触发", "trigger", '"', "“"])

    if not has_what:
        issues.append("缺少What（做什么）")
        score -= 15
    else:
        suggestions.append("✅ 有What")

    if not has_when:
        issues.append("缺少When（什么时候用）")
        score -= 15
    else:
        suggestions.append("✅ 有When")

    if not has_trigger:
        issues.append("缺少触发词（建议用引号标注）")
        score -= 10
    else:
        suggestions.append("✅ 有触发词")

    # 3. 检查是否有"不适用于"
    has_not_for = "不适用于" in desc or "not for" in desc.lower()
    if has_not_for:
        suggestions.append("✅ 有不适用于（避免误触发）")
    else:
        suggestions.append("⚠️ 建议加'不适用于'（避免误触发）")

    # 4. 检查是否有具体场景
    has_specific = any(w in desc for w in ["具体", "例如", "比如", "场景"])
    if has_specific:
        suggestions.append("✅ 有具体场景")
    else:
        suggestions.append("⚠️ 建议加具体场景示例")

    return {
        "score": score,
        "char_count": char_count,
        "word_count": word_count,
        "issues": issues,
        "suggestions": suggestions,
    }


def generate_improved_description(skill_name, desc, analysis):
    """生成改进后的description建议"""
    # 简单模板
    improved = f"""{skill_name}。{desc}
触发词："{skill_name}"。
不适用于：其他不相关的任务。"""

    return improved


def main():
    parser = argparse.ArgumentParser(description="Description Optimizer：自动描述改进")
    parser.add_argument("skill_dir", help="技能目录")
    parser.add_argument("--auto", action="store_true", help="自动改进模式")
    args = parser.parse_args()

    skill_md = Path(args.skill_dir) / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ SKILL.md不存在: {skill_md}", file=sys.stderr)
        sys.exit(1)

    desc, error = extract_description(skill_md)
    if error:
        print(f"❌ {error}", file=sys.stderr)
        sys.exit(1)

    analysis = analyze_description(desc)

    print("=" * 60)
    print("📝 Description分析报告")
    print("=" * 60)
    print(f"当前描述: {desc[:100]}...")
    print(f"长度: {analysis['char_count']}字符, {analysis['word_count']}词")
    print(f"评分: {analysis['score']}/100")
    print()

    if analysis["issues"]:
        print("❌ 问题:")
        for issue in analysis["issues"]:
            print(f"  - {issue}")
        print()

    print("💡 建议:")
    for s in analysis["suggestions"]:
        print(f"  - {s}")

    if args.auto:
        skill_name = Path(args.skill_dir).name
        improved = generate_improved_description(skill_name, desc, analysis)
        print()
        print("✨ 改进后的描述建议:")
        print(f"  {improved}")


if __name__ == "__main__":
    main()
