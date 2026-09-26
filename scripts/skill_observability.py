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

    # extract-gotchas（从使用日志中自动提取潜在Gotchas）
    eg_p = sub.add_parser("extract-gotchas", help="从使用日志中自动提取潜在的Gotchas建议")
    eg_p.add_argument("skill_name")

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

    elif args.command == "extract-gotchas":
        """从使用日志中提取潜在的Gotchas（自动经验提取）"""
        logs = read_logs(args.skill_name)
        fails = [l for l in logs if l.get("result") == "fail" and l.get("action") != "user_feedback"]
        feedbacks = [l for l in logs if l.get("action") == "user_feedback" and int(l.get("detail", "rating=3:").split("=")[1].split(":")[0]) < 3]

        # 按action分类失败
        fail_by_action = {}
        for f in fails:
            action = f.get("action", "unknown")
            if action not in fail_by_action:
                fail_by_action[action] = []
            fail_by_action[action].append(f)

        # 生成潜在的Gotchas建议
        potential_gotchas = []
        gid = 1
        for action, action_fails in fail_by_action.items():
            if len(action_fails) >= 2:  # 同一动作失败≥2次，值得提取为gotcha
                # 收集失败详情
                details = [f.get("detail", "") for f in action_fails if f.get("detail")]
                common_detail = details[0] if details else "执行失败"

                potential_gotchas.append({
                    "id": f"GOTCHA-{gid:03d}",
                    "trigger_action": action,
                    "failure_count": len(action_fails),
                    "symptom": f"执行{action}时反复失败（{len(action_fails)}次），常见错误：{common_detail[:100]}",
                    "fix": f"检查{action}的输入参数和前置条件，添加错误处理和降级机制；如果是技能本身的问题，更新SKILL.md的Gotchas section",
                    "cause": f"该动作缺少充分的错误处理或前置校验，导致同一问题反复出现",
                    "confidence": "高" if len(action_fails) >= 5 else "中",
                })
                gid += 1

        # 从低评分反馈中提取
        for fb in feedbacks[:3]:  # 最多取3条低评分反馈
            comment = fb.get("detail", "").split(":", 1)[-1].strip() if ":" in fb.get("detail", "") else fb.get("detail", "")
            if comment and len(comment) > 5:
                potential_gotchas.append({
                    "id": f"GOTCHA-{gid:03d}",
                    "trigger_action": "user_feedback",
                    "failure_count": 1,
                    "symptom": f"用户低评分反馈：{comment[:100]}",
                    "fix": "分析用户反馈的具体问题，更新技能的输出格式或工作流程，确保下次不再出现同样问题",
                    "cause": "技能的输出或行为不符合用户预期，需要从用户反馈中学习改进",
                    "confidence": "中",
                })
                gid += 1

        result = {
            "skill": args.skill_name,
            "total_logs": len(logs),
            "total_failures": len(fails),
            "low_rating_feedback": len(feedbacks),
            "potential_gotchas_count": len(potential_gotchas),
            "potential_gotchas": potential_gotchas,
            "next_step": "请人工审核以上潜在Gotchas，确认后添加到技能的references/gotchas-collection.md和SKILL.md的Gotchas section",
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
