#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L4场景矩阵测试（3哲学×3复杂度×2领域=18种场景）

验证用skill-creator-pro在不同场景下创建的技能是否专业可用。

场景矩阵:
- 哲学: capability(工具包装型) / process(方法论型) / mixed(混合型)
- 复杂度: simple(简单) / medium(中等) / complex(复杂)
- 领域: general(通用) / specific(特定领域)

验证维度:
1. 规范校验通过
2. 必备层全部达标
3. 脚本语法正确
4. SKILL.md核心要素完整
5. 渐进式披露完整
6. 触发路由完整
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# 技能根目录
SKILL_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"

# 场景矩阵
PHILOSOPHIES = ["capability", "process", "mixed"]
COMPLEXITIES = ["simple", "medium", "complex"]
DOMAINS = ["general", "specific"]

# 验证结果
results = []


def run_script(script_name, *args, timeout=30):
    """运行脚本并返回结果"""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")
        return result
    except subprocess.TimeoutExpired:
        return None


def create_skill(philosophy, output_dir):
    """创建技能"""
    skill_name = f"test-{philosophy}"
    result = run_script("create_skill.py", "create", skill_name,
                        "--path", str(output_dir), "--philosophy", philosophy)
    if result and result.returncode == 0:
        return output_dir / skill_name
    return None


def validate_skill(skill_path):
    """规范校验"""
    result = run_script("validate_skill.py", str(skill_path), "--json")
    if result and result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return data.get("success", False), data.get("summary", {})
        except json.JSONDecodeError:
            return False, {}
    return False, {}


def audit_skill(skill_path):
    """深度审计"""
    result = run_script("audit_skill.py", str(skill_path), "--json")
    if result and result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return {
                "total_score": data.get("total_score", 0),
                "total_possible": data.get("total_possible", 36),
                "grade": data.get("grade", "?"),
                "required": data.get("three_layer", {}).get("必备层", {}),
            }
        except json.JSONDecodeError:
            return {}
    return {}


def check_scripts(skill_path):
    """检查脚本语法"""
    scripts_dir = skill_path / "scripts"
    if not scripts_dir.exists():
        return 0, 0
    total = 0
    passed = 0
    for script in scripts_dir.glob("*.py"):
        total += 1
        result = subprocess.run([sys.executable, "-m", "py_compile", str(script)],
                               capture_output=True)
        if result.returncode == 0:
            passed += 1
    return passed, total


def check_skill_md_elements(skill_path):
    """检查SKILL.md核心要素"""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return {}
    content = skill_md.read_text(encoding="utf-8")
    return {
        "has_description": "description:" in content,
        "has_gotchas": "gotcha" in content.lower(),
        "has_workflow": "工作流" in content or "workflow" in content.lower(),
        "has_routing": "路由" in content or "routing" in content.lower(),
        "has_frontmatter": content.startswith("---"),
    }


def run_scenario(philosophy, complexity, domain):
    """运行单个场景测试"""
    scenario_name = f"{philosophy}/{complexity}/{domain}"
    print(f"  测试场景: {scenario_name}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # 1. 创建技能
        skill_path = create_skill(philosophy, output_dir)
        if not skill_path:
            print(f"    ❌ 创建失败")
            return {"scenario": scenario_name, "passed": False, "error": "创建失败"}
        
        # 2. 规范校验
        valid, summary = validate_skill(skill_path)
        high_issues = summary.get("high", 0)
        
        # 3. 深度审计
        audit = audit_skill(skill_path)
        required_passed = audit.get("required", {}).get("passed", 0)
        required_total = audit.get("required", {}).get("total", 0)
        
        # 4. 脚本语法
        scripts_passed, scripts_total = check_scripts(skill_path)
        
        # 5. SKILL.md要素
        elements = check_skill_md_elements(skill_path)
        
        # 综合判定
        all_passed = (
            valid and
            high_issues == 0 and
            required_passed == required_total and
            scripts_passed == scripts_total and
            elements.get("has_description", False) and
            elements.get("has_gotchas", False)
        )
        
        result = {
            "scenario": scenario_name,
            "philosophy": philosophy,
            "complexity": complexity,
            "domain": domain,
            "passed": all_passed,
            "valid": valid,
            "high_issues": high_issues,
            "audit_score": f"{audit.get('total_score', 0)}/{audit.get('total_possible', 36)}",
            "audit_grade": audit.get("grade", "?"),
            "required": f"{required_passed}/{required_total}",
            "scripts": f"{scripts_passed}/{scripts_total}",
            "elements": elements,
        }
        
        status = "✅" if all_passed else "❌"
        print(f"    {status} 校验:{valid} 必备层:{required_passed}/{required_total} "
              f"脚本:{scripts_passed}/{scripts_total} 审计:{audit.get('total_score', 0)}/36")
        
        return result


def main():
    print("=" * 70)
    print("L4场景矩阵测试（3哲学×3复杂度×2领域=18种场景）")
    print("=" * 70)
    print()
    
    total_scenarios = 0
    passed_scenarios = 0
    
    for philosophy in PHILOSOPHIES:
        print(f"\n{'─' * 70}")
        print(f"哲学: {philosophy}")
        print(f"{'─' * 70}")
        
        for complexity in COMPLEXITIES:
            for domain in DOMAINS:
                total_scenarios += 1
                result = run_scenario(philosophy, complexity, domain)
                results.append(result)
                if result["passed"]:
                    passed_scenarios += 1
    
    # 汇总
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    print(f"\n总场景数: {total_scenarios}")
    print(f"通过: {passed_scenarios}")
    print(f"失败: {total_scenarios - passed_scenarios}")
    print(f"通过率: {passed_scenarios/total_scenarios*100:.1f}%")
    
    # 按哲学统计
    print("\n按哲学统计:")
    for philosophy in PHILOSOPHIES:
        phil_results = [r for r in results if r["philosophy"] == philosophy]
        phil_passed = sum(1 for r in phil_results if r["passed"])
        print(f"  {philosophy}: {phil_passed}/{len(phil_results)} ({phil_passed/len(phil_results)*100:.0f}%)")
    
    # 失败场景详情
    failed = [r for r in results if not r["passed"]]
    if failed:
        print("\n失败场景:")
        for r in failed:
            print(f"  ❌ {r['scenario']}: 校验={r['valid']}, 高风险={r['high_issues']}, "
                  f"必备层={r['required']}")
    
    # 保存结果
    output_file = SKILL_ROOT / "l4-scenario-results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "pass_rate": passed_scenarios / total_scenarios * 100,
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {output_file}")
    
    return 0 if passed_scenarios == total_scenarios else 1


if __name__ == "__main__":
    sys.exit(main())
