#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业级技能创建器 运行时保障脚本（Runtime Guard）

防止LLM偷懒的核心机制：
  1. 完成验证（verify_completion）：检查所有必需步骤是否真的完成了
  2. 工具使用跟踪（track_usage）：记录LLM实际调用了哪些脚本/读取了哪些文档
  3. 偏差检测（detect_deviation）：检测跳步/浅用/绕流程
  4. 使用率报告（usage_report）：生成工具使用覆盖率报告

核心原理：不是靠LLM自觉遵守规则，而是在运行时监控它的行为，
发现偏差就警告，不完成就拒绝接受输出。

用法：
  python3 runtime_guard.py track --step <步骤名> --action <动作>
  python3 runtime_guard.py verify --required-steps <step1,step2,...>
  python3 runtime_guard.py report
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
SKILL_DIR = HERE.parent
DATA_DIR = Path.home() / f".{SKILL_DIR.name}_runtime"
USAGE_FILE = DATA_DIR / "usage_log.json"
STATE_FILE = DATA_DIR / "state.json"


def ensure_data_dir():
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_usage():
    """加载使用记录"""
    if USAGE_FILE.exists():
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scripts_called": [], "docs_read": [], "steps_completed": [], "route_outputs": [], "started_at": datetime.now().isoformat()}


def save_usage(usage):
    """保存使用记录"""
    ensure_data_dir()
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(usage, f, ensure_ascii=False, indent=2)


def cmd_track(args):
    """记录一个步骤/工具调用"""
    usage = load_usage()
    entry = {
        "step": args.step,
        "action": args.action,
        "timestamp": datetime.now().isoformat(),
    }
    if args.type == "script":
        usage["scripts_called"].append(entry)
    elif args.type == "doc":
        usage["docs_read"].append(entry)
    elif args.type == "step":
        usage["steps_completed"].append(entry)
    save_usage(usage)
    print(f"✅ 已记录: [{args.type}] {args.step} - {args.action}")


def cmd_route(args):
    """记录路由行输出（防LLM忘记输出路由行）
    
    增强功能：
    - 记录完整路由行文本（--line参数）
    - 自动校验路由行格式是否正确
    - 格式错误时给出明确警告
    """
    usage = load_usage()
    
    # 校验路由行格式
    route_line = getattr(args, 'line', None)
    format_valid = True
    format_error = ""
    
    if route_line:
        # 检查是否以"🔀 路由:"开头
        if not route_line.startswith("🔀 路由:"):
            format_valid = False
            format_error = "路由行必须以'🔀 路由:'开头"
        # 检查模式是否合法
        else:
            mode_part = route_line.replace("🔀 路由:", "").strip()
            valid_modes = ["🚫拒绝", "新建技能", "优化技能", "深度评审", "端到端测试"]
            if not any(mode_part.startswith(m) for m in valid_modes):
                format_valid = False
                format_error = f"路由模式'{mode_part}'不合法，必须是{valid_modes}之一"
    
    entry = {
        "mode": args.mode,
        "message": args.message,
        "route_line": route_line,
        "format_valid": format_valid,
        "format_error": format_error,
        "timestamp": datetime.now().isoformat(),
    }
    usage["route_outputs"].append(entry)
    save_usage(usage)
    
    count = len(usage["route_outputs"])
    print(f"✅ 路由行已记录: {args.mode}")
    print(f"   累计输出: {count}次")
    if route_line:
        if format_valid:
            print(f"   格式校验: ✅ 正确")
        else:
            print(f"   格式校验: ❌ 错误 - {format_error}")
            print(f"   正确格式: 🔀 路由: {{模式}}")
    else:
        print(f"   ⚠️ 未传入完整路由行文本（建议用--line参数传入，便于格式校验）")


def cmd_verify(args):
    """完成验证：检查所有必需步骤是否真的完成了"""
    usage = load_usage()
    required = [s.strip() for s in args.required_steps.split(",")]
    completed_steps = [s["step"] for s in usage["steps_completed"]]
    
    missing = [s for s in required if s not in completed_steps]
    
    result = {
        "total_required": len(required),
        "completed": len(required) - len(missing),
        "missing": missing,
        "passed": len(missing) == 0,
    }
    
    if missing:
        result["message"] = f"❌ 必需步骤未完成: {missing}。请继续执行后再提交。"
    else:
        result["message"] = "✅ 所有必需步骤已完成。"
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


def cmd_gate(args):
    """门禁检查器：交付前检查所有硬门禁是否通过
    
    检查项：
    1. 路由行是否输出（route记录）
    2. 路由行格式是否正确
    3. 关键脚本是否调用（根据模式不同）
    4. 关键文档是否阅读（根据模式不同）
    
    退出码：0=全部通过，1=有门禁未通过（严格模式）
    """
    usage = load_usage()
    mode = args.mode
    
    # 定义各模式的关键脚本和文档
    MODE_GATES = {
        "create": {
            "required_scripts": ["init_skill_pro", "validate_skill", "audit_skill"],
            "required_docs": ["best-practices.md", "design-philosophies.md", "36-element-checklist.md"],
            "label": "新建技能",
        },
        "optimize": {
            "required_scripts": ["validate_skill", "audit_skill", "output_validator"],
            "required_docs": ["36-element-checklist.md", "gotchas-collection.md", "best-practices.md"],
            "label": "优化技能",
        },
        "review": {
            "required_scripts": ["validate_skill", "audit_skill"],
            "required_docs": ["36-element-checklist.md", "review-process-guide.md", "best-practices.md"],
            "label": "深度评审",
        },
        "test": {
            "required_scripts": ["validate_skill", "output_validator"],
            "required_docs": ["eval-practice.md", "evaluation-guide.md"],
            "label": "端到端测试",
        },
    }
    
    gate_config = MODE_GATES.get(mode, MODE_GATES["optimize"])
    
    checks = []
    all_passed = True
    
    # 门禁1：路由行是否输出
    route_outputs = usage.get("route_outputs", [])
    route_count = len(route_outputs)
    route_passed = route_count >= args.min_route_outputs
    if not route_passed:
        all_passed = False
    checks.append({
        "gate": "路由行输出",
        "passed": route_passed,
        "detail": f"输出{route_count}次（要求≥{args.min_route_outputs}次）",
        "severity": "critical" if not route_passed else "ok",
    })
    
    # 门禁2：路由行格式是否正确
    if route_outputs:
        format_errors = [r for r in route_outputs if not r.get("format_valid", True)]
        format_passed = len(format_errors) == 0
        if not format_passed:
            all_passed = False
        checks.append({
            "gate": "路由行格式",
            "passed": format_passed,
            "detail": f"{len(route_outputs)-len(format_errors)}/{len(route_outputs)}次格式正确",
            "severity": "high" if not format_passed else "ok",
        })
    else:
        checks.append({
            "gate": "路由行格式",
            "passed": False,
            "detail": "无路由行记录，无法校验格式",
            "severity": "high",
        })
        all_passed = False
    
    # 门禁3：关键脚本是否调用
    called_scripts = set(s["step"] for s in usage.get("scripts_called", []))
    required_scripts = gate_config["required_scripts"]
    missing_scripts = [s for s in required_scripts if s not in called_scripts]
    scripts_passed = len(missing_scripts) == 0
    if not scripts_passed:
        all_passed = False
    checks.append({
        "gate": "关键脚本调用",
        "passed": scripts_passed,
        "detail": f"已调用{len(required_scripts)-len(missing_scripts)}/{len(required_scripts)}个" + 
                  (f"，缺失: {missing_scripts}" if missing_scripts else ""),
        "severity": "high" if not scripts_passed else "ok",
    })
    
    # 门禁4：关键文档是否阅读
    read_docs = set(d["step"] for d in usage.get("docs_read", []))
    required_docs = gate_config["required_docs"]
    missing_docs = [d for d in required_docs if d not in read_docs]
    docs_passed = len(missing_docs) == 0
    if not docs_passed:
        all_passed = False
    checks.append({
        "gate": "关键文档阅读",
        "passed": docs_passed,
        "detail": f"已阅读{len(required_docs)-len(missing_docs)}/{len(required_docs)}个" +
                  (f"，缺失: {missing_docs}" if missing_docs else ""),
        "severity": "medium" if not docs_passed else "ok",
    })
    
    # 输出结果
    print("\n" + "=" * 60)
    print(f"🔒 门禁检查报告（模式: {gate_config['label']}）")
    print("=" * 60)
    
    for check in checks:
        icon = "✅" if check["passed"] else "❌"
        print(f"\n{icon} {check['gate']}")
        print(f"   {check['detail']}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有门禁通过，可以交付")
    else:
        print("❌ 有门禁未通过，不能交付")
        print("💡 请修复上述问题后重新运行 gate 检查")
    print("=" * 60)
    
    # JSON输出
    result = {
        "mode": mode,
        "mode_label": gate_config["label"],
        "checks": checks,
        "all_passed": all_passed,
        "passed_count": sum(1 for c in checks if c["passed"]),
        "total_count": len(checks),
    }
    print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
    
    # 严格模式：任何门禁不通过都exit(1)
    if args.strict and not all_passed:
        return 1
    # 非严格模式：只有critical级别不通过才exit(1)
    critical_failed = any(c["severity"] == "critical" and not c["passed"] for c in checks)
    if critical_failed:
        return 1
    return 0


def cmd_report(args):
    """生成工具使用覆盖率报告"""
    usage = load_usage()
    
    # 统计可用资源
    scripts_dir = SKILL_DIR / "scripts"
    refs_dir = SKILL_DIR / "references"
    
    available_scripts = [f.stem for f in scripts_dir.glob("*.py")] if scripts_dir.exists() else []
    available_docs = [f.name for f in refs_dir.glob("*.md")] if refs_dir.exists() else []
    
    called_scripts = list(set(s["step"] for s in usage["scripts_called"]))
    read_docs = list(set(d["step"] for d in usage["docs_read"]))
    
    script_coverage = len(called_scripts) / len(available_scripts) * 100 if available_scripts else 0
    doc_coverage = len(read_docs) / len(available_docs) * 100 if available_docs else 0
    
    unused_scripts = set(available_scripts) - set(called_scripts)
    unused_docs = set(available_docs) - set(read_docs)
    
    report = {
        "skill": SKILL_DIR.name,
        "total_available_scripts": len(available_scripts),
        "called_scripts": len(called_scripts),
        "script_coverage_pct": round(script_coverage, 1),
        "unused_scripts": sorted(unused_scripts),
        "total_available_docs": len(available_docs),
        "read_docs": len(read_docs),
        "doc_coverage_pct": round(doc_coverage, 1),
        "unused_docs": sorted(unused_docs),
        "steps_completed": len(usage["steps_completed"]),
        "route_outputs": len(usage.get("route_outputs", [])),
        "route_output_modes": list(set(r["mode"] for r in usage.get("route_outputs", []))),
    }
    
    # 偏差检测
    deviations = []
    if script_coverage < 30:
        deviations.append(f"⚠️ 脚本使用率仅{script_coverage:.0f}%，低于30%，可能存在严重偷懒")
    if doc_coverage < 20:
        deviations.append(f"⚠️ 文档使用率仅{doc_coverage:.0f}%，低于20%，可能存在浅用")
    route_count = len(usage.get("route_outputs", []))
    if route_count == 0:
        deviations.append("🔴 路由行输出为0次！LLM完全忘记输出路由行，触发路由机制失效")
    elif route_count < 3:
        deviations.append(f"⚠️ 路由行仅输出{route_count}次，可能存在部分轮次忘记输出")
    
    report["deviations"] = deviations
    report["health"] = "🔴 严重偷懒" if script_coverage < 20 else ("🟡 可能偷懒" if script_coverage < 40 else "🟢 正常")
    
    print(json.dumps(report, ensure_ascii=False, indent=2))


def cmd_reset(args):
    """重置使用记录"""
    if USAGE_FILE.exists():
        USAGE_FILE.unlink()
    print("✅ 使用记录已重置")


def cmd_loop(args):
    """Stop Hook循环验证：不通过就继续，直到通过或达到最大次数"""
    usage = load_usage()
    required = [s.strip() for s in args.required_steps.split(",")]
    completed_steps = [s["step"] for s in usage["steps_completed"]]
    missing = [s for s in required if s not in completed_steps]
    
    iteration = 0
    max_iterations = args.max_iterations
    
    while missing and iteration < max_iterations:
        iteration += 1
        print()
        print(f"🔄 第{iteration}次循环：仍有{len(missing)}步未完成")
        print(f"   缺失步骤: {missing}")
        print(f"   请继续执行，执行完后再次运行此命令")
        print(f"   （按Ctrl+C退出循环）")
        
        # 等待用户执行
        try:
            input("   执行完成后按回车继续验证...")
        except KeyboardInterrupt:
            print("\n⏹️ 用户手动退出循环")
            break
        
        # 重新加载usage
        usage = load_usage()
        completed_steps = [s["step"] for s in usage["steps_completed"]]
        missing = [s for s in required if s not in completed_steps]
    
    if not missing:
        print()
        print(f"✅ 全部{len(required)}步已完成！循环了{iteration}次")
        return 0
    else:
        print()
        print(f"❌ 达到最大循环次数{max_iterations}，仍有{len(missing)}步未完成: {missing}")
        return 1


def cmd_budget(args):
    """执行步骤预算：检查是否超过最大步骤数"""
    usage = load_usage()
    total_steps = len(usage["steps_completed"])
    max_steps = args.max_steps
    
    result = {
        "current_steps": total_steps,
        "max_steps": max_steps,
        "budget_used_pct": round(total_steps / max_steps * 100, 1) if max_steps > 0 else 0,
        "remaining_steps": max_steps - total_steps,
        "over_budget": total_steps > max_steps,
    }
    
    if result["over_budget"]:
        result["warning"] = f"⚠️ 已超过最大步骤数{max_steps}，当前{total_steps}步"
    elif result["budget_used_pct"] > 80:
        result["warning"] = f"⚠️ 步骤预算已用{result['budget_used_pct']}%，剩余{result['remaining_steps']}步"
    else:
        result["status"] = "✅ 步骤预算正常"
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["over_budget"] else 0


def cmd_duplicate(args):
    """重复动作检测：检测是否连续重复相同动作"""
    usage = load_usage()
    recent_actions = usage["steps_completed"][-10:]  # 最近10个动作
    
    if len(recent_actions) < 3:
        print("✅ 动作历史不足3个，无法检测重复")
        return 0
    
    # 检查最近3个动作是否相同
    last_3 = [a["step"] for a in recent_actions[-3:]]
    if len(set(last_3)) == 1:
        print(f"🔴 重复动作警告：最近3次都是「{last_3[0]}」")
        print(f"   你可能卡住了，尝试换个方法或寻求帮助")
        return 1
    
    # 检查最近5个动作中重复率
    last_5 = [a["step"] for a in recent_actions[-5:]]
    from collections import Counter
    counts = Counter(last_5)
    max_repeat = max(counts.values())
    
    if max_repeat >= 4:
        most_common = counts.most_common(1)[0][0]
        print(f"🟡 重复动作警告：最近5次中「{most_common}」出现了{max_repeat}次")
        print(f"   可能效率不高，考虑换个方法")
        return 0
    
    print("✅ 未检测到重复动作模式")
    return 0


def cmd_focus(args):
    """注意力衰减检测：检查是否跑偏了"""
    usage = load_usage()
    total_actions = len(usage["steps_completed"]) + len(usage["scripts_called"])
    
    # 简单的跑偏检测：如果做了很多步但没有关键步骤完成
    if total_actions > 20 and len(usage["steps_completed"]) < 3:
        print("🔴 注意力衰减警告：已执行很多动作，但关键步骤完成很少")
        print(f"   总动作数: {total_actions}")
        print(f"   完成步骤数: {len(usage['steps_completed'])}")
        print(f"   建议：重新读取计划文件（plan.md），确认方向是否正确")
        return 1
    
    if total_actions > 10 and len(usage["steps_completed"]) < 5:
        print("🟡 注意力衰减警告：动作不少，但完成的步骤不多")
        print(f"   总动作数: {total_actions}")
        print(f"   完成步骤数: {len(usage['steps_completed'])}")
        print(f"   建议：回顾一下，是否在做无用功")
        return 0
    
    print("✅ 注意力状态正常，未检测到明显跑偏")
    return 0


def cmd_quantitative(args):
    """定量阈值检查：检查是否达到最低标准"""
    usage = load_usage()
    issues = []
    
    # 定量标准
    min_scripts_used = args.min_scripts or 3
    min_docs_read = args.min_docs or 2
    min_steps_completed = args.min_steps or 5
    
    scripts_used = len(set(s["step"] for s in usage["scripts_called"]))
    docs_read = len(set(d["step"] for d in usage["docs_read"]))
    steps_completed = len(usage["steps_completed"])
    
    if scripts_used < min_scripts_used:
        issues.append(f"❌ 脚本使用不足：仅{scripts_used}个，最低要求{min_scripts_used}个")
    
    if docs_read < min_docs_read:
        issues.append(f"❌ 文档阅读不足：仅{docs_read}个，最低要求{min_docs_read}个")
    
    if steps_completed < min_steps_completed:
        issues.append(f"❌ 步骤完成不足：仅{steps_completed}步，最低要求{min_steps_completed}步")
    
    result = {
        "scripts_used": scripts_used,
        "min_scripts_required": min_scripts_used,
        "docs_read": docs_read,
        "min_docs_required": min_docs_read,
        "steps_completed": steps_completed,
        "min_steps_required": min_steps_completed,
        "issues": issues,
        "passed": len(issues) == 0,
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description="专业级技能创建器 运行时保障（防LLM偷懒）")
    sub = parser.add_subparsers(dest="command")
    
    # track
    track_p = sub.add_parser("track", help="记录步骤/工具调用")
    track_p.add_argument("--step", required=True, help="步骤或工具名称")
    track_p.add_argument("--action", required=True, help="动作描述")
    track_p.add_argument("--type", choices=["script", "doc", "step"], required=True, help="类型")
    
    # route（路由行输出记录）
    route_p = sub.add_parser("route", help="记录路由行输出（防LLM忘记输出路由行）")
    route_p.add_argument("--mode", required=True, help="路由模式（如新建技能/优化技能/深度评审/端到端测试）")
    route_p.add_argument("--message", default="", help="用户消息摘要")
    route_p.add_argument("--line", default="", help="完整路由行文本（用于格式校验，如'🔀 路由: 深度评审'）")
    
    # verify
    verify_p = sub.add_parser("verify", help="完成验证")
    verify_p.add_argument("--required-steps", required=True, help="必需步骤列表（逗号分隔）")
    
    # gate（门禁检查器：检查路由行+关键脚本+关键文档）
    gate_p = sub.add_parser("gate", help="门禁检查器：交付前检查所有硬门禁是否通过")
    gate_p.add_argument("--mode", default="optimize", choices=["create", "optimize", "review", "test"],
                        help="工作模式（决定检查哪些门禁）")
    gate_p.add_argument("--min-route-outputs", type=int, default=1, help="最少路由行输出次数（默认1）")
    gate_p.add_argument("--strict", action="store_true", help="严格模式：任何门禁不通过都exit(1)")
    
    # report
    sub.add_parser("report", help="生成使用覆盖率报告")
    
    # reset
    sub.add_parser("reset", help="重置使用记录")
    
    # loop（Stop Hook循环验证）
    loop_p = sub.add_parser("loop", help="Stop Hook循环验证：不通过就继续")
    loop_p.add_argument("--required-steps", required=True, help="必需步骤列表（逗号分隔）")
    loop_p.add_argument("--max-iterations", type=int, default=10, help="最大循环次数（默认10）")
    
    # budget（执行步骤预算）
    budget_p = sub.add_parser("budget", help="执行步骤预算检查")
    budget_p.add_argument("--max-steps", type=int, required=True, help="最大步骤数")
    
    # duplicate（重复动作检测）
    sub.add_parser("duplicate", help="重复动作检测")
    
    # focus（注意力衰减检测）
    sub.add_parser("focus", help="注意力衰减检测（检查是否跑偏）")
    
    # quantitative（定量阈值检查）
    quant_p = sub.add_parser("quantitative", help="定量阈值检查")
    quant_p.add_argument("--min-scripts", type=int, help="最少脚本使用数")
    quant_p.add_argument("--min-docs", type=int, help="最少文档阅读数")
    quant_p.add_argument("--min-steps", type=int, help="最少步骤完成数")
    
    args = parser.parse_args()
    
    if args.command == "track":
        cmd_track(args)
    elif args.command == "route":
        cmd_route(args)
    elif args.command == "verify":
        sys.exit(cmd_verify(args))
    elif args.command == "gate":
        sys.exit(cmd_gate(args))
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "reset":
        cmd_reset(args)
    elif args.command == "loop":
        sys.exit(cmd_loop(args))
    elif args.command == "budget":
        sys.exit(cmd_budget(args))
    elif args.command == "duplicate":
        sys.exit(cmd_duplicate(args))
    elif args.command == "focus":
        sys.exit(cmd_focus(args))
    elif args.command == "quantitative":
        sys.exit(cmd_quantitative(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
