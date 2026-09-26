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




# ============================================================
# 触发诊断功能（从diagnose_trigger.py合并）
# ============================================================

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
    parser = argparse.ArgumentParser(description="技能描述优化与触发诊断工具")
    sub = parser.add_subparsers(dest="command")
    
    # optimize子命令
    opt_p = sub.add_parser("optimize", help="优化description")
    opt_p.add_argument("skill_path", help="技能目录路径")
    
    # diagnose子命令
    diag_p = sub.add_parser("diagnose", help="诊断触发问题")
    diag_p.add_argument("skill_path", help="技能目录路径")
    diag_p.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    if args.command == "optimize":
        # 原description_optimizer的逻辑
        skill_md = os.path.join(args.skill_path, "SKILL.md")
        if not os.path.isfile(skill_md):
            print(f"❌ SKILL.md不存在: {skill_md}", file=sys.stderr)
            sys.exit(1)
        
        desc, error = extract_description(skill_md)
        if error:
            print(f"❌ {error}", file=sys.stderr)
            sys.exit(1)
        
        analysis = analyze_description(desc)
        improved = generate_improved_description(os.path.basename(args.skill_path), desc, analysis)
        
        print("\n" + "="*60)
        print("📝 Description分析报告")
        print("="*60)
        print(f"\n当前描述: {desc[:100]}...")
        print(f"\n分析结果:")
        for k, v in analysis.items():
            print(f"  - {k}: {v}")
        print(f"\n建议改进:")
        print(improved)
        
    elif args.command == "diagnose":
        # 原diagnose_trigger的逻辑
        result, error = read_skill_md(args.skill_path)
        if error:
            print(f"❌ {error}", file=sys.stderr)
            sys.exit(1)
        
        fm = result["frontmatter"]
        body = result["body"]
        
        desc_diag = diagnose_description(fm)
        body_diag = diagnose_body(body)
        dir_diag = diagnose_directory(args.skill_path)
        
        if args.json:
            print(json.dumps({
                "description": desc_diag,
                "body": body_diag,
                "directory": dir_diag,
            }, ensure_ascii=False, indent=2))
        else:
            print("\n" + "="*60)
            print("🔍 技能触发诊断报告")
            print("="*60)
            print(f"\n技能: {fm.get('name', '未知')}")
            print(f"\n--- Description诊断 ---")
            print(f"  得分: {desc_diag.get('score', 0)}/100")
            for issue in desc_diag.get('issues', []):
                print(f"  ⚠️  {issue}")
            for sug in desc_diag.get('suggestions', []):
                print(f"  💡 {sug}")
            
            print(f"\n--- 正文诊断 ---")
            for issue in body_diag.get('issues', []):
                print(f"  ⚠️  {issue}")
            
            print(f"\n--- 目录诊断 ---")
            for issue in dir_diag.get('issues', []):
                print(f"  ⚠️  {issue}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
