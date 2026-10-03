#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L7基准测试（有技能vs无技能质量对比）

量化skill-creator-pro的价值：对比用技能创建的技能 vs 手动创建的技能的质量差异。

对比维度:
1. 规范校验通过率
2. 深度审计评分
3. 必备层达标率
4. 脚本可运行率
5. SKILL.md核心要素完整率
6. 文件结构完整率
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


def run_script(script_name, *args, timeout=30):
    """运行脚本并返回结果"""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")
        return result
    except subprocess.TimeoutExpired:
        return None


def create_with_skill(output_dir, philosophy="mixed"):
    """用skill-creator-pro创建技能"""
    skill_name = "benchmark-with-skill"
    result = run_script("create_skill.py", "create", skill_name,
                        "--path", str(output_dir), "--philosophy", philosophy)
    if result and result.returncode == 0:
        return output_dir / skill_name
    return None


def create_without_skill(output_dir):
    """手动创建一个简单的技能（模拟不用技能的情况）"""
    skill_dir = output_dir / "benchmark-manual"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)

    # 简单的SKILL.md（很多要素缺失）
    skill_md = """---
name: benchmark-manual
description: "手动创建的测试技能"
---

# Benchmark Manual Skill

这是一个手动创建的技能，用于基准测试对比。

## 使用方法

直接运行脚本即可。
"""
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # 简单的脚本
    main_py = '''#!/usr/bin/env python3
"""手动创建的简单脚本"""
def main():
    print("Hello from manual skill")

if __name__ == "__main__":
    main()
'''
    (skill_dir / "scripts" / "main.py").write_text(main_py, encoding="utf-8")

    return skill_dir


def validate_skill(skill_path):
    """规范校验"""
    result = run_script("validate_skill.py", str(skill_path), "--json")
    if result and result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return {
                "success": data.get("success", False),
                "high": data.get("summary", {}).get("high", 0),
                "medium": data.get("summary", {}).get("medium", 0),
                "low": data.get("summary", {}).get("low", 0),
            }
        except json.JSONDecodeError:
            pass
    return {"success": False, "high": -1, "medium": -1, "low": -1}


def audit_skill(skill_path):
    """深度审计"""
    result = run_script("audit_skill.py", str(skill_path), "--json")
    if result and result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            tl = data.get("three_layer", {})
            return {
                "total_score": data.get("total_score", 0),
                "total_possible": data.get("total_possible", 36),
                "grade": data.get("grade", "?"),
                "required": tl.get("必备层", {}),
                "recommended": tl.get("推荐层", {}),
                "optional": tl.get("可选层", {}),
            }
        except json.JSONDecodeError:
            pass
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


def check_elements(skill_path):
    """检查SKILL.md核心要素"""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return {}
    content = skill_md.read_text(encoding="utf-8")
    elements = {
        "frontmatter": content.startswith("---"),
        "description": "description:" in content,
        "name": "name:" in content,
        "gotchas": "gotcha" in content.lower(),
        "workflow": "工作流" in content or "workflow" in content.lower(),
        "routing": "路由" in content or "routing" in content.lower(),
        "progressive_disclosure": "渐进式" in content or "progressive" in content.lower(),
        "hard_gate": "门禁" in content or "gate" in content.lower(),
        "references": "references/" in content,
        "scripts": "scripts/" in content,
    }
    return elements


def check_structure(skill_path):
    """检查文件结构完整性"""
    checks = {
        "SKILL.md": (skill_path / "SKILL.md").exists(),
        "scripts/": (skill_path / "scripts").is_dir(),
        "references/": (skill_path / "references").is_dir(),
        "has_script": len(list((skill_path / "scripts").glob("*.py"))) > 0 if (skill_path / "scripts").exists() else False,
        "has_reference": len(list((skill_path / "references").glob("*.md"))) > 0 if (skill_path / "references").exists() else False,
    }
    return checks


def evaluate_skill(skill_path, label):
    """综合评估一个技能"""
    print(f"\n{'─' * 60}")
    print(f"评估: {label}")
    print(f"{'─' * 60}")

    # 1. 规范校验
    validation = validate_skill(skill_path)
    print(f"  规范校验: {'✅ 通过' if validation['success'] else '❌ 未通过'} "
          f"(高:{validation['high']} 中:{validation['medium']} 低:{validation['low']})")

    # 2. 深度审计
    audit = audit_skill(skill_path)
    print(f"  深度审计: {audit.get('total_score', 0)}/{audit.get('total_possible', 36)} "
          f"({audit.get('grade', '?')})")
    req = audit.get("required", {})
    print(f"  必备层: {req.get('passed', 0)}/{req.get('total', 0)}")

    # 3. 脚本语法
    scripts_passed, scripts_total = check_scripts(skill_path)
    print(f"  脚本语法: {scripts_passed}/{scripts_total}")

    # 4. SKILL.md要素
    elements = check_elements(skill_path)
    elements_passed = sum(1 for v in elements.values() if v)
    elements_total = len(elements)
    print(f"  SKILL.md要素: {elements_passed}/{elements_total}")

    # 5. 文件结构
    structure = check_structure(skill_path)
    structure_passed = sum(1 for v in structure.values() if v)
    structure_total = len(structure)
    print(f"  文件结构: {structure_passed}/{structure_total}")

    return {
        "label": label,
        "validation": validation,
        "audit": audit,
        "scripts": {"passed": scripts_passed, "total": scripts_total},
        "elements": {"passed": elements_passed, "total": elements_total, "details": elements},
        "structure": {"passed": structure_passed, "total": structure_total, "details": structure},
    }


def main():
    print("=" * 70)
    print("L7基准测试（有技能vs无技能质量对比）")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # 创建两组技能
        print("\n1. 创建对比组...")
        with_skill_path = create_with_skill(output_dir)
        without_skill_path = create_without_skill(output_dir)

        if not with_skill_path:
            print("❌ 用技能创建失败")
            return 1

        # 评估两组
        with_result = evaluate_skill(with_skill_path, "有技能 (skill-creator-pro创建)")
        without_result = evaluate_skill(without_skill_path, "无技能 (手动创建)")

        # 对比分析
        print("\n" + "=" * 70)
        print("对比分析")
        print("=" * 70)

        comparisons = [
            ("规范校验", "✅ 通过" if with_result["validation"]["success"] else "❌ 未通过",
             "✅ 通过" if without_result["validation"]["success"] else "❌ 未通过"),
            ("深度审计", f"{with_result['audit'].get('total_score', 0)}/36",
             f"{without_result['audit'].get('total_score', 0)}/36"),
            ("必备层", f"{with_result['audit'].get('required', {}).get('passed', 0)}/20",
             f"{without_result['audit'].get('required', {}).get('passed', 0)}/20"),
            ("脚本语法", f"{with_result['scripts']['passed']}/{with_result['scripts']['total']}",
             f"{without_result['scripts']['passed']}/{without_result['scripts']['total']}"),
            ("SKILL.md要素", f"{with_result['elements']['passed']}/{with_result['elements']['total']}",
             f"{without_result['elements']['passed']}/{without_result['elements']['total']}"),
            ("文件结构", f"{with_result['structure']['passed']}/{with_result['structure']['total']}",
             f"{without_result['structure']['passed']}/{without_result['structure']['total']}"),
        ]

        print(f"\n{'维度':<15} {'有技能':<20} {'无技能':<20} {'提升'}")
        print("-" * 70)

        total_improvement = 0
        for dim, with_val, without_val in comparisons:
            # 计算提升
            try:
                with_num = int(with_val.split("/")[0]) if "/" in with_val else (1 if "✅" in with_val else 0)
                without_num = int(without_val.split("/")[0]) if "/" in without_val else (1 if "✅" in without_val else 0)
                improvement = with_num - without_num
                total_improvement += improvement
                improvement_str = f"+{improvement}" if improvement > 0 else str(improvement)
            except (ValueError, IndexError):
                improvement_str = "?"

            print(f"{dim:<15} {with_val:<20} {without_val:<20} {improvement_str}")

        # 综合评分
        with_score = with_result["audit"].get("total_score", 0)
        without_score = without_result["audit"].get("total_score", 0)
        score_improvement = with_score - without_score

        print(f"\n{'=' * 70}")
        print(f"综合提升: +{score_improvement}分 ({with_score}/36 vs {without_score}/36)")
        print(f"提升率: {score_improvement/without_score*100:.0f}%" if without_score > 0 else "提升率: N/A")
        print(f"{'=' * 70}")

        # 结论
        if score_improvement > 0:
            print(f"\n✅ 结论: skill-creator-pro能显著提升技能质量 (+{score_improvement}分)")
        else:
            print(f"\n⚠️ 结论: skill-creator-pro未显著提升技能质量")

        # 保存结果
        benchmark_result = {
            "with_skill": with_result,
            "without_skill": without_result,
            "score_improvement": score_improvement,
            "total_improvement": total_improvement,
        }

        output_file = SKILL_ROOT / "l7-benchmark-results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(benchmark_result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存: {output_file}")

        return 0 if score_improvement > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
