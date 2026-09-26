#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能生命周期管理工具（skill_lifecycle.py）

管理技能的完整生命周期：使用监控、退役信号检测、归档、删除SLA、上下文膨胀监控。
帮助用户保持技能库的健康和高效，避免技能堆积和上下文膨胀。

用法：
  python3 skill_lifecycle.py monitor <skills-dir>              # 监控所有技能的生命周期状态
  python3 skill_lifecycle.py retire <skills-dir>                # 检测应该退役的技能
  python3 skill_lifecycle.py archive <skill-path> --output <dir> # 归档技能
  python3 skill_lifecycle.py bloat <skills-dir>                 # 上下文膨胀监控
  python3 skill_lifecycle.py cleanup <skills-dir> --dry-run     # 清理建议（默认dry-run）
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timedelta


def get_skill_age(skill_path):
    """获取技能的年龄和最后修改时间"""
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        return None

    mtime = os.path.getmtime(skill_md)
    ctime = os.path.getctime(skill_md)
    now = datetime.now().timestamp()

    return {
        "last_modified": datetime.fromtimestamp(mtime).isoformat(),
        "created": datetime.fromtimestamp(ctime).isoformat(),
        "days_since_modified": int((now - mtime) / 86400),
        "days_since_created": int((now - ctime) / 86400),
    }


def get_skill_size(skill_path):
    """获取技能的大小统计"""
    total_size = 0
    file_count = 0
    sk_md_lines = 0
    sk_md_size = 0

    for root, dirs, files in os.walk(skill_path):
        # 跳过缓存目录
        dirs[:] = [d for d in dirs if not d.startswith("__") and not d.startswith(".")]
        for f in files:
            if f.startswith("."):
                continue
            fp = os.path.join(root, f)
            try:
                size = os.path.getsize(fp)
                total_size += size
                file_count += 1
                if f == "SKILL.md":
                    sk_md_size = size
                    with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                        sk_md_lines = len(fh.readlines())
            except Exception:
                pass

    # 统计各目录
    dir_counts = {}
    for subdir in ["scripts", "references", "examples", "assets", "tests"]:
        dir_path = os.path.join(skill_path, subdir)
        if os.path.isdir(dir_path):
            dir_counts[subdir] = len([f for f in os.listdir(dir_path) if not f.startswith(".")])
        else:
            dir_counts[subdir] = 0

    return {
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "file_count": file_count,
        "skill_md_lines": sk_md_lines,
        "skill_md_size": sk_md_size,
        "dir_counts": dir_counts,
    }


def detect_retirement_signals(skill_path, size_info, age_info):
    """检测技能的退役信号"""
    signals = []
    score = 0  # 退役分数，越高越应该退役

    if not age_info or not size_info:
        return {"should_retire": False, "score": 0, "signals": []}

    # 信号1：长期未更新（>180天）
    if age_info["days_since_modified"] > 180:
        signals.append(f"长期未更新（{age_info['days_since_modified']}天）")
        score += 3
    elif age_info["days_since_modified"] > 90:
        signals.append(f"较长时间未更新（{age_info['days_since_modified']}天）")
        score += 1

    # 信号2：SKILL.md过小（<20行，可能是占位符）
    if size_info["skill_md_lines"] < 20:
        signals.append(f"SKILL.md过小（{size_info['skill_md_lines']}行，可能是未完成的占位符）")
        score += 3

    # 信号3：没有脚本且没有references（基础型技能，可能已被吸收）
    if size_info["dir_counts"]["scripts"] == 0 and size_info["dir_counts"]["references"] == 0:
        signals.append("无脚本无文档（基础型技能，功能可能已被其他技能吸收）")
        score += 2

    # 信号4：包含TODO/待填写
    skill_md = os.path.join(skill_path, "SKILL.md")
    if os.path.isfile(skill_md):
        try:
            with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if "TODO" in content or "待填写" in content or "占位" in content:
                signals.append("包含TODO/待填写占位符（未完成的技能）")
                score += 2
        except Exception:
            pass

    # 信号5：文件数过少（<3个文件）
    if size_info["file_count"] < 3:
        signals.append(f"文件数过少（{size_info['file_count']}个，可能是废弃技能）")
        score += 1

    should_retire = score >= 5
    level = "建议退役" if score >= 7 else "考虑退役" if score >= 5 else "关注" if score >= 3 else "健康"

    return {
        "should_retire": should_retire,
        "retirement_score": score,
        "level": level,
        "signals": signals,
    }


def detect_bloat(skill_path, size_info):
    """检测上下文膨胀"""
    issues = []
    score = 0  # 膨胀分数，越高越膨胀

    if not size_info:
        return {"is_bloated": False, "score": 0, "issues": []}

    # 问题1：SKILL.md过长（>500行）
    if size_info["skill_md_lines"] > 500:
        issues.append(f"SKILL.md过长（{size_info['skill_md_lines']}行，超过500行上限，必须拆分）")
        score += 3
    elif size_info["skill_md_lines"] > 300:
        issues.append(f"SKILL.md较长（{size_info['skill_md_lines']}行，超过300行建议拆分）")
        score += 1

    # 问题2：references过多（>20个）
    if size_info["dir_counts"]["references"] > 20:
        issues.append(f"references过多（{size_info['dir_counts']['references']}个，建议合并或归档）")
        score += 2
    elif size_info["dir_counts"]["references"] > 15:
        issues.append(f"references较多（{size_info['dir_counts']['references']}个，关注是否有冗余）")
        score += 1

    # 问题3：脚本过多（>20个）
    if size_info["dir_counts"]["scripts"] > 20:
        issues.append(f"脚本过多（{size_info['dir_counts']['scripts']}个，建议合并或拆分模块）")
        score += 2
    elif size_info["dir_counts"]["scripts"] > 15:
        issues.append(f"脚本较多（{size_info['dir_counts']['scripts']}个，关注是否有冗余）")
        score += 1

    # 问题4：总大小过大（>5MB）
    if size_info["total_size_mb"] > 5:
        issues.append(f"总大小过大（{size_info['total_size_mb']}MB，建议清理assets或归档）")
        score += 2
    elif size_info["total_size_mb"] > 2:
        issues.append(f"总大小较大（{size_info['total_size_mb']}MB，关注是否有冗余文件）")
        score += 1

    # 问题5：assets过大（>2MB）
    assets_dir = os.path.join(skill_path, "assets")
    if os.path.isdir(assets_dir):
        assets_size = 0
        for root, dirs, files in os.walk(assets_dir):
            for f in files:
                try:
                    assets_size += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
        if assets_size > 2 * 1024 * 1024:
            issues.append(f"assets过大（{round(assets_size/1024/1024, 2)}MB，建议压缩或移到外部存储）")
            score += 1

    is_bloated = score >= 4
    level = "严重膨胀" if score >= 6 else "膨胀" if score >= 4 else "关注" if score >= 2 else "健康"

    return {
        "is_bloated": is_bloated,
        "bloat_score": score,
        "level": level,
        "issues": issues,
    }


def archive_skill(skill_path, output_dir):
    """归档技能（压缩并移到archive目录）"""
    if not os.path.isdir(skill_path):
        return {"success": False, "error": f"技能不存在: {skill_path}"}

    skill_name = os.path.basename(skill_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{skill_name}_archived_{timestamp}"
    archive_path = os.path.join(output_dir, archive_name)

    os.makedirs(output_dir, exist_ok=True)

    # 复制技能到归档目录
    shutil.copytree(skill_path, archive_path, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))

    # 创建归档标记文件
    marker = {
        "archived_at": datetime.now().isoformat(),
        "original_path": skill_path,
        "original_name": skill_name,
        "reason": "用户主动归档",
    }
    with open(os.path.join(archive_path, ".archive_info.json"), "w", encoding="utf-8") as f:
        json.dump(marker, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "archive_name": archive_name,
        "archive_path": archive_path,
        "original_path": skill_path,
        "next_step": f"归档完成。如需恢复，将 {archive_path} 复制回原位置即可。原技能未删除，请确认后手动删除。",
    }


def monitor_lifecycle(skills_dir):
    """监控所有技能的生命周期状态"""
    if not os.path.isdir(skills_dir):
        return {"error": f"目录不存在: {skills_dir}", "skills": []}

    skills = []
    for item in sorted(os.listdir(skills_dir)):
        item_path = os.path.join(skills_dir, item)
        if not os.path.isdir(item_path) or item.startswith(".") or item == "archive":
            continue

        skill_md = os.path.join(item_path, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue

        age = get_skill_age(item_path)
        size = get_skill_size(item_path)
        retirement = detect_retirement_signals(item_path, size, age)
        bloat = detect_bloat(item_path, size)

        skills.append({
            "name": item,
            "path": item_path,
            "age": age,
            "size": size,
            "retirement": retirement,
            "bloat": bloat,
        })

    # 统计
    retire_candidates = [s for s in skills if s["retirement"]["should_retire"]]
    bloat_candidates = [s for s in skills if s["bloat"]["is_bloated"]]

    return {
        "scan_path": skills_dir,
        "scan_time": datetime.now().isoformat(),
        "total_skills": len(skills),
        "retire_candidates": len(retire_candidates),
        "bloat_candidates": len(bloat_candidates),
        "skills": skills,
    }


def main():
    parser = argparse.ArgumentParser(description="技能生命周期管理工具——监控/退役/归档/膨胀检测/清理")
    sub = parser.add_subparsers(dest="command", required=True)

    # monitor
    p_mon = sub.add_parser("monitor", help="监控所有技能的生命周期状态")
    p_mon.add_argument("skills_dir", help="技能根目录路径")

    # retire
    p_ret = sub.add_parser("retire", help="检测应该退役的技能")
    p_ret.add_argument("skills_dir", help="技能根目录路径")

    # archive
    p_arch = sub.add_parser("archive", help="归档技能")
    p_arch.add_argument("skill_path", help="技能路径")
    p_arch.add_argument("--output", required=True, help="归档输出目录")

    # bloat
    p_bloat = sub.add_parser("bloat", help="上下文膨胀监控")
    p_bloat.add_argument("skills_dir", help="技能根目录路径")

    # cleanup
    p_clean = sub.add_parser("cleanup", help="清理建议（默认dry-run）")
    p_clean.add_argument("skills_dir", help="技能根目录路径")
    p_clean.add_argument("--dry-run", action="store_true", default=True, help="只显示建议，不执行")
    p_clean.add_argument("--execute", action="store_true", help="执行清理（谨慎使用）")

    args = parser.parse_args()

    if args.command == "monitor":
        result = monitor_lifecycle(args.skills_dir)
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        print(f"\n{'='*70}")
        print(f"技能生命周期监控: {result['scan_path']}")
        print(f"扫描时间: {result['scan_time']} | 总技能: {result['total_skills']}")
        print(f"退役候选: {result['retire_candidates']} | 膨胀候选: {result['bloat_candidates']}")
        print(f"{'='*70}")
        print(f"\n{'技能名称':30s} {'最后修改':12s} {'SKILL.md':7s} {'脚本':4s} {'文档':4s} {'退役':6s} {'膨胀':6s}")
        print(f"{'-'*70}")
        for s in result["skills"]:
            days = s["age"]["days_since_modified"] if s["age"] else "-"
            lines = s["size"]["skill_md_lines"] if s["size"] else "-"
            scripts = s["size"]["dir_counts"]["scripts"] if s["size"] else "-"
            refs = s["size"]["dir_counts"]["references"] if s["size"] else "-"
            ret_icon = "🔴" if s["retirement"]["should_retire"] else "⚠️" if s["retirement"]["retirement_score"] >= 3 else "✅"
            bloat_icon = "🔴" if s["bloat"]["is_bloated"] else "⚠️" if s["bloat"]["bloat_score"] >= 2 else "✅"
            print(f"{s['name']:30s} {days:>8}天前  {lines:>5}行  {scripts:>4}  {refs:>4}  {ret_icon}{s['retirement']['level']:4s}  {bloat_icon}{s['bloat']['level']:4s}")

    elif args.command == "retire":
        result = monitor_lifecycle(args.skills_dir)
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        retire_skills = [s for s in result["skills"] if s["retirement"]["should_retire"]]
        print(f"\n{'='*70}")
        print(f"退役技能检测: {result['scan_path']}")
        print(f"{'='*70}")
        if not retire_skills:
            print("✅ 没有发现应该退役的技能")
        else:
            print(f"⚠️  发现 {len(retire_skills)} 个应该退役的技能:")
            for s in retire_skills:
                print(f"\n🔴 {s['name']} (退役分数: {s['retirement']['retirement_score']})")
                print(f"   路径: {s['path']}")
                for sig in s["retirement"]["signals"]:
                    print(f"   - {sig}")
                print(f"   建议: 归档后删除，或合并到其他技能")

    elif args.command == "archive":
        result = archive_skill(args.skill_path, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "bloat":
        result = monitor_lifecycle(args.skills_dir)
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        bloat_skills = [s for s in result["skills"] if s["bloat"]["is_bloated"] or s["bloat"]["bloat_score"] >= 2]
        print(f"\n{'='*70}")
        print(f"上下文膨胀监控: {result['scan_path']}")
        print(f"{'='*70}")
        if not bloat_skills:
            print("✅ 没有发现膨胀的技能")
        else:
            print(f"⚠️  发现 {len(bloat_skills)} 个需要关注的技能:")
            for s in bloat_skills:
                print(f"\n{'🔴' if s['bloat']['is_bloated'] else '⚠️'} {s['name']} (膨胀分数: {s['bloat']['bloat_score']}, {s['bloat']['level']})")
                print(f"   总大小: {s['size']['total_size_mb']}MB | SKILL.md: {s['size']['skill_md_lines']}行")
                print(f"   脚本: {s['size']['dir_counts']['scripts']}个 | 文档: {s['size']['dir_counts']['references']}个")
                for issue in s["bloat"]["issues"]:
                    print(f"   - {issue}")

    elif args.command == "cleanup":
        result = monitor_lifecycle(args.skills_dir)
        if "error" in result:
            print(f"❌ {result['error']}")
            return

        print(f"\n{'='*70}")
        print(f"技能清理建议: {result['scan_path']}")
        print(f"模式: {'执行' if args.execute else 'Dry-run（只显示建议）'}")
        print(f"{'='*70}")

        retire_skills = [s for s in result["skills"] if s["retirement"]["should_retire"]]
        bloat_skills = [s for s in result["skills"] if s["bloat"]["is_bloated"]]

        if retire_skills:
            print(f"\n🔴 建议退役（{len(retire_skills)}个）:")
            for s in retire_skills:
                print(f"   - {s['name']}: {', '.join(s['retirement']['signals'][:2])}")

        if bloat_skills:
            print(f"\n🟡 建议优化（{len(bloat_skills)}个）:")
            for s in bloat_skills:
                print(f"   - {s['name']}: {', '.join(s['bloat']['issues'][:2])}")

        if not retire_skills and not bloat_skills:
            print("\n✅ 技能库健康，无需清理")

        if args.execute:
            print("\n⚠️  自动清理功能暂未实现，请根据上述建议手动操作")
        else:
            print(f"\n💡 如需执行清理，添加 --execute 参数（谨慎使用）")


if __name__ == "__main__":
    main()
