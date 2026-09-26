#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能触发诊断工具（diagnose_trigger.py）

诊断技能description是否会导致：
  - 不触发（太窄/太模糊）
  - 误触发（太宽/不相关场景）
  - 竞争触发（与其他技能description重叠）

用法：
  python3 diagnose_trigger.py <skill-path>
  python3 diagnose_trigger.py <skill-path> --json
"""
import argparse
import json
import os
import re
import sys


def read_skill_md(skill_path):
    """读取SKILL.md并解析frontmatter"""
    md_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(md_path):
        return None, "SKILL.md不存在"

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析frontmatter
    if not content.startswith("---"):
        return None, "frontmatter未找到（必须以---开头）"

    end = content.find("---", 3)
    if end == -1:
        return None, "frontmatter未正确闭合"

    fm_text = content[3:end]
    fm = {}
    current_key = None
    for line in fm_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # 新key（非缩进行）
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val in (">", "|", ">-", "|-"):
                current_key = key
                fm[key] = ""
            else:
                fm[key] = val.strip('"').strip("'")
                current_key = None
        elif current_key and (line.startswith(" ") or line.startswith("\t")):
            fm[current_key] += " " + stripped

    body = content[end + 3:]
    return {"frontmatter": fm, "body": body, "raw": content}, None


def diagnose_description(fm):
    """诊断description质量"""
    desc = fm.get("description", "")
    name = fm.get("name", "")
    issues = []
    suggestions = []
    score = 100

    # 1. 长度检查
    desc_len = len(desc)
    if desc_len < 50:
        issues.append(f"description太短（{desc_len}字符），LLM无法判断何时使用")
        suggestions.append("增加具体场景和触发词，目标100-300字符")
        score -= 20
    elif desc_len > 500:
        issues.append(f"description太长（{desc_len}字符），可能被截断")
        suggestions.append("精简到200字符以内，详细信息放body")
        score -= 10

    # 2. 三要素检查
    has_what = len(desc) > 30
    has_when = any(w in desc for w in ["当", "使用", "用于", "场景", "when", "use", "trigger", "触发"])
    has_trigger = any(w in desc for w in ["\"", "触发词", "trigger", "关键词"])

    if not has_what:
        issues.append("缺少What（做什么）描述")
        suggestions.append("明确说明技能的核心功能")
        score -= 15

    if not has_when:
        issues.append("缺少When（什么时候用）描述")
        suggestions.append("说明具体使用场景，如'当用户说XX时使用'")
        score -= 15

    if not has_trigger:
        issues.append("缺少触发词列表")
        suggestions.append("在description中列出具体触发词，如触发词：\"XX\"\"YY\"")
        score -= 10

    # 3. 模糊词检查
    vague_words = ["帮助", "处理", "支持", "工具", "助手", "万能", "各种", "所有"]
    vague_found = [w for w in vague_words if w in desc and len(desc) < 200]
    if vague_found and len(desc) < 200:
        issues.append(f"description使用了模糊词：{vague_found}")
        suggestions.append("替换为具体描述，如'帮助处理文档'→'从PDF提取文本和表格'")
        score -= 10

    # 4. 第三人称检查
    first_person = any(p in desc for p in ["我可以", "我能", "你可以用我", "I can", "I help"])
    if first_person:
        issues.append("description使用第一人称，应改为第三人称")
        suggestions.append("改为'Processes X and generates Y'而非'I can help you'")
        score -= 10

    # 5. 否定检查（不适用于）
    has_not_for = "不适用于" in desc or "不用于" in desc or "not for" in desc.lower()
    if not has_not_for:
        suggestions.append("建议在description末尾加'不适用于：XXX'，避免误触发")
        score -= 5

    # 6. name检查
    if not name:
        issues.append("缺少name字段")
        score -= 20
    elif not re.match(r'^[a-z][a-z0-9-]*$', name):
        issues.append(f"name '{name}' 不符合规范（小写+连字符）")
        suggestions.append("改为kebab-case，如'pdf-processing'")
        score -= 10

    return {
        "score": max(0, score),
        "length": desc_len,
        "has_what": has_what,
        "has_when": has_when,
        "has_trigger": has_trigger,
        "has_not_for": has_not_for,
        "issues": issues,
        "suggestions": suggestions,
        "description": desc,
    }


def diagnose_body(body):
    """诊断body内容"""
    issues = []
    suggestions = []

    lines = body.count("\n") + 1

    if lines > 500:
        issues.append(f"SKILL.md body {lines}行，超过500行限制")
        suggestions.append("拆分到references/")
    elif lines > 300:
        suggestions.append(f"SKILL.md {lines}行，建议考虑拆分到references/")

    # 检查是否有路由
    has_router = "路由" in body or "router" in body.lower() or "route" in body.lower()
    if not has_router:
        suggestions.append("建议在SKILL.md开头加触发路由（多模式技能）")

    # 检查是否有Gotchas
    has_gotchas = "Gotchas" in body or "常见坑" in body or "坑" in body
    if not has_gotchas:
        suggestions.append("建议加Gotchas章节（真实失败模式+修正）")

    # 检查是否有输出格式
    has_output = "输出" in body and ("格式" in body or "格式" in body)
    if not has_output:
        suggestions.append("建议明确输出格式")

    return {
        "body_lines": lines,
        "has_router": has_router,
        "has_gotchas": has_gotchas,
        "has_output_format": has_output,
        "issues": issues,
        "suggestions": suggestions,
    }


def diagnose_directory(skill_path):
    """诊断目录结构"""
    issues = []
    suggestions = []

    expected_dirs = ["scripts", "references", "examples"]
    existing = [d for d in expected_dirs if os.path.isdir(os.path.join(skill_path, d))]

    if not os.path.isdir(os.path.join(skill_path, "references")):
        suggestions.append("建议创建references/目录存放详细文档")

    if not os.path.isdir(os.path.join(skill_path, "examples")):
        suggestions.append("建议创建examples/目录存放完整示例")

    # 检查文件命名
    ref_dir = os.path.join(skill_path, "references")
    if os.path.isdir(ref_dir):
        bad_names = [f for f in os.listdir(ref_dir)
                     if f.startswith("doc") or f.startswith("untitled") or f == "readme.md"]
        if bad_names:
            issues.append(f"references/中有不描述性的文件名：{bad_names}")
            suggestions.append("改为描述性文件名，如'form-validation.md'")

    return {
        "existing_dirs": existing,
        "issues": issues,
        "suggestions": suggestions,
    }


def main():
    parser = argparse.ArgumentParser(description="技能触发诊断工具")
    parser.add_argument("skill_path", help="技能目录路径")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    if not os.path.isdir(args.skill_path):
        print(f"❌ 目录不存在: {args.skill_path}", file=sys.stderr)
        sys.exit(1)

    # 读取SKILL.md
    data, err = read_skill_md(args.skill_path)
    if err:
        print(f"❌ {err}", file=sys.stderr)
        sys.exit(1)

    fm = data["frontmatter"]
    body = data["body"]

    # 诊断
    desc_diag = diagnose_description(fm)
    body_diag = diagnose_body(body)
    dir_diag = diagnose_directory(args.skill_path)

    # 汇总
    total_score = desc_diag["score"]
    all_issues = desc_diag["issues"] + body_diag["issues"] + dir_diag["issues"]
    all_suggestions = desc_diag["suggestions"] + body_diag["suggestions"] + dir_diag["suggestions"]

    result = {
        "skill_path": args.skill_path,
        "name": fm.get("name", ""),
        "description_score": desc_diag["score"],
        "description_length": desc_diag["length"],
        "body_lines": body_diag["body_lines"],
        "total_issues": len(all_issues),
        "total_suggestions": len(all_suggestions),
        "issues": all_issues,
        "suggestions": all_suggestions,
        "description_details": {
            "has_what": desc_diag["has_what"],
            "has_when": desc_diag["has_when"],
            "has_trigger_words": desc_diag["has_trigger"],
            "has_not_for": desc_diag["has_not_for"],
        },
        "body_details": body_diag,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("🔍 技能触发诊断报告")
        print("=" * 60)
        print(f"\n技能: {fm.get('name', '?')}")
        print(f"Description长度: {desc_diag['length']}字符")
        print(f"Body行数: {body_diag['body_lines']}行")
        print(f"Description评分: {desc_diag['score']}/100")

        if all_issues:
            print(f"\n❌ 问题（{len(all_issues)}个）:")
            for i, issue in enumerate(all_issues, 1):
                print(f"  {i}. {issue}")

        if all_suggestions:
            print(f"\n💡 建议（{len(all_suggestions)}个）:")
            for i, sug in enumerate(all_suggestions, 1):
                print(f"  {i}. {sug}")

        # 评级
        if desc_diag["score"] >= 90:
            rating = "🟢 优秀"
        elif desc_diag["score"] >= 70:
            rating = "🟡 良好"
        elif desc_diag["score"] >= 50:
            rating = "🟠 一般"
        else:
            rating = "🔴 需改进"

        print(f"\n评级: {rating}")

    # 有严重问题时退出码1
    if desc_diag["score"] < 50 or len(all_issues) > 3:
        sys.exit(1)


if __name__ == "__main__":
    main()
