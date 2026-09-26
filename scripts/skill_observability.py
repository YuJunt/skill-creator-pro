#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能使用可观测性脚本（skill_observability.py）

记录技能使用日志：
  - 哪些脚本被调用
  - 哪些references被读取
  - 执行时间
  - 成功/失败

用法：
  python3 skill_observability.py log <skill-name> <action> --result success/fail --detail "..."
  python3 skill_observability.py report <skill-name>
  python3 skill_observability.py stats
"""
import argparse
import json
import os
import sys
from datetime import datetime


def get_log_dir():
    """获取日志目录"""
    log_dir = os.path.expanduser("~/.skill_observability")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def log_usage(skill_name, action, result="success", detail="", duration=0):
    """记录一次技能使用"""
    log_file = os.path.join(get_log_dir(), f"{skill_name}.jsonl")
    entry = {
        "timestamp": datetime.now().isoformat(),
        "skill": skill_name,
        "action": action,
        "result": result,
        "detail": detail,
        "duration_sec": round(duration, 2),
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_logs(skill_name=None):
    """读取日志"""
    log_dir = get_log_dir()
    logs = []
    if skill_name:
        files = [os.path.join(log_dir, f"{skill_name}.jsonl")]
    else:
        files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".jsonl")]

    for fp in files:
        if not os.path.isfile(fp):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return logs


def generate_report(skill_name):
    """生成技能使用报告"""
    logs = read_logs(skill_name)
    if not logs:
        return {"skill": skill_name, "total_uses": 0, "message": "无使用记录"}

    total = len(logs)
    success = sum(1 for l in logs if l.get("result") == "success")
    fail = total - success
    by_action = {}
    total_duration = 0

    for l in logs:
        action = l.get("action", "unknown")
        by_action[action] = by_action.get(action, 0) + 1
        total_duration += l.get("duration_sec", 0)

    return {
        "skill": skill_name,
        "total_uses": total,
        "success": success,
        "fail": fail,
        "success_rate": round(success / total * 100, 1) if total else 0,
        "avg_duration_sec": round(total_duration / total, 2) if total else 0,
        "by_action": by_action,
        "last_used": logs[-1].get("timestamp", "") if logs else "",
    }


def main():
    parser = argparse.ArgumentParser(description="技能使用可观测性")
    sub = parser.add_subparsers(dest="command")

    # log
    log_p = sub.add_parser("log")
    log_p.add_argument("skill_name")
    log_p.add_argument("action")
    log_p.add_argument("--result", default="success", choices=["success", "fail"])
    log_p.add_argument("--detail", default="")
    log_p.add_argument("--duration", type=float, default=0)

    # report
    rep_p = sub.add_parser("report")
    rep_p.add_argument("skill_name")

    # feedback
    fb_p = sub.add_parser("feedback")
    fb_p.add_argument("skill_name")
    fb_p.add_argument("rating", type=int, choices=[1, 2, 3, 4, 5], help="1-5分")
    fb_p.add_argument("--comment", default="")

    # improve（基于统计生成改进建议）
    imp_p = sub.add_parser("improve")
    imp_p.add_argument("skill_name")

    # stats
    sub.add_parser("stats")

    args = parser.parse_args()

    if args.command == "log":
        entry = log_usage(args.skill_name, args.action, args.result, args.detail, args.duration)
        print(json.dumps(entry, ensure_ascii=False, indent=2))

    elif args.command == "report":
        report = generate_report(args.skill_name)
        print(json.dumps(report, ensure_ascii=False, indent=2))

    elif args.command == "stats":
        logs = read_logs()
        skills = set(l.get("skill", "") for l in logs)
        summary = {}
        for s in skills:
            r = generate_report(s)
            summary[s] = {
                "total": r.get("total_uses", 0),
                "success_rate": r.get("success_rate", 0),
            }
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    elif args.command == "feedback":
        entry = log_usage(args.skill_name, "user_feedback", "success" if args.rating >= 3 else "fail",
                          f"rating={args.rating}: {args.comment}")
        print(f"✅ 反馈已记录: {args.rating}/5")

    elif args.command == "improve":
        logs = read_logs(args.skill_name)
        feedbacks = [l for l in logs if l.get("action") == "user_feedback"]
        fails = [l for l in logs if l.get("result") == "fail" and l.get("action") != "user_feedback"]

        suggestions = []
        if feedbacks:
            avg_rating = sum(int(l.get("detail", "rating=3:").split("=")[1].split(":")[0]) for l in feedbacks) / len(feedbacks)
            if avg_rating < 3:
                suggestions.append(f"⚠️ 平均评分{avg_rating:.1f}/5，需要改进输出质量")
            elif avg_rating < 4:
                suggestions.append(f"平均评分{avg_rating:.1f}/5，有提升空间")
            else:
                suggestions.append(f"✅ 平均评分{avg_rating:.1f}/5，表现良好")

        if len(fails) > len(logs) * 0.2:
            suggestions.append(f"⚠️ 失败率{len(fails)/len(logs)*100:.0f}%，检查错误处理")

        if not suggestions:
            suggestions.append("✅ 无明显改进建议，继续保持")

        print(json.dumps({
            "skill": args.skill_name,
            "total_feedback": len(feedbacks),
            "total_failures": len(fails),
            "suggestions": suggestions,
        }, ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
