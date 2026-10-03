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
import json
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


def _get_runtime_guard_template(skill_title):
    """读取runtime_guard.py模板文件并替换{skill_title}"""
    runtime_guard_path = os.path.join(os.path.dirname(__file__), "runtime_guard.py")
    with open(runtime_guard_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content.replace("专业级技能创建器", skill_title)


def _generate_capability_main_script(skill_title, skill_name=None):
    """生成Capability模式的核心工具脚本（完整框架版）

    包含：
    - 通用工具函数（输入校验/错误处理/JSON输出/操作日志）
    - 4个标准命令：preview（预览）/run（执行）/undo（撤销）/history（历史）
    - 每个命令都有完整的参数解析和错误处理框架
    - 清晰的TODO标记，用户只需填充业务逻辑
    """
    # 如果没有提供skill_name，用skill_title转换
    if skill_name is None:
        skill_name = skill_title.lower().replace(" ", "-")
    return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{skill_title} 核心工具脚本

设计哲学：Capability（工具包装型）——逻辑活在代码里，SKILL.md教agent怎么调用。

命令列表：
  preview  预览执行结果（dry-run，不实际修改）
  run      实际执行
  undo     撤销上一次操作
  history  查看操作历史

用法：
  python3 main.py --help
  python3 main.py preview --input <输入> [选项]
  python3 main.py run --input <输入> [选项]
  python3 main.py undo [--log-id <ID>]
  python3 main.py history [--limit <N>]
"""
import argparse
import json
import os
import sys
from datetime import datetime


# ============================================================
# 通用工具函数
# ============================================================

def validate_input_path(path):
    """校验输入路径是否存在且可读"""
    if not os.path.exists(path):
        return False, f"输入路径不存在: {{path}}"
    if not os.access(path, os.R_OK):
        return False, f"输入路径不可读: {{path}}"
    return True, ""


def validate_output_dir(path):
    """校验输出目录是否存在且可写"""
    if not os.path.exists(path):
        return False, f"输出目录不存在: {{path}}"
    if not os.access(path, os.W_OK):
        return False, f"输出目录不可写: {{path}}"
    return True, ""


def print_json_result(success, message, data=None, error=None):
    """统一JSON输出格式"""
    result = {{
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }}
    if data is not None:
        result["data"] = data
    if error is not None:
        result["error"] = error
    print(json.dumps(result, ensure_ascii=False, indent=2))


def handle_error(message, exit_code=1):
    """统一错误处理"""
    print_json_result(False, message, error=message)
    sys.exit(exit_code)


def get_log_path(input_path):
    """获取操作日志文件路径"""
    base_dir = os.path.dirname(os.path.abspath(input_path)) if os.path.isfile(input_path) else input_path
    return os.path.join(base_dir, ".{skill_name}_log.json")


def save_operation_log(log_path, operation, input_path, result_data):
    """保存操作日志（用于撤销）"""
    logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    log_entry = {{
        "id": len(logs) + 1,
        "operation": operation,
        "input": input_path,
        "timestamp": datetime.now().isoformat(),
        "result": result_data,
    }}
    logs.append(log_entry)

    try:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  警告：操作日志保存失败: {{e}}", file=sys.stderr)

    return log_entry["id"]


def load_operation_logs(log_path):
    """加载操作日志"""
    if not os.path.exists(log_path):
        return []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# ============================================================
# 命令实现（TODO: 填充具体业务逻辑）
# ============================================================

def cmd_preview(args):
    """预览执行结果（dry-run，不实际修改）

    TODO: 在此实现预览逻辑
    - 读取输入
    - 计算将要执行的操作
    - 输出预览列表（不实际修改）
    """
    # 输入校验
    valid, error = validate_input_path(args.input)
    if not valid:
        handle_error(error)

    # TODO: 实现预览逻辑
    preview_data = {{
        "input": args.input,
        "items": [
            # {{"original": "原文件名", "new": "新文件名", "action": "重命名"}}
        ],
        "total": 0,
        "message": "预览框架已就绪，请在cmd_preview中实现具体逻辑",
    }}

    print_json_result(True, "预览完成（dry-run，未实际修改）", data=preview_data)


def cmd_run(args):
    """实际执行

    TODO: 在此实现执行逻辑
    - 读取输入
    - 执行操作
    - 保存操作日志（用于撤销）
    - 输出执行结果
    """
    # 输入校验
    valid, error = validate_input_path(args.input)
    if not valid:
        handle_error(error)

    # TODO: 实现执行逻辑
    result_data = {{
        "input": args.input,
        "success_count": 0,
        "fail_count": 0,
        "skip_count": 0,
        "message": "执行框架已就绪，请在cmd_run中实现具体逻辑",
    }}

    # 保存操作日志（支持撤销）
    log_path = get_log_path(args.input)
    log_id = save_operation_log(log_path, "run", args.input, result_data)
    result_data["log_id"] = log_id

    print_json_result(True, "执行完成", data=result_data)


def cmd_undo(args):
    """撤销上一次操作

    TODO: 在此实现撤销逻辑
    - 读取操作日志
    - 根据日志恢复原状态
    - 输出撤销结果
    """
    # 确定日志路径
    if args.input:
        log_path = get_log_path(args.input)
    else:
        log_path = ".{skill_name}_log.json"

    logs = load_operation_logs(log_path)
    if not logs:
        handle_error("没有可撤销的操作（未找到操作日志）")

    # 确定要撤销的操作
    if args.log_id:
        target_log = next((l for l in logs if l["id"] == args.log_id), None)
        if not target_log:
            handle_error(f"指定的日志ID不存在: {{args.log_id}}")
    else:
        target_log = logs[-1]  # 默认撤销最近一次

    # TODO: 实现撤销逻辑
    undo_data = {{
        "log_id": target_log["id"],
        "operation": target_log["operation"],
        "input": target_log["input"],
        "restored_count": 0,
        "fail_count": 0,
        "message": "撤销框架已就绪，请在cmd_undo中实现具体逻辑",
    }}

    print_json_result(True, f"已撤销操作 #{{target_log['id']}}", data=undo_data)


def cmd_history(args):
    """查看操作历史"""
    # 确定日志路径
    if args.input:
        log_path = get_log_path(args.input)
    else:
        log_path = ".{skill_name}_log.json"

    logs = load_operation_logs(log_path)
    if not logs:
        print_json_result(True, "暂无操作历史", data={{"logs": []}})
        return

    # 按limit限制
    limit = args.limit or 10
    recent_logs = logs[-limit:] if len(logs) > limit else logs

    history_data = {{
        "total": len(logs),
        "shown": len(recent_logs),
        "logs": [
            {{
                "id": l["id"],
                "operation": l["operation"],
                "input": l["input"],
                "timestamp": l["timestamp"],
            }}
            for l in reversed(recent_logs)
        ],
    }}

    print_json_result(True, f"共{{len(logs)}}条操作历史，显示最近{{len(recent_logs)}}条", data=history_data)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="{skill_title} 核心工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 main.py preview --input /path/to/files
  python3 main.py run --input /path/to/files --option value
  python3 main.py undo --log-id 3
  python3 main.py history --limit 20
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True, help="可用命令")

    # preview 命令
    p_preview = sub.add_parser("preview", help="预览执行结果（dry-run，不实际修改）")
    p_preview.add_argument("--input", required=True, help="输入文件或目录")
    p_preview.add_argument("--option", default=None, help="选项（根据具体功能定义）")
    p_preview.set_defaults(func=cmd_preview)

    # run 命令
    p_run = sub.add_parser("run", help="实际执行")
    p_run.add_argument("--input", required=True, help="输入文件或目录")
    p_run.add_argument("--option", default=None, help="选项（根据具体功能定义）")
    p_run.add_argument("--force", action="store_true", help="强制执行（跳过确认）")
    p_run.set_defaults(func=cmd_run)

    # undo 命令
    p_undo = sub.add_parser("undo", help="撤销上一次操作")
    p_undo.add_argument("--input", default=None, help="输入路径（用于定位日志文件）")
    p_undo.add_argument("--log-id", type=int, default=None, help="指定要撤销的日志ID（默认撤销最近一次）")
    p_undo.set_defaults(func=cmd_undo)

    # history 命令
    p_history = sub.add_parser("history", help="查看操作历史")
    p_history.add_argument("--input", default=None, help="输入路径（用于定位日志文件）")
    p_history.add_argument("--limit", type=int, default=10, help="显示最近N条记录（默认10）")
    p_history.set_defaults(func=cmd_history)

    args = parser.parse_args()

    try:
        args.func(args)
    except Exception as e:
        handle_error(f"执行失败: {{str(e)}}", exit_code=2)



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
    original_name = skill_name
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

    # 检测非ASCII字符（如中文），自动转换为英文目录名
    if not re.match(r"^[a-z0-9-]+$", skill_name):
        # 检查是否包含非ASCII字符
        if any(ord(c) > 127 for c in skill_name):
            # 自动生成英文目录名
            import hashlib
            name_hash = hashlib.md5(skill_name.encode('utf-8')).hexdigest()[:6]
            english_name = f"skill-{name_hash}"
            print(f"⚠️  检测到非英文名称: '{skill_name}'")
            print(f"   目录名自动转换为: '{english_name}'（跨平台兼容性更好）")
            print(f"   技能标题保持为: '{skill_name}'")
            if skill_title == original_name.replace("-", " ").title():
                skill_title = original_name  # 标题保持用户输入的原始名称
            skill_name = english_name
        else:
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
        skill_description = skill_description or (
            f"{skill_title}专业工具。基于确定性脚本封装核心功能，提供可靠、可复现的执行能力。"
            f"当用户需要{skill_title}相关的确定性计算、批量处理或工具调用时使用。"
            f"触发词：\"{skill_name}\"\"{skill_title}\"。"
            f"不适用于：需要灵活判断或创造性思维的任务。"
        )
    elif philosophy == "process":
        skill_description = skill_description or (
            f"{skill_title}方法论。编码完整工作流和检查清单，指导Agent按标准流程执行，确保不遗漏关键步骤。"
            f"当用户需要{skill_title}相关的多步骤流程、标准化操作或质量保证时使用。"
            f"触发词：\"{skill_name}\"\"{skill_title}\"。"
            f"不适用于：单步简单操作或不需要流程约束的任务。"
        )
    else:
        skill_description = skill_description or (
            f"{skill_title}专业处理。工具脚本与方法论结合，支持完整流程执行/快速操作/单步调试多种模式。"
            f"当用户需要{skill_title}相关的分析、处理、优化或评审时使用。"
            f"触发词：\"{skill_name}\"\"{skill_title}\"。"
            f"不适用于：与{skill_title}无关的通用对话。"
        )
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
        # 默认安全白名单（操作日志和使用记录需要写入文件，这是正常功能）
        ".security-whitelist.json": json.dumps({
            "allowed_files": [],
            "allowed_patterns": [
                "文件写入：技能会写入文件",
                "with open(",
            ],
            "exclude_dirs": ["__pycache__/", ".pytest_cache/", ".git/"]
        }, ensure_ascii=False, indent=2),
    }

    # 根据设计哲学生成不同的文件
    if philosophy == "capability":
        # Capability模式：1个核心工具脚本 + 1个示例 + 评估用例 + 运行时保障
        files["scripts/main.py"] = _generate_capability_main_script(skill_title, skill_name)
        files["scripts/runtime_guard.py"] = _get_runtime_guard_template(skill_title)
        files["examples/example-usage.md"] = EXAMPLE_USAGE_TEMPLATE.format(skill_title=skill_title)
        files["references/evaluation-cases.md"] = EVALUATION_CASES_TEMPLATE.format(skill_title=skill_title)
        files["scripts/evolution.py"] = EVOLUTION_SCRIPT_TEMPLATE

    elif philosophy == "process":
        # Process模式：references方法论文档 + 检查清单 + 编排脚本 + 校验脚本 + 工作流示例 + 评估用例 + 运行时保障
        files["references/workflow-guide.md"] = WORKFLOW_GUIDE_TEMPLATE.format(skill_title=skill_title)
        files["references/checklist.md"] = CHECKLIST_TEMPLATE.format(skill_title=skill_title)
        files["scripts/orchestrator.py"] = ORCHESTRATOR_TEMPLATE.replace("{skill_title}", skill_title)
        files["scripts/validator.py"] = PROCESS_VALIDATOR_TEMPLATE.replace("{skill_title}", skill_title)
        files["scripts/runtime_guard.py"] = _get_runtime_guard_template(skill_title)
        files["examples/example-workflow.md"] = EXAMPLE_WORKFLOW_TEMPLATE.format(skill_title=skill_title)
        files["references/evaluation-cases.md"] = EVALUATION_CASES_TEMPLATE.format(skill_title=skill_title)
        files["scripts/evolution.py"] = EVOLUTION_SCRIPT_TEMPLATE

    else:
        # Mixed模式：完整专业技能（4个脚本 + 2个references + 1个示例）
        files["scripts/main.py"] = _generate_capability_main_script(skill_title, skill_name)
        files["scripts/orchestrator.py"] = ORCHESTRATOR_TEMPLATE.replace("{skill_title}", skill_title)
        files["scripts/validator.py"] = VALIDATOR_TEMPLATE.replace("{skill_title}", skill_title)
        files["scripts/runtime_guard.py"] = _get_runtime_guard_template(skill_title)
        files["references/best-practices.md"] = BEST_PRACTICES_TEMPLATE.format(skill_title=skill_title)
        files["references/evaluation-cases.md"] = EVALUATION_CASES_TEMPLATE.format(skill_title=skill_title)
        files["examples/example-usage.md"] = EXAMPLE_USAGE_TEMPLATE.format(skill_title=skill_title)
        files["scripts/evolution.py"] = EVOLUTION_SCRIPT_TEMPLATE

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
    parser.add_argument("--philosophy", default="mixed",
                        help="设计哲学：capability(工具包装型)/process(方法论型)/mixed(混合型，默认)")
    args = parser.parse_args()

    # 手动验证设计哲学（提供更友好的错误提示）
    valid_philosophies = ["capability", "process", "mixed"]
    if args.philosophy not in valid_philosophies:
        print(f"❌ 无效的设计哲学: '{args.philosophy}'")
        print(f"   可选值: {', '.join(valid_philosophies)}")
        print(f"   说明:")
        print(f"     - capability: 工具包装型（简洁SKILL.md + 核心工具脚本）")
        print(f"     - process: 方法论型（完整SKILL.md流程 + references方法论文档）")
        print(f"     - mixed: 混合型（完整SKILL.md + 编排脚本 + 校验脚本 + references，默认）")
        sys.exit(1)

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
