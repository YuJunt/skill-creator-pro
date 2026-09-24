#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本: v1.0.0 | 许可证: MIT | 最低Python: 3.8+

专业版技能模板生成脚本（Skill Initializer Pro）

基于三层分类36要素最佳实践，生成通用专业级技能模板。
支持三种设计哲学：capability（工具包装型）/ process（方法论型）/ mixed（混合型）。

用法：
  python3 init_skill_pro.py <skill-name> --path <output-dir> --philosophy mixed
  python3 init_skill_pro.py my-skill --path /path/to/workspace/.user_skills
"""
import argparse
import datetime
import os
import re
import shutil
import sys


# ============================================================
# Mixed 模式模板（混合型）
# 特点：完整SKILL.md + 编排脚本 + 校验脚本 + 核心工具脚本 + references + examples
# ============================================================


# 从templates模块导入所有模板字符串
from templates import *  # noqa: F401,F403

def _generate_capability_main_script(skill_title):
    """生成Capability模式的核心工具脚本"""
    return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{skill_title} 核心工具脚本

用法：
  python3 main.py --help
  python3 main.py --input <输入文件> --output <输出文件>
"""
import argparse
import os
import sys


def cmd_process(args):
    """处理核心功能"""
    # TODO: 实现核心功能
    print(json.dumps({{
        "success": True,
        "input": args.input,
        "output": args.output,
        "message": "核心功能框架已就绪，请实现具体逻辑"
    }}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="{skill_title} 核心工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_process = sub.add_parser("process", help="处理核心功能")
    p_process.add_argument("--input", required=True, help="输入文件")
    p_process.add_argument("--output", required=True, help="输出文件")
    p_process.set_defaults(func=cmd_process)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    import json
    main()
'''


# ============================================================
# 主函数
# ============================================================

def init_skill(skill_name, output_dir, skill_title=None, skill_description=None,
                trigger_words=None, not_for=None, philosophy="mixed"):
    """初始化技能模板（按设计哲学生成差异化模板）

    philosophy:
      - capability: 工具包装型（简洁SKILL.md + 核心工具脚本）
      - process: 方法论型（完整SKILL.md流程 + references方法论文档）
      - mixed: 混合型（完整SKILL.md + 编排脚本 + 校验脚本 + references）
    """
    # 参数处理
    skill_title = skill_title or skill_name.replace("-", " ").title()

    # 技能名安全校验（防止路径遍历攻击）
    if not skill_name:
        print("❌ 技能名不能为空")
        sys.exit(1)
    if "/" in skill_name or "\\" in skill_name:
        print(f"❌ 技能名不能包含路径分隔符: {skill_name}")
        sys.exit(1)
    if ".." in skill_name:
        print(f"❌ 技能名不能包含 '..': {skill_name}")
        sys.exit(1)
    if not re.match(r"^[a-z0-9-]+$", skill_name):
        print(f"❌ 技能名格式错误: {skill_name}（只允许小写字母、数字、连字符）")
        sys.exit(1)
    if skill_name.startswith("-"):
        print(f"❌ 技能名不能以连字符开头: {skill_name}")
        sys.exit(1)
    if skill_name.endswith("-"):
        print(f"❌ 技能名不能以连字符结尾: {skill_name}")
        sys.exit(1)
    if set(skill_name) == {"-"}:
        print(f"❌ 技能名不能只有连字符: {skill_name}")
        sys.exit(1)
    if len(skill_name) > 64:
        print(f"❌ 技能名过长: {len(skill_name)}字符（max 64）")
        sys.exit(1)

    # 输出目录校验
    if not os.path.exists(output_dir):
        print(f"❌ 输出目录不存在: {output_dir}")
        sys.exit(1)
    if not os.path.isdir(output_dir):
        print(f"❌ 输出路径不是目录: {output_dir}")
        sys.exit(1)

    if philosophy == "capability":
        skill_description = skill_description or f"{skill_title}工具。提供确定性命令行工具，封装核心功能。"
    elif philosophy == "process":
        skill_description = skill_description or f"{skill_title}方法论。编码完整工作流和checklist，指导agent按流程执行。"
    else:
        skill_description = skill_description or f"{skill_title}专业处理。基于最佳实践，支持完整处理/快速执行/单步操作多种模式。"
    trigger_words = trigger_words or skill_name
    not_for = not_for or "其他不相关的任务"

    # 创建目录
    skill_path = os.path.join(output_dir, skill_name)
    if os.path.exists(skill_path):
        print(f"❌ 目录已存在: {skill_path}")
        sys.exit(1)

    dirs = ["scripts", "references", "examples", "assets"]
    for d in dirs:
        os.makedirs(os.path.join(skill_path, d), exist_ok=True)

    scripts_path = os.path.join(skill_path, "scripts")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # 选择SKILL.md模板
    if philosophy == "capability":
        skill_md_content = SKILL_MD_CAPABILITY_TEMPLATE.format(
            skill_name=skill_name, skill_title=skill_title,
            skill_description=skill_description, trigger_words=trigger_words,
            not_for=not_for, scripts_path=scripts_path, date=date_str,
        )
    elif philosophy == "process":
        skill_md_content = SKILL_MD_PROCESS_TEMPLATE.format(
            skill_name=skill_name, skill_title=skill_title,
            skill_description=skill_description, trigger_words=trigger_words,
            not_for=not_for, scripts_path=scripts_path, date=date_str,
        )
    else:
        skill_md_content = SKILL_MD_MIXED_TEMPLATE.format(
            skill_name=skill_name, skill_title=skill_title,
            skill_description=skill_description, trigger_words=trigger_words,
            not_for=not_for, scripts_path=scripts_path, date=date_str,
        )

    # 基础文件（所有模式都有）
    files = {
        "SKILL.md": skill_md_content,
    }

    # 根据设计哲学生成不同的文件
    if philosophy == "capability":
        # Capability模式：1个核心工具脚本 + 1个示例 + 评估用例
        files["scripts/main.py"] = _generate_capability_main_script(skill_title)
        files["examples/example-usage.md"] = EXAMPLE_USAGE_TEMPLATE.format(skill_title=skill_title)
        files["references/evaluation-cases.md"] = EVALUATION_CASES_TEMPLATE.format(skill_title=skill_title)

    elif philosophy == "process":
        # Process模式：references方法论文档 + 检查清单 + 编排脚本 + 校验脚本 + 工作流示例 + 评估用例
        files["references/workflow-guide.md"] = WORKFLOW_GUIDE_TEMPLATE.format(skill_title=skill_title)
        files["references/checklist.md"] = CHECKLIST_TEMPLATE.format(skill_title=skill_title)
        files["scripts/orchestrator.py"] = ORCHESTRATOR_TEMPLATE.replace("{skill_title}", skill_title)
        files["scripts/validator.py"] = PROCESS_VALIDATOR_TEMPLATE.replace("{skill_title}", skill_title)
        files["examples/example-workflow.md"] = EXAMPLE_WORKFLOW_TEMPLATE.format(skill_title=skill_title)
        files["references/evaluation-cases.md"] = EVALUATION_CASES_TEMPLATE.format(skill_title=skill_title)

    else:
        # Mixed模式：完整专业技能（3个脚本 + 2个references + 1个示例）
        files["scripts/main.py"] = _generate_capability_main_script(skill_title)
        files["scripts/orchestrator.py"] = ORCHESTRATOR_TEMPLATE.replace("{skill_title}", skill_title)
        files["scripts/validator.py"] = VALIDATOR_TEMPLATE.replace("{skill_title}", skill_title)
        files["references/best-practices.md"] = BEST_PRACTICES_TEMPLATE.format(skill_title=skill_title)
        files["references/evaluation-cases.md"] = EVALUATION_CASES_TEMPLATE.format(skill_title=skill_title)
        files["examples/example-usage.md"] = EXAMPLE_USAGE_TEMPLATE.format(skill_title=skill_title)

    # 写入文件
    try:
        for filepath, content in files.items():
            full_path = os.path.join(skill_path, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            # 给脚本加执行权限
            if filepath.endswith(".py"):
                os.chmod(full_path, 0o755)
    except OSError as e:
        print(f"❌ 文件写入失败: {e}")
        print(f"   可能原因：磁盘空间不足、权限不足、路径不存在")
        # 清理已创建的部分文件
        shutil.rmtree(skill_path, ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        shutil.rmtree(skill_path, ignore_errors=True)
        sys.exit(1)

    # 清理Python编译缓存（校验过程中可能生成__pycache__）
    for root, dirs, _ in os.walk(skill_path):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)

    return skill_path


def main():
    parser = argparse.ArgumentParser(description="专业版技能模板生成脚本（Skill Initializer Pro）")
    parser.add_argument("skill_name", help="技能名称（小写+连字符，如 my-skill）")
    parser.add_argument("--path", required=True, help="输出目录（通常是 workspace/.user_skills）")
    parser.add_argument("--title", help="技能标题（默认从skill_name生成）")
    parser.add_argument("--description", help="技能描述（默认根据设计哲学生成）")
    parser.add_argument("--triggers", help="触发词（默认用skill_name）")
    parser.add_argument("--not-for", help="不适用于（默认'其他不相关的任务'）")
    parser.add_argument("--philosophy", choices=["capability", "process", "mixed"], default="mixed",
                        help="设计哲学：capability(工具包装型)/process(方法论型)/mixed(混合型，默认)")
    args = parser.parse_args()

    skill_path = init_skill(
        skill_name=args.skill_name,
        output_dir=args.path,
        skill_title=args.title,
        skill_description=args.description,
        trigger_words=args.triggers,
        not_for=args.not_for,
        philosophy=args.philosophy,
    )

    print(f"✅ 技能创建成功: {skill_path}")
    print(f"   设计哲学: {args.philosophy}")
    print(f"   下一步: 编辑 SKILL.md 和相关文件，替换 TODO 占位符")


if __name__ == "__main__":
    main()
