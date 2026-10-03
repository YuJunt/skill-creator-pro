#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-creator-pro 发布前审计脚本（借鉴agent-plugin-creator的release_audit）

发布前必须运行的8大门禁检查，全部通过才能发布。
任何一项失败都会阻止发布（exit 1）。

8大门禁：
  1. 规范校验（validate_skill.py）
  2. 深度审计（audit_skill.py）- 必备层必须100%达标
  3. 安全扫描（security_scan.py）- 高风险必须为0
  4. 输出校验（output_validator.py）
  5. 单元测试（pytest）- 全部通过
  6. 集成测试（pytest tests/test_e2e_integration.py）
  7. Git工作区干净（无未提交修改）
  8. 版本号一致性检查

用法：
  python3 scripts/release_audit.py                    # 审计当前技能
  python3 scripts/release_audit.py --skill <path>    # 审计指定技能
  python3 scripts/release_audit.py --skip-tests       # 跳过测试（不推荐）
  python3 scripts/release_audit.py --json             # JSON格式输出
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

# 技能根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")


def run_command(cmd, description, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd or SKILL_ROOT,
            timeout=120, encoding="utf-8")
        return {
            "name": description,
            "cmd": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "name": description,
            "cmd": " ".join(cmd),
            "returncode": -1,
            "stdout": "",
            "stderr": "命令超时（120秒）",
            "passed": False,
        }
    except Exception as e:
        return {
            "name": description,
            "cmd": " ".join(cmd),
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "passed": False,
        }


def audit_skill(skill_path, skip_tests=False):
    """执行发布前审计"""
    results = []
    print("\n" + "=" * 60)
    print("🔒 发布前审计（Release Audit）")
    print("=" * 60)
    print(f"\n📂 审计目标: {skill_path}")
    print(f"⏭️  跳过测试: {'是' if skip_tests else '否'}")

    # 门禁1：规范校验
    print("\n--- 门禁1/8: 规范校验 ---")
    r = run_command(
        [sys.executable, os.path.join(SCRIPTS_DIR, "validate_skill.py"), skill_path],
        "规范校验"
    )
    results.append(r)
    print(f"  {'✅' if r['passed'] else '❌'} 规范校验: {'通过' if r['passed'] else '失败'}")
    if not r["passed"]:
        print(f"  错误: {r['stderr'][:200]}")

    # 门禁2：深度审计（必备层必须100%达标）
    print("\n--- 门禁2/8: 深度审计（必备层硬门禁） ---")
    r = run_command(
        [sys.executable, os.path.join(SCRIPTS_DIR, "audit_skill.py"), skill_path],
        "深度审计"
    )
    # 检查必备层是否全部达标
    required_pass = "必备层" in r["stdout"] and ("20/20" in r["stdout"] or "全部达标" in r["stdout"])
    r["passed"] = r["returncode"] == 0 and required_pass
    results.append(r)
    print(f"  {'✅' if r['passed'] else '❌'} 深度审计: {'通过' if r['passed'] else '失败'}")
    if not required_pass:
        print(f"  ⚠️  必备层未100%达标，必须修复后才能发布")

    # 门禁3：安全扫描（高风险必须为0）
    print("\n--- 门禁3/8: 安全扫描（高风险硬门禁） ---")
    r = run_command(
        [sys.executable, os.path.join(SCRIPTS_DIR, "security_scan.py"), skill_path],
        "安全扫描"
    )
    # 检查高风险是否为0
    high_risk_zero = "高风险: 0" in r["stdout"]
    r["passed"] = r["returncode"] == 0 and high_risk_zero
    results.append(r)
    print(f"  {'✅' if r['passed'] else '❌'} 安全扫描: {'通过' if r['passed'] else '失败'}")
    if not high_risk_zero:
        print(f"  ⚠️  存在高风险问题，必须修复后才能发布")

    # 门禁4：输出校验
    print("\n--- 门禁4/8: 输出校验 ---")
    r = run_command(
        [sys.executable, os.path.join(SCRIPTS_DIR, "output_validator.py"), skill_path],
        "输出校验"
    )
    results.append(r)
    print(f"  {'✅' if r['passed'] else '❌'} 输出校验: {'通过' if r['passed'] else '失败'}")

    # 门禁5：单元测试
    if not skip_tests:
        print("\n--- 门禁5/8: 单元测试 ---")
        r = run_command(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
            "单元测试"
        )
        results.append(r)
        print(f"  {'✅' if r['passed'] else '❌'} 单元测试: {'通过' if r['passed'] else '失败'}")
        if not r["passed"]:
            print(f"  输出: {r['stdout'][-300:]}")

        # 门禁6：集成测试
        print("\n--- 门禁6/8: 集成测试 ---")
        r = run_command(
            [sys.executable, "-m", "pytest", "tests/test_e2e_integration.py", "-q", "--tb=short"],
            "集成测试"
        )
        results.append(r)
        print(f"  {'✅' if r['passed'] else '❌'} 集成测试: {'通过' if r['passed'] else '失败'}")
    else:
        print("\n--- 门禁5-6/8: 测试（已跳过） ---")
        print("  ⏭️  已跳过单元测试和集成测试（不推荐）")

    # 门禁7：Git工作区干净
    print("\n--- 门禁7/8: Git工作区干净 ---")
    r = run_command(["git", "status", "--porcelain"], "Git状态检查")
    clean = r["stdout"].strip() == ""
    r["passed"] = clean
    results.append(r)
    print(f"  {'✅' if clean else '⚠️'} Git工作区: {'干净' if clean else '有未提交修改'}")
    if not clean:
        print(f"  未提交文件:\n{r['stdout'][:500]}")

    # 门禁8：版本号一致性
    print("\n--- 门禁8/8: 版本号一致性 ---")
    version_consistent = True
    version = ""
    try:
        with open(os.path.join(skill_path, "SKILL.md"), "r", encoding="utf-8") as f:
            content = f.read()
        # 提取版本号
        import re
        match = re.search(r"版本[：:]\s*v?([\d.]+)", content)
        if match:
            version = match.group(1)
        # 检查CHANGELOG是否有对应版本
        changelog_path = os.path.join(skill_path, "CHANGELOG.md")
        if os.path.isfile(changelog_path):
            with open(changelog_path, "r", encoding="utf-8") as f:
                changelog = f.read()
            if version and version not in changelog:
                version_consistent = False
                print(f"  ⚠️  CHANGELOG中未找到版本 v{version}")
    except Exception as e:
        version_consistent = False
        print(f"  ⚠️  版本检查异常: {e}")

    r = {"name": "版本号一致性", "passed": version_consistent, "version": version}
    results.append(r)
    print(f"  {'✅' if version_consistent else '⚠️'} 版本号一致性: {'一致' if version_consistent else '不一致'}")
    if version:
        print(f"  当前版本: v{version}")

    # 汇总
    print("\n" + "=" * 60)
    print("📊 审计结果汇总")
    print("=" * 60)

    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    all_passed = all(r["passed"] for r in results)

    for i, r in enumerate(results, 1):
        icon = "✅" if r["passed"] else "❌"
        print(f"  {i}. {icon} {r['name']}")

    print(f"\n  通过: {passed_count}/{total_count}")
    print(f"  状态: {'🎉 全部通过，可以发布' if all_passed else '❌ 存在失败项，禁止发布'}")

    if not all_passed:
        print(f"\n  🔴 失败项:")
        for r in results:
            if not r["passed"]:
                print(f"    - {r['name']}")

    return {
        "skill_path": skill_path,
        "total": total_count,
        "passed": passed_count,
        "all_passed": all_passed,
        "results": [{"name": r["name"], "passed": r["passed"]} for r in results],
    }


# ============================================================
# 版本管理功能（合并自version_manager.py）
# ============================================================

def read_skill_md(skill_path):
    """读取SKILL.md"""
    md_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(md_path):
        return None
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_version(content):
    """从SKILL.md提取版本号"""
    patterns = [
        r'v(\d+)\.(\d+)\.(\d+)',
        r'版本[：:]\s*v?(\d+)\.(\d+)\.(\d+)',
        r'Version[：:]\s*v?(\d+)\.(\d+)\.(\d+)',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return 0, 0, 0


def bump_version(current, bump_type):
    """版本号+1"""
    major, minor, patch = current
    if bump_type == "major":
        return major + 1, 0, 0
    elif bump_type == "minor":
        return major, minor + 1, 0
    else:
        return major, minor, patch + 1


def update_skill_md_version(skill_path, new_version):
    """更新SKILL.md中的版本号"""
    md_path = os.path.join(skill_path, "SKILL.md")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    major, minor, patch = new_version
    new_ver_str = f"v{major}.{minor}.{patch}"
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


def cmd_version_status(skill_path):
    """查看当前版本"""
    content = read_skill_md(skill_path)
    if content is None:
        print("❌ SKILL.md不存在", file=sys.stderr)
        return 1
    current = extract_version(content)
    print(f"当前版本: v{current[0]}.{current[1]}.{current[2]}")
    print("✅ 无破坏性变更")
    return 0


def cmd_version_bump(skill_path, bump_type, changes=None):
    """版本号+1"""
    content = read_skill_md(skill_path)
    if content is None:
        print("❌ SKILL.md不存在", file=sys.stderr)
        return 1
    current = extract_version(content)
    new_ver = bump_version(current, bump_type)
    updated = update_skill_md_version(skill_path, new_ver)
    if updated:
        print(f"✅ 版本更新: v{current[0]}.{current[1]}.{current[2]} → v{new_ver[0]}.{new_ver[1]}.{new_ver[2]}")
    else:
        print("⚠️ 未找到版本号，未更新")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 发布工具（审计+版本管理，合并自version_manager.py）"
    )
    sub = parser.add_subparsers(dest="command")

    # audit（默认命令）
    audit_p = sub.add_parser("audit", help="发布前审计（8大门禁）")
    audit_p.add_argument("--skill", default=SKILL_ROOT, help="要审计的技能目录路径")
    audit_p.add_argument("--skip-tests", action="store_true", help="跳过测试（不推荐）")
    audit_p.add_argument("--json", action="store_true", help="JSON格式输出")

    # version status
    status_p = sub.add_parser("status", help="查看当前版本")
    status_p.add_argument("skill_path", nargs="?", default=SKILL_ROOT, help="技能目录路径")

    # version bump
    bump_p = sub.add_parser("bump", help="版本号+1")
    bump_p.add_argument("skill_path", nargs="?", default=SKILL_ROOT, help="技能目录路径")
    bump_p.add_argument("--type", choices=["patch", "minor", "major"], default="patch")

    args = parser.parse_args()

    # 默认执行audit
    if args.command is None or args.command == "audit":
        skill = getattr(args, "skill", SKILL_ROOT)
        if not os.path.isdir(skill):
            print(f"❌ 技能目录不存在: {skill}", file=sys.stderr)
            sys.exit(1)
        result = audit_skill(skill, skip_tests=getattr(args, "skip_tests", False))
        if getattr(args, "json", False):
            print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
        report_path = os.path.join(SKILL_ROOT, "release-audit.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n📄 审计报告已保存: {report_path}")
        sys.exit(0 if result["all_passed"] else 1)

    elif args.command == "status":
        sys.exit(cmd_version_status(args.skill_path))

    elif args.command == "bump":
        sys.exit(cmd_version_bump(args.skill_path, args.type))

    else:
        parser.print_help()
        sys.exit(1)



# ===== UTF-8 输出兼容（Windows cp1252 无法输出 emoji，统一 UTF-8） =====
try:
    import sys as _sys
    for _s in (_sys.stdout, _sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
except Exception:
    pass

if __name__ == "__main__":
    main()
