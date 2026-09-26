#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能版本管理器（version_manager.py）

自动管理技能版本号（semver: MAJOR.MINOR.PATCH），
生成changelog，检测破坏性变更。

用法：
  python3 version_manager.py status <skill-path>       # 查看当前版本
  python3 version_manager.py bump <skill-path> --type patch   # 补丁+1
  python3 version_manager.py bump <skill-path> --type minor   # 次版本+1
  python3 version_manager.py bump <skill-path> --type major   # 主版本+1
  python3 version_manager.py changelog <skill-path>           # 生成changelog
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime


def read_skill_md(skill_path):
    """读取SKILL.md"""
    md_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(md_path):
        return None
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_version(content):
    """从SKILL.md提取版本号"""
    # 匹配各种版本格式
    patterns = [
        r'v(\d+)\.(\d+)\.(\d+)',  # v1.0.0
        r'版本[：:]\s*v?(\d+)\.(\d+)\.(\d+)',  # 版本: v1.0.0
        r'Version[：:]\s*v?(\d+)\.(\d+)\.(\d+)',  # Version: v1.0.0
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return 0, 0, 0


def detect_breaking_changes(skill_path):
    """检测破坏性变更"""
    issues = []
    scripts_dir = os.path.join(skill_path, "scripts")
    refs_dir = os.path.join(skill_path, "references")

    # 检查scripts目录是否有文件被删除
    # （简单检查：如果scripts目录为空但SKILL.md引用了脚本）
    md = read_skill_md(skill_path) or ""
    script_refs = re.findall(r'scripts/(\w+\.py)', md)
    for s in script_refs:
        if not os.path.isfile(os.path.join(scripts_dir, s)):
            issues.append(f"SKILL.md引用了scripts/{s}但文件不存在")

    # 检查references引用
    ref_refs = re.findall(r'references/([\w-]+\.md)', md)
    for r in ref_refs:
        if not os.path.isfile(os.path.join(refs_dir, r)):
            issues.append(f"SKILL.md引用了references/{r}但文件不存在")

    return issues


def bump_version(current, bump_type):
    """版本号+1"""
    major, minor, patch = current
    if bump_type == "major":
        return major + 1, 0, 0
    elif bump_type == "minor":
        return major, minor + 1, 0
    else:  # patch
        return major, minor, patch + 1


def update_skill_md_version(skill_path, new_version):
    """更新SKILL.md中的版本号"""
    md_path = os.path.join(skill_path, "SKILL.md")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    major, minor, patch = new_version
    new_ver_str = f"v{major}.{minor}.{patch}"

    # 替换版本行
    patterns = [
        (r'(版本[：:]\s*)v?\d+\.\d+\.\d+', rf'\g<1>{new_ver_str}'),
        (r'(Version[：:]\s*)v?\d+\.\d+\.\d+', rf'\g<1>{new_ver_str}'),
    ]

    updated = content
    for pat, repl in patterns:
        updated = re.sub(pat, repl, updated, flags=re.IGNORECASE)

    if updated != content:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(updated)
        return True
    return False


def generate_changelog(skill_path, new_version, changes=None):
    """生成CHANGELOG"""
    major, minor, patch = new_version
    ver_str = f"v{major}.{minor}.{patch}"
    date = datetime.now().strftime("%Y-%m-%d")

    changelog_path = os.path.join(skill_path, "CHANGELOG.md")

    entry = f"""## {ver_str} ({date})

"""
    if changes:
        for c in changes:
            entry += f"- {c}\n"
    else:
        entry += "- 版本更新\n"

    entry += "\n---\n\n"

    # 追加到文件头部
    if os.path.isfile(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            old = f.read()
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(entry + old)
    else:
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(f"# Changelog\n\n{entry}")

    return changelog_path


def main():
    parser = argparse.ArgumentParser(description="技能版本管理器")
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status")

    # bump
    bump_p = sub.add_parser("bump")
    bump_p.add_argument("--type", choices=["patch", "minor", "major"], default="patch")
    bump_p.add_argument("--changes", nargs="*", help="变更描述")

    # changelog
    sub.add_parser("changelog")

    for p in sub.choices.values():
        p.add_argument("skill_path", help="技能目录路径")

    args = parser.parse_args()

    content = read_skill_md(args.skill_path)
    if content is None:
        print("❌ SKILL.md不存在", file=sys.stderr)
        sys.exit(1)

    current = extract_version(content)
    breaking = detect_breaking_changes(args.skill_path)

    if args.command == "status":
        print(f"当前版本: v{current[0]}.{current[1]}.{current[2]}")
        if breaking:
            print(f"\n⚠️ 破坏性变更检测:")
            for b in breaking:
                print(f"  - {b}")
        else:
            print("✅ 无破坏性变更")

    elif args.command == "bump":
        new_ver = bump_version(current, args.type)
        updated = update_skill_md_version(args.skill_path, new_ver)
        if updated:
            print(f"✅ 版本更新: v{current[0]}.{current[1]}.{current[2]} → v{new_ver[0]}.{new_ver[1]}.{new_ver[2]}")
        else:
            print("⚠️ 未找到版本号，未更新")

        if args.changes:
            cl = generate_changelog(args.skill_path, new_ver, args.changes)
            print(f"✅ Changelog已生成: {cl}")

    elif args.command == "changelog":
        cl = generate_changelog(args.skill_path, current, args.changes or [])
        print(f"✅ Changelog已生成: {cl}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
