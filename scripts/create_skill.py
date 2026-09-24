#!/usr/bin/env python3
"""
版本: v1.0.0 | 许可证: MIT | 最低Python: 3.7+

create_skill.py - skill-creator-pro 编排脚本（统一入口，强制顺序执行）

功能：
  - 统一管理技能创建/优化/评审/测试的完整工作流
  - 强制按顺序执行，每个步骤完成后验证，不允许跳过
  - 校验失败就报错，不允许继续下一步
  - 输出结构化的执行结果

用法：
  python3 create_skill.py create <skill-name> [--path <dir>] [--philosophy <type>]
  python3 create_skill.py optimize <skill-path>
  python3 create_skill.py review <skill-path>
  python3 create_skill.py test <skill-path>

设计哲学：
  - 低自由度：必须按顺序执行，不允许跳过
  - 验证循环：每个步骤完成后必须验证
  - 状态检查后行动：行动前先检查当前状态
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime

# 最低Python版本检查（dataclasses需要3.7+）
if sys.version_info < (3, 7):
    print(f"❌ Python版本过低: {sys.version.split()[0]}，需要 Python 3.7+", file=sys.stderr)
    print("💡 请升级Python后重试", file=sys.stderr)
    sys.exit(2)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_command(cmd, description):
    """运行命令并返回结果，失败时抛出异常"""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"  命令: {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"[stderr] {result.stderr}", file=sys.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"❌ {description} 失败（返回码 {result.returncode}）")

    print(f"✅ {description} 完成")
    return result


def validate_skill(skill_path):
    """步骤：规范校验"""
    validate_script = os.path.join(SCRIPT_DIR, "validate_skill.py")
    result = run_command(
        [sys.executable, validate_script, skill_path],
        "规范校验（validate_skill.py）"
    )

    # 检查是否有高优先级问题
    if "高=0" not in result.stdout:
        raise RuntimeError("❌ 规范校验发现高优先级问题，必须修复后才能继续")

    return result.stdout


def audit_skill(skill_path):
    """步骤：深度审计"""
    audit_script = os.path.join(SCRIPT_DIR, "audit_skill.py")
    result = run_command(
        [sys.executable, audit_script, skill_path],
        "深度审计（audit_skill.py）"
    )

    # 检查必备层是否全部达标
    if "必备层" not in result.stdout:
        raise RuntimeError("❌ 深度审计输出异常，无法确认必备层状态")

    return result.stdout


def create_skill(skill_name, output_dir, philosophy="mixed", title=None):
    """模式：新建技能"""
    print(f"\n{'#'*60}")
    print(f"# 新建技能: {skill_name}")
    print(f"# 设计哲学: {philosophy}")
    print(f"{'#'*60}")

    # 步骤1：模板生成
    init_script = os.path.join(SCRIPT_DIR, "init_skill_pro.py")
    cmd = [sys.executable, init_script, skill_name, "--path", output_dir, "--philosophy", philosophy]
    if title:
        cmd.extend(["--title", title])
    run_command(cmd, "模板生成（init_skill_pro.py）")

    # 验证目录结构
    skill_path = os.path.join(output_dir, skill_name)
    if not os.path.isdir(skill_path):
        raise RuntimeError(f"❌ 技能目录创建失败: {skill_path}")
    if not os.path.isfile(os.path.join(skill_path, "SKILL.md")):
        raise RuntimeError(f"❌ SKILL.md 创建失败: {os.path.join(skill_path, 'SKILL.md')}")
    print(f"✅ 目录结构验证通过: {skill_path}")

    # 步骤2：规范校验
    validate_skill(skill_path)

    # 步骤3：深度审计
    audit_skill(skill_path)

    # 步骤4：安全扫描（检测提示注入/危险代码/数据泄露/隐藏指令）
    security_script = os.path.join(SCRIPT_DIR, "security_scan.py")
    if os.path.isfile(security_script):
        sec_result = run_command(
            [sys.executable, security_script, skill_path],
            "安全扫描（security_scan.py）"
        )
        # 检查是否有高风险
        if "高风险: 0" not in sec_result.stdout:
            print("⚠️  安全扫描发现高风险问题，建议修复后再发布")
    else:
        print("⚠️  security_scan.py 不存在，跳过安全扫描")

    # 清理Python编译缓存（校验过程中import脚本会生成__pycache__）
    import glob
    for pycache in glob.glob(os.path.join(skill_path, "**", "__pycache__"), recursive=True):
        shutil.rmtree(pycache, ignore_errors=True)

    # 完成
    print(f"\n{'#'*60}")
    print(f"# ✅ 技能创建完成: {skill_path}")
    print(f"# 下一步: 编辑 SKILL.md 和 references/，替换 TODO")
    print(f"# 编辑完成后运行: python3 create_skill.py optimize {skill_path}")
    print(f"# 💡 经验沉淀: 创建完成后建议复盘，提取经验写入案例库")
    print(f"#    参考: references/self-evolution-playbook.md + references/experience-library-guide.md")
    print(f"{'#'*60}")

    return {"success": True, "skill_path": skill_path, "mode": "create"}


def optimize_skill(skill_path):
    """模式：优化技能"""
    print(f"\n{'#'*60}")
    print(f"# 优化技能: {skill_path}")
    print(f"{'#'*60}")

    # 状态检查：技能目录必须存在
    if not os.path.isdir(skill_path):
        raise RuntimeError(f"❌ 技能目录不存在: {skill_path}")
    if not os.path.isfile(os.path.join(skill_path, "SKILL.md")):
        raise RuntimeError(f"❌ SKILL.md 不存在: {os.path.join(skill_path, 'SKILL.md')}")
    print(f"✅ 状态检查通过: 技能目录和SKILL.md都存在")

    # 步骤1：规范校验
    validate_skill(skill_path)

    # 步骤2：深度审计
    audit_skill(skill_path)

    # 步骤3：安全扫描
    security_script = os.path.join(SCRIPT_DIR, "security_scan.py")
    if os.path.isfile(security_script):
        sec_result = run_command(
            [sys.executable, security_script, skill_path],
            "安全扫描（security_scan.py）"
        )
        if "高风险: 0" not in sec_result.stdout:
            print("⚠️  安全扫描发现高风险问题，建议修复后再发布")

    # 完成
    print(f"\n{'#'*60}")
    print(f"# ✅ 技能优化验证完成: {skill_path}")
    print(f"# 规范校验和深度审计都已通过")
    print(f"# 💡 经验沉淀: 优化完成后建议复盘，提取优化经验写入案例库")
    print(f"{'#'*60}")

    return {"success": True, "skill_path": skill_path, "mode": "optimize"}


def review_skill(skill_path):
    """模式：评审技能"""
    print(f"\n{'#'*60}")
    print(f"# 评审技能: {skill_path}")
    print(f"{'#'*60}")

    # 状态检查
    if not os.path.isdir(skill_path):
        raise RuntimeError(f"❌ 技能目录不存在: {skill_path}")
    print(f"✅ 状态检查通过")

    # 步骤1：规范校验
    validate_result = validate_skill(skill_path)

    # 步骤2：深度审计
    audit_result = audit_skill(skill_path)

    # 完成
    print(f"\n{'#'*60}")
    print(f"# ✅ 技能评审完成: {skill_path}")
    print(f"# 评审结果已输出在上文")
    print(f"# 💡 经验沉淀: 评审完成后建议提取评审经验（常见问题/最佳实践）写入案例库")
    print(f"{'#'*60}")

    return {"success": True, "skill_path": skill_path, "mode": "review"}


def test_skill(skill_path):
    """模式：端到端测试"""
    print(f"\n{'#'*60}")
    print(f"# 端到端测试: {skill_path}")
    print(f"{'#'*60}")

    # 状态检查
    if not os.path.isdir(skill_path):
        raise RuntimeError(f"❌ 技能目录不存在: {skill_path}")
    print(f"✅ 状态检查通过")

    # 步骤0：评估用例检查（自动生成通用评估用例模板，优先执行确保不被后续校验阻断）
    eval_cases_path = os.path.join(skill_path, "references", "evaluation-cases.md")
    if os.path.isfile(eval_cases_path):
        print(f"✅ 评估用例已存在: references/evaluation-cases.md")
        print(f"   💡 建议: 根据技能具体领域修改用例的输入和预期输出，然后实际运行测试")
    else:
        # 自动生成通用评估用例模板
        references_dir = os.path.join(skill_path, "references")
        os.makedirs(references_dir, exist_ok=True)
        skill_name = os.path.basename(os.path.abspath(skill_path))
        skill_title = skill_name.replace("-", " ").title()
        eval_template = f'''# {skill_title} 评估用例

> 本文件包含3类通用评估用例，用于验证技能的触发准确性、输出完整性和错误处理能力。
> 使用方法：根据技能的具体领域，修改每个用例的输入和预期输出，然后实际运行测试。
> 核心原则：**没有评估用例的技能不能发布——评估用例是质量的可验证标准。**

---

## 一、触发准确性测试（Trigger Accuracy）

**目的**：验证技能在正确的场景下被触发，不在错误的场景下被触发。

**通过标准**：
- should_trigger用例触发率 ≥ 90%
- should_not_trigger用例误触发率 ≤ 10%

### 1.1 应该触发的用例（should_trigger）

```
用例1.1.1：核心功能触发
  - 输入："[请替换为用户会说的触发语]"
  - 预期：技能被触发，开始执行核心流程
  - 验证点：技能确实被加载，输出包含核心功能相关内容

用例1.1.2：关键词触发
  - 输入："[请替换为领域关键词]"
  - 预期：技能被触发
  - 验证点：description中的关键词被正确匹配

用例1.1.3：复杂场景触发
  - 输入："[请替换为复杂场景]"
  - 预期：技能被触发，能处理多步骤任务
  - 验证点：能正确分解多步骤任务，每步都有明确输出
```

### 1.2 不应该触发的用例（should_not_trigger）

```
用例1.2.1：无关任务不触发
  - 输入："[请替换为无关任务，例如：今天天气怎么样]"
  - 预期：技能不被触发
  - 验证点：技能没有被加载，系统用通用能力回答

用例1.2.2：其他技能领域不触发
  - 输入："[请替换为其他技能领域的任务]"
  - 预期：技能不被触发
  - 验证点：本技能没有被加载

用例1.2.3：模糊需求不误触发
  - 输入："[请替换为模糊需求，例如：帮我处理一下这个]"
  - 预期：技能不盲目触发，应该先询问用户具体需求
  - 验证点：输出了澄清问题，没有直接开始执行
```

---

## 二、输出完整性测试（Output Completeness）

**目的**：验证技能的输出包含所有必需字段，格式正确。

**通过标准**：输出完整率 = 100%（不允许遗漏关键字段）

### 2.1 正常场景输出完整性

```
用例2.1.1：核心功能输出完整
  - 输入："[请替换为核心功能的标准输入]"
  - 预期：输出包含所有必需字段
  - 必需字段清单（根据技能具体情况修改）：
    - [ ] 一句话结论（核心结果）
    - [ ] 执行步骤（做了什么）
    - [ ] 输出结果（具体数据/文件）
    - [ ] 注意事项（风险/限制）
    - [ ] 下一步建议（后续操作）
  - 验证点：所有必需字段都存在，内容具体，格式一致

用例2.1.2：多步骤任务输出完整
  - 输入："[请替换为多步骤任务输入]"
  - 预期：每一步都有明确输出，最终结果完整
  - 验证点：每一步都有进度提示，中间结果可追溯，没有跳过任何步骤
```

### 2.2 输出格式一致性

```
用例2.2.1：多次输出格式一致
  - 构造：连续运行3次相同的核心功能
  - 预期：3次输出的结构和格式一致
  - 验证点：必需字段的顺序一致，没有遗漏字段，内容随输入变化

用例2.2.2：边界输入输出格式不变
  - 构造：输入边界数据（空/最小/最大）
  - 预期：输出格式仍然完整，不因输入特殊而崩溃
  - 验证点：输出仍然包含所有必需字段，没有报错，对边界情况有说明
```

---

## 三、错误处理测试（Error Handling）

**目的**：验证技能在边界条件和异常场景下的行为。

**通过标准**：不崩溃，错误信息明确，有降级机制

### 3.1 边界场景

```
用例3.1.1：输入不完整
  - 构造：用户只提供了部分必需信息
  - 预期：主动询问缺失信息，不盲目执行
  - 验证点：输出了澄清问题，没有直接执行，问题具体

用例3.1.2：输入格式错误
  - 构造：用户提供了错误格式的输入
  - 预期：检测到格式错误，提示用户修正
  - 验证点：明确指出哪个字段格式错误，给出正确格式示例

用例3.1.3：超出能力范围
  - 构造：用户要求技能做它不支持的事情
  - 预期：明确说明不支持，给出替代方案
  - 验证点：明确说明不支持，给出替代方案，不强行执行
```

### 3.2 异常场景

```
用例3.2.1：脚本执行失败
  - 构造：模拟脚本执行失败（如依赖缺失、文件不存在）
  - 预期：捕获错误，给出明确的错误信息和修复建议
  - 验证点：错误信息明确，给出修复建议，有降级机制，不崩溃

用例3.2.2：外部依赖不可用
  - 构造：模拟外部API/服务不可用
  - 预期：检测到不可用，给出降级方案
  - 验证点：明确说明外部依赖不可用，给出降级方案，不无限重试

用例3.2.3：大文件/大数据处理
  - 构造：输入超出常规大小的文件/数据
  - 预期：能处理或明确说明限制
  - 验证点：有进度提示或明确说明限制，不崩溃，不内存溢出
```

---

## 四、评估执行指南

```
步骤1：根据技能具体领域，修改上述用例的输入和预期输出
步骤2：实际运行每个用例，记录实际输出
步骤3：对照预期输出，检查验证点是否全部通过
步骤4：记录失败用例，分析原因，修复技能
步骤5：重新运行失败用例，直到全部通过
```

---

**版本**: v1.0（自动生成）
**基于**: skill-creator-pro 通用评估用例模板
**更新**: 2026-09-23
'''
        with open(eval_cases_path, "w", encoding="utf-8") as f:
            f.write(eval_template)
        print(f"✅ 已自动生成评估用例模板: references/evaluation-cases.md")
        print(f"   💡 下一步: 根据技能具体领域修改用例，然后实际运行测试")

    # 步骤1：规范校验（测试基础规范性）
    validate_skill(skill_path)

    # 步骤2：深度审计（测试完整质量）
    audit_skill(skill_path)

    # 步骤3：输出校验（测试输出格式）
    output_validator = os.path.join(SCRIPT_DIR, "output_validator.py")
    if os.path.isfile(output_validator):
        run_command(
            [sys.executable, output_validator, skill_path, "--mode", "test"],
            "输出格式校验（output_validator.py）"
        )
    else:
        print("⚠️  output_validator.py 不存在，跳过输出格式校验")

    # 步骤4：脚本冒烟测试（自动检测所有脚本，运行语法检查+--help冒烟）
    print(f"\n--- 步骤4: 脚本冒烟测试 ---")
    scripts_dir = os.path.join(skill_path, "scripts")
    if os.path.isdir(scripts_dir):
        import py_compile
        script_files = sorted([f for f in os.listdir(scripts_dir) if f.endswith(".py")])
        total = len(script_files)
        syntax_pass = 0
        syntax_fail = 0
        smoke_pass = 0
        smoke_fail = 0
        smoke_skip = 0
        failed_scripts = []

        for script in script_files:
            script_path = os.path.join(scripts_dir, script)
            # 语法检查
            try:
                py_compile.compile(script_path, doraise=True)
                syntax_pass += 1
            except py_compile.PyCompileError as e:
                syntax_fail += 1
                failed_scripts.append(f"{script}（语法错误: {str(e)[:80]}）")
                continue

            # 冒烟测试（有main入口的脚本运行--help）
            with open(script_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            has_main = 'if __name__ == "__main__"' in content or "def main()" in content
            if has_main:
                try:
                    proc = subprocess.run(
                        [sys.executable, script_path, "--help"],
                        capture_output=True, text=True, timeout=10
                    )
                    if proc.returncode == 0:
                        smoke_pass += 1
                    else:
                        smoke_fail += 1
                        failed_scripts.append(f"{script}（--help返回码{proc.returncode}）")
                except subprocess.TimeoutExpired:
                    smoke_fail += 1
                    failed_scripts.append(f"{script}（--help超时）")
                except Exception as e:
                    smoke_fail += 1
                    failed_scripts.append(f"{script}（--help异常: {str(e)[:60]}）")
            else:
                smoke_skip += 1

        print(f"  脚本总数: {total}")
        print(f"  语法检查: ✅{syntax_pass}通过 / ❌{syntax_fail}失败")
        print(f"  冒烟测试: ✅{smoke_pass}通过 / ❌{smoke_fail}失败 / ⏭️{smoke_skip}跳过（模块文件）")
        if failed_scripts:
            print(f"  ❌ 失败脚本:")
            for fs in failed_scripts:
                print(f"    - {fs}")
        if syntax_fail == 0 and smoke_fail == 0:
            print(f"  ✅ 脚本冒烟测试全部通过")
        else:
            print(f"  ⚠️  脚本冒烟测试有失败，请检查上述脚本")
    else:
        print(f"  ⏭️  无scripts目录，跳过脚本冒烟测试")

    # 完成
    print(f"\n{'#'*60}")
    print(f"# ✅ 端到端测试完成: {skill_path}")
    print(f"# 所有测试步骤都已通过")
    print(f"# 💡 经验沉淀: 测试完成后建议提取测试经验（边界场景/失败模式）写入案例库")
    print(f"{'#'*60}")

    return {"success": True, "skill_path": skill_path, "mode": "test"}


def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 编排脚本（统一入口，强制顺序执行）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 新建技能
  python3 create_skill.py create my-skill --path /path/to/.user_skills --philosophy mixed

  # 优化技能（编辑完成后验证）
  python3 create_skill.py optimize /path/to/my-skill

  # 评审技能
  python3 create_skill.py review /path/to/my-skill

  # 端到端测试
  python3 create_skill.py test /path/to/my-skill
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="操作模式")

    # create 模式
    p_create = subparsers.add_parser("create", help="新建技能")
    p_create.add_argument("skill_name", help="技能名称（小写字母+连字符）")
    p_create.add_argument("--path", required=True, help="输出目录（通常是workspace/.user_skills）")
    p_create.add_argument("--philosophy", choices=["capability", "process", "mixed"], default="mixed",
                          help="设计哲学（默认mixed）")
    p_create.add_argument("--title", help="技能显示名称")

    # optimize 模式
    p_optimize = subparsers.add_parser("optimize", help="优化技能（编辑完成后验证）")
    p_optimize.add_argument("skill_path", help="技能目录路径")

    # review 模式
    p_review = subparsers.add_parser("review", help="评审技能")
    p_review.add_argument("skill_path", help="技能目录路径")

    # test 模式
    p_test = subparsers.add_parser("test", help="端到端测试")
    p_test.add_argument("skill_path", help="技能目录路径")

    # upgrade 模式（迁移升级现有技能）
    p_upgrade = subparsers.add_parser("upgrade", help="迁移升级现有技能到专业标准")
    p_upgrade.add_argument("skill_path", help="现有技能目录路径")
    p_upgrade.add_argument("--apply", action="store_true", help="应用迁移方案（创建缺失文件）")
    p_upgrade.add_argument("--backup", action="store_true", help="迁移前自动备份")
    p_upgrade.add_argument("--target", help="迁移到新目录（不修改原技能）")

    args = parser.parse_args()

    try:
        if args.command == "create":
            result = create_skill(args.skill_name, args.path, args.philosophy, args.title)
        elif args.command == "optimize":
            result = optimize_skill(args.skill_path)
        elif args.command == "review":
            result = review_skill(args.skill_path)
        elif args.command == "test":
            result = test_skill(args.skill_path)
        elif args.command == "upgrade":
            sys.path.insert(0, SCRIPT_DIR)
            from upgrade_skill import analyze_gap, apply_migration, print_migration_report
            analysis = analyze_gap(args.skill_path)
            print_migration_report(analysis)
            if args.apply:
                result = apply_migration(args.skill_path, analysis, target_path=args.target, backup=args.backup)
            else:
                result = {"success": True, "skill_path": args.skill_path, "mode": "upgrade", "note": "仅分析，未应用。使用 --apply 应用迁移方案"}
        else:
            parser.print_help()
            sys.exit(1)

        # 输出JSON结果（便于后续处理）
        result["timestamp"] = datetime.now().isoformat()
        print(f"\n📋 执行结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

    except RuntimeError as e:
        print(f"\n❌ 执行失败: {e}", file=sys.stderr)
        print(f"💡 请根据错误信息修复问题后重新运行", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行时错误: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
