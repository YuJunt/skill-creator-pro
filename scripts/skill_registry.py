#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能注册表工具（skill_registry.py）

程序化发现和管理所有已安装技能的元数据，生成技能注册表。
支持：扫描技能目录、提取元数据、生成注册表JSON/Markdown、查询技能、统计分析。

用法：
  python3 skill_registry.py scan <skills-dir>              # 扫描技能目录，生成注册表
  python3 skill_registry.py scan <skills-dir> --json        # JSON格式输出
  python3 skill_registry.py scan <skills-dir> --markdown    # Markdown格式输出
  python3 skill_registry.py query <skills-dir> --name <name> # 查询特定技能
  python3 skill_registry.py stats <skills-dir>               # 统计分析
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime


def extract_frontmatter(skill_md_path):
    """从SKILL.md提取frontmatter"""
    try:
        with open(skill_md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return {}

    if not content.startswith("---"):
        return {}

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    fm = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def extract_skill_info(skill_path):
    """提取单个技能的完整元数据"""
    skill_name = os.path.basename(skill_path)
    skill_md = os.path.join(skill_path, "SKILL.md")

    if not os.path.isfile(skill_md):
        return None

    # 基本信息
    info = {
        "name": skill_name,
        "path": skill_path,
        "skill_md_exists": True,
        "last_modified": datetime.fromtimestamp(os.path.getmtime(skill_md)).isoformat(),
    }

    # frontmatter
    fm = extract_frontmatter(skill_md)
    info["frontmatter"] = fm
    info["description"] = fm.get("description", "")[:200]  # 截断，避免过长
    info["version"] = fm.get("version", "")

    # SKILL.md统计
    try:
        with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        info["skill_md_lines"] = len(lines)
        info["skill_md_size"] = os.path.getsize(skill_md)
    except Exception:
        info["skill_md_lines"] = 0
        info["skill_md_size"] = 0

    # 目录结构统计
    for subdir in ["scripts", "references", "examples", "assets", "tests"]:
        dir_path = os.path.join(skill_path, subdir)
        if os.path.isdir(dir_path):
            files = [f for f in os.listdir(dir_path) if not f.startswith("__") and not f.startswith(".")]
            info[f"{subdir}_count"] = len(files)
        else:
            info[f"{subdir}_count"] = 0

    # 脚本类型统计
    scripts_dir = os.path.join(skill_path, "scripts")
    if os.path.isdir(scripts_dir):
        py_scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]
        sh_scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".sh")]
        info["python_scripts"] = len(py_scripts)
        info["shell_scripts"] = len(sh_scripts)
    else:
        info["python_scripts"] = 0
        info["shell_scripts"] = 0

    # 技能类型推断
    if info["python_scripts"] > 0 or info["shell_scripts"] > 0:
        if info["references_count"] > 3:
            info["skill_type"] = "混合型（工具+方法论）"
        else:
            info["skill_type"] = "工具型（脚本为主）"
    elif info["references_count"] > 3:
        info["skill_type"] = "方法论型（文档为主）"
    else:
        info["skill_type"] = "基础型（仅SKILL.md）"

    # 成熟度评估
    score = 0
    if info["skill_md_lines"] > 50:
        score += 1
    if info["scripts_count"] > 0:
        score += 1
    if info["references_count"] > 2:
        score += 1
    if info["examples_count"] > 0:
        score += 1
    if info["tests_count"] > 0:
        score += 1
    if info["skill_md_lines"] > 200:
        score += 1

    maturity_levels = ["初始", "基础", "可用", "良好", "优秀", "生产级"]
    info["maturity_score"] = score
    info["maturity"] = maturity_levels[min(score, len(maturity_levels) - 1)]

    return info


def scan_skills(skills_dir):
    """扫描技能目录，发现所有技能"""
    if not os.path.isdir(skills_dir):
        return {"error": f"目录不存在: {skills_dir}", "skills": []}

    skills = []
    for item in sorted(os.listdir(skills_dir)):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path) and not item.startswith(".") and not item.startswith("__"):
            skill_md = os.path.join(item_path, "SKILL.md")
            if os.path.isfile(skill_md):
                info = extract_skill_info(item_path)
                if info:
                    skills.append(info)

    return {
        "scan_path": skills_dir,
        "scan_time": datetime.now().isoformat(),
        "total_skills": len(skills),
        "skills": skills,
    }


def generate_stats(registry):
    """生成统计分析"""
    skills = registry.get("skills", [])
    if not skills:
        return {"error": "无技能数据"}

    stats = {
        "total_skills": len(skills),
        "by_type": {},
        "by_maturity": {},
        "total_scripts": 0,
        "total_references": 0,
        "total_examples": 0,
        "avg_skill_md_lines": 0,
        "skills_with_tests": 0,
        "skills_with_scripts": 0,
        "skills_with_examples": 0,
    }

    total_lines = 0
    for s in skills:
        # 按类型统计
        stype = s.get("skill_type", "未知")
        stats["by_type"][stype] = stats["by_type"].get(stype, 0) + 1

        # 按成熟度统计
        maturity = s.get("maturity", "未知")
        stats["by_maturity"][maturity] = stats["by_maturity"].get(maturity, 0) + 1

        # 总量统计
        stats["total_scripts"] += s.get("scripts_count", 0)
        stats["total_references"] += s.get("references_count", 0)
        stats["total_examples"] += s.get("examples_count", 0)
        total_lines += s.get("skill_md_lines", 0)

        if s.get("tests_count", 0) > 0:
            stats["skills_with_tests"] += 1
        if s.get("scripts_count", 0) > 0:
            stats["skills_with_scripts"] += 1
        if s.get("examples_count", 0) > 0:
            stats["skills_with_examples"] += 1

    stats["avg_skill_md_lines"] = round(total_lines / len(skills), 1) if skills else 0

    return stats


def print_registry(registry, output_format="table"):
    """输出注册表"""
    if "error" in registry:
        print(f"❌ {registry['error']}")
        return

    skills = registry.get("skills", [])

    if output_format == "json":
        print(json.dumps(registry, ensure_ascii=False, indent=2))
        return

    if output_format == "markdown":
        print(f"# 技能注册表")
        print(f"\n> 扫描路径: `{registry['scan_path']}`")
        print(f"> 扫描时间: {registry['scan_time']}")
        print(f"> 技能总数: {registry['total_skills']}")
        print(f"\n| 技能名称 | 类型 | 成熟度 | 脚本 | 文档 | 示例 | SKILL.md行数 | 最后修改 |")
        print(f"|---------|------|--------|------|------|------|-------------|---------|")
        for s in skills:
            print(f"| {s['name']} | {s.get('skill_type', '-')} | {s.get('maturity', '-')} | "
                  f"{s.get('scripts_count', 0)} | {s.get('references_count', 0)} | "
                  f"{s.get('examples_count', 0)} | {s.get('skill_md_lines', 0)} | "
                  f"{s.get('last_modified', '-')[:10]} |")
        return

    # 默认表格输出
    print(f"\n{'='*90}")
    print(f"技能注册表: {registry['scan_path']}")
    print(f"扫描时间: {registry['scan_time']} | 技能总数: {registry['total_skills']}")
    print(f"{'='*90}")
    print(f"{'技能名称':30s} {'类型':16s} {'成熟度':8s} {'脚本':4s} {'文档':4s} {'示例':4s} {'行数':5s}")
    print(f"{'-'*90}")
    for s in skills:
        print(f"{s['name']:30s} {s.get('skill_type', '-'):16s} {s.get('maturity', '-'):8s} "
              f"{s.get('scripts_count', 0):4d} {s.get('references_count', 0):4d} "
              f"{s.get('examples_count', 0):4d} {s.get('skill_md_lines', 0):5d}")


def main():
    parser = argparse.ArgumentParser(description="技能注册表工具——程序化发现和管理所有技能的元数据")
    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = sub.add_parser("scan", help="扫描技能目录，生成注册表")
    p_scan.add_argument("skills_dir", help="技能根目录路径")
    p_scan.add_argument("--json", action="store_true", help="JSON格式输出")
    p_scan.add_argument("--markdown", action="store_true", help="Markdown格式输出")

    # query
    p_query = sub.add_parser("query", help="查询特定技能")
    p_query.add_argument("skills_dir", help="技能根目录路径")
    p_query.add_argument("--name", required=True, help="技能名称（支持模糊匹配）")

    # stats
    p_stats = sub.add_parser("stats", help="统计分析")
    p_stats.add_argument("skills_dir", help="技能根目录路径")

    args = parser.parse_args()

    if args.command == "scan":
        registry = scan_skills(args.skills_dir)
        if args.json:
            print_registry(registry, "json")
        elif args.markdown:
            print_registry(registry, "markdown")
        else:
            print_registry(registry, "table")

    elif args.command == "query":
        registry = scan_skills(args.skills_dir)
        if "error" in registry:
            print(f"❌ {registry['error']}")
            return
        matched = [s for s in registry["skills"] if args.name.lower() in s["name"].lower()]
        if not matched:
            print(f"❌ 未找到匹配的技能: {args.name}")
            return
        print(f"\n找到 {len(matched)} 个匹配技能:")
        for s in matched:
            print(f"\n{'='*60}")
            print(f"技能: {s['name']}")
            print(f"路径: {s['path']}")
            print(f"类型: {s.get('skill_type', '-')}")
            print(f"成熟度: {s.get('maturity', '-')} ({s.get('maturity_score', 0)}/6)")
            print(f"SKILL.md: {s.get('skill_md_lines', 0)}行, {s.get('skill_md_size', 0)}字节")
            print(f"脚本: {s.get('scripts_count', 0)}个 (Python:{s.get('python_scripts', 0)}, Shell:{s.get('shell_scripts', 0)})")
            print(f"文档: {s.get('references_count', 0)}个")
            print(f"示例: {s.get('examples_count', 0)}个")
            print(f"测试: {s.get('tests_count', 0)}个")
            print(f"最后修改: {s.get('last_modified', '-')}")
            print(f"描述: {s.get('description', '-')[:100]}...")

    elif args.command == "stats":
        registry = scan_skills(args.skills_dir)
        if "error" in registry:
            print(f"❌ {registry['error']}")
            return
        stats = generate_stats(registry)
        print(f"\n{'='*60}")
        print(f"技能统计分析")
        print(f"{'='*60}")
        print(f"总技能数: {stats['total_skills']}")
        print(f"总脚本数: {stats['total_scripts']}")
        print(f"总文档数: {stats['total_references']}")
        print(f"总示例数: {stats['total_examples']}")
        print(f"平均SKILL.md行数: {stats['avg_skill_md_lines']}")
        print(f"有测试的技能: {stats['skills_with_tests']} ({stats['skills_with_tests']/stats['total_skills']*100:.0f}%)")
        print(f"有脚本的技能: {stats['skills_with_scripts']} ({stats['skills_with_scripts']/stats['total_skills']*100:.0f}%)")
        print(f"有示例的技能: {stats['skills_with_examples']} ({stats['skills_with_examples']/stats['total_skills']*100:.0f}%)")
        print(f"\n按类型分布:")
        for stype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            print(f"  {stype}: {count}个")
        print(f"\n按成熟度分布:")
        for maturity, count in sorted(stats['by_maturity'].items(), key=lambda x: -x[1]):
            print(f"  {maturity}: {count}个")


if __name__ == "__main__":
    main()
