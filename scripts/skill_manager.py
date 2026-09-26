#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级技能管理工具（skill_manager.py）

提供企业级技能管理功能：去重检测、技能合并、批量校验、健康检查。
版本管理复用version_manager.py，分发打包复用package.sh。

用法：
  python3 skill_manager.py dedup <skills-dir>                    # 检测重复/相似技能
  python3 skill_manager.py merge <skill1> <skill2> --output <dir> # 合并两个技能
  python3 skill_manager.py health <skills-dir>                    # 批量健康检查
  python3 skill_manager.py batch-validate <skills-dir>            # 批量规范校验
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime


def extract_skill_signature(skill_path):
    """提取技能签名（用于去重检测）"""
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        return None

    try:
        with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return None

    # 提取frontmatter中的name和description
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    name = ""
    description = ""
    if fm_match:
        fm = fm_match.group(1)
        name_match = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
        desc_match = re.search(r"^description:\s*(.+?)(?=\n[a-z_]+:|\Z)", fm, re.DOTALL | re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip('"').strip("'")
        if desc_match:
            description = desc_match.group(1).strip().strip('"').strip("'")

    # 提取脚本列表
    scripts_dir = os.path.join(skill_path, "scripts")
    scripts = []
    if os.path.isdir(scripts_dir):
        scripts = sorted([f for f in os.listdir(scripts_dir) if f.endswith(".py") or f.endswith(".sh")])

    # 提取references列表
    refs_dir = os.path.join(skill_path, "references")
    references = []
    if os.path.isdir(refs_dir):
        references = sorted([f for f in os.listdir(refs_dir) if f.endswith(".md")])

    return {
        "name": name or os.path.basename(skill_path),
        "path": skill_path,
        "description": description[:200],
        "scripts": scripts,
        "references": references,
        "script_count": len(scripts),
        "ref_count": len(references),
    }


def calculate_similarity(sig1, sig2):
    """计算两个技能的相似度（0-100）"""
    score = 0
    max_score = 0

    # 1. 名称相似度（20分）
    max_score += 20
    name1 = sig1["name"].lower()
    name2 = sig2["name"].lower()
    if name1 == name2:
        score += 20
    elif name1 in name2 or name2 in name1:
        score += 15
    else:
        # 计算共同字符比例
        common = len(set(name1) & set(name2))
        total = len(set(name1) | set(name2))
        if total > 0:
            score += int(common / total * 10)

    # 2. 描述相似度（30分）
    max_score += 30
    desc1_words = set(re.findall(r'\w+', sig1["description"].lower()))
    desc2_words = set(re.findall(r'\w+', sig2["description"].lower()))
    if desc1_words and desc2_words:
        common = len(desc1_words & desc2_words)
        total = len(desc1_words | desc2_words)
        if total > 0:
            score += int(common / total * 30)

    # 3. 脚本重叠度（30分）
    max_score += 30
    scripts1 = set(sig1["scripts"])
    scripts2 = set(sig2["scripts"])
    if scripts1 and scripts2:
        common = len(scripts1 & scripts2)
        total = len(scripts1 | scripts2)
        if total > 0:
            score += int(common / total * 30)

    # 4. 文档重叠度（20分）
    max_score += 20
    refs1 = set(sig1["references"])
    refs2 = set(sig2["references"])
    if refs1 and refs2:
        common = len(refs1 & refs2)
        total = len(refs1 | refs2)
        if total > 0:
            score += int(common / total * 20)

    return int(score / max_score * 100) if max_score > 0 else 0


def detect_duplicates(skills_dir):
    """检测重复/相似技能"""
    if not os.path.isdir(skills_dir):
        return {"error": f"目录不存在: {skills_dir}", "pairs": []}

    # 扫描所有技能
    signatures = []
    for item in sorted(os.listdir(skills_dir)):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path) and not item.startswith("."):
            sig = extract_skill_signature(item_path)
            if sig:
                signatures.append(sig)

    # 两两比较
    pairs = []
    for i in range(len(signatures)):
        for j in range(i + 1, len(signatures)):
            sim = calculate_similarity(signatures[i], signatures[j])
            if sim >= 50:  # 相似度≥50%才报告
                level = "极高（可能重复）" if sim >= 80 else "高（建议合并）" if sim >= 60 else "中（有关联）"
                pairs.append({
                    "skill1": signatures[i]["name"],
                    "skill2": signatures[j]["name"],
                    "similarity": sim,
                    "level": level,
                    "skill1_path": signatures[i]["path"],
                    "skill2_path": signatures[j]["path"],
                })

    pairs.sort(key=lambda x: -x["similarity"])

    return {
        "scan_path": skills_dir,
        "scan_time": datetime.now().isoformat(),
        "total_skills": len(signatures),
        "similar_pairs": len(pairs),
        "pairs": pairs,
    }


def merge_skills(skill1_path, skill2_path, output_dir):
    """合并两个技能（取并集，冲突时以skill1为准）"""
    if not os.path.isdir(skill1_path):
        return {"success": False, "error": f"技能1不存在: {skill1_path}"}
    if not os.path.isdir(skill2_path):
        return {"success": False, "error": f"技能2不存在: {skill2_path}"}

    name1 = os.path.basename(skill1_path)
    name2 = os.path.basename(skill2_path)
    merged_name = f"{name1}_{name2}_merged"
    merged_path = os.path.join(output_dir, merged_name)

    if os.path.exists(merged_path):
        return {"success": False, "error": f"合并目标已存在: {merged_path}"}

    os.makedirs(merged_path, exist_ok=True)

    merge_log = []

    # 合并SKILL.md（以skill1为基础，追加skill2的独有内容）
    sk1_md = os.path.join(skill1_path, "SKILL.md")
    sk2_md = os.path.join(skill2_path, "SKILL.md")

    if os.path.isfile(sk1_md):
        shutil.copy2(sk1_md, os.path.join(merged_path, "SKILL.md"))
        merge_log.append("SKILL.md: 以技能1为基础")
        if os.path.isfile(sk2_md):
            # 追加skill2的内容标记
            with open(os.path.join(merged_path, "SKILL.md"), "a", encoding="utf-8") as f:
                f.write(f"\n\n---\n\n## 合并自技能2: {name2}\n\n> 以下内容来自技能2，需要人工整合到对应章节。\n")
                with open(sk2_md, "r", encoding="utf-8", errors="replace") as f2:
                    f.write(f2.read())
            merge_log.append("SKILL.md: 追加技能2内容（需人工整合）")
    elif os.path.isfile(sk2_md):
        shutil.copy2(sk2_md, os.path.join(merged_path, "SKILL.md"))
        merge_log.append("SKILL.md: 使用技能2（技能1无SKILL.md）")

    # 合并scripts（取并集，重名时以skill1为准）
    for subdir in ["scripts", "references", "examples", "assets", "tests"]:
        dir1 = os.path.join(skill1_path, subdir)
        dir2 = os.path.join(skill2_path, subdir)
        merged_dir = os.path.join(merged_path, subdir)

        files1 = set()
        files2 = set()

        if os.path.isdir(dir1):
            files1 = set(os.listdir(dir1))
            shutil.copytree(dir1, merged_dir, dirs_exist_ok=True)

        if os.path.isdir(dir2):
            files2 = set(os.listdir(dir2))
            os.makedirs(merged_dir, exist_ok=True)
            for f in files2:
                if f not in files1:  # skill1没有的才复制
                    src = os.path.join(dir2, f)
                    dst = os.path.join(merged_dir, f)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)

        common = files1 & files2
        only2 = files2 - files1
        if common or only2:
            merge_log.append(f"{subdir}/: 技能1有{len(files1)}个，技能2有{len(files2)}个，"
                           f"重名{len(common)}个（以技能1为准），新增{len(only2)}个")

    return {
        "success": True,
        "merged_name": merged_name,
        "merged_path": merged_path,
        "merge_log": merge_log,
        "next_step": "请人工检查合并结果，整合SKILL.md内容，删除不需要的文件",
    }


def batch_health_check(skills_dir):
    """批量健康检查"""
    if not os.path.isdir(skills_dir):
        return {"error": f"目录不存在: {skills_dir}", "results": []}

    results = []
    for item in sorted(os.listdir(skills_dir)):
        item_path = os.path.join(skills_dir, item)
        if not os.path.isdir(item_path) or item.startswith("."):
            continue

        skill_md = os.path.join(item_path, "SKILL.md")
        issues = []
        status = "健康"

        if not os.path.isfile(skill_md):
            issues.append("缺少SKILL.md")
            status = "严重问题"
        else:
            # 检查SKILL.md大小
            size = os.path.getsize(skill_md)
            if size == 0:
                issues.append("SKILL.md为空")
                status = "严重问题"
            elif size > 100000:  # >100KB
                issues.append(f"SKILL.md过大（{size}字节），建议拆分")
                if status == "健康":
                    status = "警告"

            # 检查是否有TODO
            try:
                with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                if "TODO" in content or "待填写" in content:
                    issues.append("包含TODO/待填写占位符")
                    if status == "健康":
                        status = "警告"
            except Exception:
                pass

        # 检查scripts目录
        scripts_dir = os.path.join(item_path, "scripts")
        if os.path.isdir(scripts_dir):
            py_files = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]
            for py in py_files[:5]:  # 最多检查5个
                py_path = os.path.join(scripts_dir, py)
                try:
                    with open(py_path, "r", encoding="utf-8", errors="replace") as f:
                        compile(f.read(), py, "exec")
                except SyntaxError as e:
                    issues.append(f"脚本语法错误: {py} - {e}")
                    status = "严重问题"

        results.append({
            "name": item,
            "status": status,
            "issues": issues,
            "issue_count": len(issues),
        })

    healthy = sum(1 for r in results if r["status"] == "健康")
    warning = sum(1 for r in results if r["status"] == "警告")
    critical = sum(1 for r in results if r["status"] == "严重问题")

    return {
        "scan_path": skills_dir,
        "scan_time": datetime.now().isoformat(),
        "total": len(results),
        "healthy": healthy,
        "warning": warning,
        "critical": critical,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="企业级技能管理工具——去重/合并/健康检查/批量校验")
    sub = parser.add_subparsers(dest="command", required=True)

    # dedup
    p_dedup = sub.add_parser("dedup", help="检测重复/相似技能")
    p_dedup.add_argument("skills_dir", help="技能根目录路径")
    p_dedup.add_argument("--json", action="store_true", help="JSON格式输出")

    # merge
    p_merge = sub.add_parser("merge", help="合并两个技能")
    p_merge.add_argument("skill1", help="技能1路径")
    p_merge.add_argument("skill2", help="技能2路径")
    p_merge.add_argument("--output", required=True, help="输出目录")

    # health
    p_health = sub.add_parser("health", help="批量健康检查")
    p_health.add_argument("skills_dir", help="技能根目录路径")
    p_health.add_argument("--json", action="store_true", help="JSON格式输出")

    # batch-validate
    p_bv = sub.add_parser("batch-validate", help="批量规范校验")
    p_bv.add_argument("skills_dir", help="技能根目录路径")

    args = parser.parse_args()

    if args.command == "dedup":
        result = detect_duplicates(args.skills_dir)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*70}")
            print(f"技能去重检测: {result.get('scan_path', '')}")
            print(f"扫描时间: {result.get('scan_time', '')} | 总技能数: {result.get('total_skills', 0)}")
            print(f"{'='*70}")
            if not result.get("pairs"):
                print("✅ 未发现相似技能对")
            else:
                print(f"⚠️  发现 {result['similar_pairs']} 对相似技能:")
                print()
                for i, p in enumerate(result["pairs"], 1):
                    print(f"{i}. [{p['level']}] {p['skill1']} ↔ {p['skill2']} (相似度: {p['similarity']}%)")
                    print(f"   技能1: {p['skill1_path']}")
                    print(f"   技能2: {p['skill2_path']}")
                    print()

    elif args.command == "merge":
        result = merge_skills(args.skill1, args.skill2, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "health":
        result = batch_health_check(args.skills_dir)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*70}")
            print(f"技能健康检查: {result.get('scan_path', '')}")
            print(f"总技能: {result.get('total', 0)} | ✅健康: {result.get('healthy', 0)} | "
                  f"⚠️警告: {result.get('warning', 0)} | 🔴严重: {result.get('critical', 0)}")
            print(f"{'='*70}")
            for r in result.get("results", []):
                icon = "✅" if r["status"] == "健康" else "⚠️" if r["status"] == "警告" else "🔴"
                print(f"{icon} {r['name']}: {r['status']}" + (f" ({r['issue_count']}个问题)" if r["issues"] else ""))
                for issue in r["issues"]:
                    print(f"   - {issue}")

    elif args.command == "batch-validate":
        # 批量调用validate_skill.py
        script_dir = os.path.dirname(os.path.abspath(__file__))
        validator = os.path.join(script_dir, "validate_skill.py")
        if not os.path.isfile(validator):
            print(f"❌ 找不到validate_skill.py: {validator}")
            return

        if not os.path.isdir(args.skills_dir):
            print(f"❌ 目录不存在: {args.skills_dir}")
            return

        print(f"\n{'='*70}")
        print(f"批量规范校验: {args.skills_dir}")
        print(f"{'='*70}")

        passed = 0
        failed = 0
        for item in sorted(os.listdir(args.skills_dir)):
            item_path = os.path.join(args.skills_dir, item)
            if not os.path.isdir(item_path) or item.startswith("."):
                continue
            skill_md = os.path.join(item_path, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue

            import subprocess
            try:
                proc = subprocess.run(
                    [sys.executable, validator, item_path],
                    capture_output=True, text=True, timeout=30
                )
                if proc.returncode == 0:
                    print(f"✅ {item}: 通过")
                    passed += 1
                else:
                    print(f"❌ {item}: 未通过")
                    # 提取问题摘要
                    for line in proc.stdout.split("\n"):
                        if "问题统计" in line or "高=" in line:
                            print(f"   {line.strip()}")
                            break
                    failed += 1
            except Exception as e:
                print(f"⚠️  {item}: 校验异常 - {e}")
                failed += 1

        print(f"\n{'='*70}")
        print(f"汇总: 通过{passed}个，未通过{failed}个，共{passed+failed}个")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()
