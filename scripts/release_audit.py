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
import subprocess
import sys

# 技能根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")


def run_command(cmd, description, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd or SKILL_ROOT,
            timeout=120
        )
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


def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 发布前审计脚本（8大门禁，全部通过才能发布）"
    )
    parser.add_argument("--skill", default=SKILL_ROOT, help="要审计的技能目录路径（默认当前技能）")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试（不推荐）")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    if not os.path.isdir(args.skill):
        print(f"❌ 技能目录不存在: {args.skill}", file=sys.stderr)
        sys.exit(1)

    result = audit_skill(args.skill, skip_tests=args.skip_tests)

    if args.json:
        print("\n" + json.dumps(result, ensure_ascii=False, indent=2))

    # 保存审计报告
    report_path = os.path.join(SKILL_ROOT, "release-audit.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n📄 审计报告已保存: {report_path}")

    sys.exit(0 if result["all_passed"] else 1)


if __name__ == "__main__":
    main()
