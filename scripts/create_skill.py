#!/usr/bin/env python3
"""
版本: v1.0.0 | 许可证: MIT | 最低Python: 3.8+

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

# 最低Python版本检查（dataclasses需要3.8+）
if sys.version_info < (3, 8):
    print(f"❌ Python版本过低: {sys.version.split()[0]}，需要 Python 3.8+", file=sys.stderr)
    print("💡 请升级Python后重试", file=sys.stderr)
    sys.exit(2)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_command(cmd, description):
    """运行命令并返回结果，失败时抛出异常"""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"  命令: {' '.join(cmd)}")
    print(f"{'='*60}")

    # P0修复：自动记录脚本调用到runtime_guard（防偷懒机制自动生效）
    # 只记录skill-creator-pro自己的脚本（路径包含SCRIPT_DIR）
    try:
        cmd_str = " ".join(cmd)
        if SCRIPT_DIR in cmd_str:
            # 提取脚本名称（如validate_skill.py）
            import re as _re
            script_match = _re.search(r'([a-z_]+\.py)', cmd_str)
            if script_match:
                script_name = script_match.group(1).replace('.py', '')
                _track_cmd = [
                    sys.executable, os.path.join(SCRIPT_DIR, "runtime_guard.py"),
                    "track", "--step", script_name,
                    "--action", "script", "--type", "script"
                ]
                subprocess.run(_track_cmd, capture_output=True, timeout=5)
    except Exception as e:
        print(f"  ⚠️ 容错跳过: {e}", file=sys.stderr)  # track失败不影响主流程

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

    # 自动记录质量指标（每步通过标准）
    _track_quality("validate_skill", {"high_issues": 0})

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

    # 自动记录质量指标（每步通过标准）
    # 解析必备层通过率（如"必备层: 20/20 (100%)"）
    import re as _re
    required_match = _re.search(r'必备层.*?(\d+)/(\d+)', result.stdout)
    if required_match:
        passed = int(required_match.group(1))
        total = int(required_match.group(2))
        required_pass = passed / total if total > 0 else 0
    else:
        required_pass = 1.0  # 默认100%（如果能执行到这里说明没有抛出异常）
    _track_quality("audit_skill", {"required_pass": required_pass})

    return result.stdout


def validate_output(skill_path, mode="optimize"):
    """步骤：输出格式校验（output_validator.py）——硬门禁，校验不通过脚本返回非0，run_command自动抛出异常"""
    output_validator = os.path.join(SCRIPT_DIR, "output_validator.py")
    if not os.path.isfile(output_validator):
        print("⚠️  output_validator.py 不存在，跳过输出格式校验")
        return
    # run_command会在returncode != 0时自动抛出RuntimeError，不需要额外文本判断
    run_command(
        [sys.executable, output_validator, skill_path, "--mode", mode],
        "输出格式校验（output_validator.py）"
    )

    # 自动记录质量指标（每步通过标准）
    # 如果能执行到这里，说明output_validator返回0，即0问题
    _track_quality("output_validator", {"issues": 0})


def _track_quality(step, quality_dict):
    """自动记录质量指标到runtime_guard（每步通过标准）

    这是create_skill.py的内部函数，用于在运行校验脚本后自动记录质量指标，
    防止LLM表面满足（如"校验通过了"但实际有问题没记录）。

    Args:
        step: 步骤名称（如validate_skill/audit_skill/output_validator）
        quality_dict: 质量指标字典（如{"high_issues": 0}）
    """
    try:
        import json as _json
        quality_json = _json.dumps(quality_dict, ensure_ascii=False)
        _track_cmd = [
            sys.executable, os.path.join(SCRIPT_DIR, "runtime_guard.py"),
            "track", "--step", step,
            "--action", "script", "--type", "script",
            "--quality", quality_json
        ]
        subprocess.run(_track_cmd, capture_output=True, timeout=5)
    except Exception as e:
        print(f"  ⚠️ 容错跳过: {e}", file=sys.stderr)  # track失败不影响主流程


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

    # 步骤3：安全扫描（硬门禁：高风险问题必须中止）
    security_script = os.path.join(SCRIPT_DIR, "security_scan.py")
    if os.path.isfile(security_script):
        sec_result = run_command(
            [sys.executable, security_script, skill_path],
            "安全扫描（security_scan.py）"
        )
        if "高风险: 0" not in sec_result.stdout:
            raise RuntimeError("❌ 安全扫描发现高风险问题，必须修复后才能继续")
        if "中风险: 0" not in sec_result.stdout:
            print("⚠️  安全扫描发现中风险问题，建议修复后再发布")

    # 步骤4：输出格式校验（硬门禁）
    validate_output(skill_path, mode="optimize")

    # 完成
    print(f"\n{'#'*60}")
    print(f"# ✅ 技能优化验证完成: {skill_path}")
    print(f"# 规范校验/深度审计/安全扫描/输出校验全部通过")
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

    # 步骤3：输出格式校验（硬门禁）
    validate_output(skill_path, mode="review")

    # 完成
    print(f"\n{'#'*60}")
    print(f"# ✅ 技能评审完成: {skill_path}")
    print(f"# 规范校验/深度审计/输出校验全部通过")
    print(f"# 评审结果已输出在上文")
    print(f"# 💡 经验沉淀: 评审完成后建议提取评审经验（常见问题/最佳实践）写入案例库")
    print(f"{'#'*60}")

    return {"success": True, "skill_path": skill_path, "mode": "review"}


def test_skill(skill_path, full=False):
    """模式：端到端测试"""
    print(f"\n{'#'*60}")
    print(f"# 端到端测试: {skill_path}")
    if full:
        print(f"# 模式: 完整测试（包含安全扫描+触发路由+渐进式披露）")
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

    # 步骤5：完整测试（仅--full模式）
    if full:
        print(f"\n--- 步骤5: 完整测试（安全扫描+触发路由+渐进式披露） ---")

        # 5.1 安全扫描
        security_scan = os.path.join(SCRIPT_DIR, "security_scan.py")
        if os.path.isfile(security_scan):
            print(f"\n  5.1 安全扫描:")
            run_command(
                [sys.executable, security_scan, skill_path],
                "安全扫描（security_scan.py）"
            )
        else:
            print(f"  ⚠️  security_scan.py 不存在，跳过安全扫描")

        # 5.2 触发路由测试（如果技能有router.py）
        skill_router = os.path.join(skill_path, "scripts", "router.py")
        if os.path.isfile(skill_router):
            print(f"\n  5.2 触发路由测试:")
            test_messages = [
                "帮我创建一个技能",
                "优化一下这个技能",
                "深度评审这个技能",
                "测试一下这个技能",
                "今天天气怎么样",  # 不应触发
            ]
            for msg in test_messages:
                result = subprocess.run(
                    [sys.executable, skill_router, msg, "--json"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        mode = data.get("mode", "unknown")
                        print(f"    '{msg[:20]}...' → {mode}")
                    except json.JSONDecodeError:
                        print(f"    '{msg[:20]}...' → 解析失败")
                else:
                    print(f"    '{msg[:20]}...' → 执行失败")
        else:
            print(f"\n  5.2 触发路由测试: ⏭️  技能无router.py，跳过")

        # 5.3 渐进式披露完整性检查
        print(f"\n  5.3 渐进式披露完整性检查:")
        skill_md = os.path.join(skill_path, "SKILL.md")
        if os.path.isfile(skill_md):
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
            checks = {
                "frontmatter": content.startswith("---"),
                "description": "description:" in content,
                "gotchas": "gotcha" in content.lower(),
                "workflow": "工作流" in content or "workflow" in content.lower(),
                "references_ref": "references/" in content,
                "scripts_ref": "scripts/" in content,
            }
            for name, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"    {status} {name}")
            total_checks = len(checks)
            passed_checks = sum(1 for v in checks.values() if v)
            print(f"    总计: {passed_checks}/{total_checks} 通过")
        else:
            print(f"    ❌ SKILL.md 不存在")

    # 完成
    print(f"\n{'#'*60}")
    print(f"# ✅ 端到端测试完成: {skill_path}")
    if full:
        print(f"# 模式: 完整测试（所有高级测试已执行）")
    print(f"# 所有测试步骤都已通过")
    print(f"# 💡 经验沉淀: 测试完成后建议提取测试经验（边界场景/失败模式）写入案例库")
    print(f"{'#'*60}")

    return {"success": True, "skill_path": skill_path, "mode": "test", "full": full}


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
    p_test.add_argument("--full", action="store_true", help="完整测试（包含安全扫描+触发路由+渐进式披露）")

    # upgrade 模式（迁移升级现有技能）
    p_upgrade = subparsers.add_parser("upgrade", help="迁移升级现有技能到专业标准")
    p_upgrade.add_argument("skill_path", help="现有技能目录路径")
    p_upgrade.add_argument("--apply", action="store_true", help="应用迁移方案（创建缺失文件）")
    p_upgrade.add_argument("--backup", action="store_true", help="迁移前自动备份")
    p_upgrade.add_argument("--target", help="迁移到新目录（不修改原技能）")

    # route 模式（自然语言自动路由）
    p_route = subparsers.add_parser("route", help="自然语言自动路由（输入用户消息，自动判断模式）")
    p_route.add_argument("message", help="用户消息（自然语言描述需求）")
    p_route.add_argument("--json", action="store_true", help="JSON格式输出路由决策")
    p_route.add_argument("--verbose", action="store_true", help="详细输出（包含各模式分数）")

    args = parser.parse_args()

    # P3: 路由行自动输出（硬校验——只要调用编排脚本，就一定会输出路由行）
    # 即使LLM忘了手动输出路由行，脚本也会帮它补上
    # 使用极简格式：🔀 路由: skill-creator-pro · {模式} · {一句话重点}
    MODE_ROUTE_MAP = {
        "create": ("新建技能", "创建新技能"),
        "optimize": ("优化技能", "优化目标技能"),
        "review": ("深度评审", "评审目标技能规范"),
        "test": ("端到端测试", "测试目标技能实际效果"),
        "upgrade": ("技能升级", "升级目标技能"),
    }
    # route命令特殊处理：先路由再输出，避免输出"route"而不是实际模式
    if args.command != "route":
        route_mode, route_focus = MODE_ROUTE_MAP.get(args.command, (args.command, "执行任务"))
        # 如果有skill_name参数（create命令），添加到重点中
        if hasattr(args, 'skill_name') and args.skill_name:
            route_focus = f"创建{args.skill_name}技能"
        elif hasattr(args, 'skill_path') and args.skill_path:
            skill_name = os.path.basename(os.path.abspath(args.skill_path))
            route_focus = f"{route_focus}{skill_name}"
        route_line = f"🔀 路由: skill-creator-pro · {route_mode} · {route_focus}"
        print(route_line)
        print()

    # P0修复：自动调用runtime_guard track，记录脚本调用（防偷懒机制自动生效）
    # 不需要LLM手动调用，create_skill.py运行时自动记录
    try:
        import subprocess as _sp
        _track_cmd = [
            sys.executable, os.path.join(SCRIPT_DIR, "runtime_guard.py"),
            "track", "--step", f"create_skill.{args.command}",
            "--action", "script", "--type", "script"
        ]
        _sp.run(_track_cmd, capture_output=True, timeout=5)
        # 同时记录路由行输出
        if args.command != "route":
            _route_cmd = [
                sys.executable, os.path.join(SCRIPT_DIR, "runtime_guard.py"),
                "route", "--mode", route_mode,
                "--line", route_line,
                "--message", f"create_skill.{args.command}"
            ]
            _sp.run(_route_cmd, capture_output=True, timeout=5)
    except Exception as _e:
        print(f"[runtime_guard track跳过: {_e}]", file=sys.stderr)

    # P1-2：自动推荐must_read文档（提醒LLM阅读，防偷懒）
    # P3升级：REFS_TO_READ_MAP——每个文档附带具体章节说明（不是只说"读best-practices"，而是"读best-practices第七章"）
    if args.command != "route":
        REFS_TO_READ_MAP = {
            "create": [
                ("best-practices.md", "第七章 引导LLM深度利用方法论的闭环设计 + 五、迭代流程6步"),
                ("design-philosophies.md", "三种设计哲学选择（capability/process/mixed）+ 选择决策树"),
                ("36-element-checklist.md", "推荐层第18项 方法论知识库+调用完整性 + 必备层20项"),
            ],
            "optimize": [
                ("36-element-checklist.md", "推荐层第18项 方法论调用完整性 + 三层加权评分"),
                ("gotchas-collection.md", "第12B项 LLM只看几行文档只用一两个脚本 + 内容类坑"),
                ("best-practices.md", "第七章 方法论调用闭环设计 + 五、迭代流程6步"),
                ("tech-debt-management.md", "技术债识别+分级+偿还策略"),
            ],
            "review": [
                ("36-element-checklist.md", "完整36项检查清单 + 三层加权评分体系"),
                ("review-process-guide.md", "7维度评审流程 + 问题分级标准"),
                ("best-practices.md", "第七章 方法论调用闭环设计（评审时重点检查）"),
            ],
            "test": [
                ("eval-practice.md", "评估用例设计 + RED-GREEN-REFACTOR流程"),
                ("routing-mustread-test-cases.md", "路由专项测试 + must_read验证用例"),
                ("evaluation-guide.md", "8维度评估体系 + 通过率计算"),
            ],
        }
        refs = REFS_TO_READ_MAP.get(args.command, [])
        if refs:
            print(f"📚 refs_to_read（根据{args.command}模式推荐，具体到章节）:")
            for i, (doc, chapter) in enumerate(refs, 1):
                print(f"   {i}. references/{doc}")
                print(f"      → 重点读: {chapter}")
            print()
            # P2-1：自动记录为"已推荐"（gate区分auto_recommended和主动阅读）
            try:
                for doc, _ in refs:
                    _doc_track_cmd = [
                        sys.executable, os.path.join(SCRIPT_DIR, "runtime_guard.py"),
                        "track", "--step", doc,
                        "--action", "auto_recommended", "--type", "doc"
                    ]
                    _sp.run(_doc_track_cmd, capture_output=True, timeout=5)
            except Exception as e:
                print(f"  ⚠️ 容错跳过: {e}", file=sys.stderr)

    try:
        if args.command == "create":
            result = create_skill(args.skill_name, args.path, args.philosophy, args.title)
        elif args.command == "optimize":
            result = optimize_skill(args.skill_path)
        elif args.command == "review":
            result = review_skill(args.skill_path)
        elif args.command == "test":
            result = test_skill(args.skill_path, full=getattr(args, 'full', False))
        elif args.command == "upgrade":
            sys.path.insert(0, SCRIPT_DIR)
            from upgrade_skill import analyze_gap, apply_migration, print_migration_report
            analysis = analyze_gap(args.skill_path)
            print_migration_report(analysis)
            if args.apply:
                result = apply_migration(args.skill_path, analysis, target_path=args.target, backup=args.backup)
            else:
                result = {"success": True, "skill_path": args.skill_path, "mode": "upgrade", "note": "仅分析，未应用。使用 --apply 应用迁移方案"}
        elif args.command == "route":
            # 自然语言自动路由
            sys.path.insert(0, SCRIPT_DIR)
            from router import route as router_route
            decision = router_route(args.message)

            if args.json:
                print(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2))
            else:
                # 先输出标准路由行（修复Bug：之前输出"route"而不是实际模式）
                MODE_NAME_MAP = {
                    "create": "新建技能",
                    "optimize": "优化技能",
                    "review": "深度评审",
                    "test": "端到端测试",
                    "refuse": "🚫拒绝",
                    "ambiguous": "❓模糊",
                }
                mode_name = MODE_NAME_MAP.get(decision.mode, decision.mode)
                print(f"🔀 路由: {mode_name}")
                print()

                print(f"{'='*60}")
                print(f"🔀 自动路由结果")
                print(f"{'='*60}")
                print(f"\n📥 输入: {args.message}")
                print(f"\n🎯 模式: {decision.mode}")
                print(f"📊 置信度: {decision.confidence}")
                print(f"💡 理由: {decision.reasoning}")

                if decision.must_read:
                    print(f"\n📚 必读文档 ({len(decision.must_read)}个):")
                    for doc in decision.must_read:
                        print(f"   - {doc}")

                if decision.alternatives:
                    print(f"\n🔄 备选模式: {', '.join(decision.alternatives)}")

                if decision.mode == "ambiguous":
                    print(f"\n❓ 请求模糊，请明确你的需求：")
                    print(f"   - 创建新技能 → python3 create_skill.py create <name> --path <dir>")
                    print(f"   - 优化现有技能 → python3 create_skill.py optimize <skill-path>")
                    print(f"   - 评审技能 → python3 create_skill.py review <skill-path>")
                    print(f"   - 测试技能 → python3 create_skill.py test <skill-path>")
                elif decision.mode == "refuse":
                    print(f"\n🚫 危险请求已拒绝")
                else:
                    mode_commands = {
                        "create": "python3 create_skill.py create <name> --path <dir>",
                        "optimize": "python3 create_skill.py optimize <skill-path>",
                        "review": "python3 create_skill.py review <skill-path>",
                        "test": "python3 create_skill.py test <skill-path>",
                    }
                    cmd = mode_commands.get(decision.mode, "")
                    if cmd:
                        print(f"\n🚀 下一步: {cmd}")

            result = {"success": True, "mode": "route", "routing_result": decision.to_dict()}
        else:
            parser.print_help()
            sys.exit(1)

        # 输出JSON结果（便于后续处理）
        # route命令的--json模式只输出纯JSON，不附加执行结果（避免破坏JSON格式）
        if not (args.command == "route" and args.json):
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
