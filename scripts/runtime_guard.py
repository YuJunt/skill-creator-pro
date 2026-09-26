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
    return {"scripts_called": [], "docs_read": [], "steps_completed": [], "started_at": datetime.now().isoformat()}


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
    }
    
    # 偏差检测
    deviations = []
    if script_coverage < 30:
        deviations.append(f"⚠️ 脚本使用率仅{script_coverage:.0f}%，低于30%，可能存在严重偷懒")
    if doc_coverage < 20:
        deviations.append(f"⚠️ 文档使用率仅{doc_coverage:.0f}%，低于20%，可能存在浅用")
    
    report["deviations"] = deviations
    report["health"] = "🔴 严重偷懒" if script_coverage < 20 else ("🟡 可能偷懒" if script_coverage < 40 else "🟢 正常")
    
    print(json.dumps(report, ensure_ascii=False, indent=2))


def cmd_reset(args):
    """重置使用记录"""
    if USAGE_FILE.exists():
        USAGE_FILE.unlink()
    print("✅ 使用记录已重置")


def main():
    parser = argparse.ArgumentParser(description="专业级技能创建器 运行时保障（防LLM偷懒）")
    sub = parser.add_subparsers(dest="command")
    
    # track
    track_p = sub.add_parser("track", help="记录步骤/工具调用")
    track_p.add_argument("--step", required=True, help="步骤或工具名称")
    track_p.add_argument("--action", required=True, help="动作描述")
    track_p.add_argument("--type", choices=["script", "doc", "step"], required=True, help="类型")
    
    # verify
    verify_p = sub.add_parser("verify", help="完成验证")
    verify_p.add_argument("--required-steps", required=True, help="必需步骤列表（逗号分隔）")
    
    # report
    sub.add_parser("report", help="生成使用覆盖率报告")
    
    # reset
    sub.add_parser("reset", help="重置使用记录")
    
    args = parser.parse_args()
    
    if args.command == "track":
        cmd_track(args)
    elif args.command == "verify":
        sys.exit(cmd_verify(args))
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "reset":
        cmd_reset(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
