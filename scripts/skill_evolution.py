#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能自进化工具（skill_evolution.py）

整合使用可观测性与反馈循环管理，帮助技能建立持续优化的自进化能力。

功能分为两部分：
  1. 可观测性：记录使用日志、生成报告、提取经验
  2. 反馈循环：管理技能优化的完整迭代循环（draft→test→review→improve→done）

用法：
  # 可观测性
  python3 skill_evolution.py log <skill-name> <action> --result success/fail
  python3 skill_evolution.py report <skill-name>
  python3 skill_evolution.py stats
  python3 skill_evolution.py improve <skill-name>
  python3 skill_evolution.py extract-gotchas <skill-name>

  # 反馈循环
  python3 skill_evolution.py loop-init <skill-path>
  python3 skill_evolution.py loop-status <skill-path>
  python3 skill_evolution.py loop-next <skill-path>
  python3 skill_evolution.py loop-review <skill-path> --feedback "..."
  python3 skill_evolution.py loop-history <skill-path>
"""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime


# ============================================================
# 第一部分：可观测性（Observability）
# ============================================================

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


def cmd_improve(skill_name):
    """基于统计生成改进建议"""
    logs = read_logs(skill_name)
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
        "skill": skill_name,
        "total_feedback": len(feedbacks),
        "total_failures": len(fails),
        "suggestions": suggestions,
    }, ensure_ascii=False, indent=2))


def cmd_extract_gotchas(skill_name):
    """从使用日志中自动提取潜在Gotchas"""
    logs = read_logs(skill_name)
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
        if len(action_fails) >= 2:
            details = [f.get("detail", "") for f in action_fails if f.get("detail")]
            common_detail = details[0] if details else "执行失败"

            potential_gotchas.append({
                "id": f"GOTCHA-{gid:03d}",
                "trigger_action": action,
                "failure_count": len(action_fails),
                "symptom": f"执行{action}时反复失败（{len(action_fails)}次），常见错误：{common_detail[:100]}",
                "fix": f"检查{action}的输入参数和前置条件，添加错误处理和降级机制",
                "cause": f"该动作缺少充分的错误处理或前置校验",
                "confidence": "高" if len(action_fails) >= 5 else "中",
            })
            gid += 1

    # 从低评分反馈中提取
    for fb in feedbacks[:3]:
        comment = fb.get("detail", "").split(":", 1)[-1].strip() if ":" in fb.get("detail", "") else fb.get("detail", "")
        if comment and len(comment) > 5:
            potential_gotchas.append({
                "id": f"GOTCHA-{gid:03d}",
                "trigger_action": "user_feedback",
                "failure_count": 1,
                "symptom": f"用户低评分反馈：{comment[:100]}",
                "fix": "分析用户反馈的具体问题，更新技能的输出格式或工作流程",
                "cause": "技能的输出或行为不符合用户预期",
                "confidence": "中",
            })
            gid += 1

    result = {
        "skill": skill_name,
        "total_logs": len(logs),
        "total_failures": len(fails),
        "low_rating_feedback": len(feedbacks),
        "potential_gotchas_count": len(potential_gotchas),
        "potential_gotchas": potential_gotchas,
        "next_step": "请人工审核以上潜在Gotchas，确认后添加到技能的Gotchas section",
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


# ============================================================
# 第二部分：反馈循环（Feedback Loop）
# ============================================================

STAGES = ["draft", "test", "review", "improve", "done"]
STAGE_NAMES = {
    "draft": "草稿阶段",
    "test": "测试阶段",
    "review": "评审阶段",
    "improve": "改进阶段",
    "done": "完成",
}


def get_loop_path(skill_path):
    """获取循环状态文件路径"""
    return Path(skill_path) / ".feedback_loop.json"


def init_loop(skill_path):
    """初始化循环"""
    loop_path = get_loop_path(skill_path)
    loop_path.parent.mkdir(parents=True, exist_ok=True)

    if loop_path.exists():
        print(f"⚠️ 循环已存在: {loop_path}")
        return

    loop = {
        "skill_path": skill_path,
        "created_at": datetime.now().isoformat(),
        "current_stage": "draft",
        "current_iteration": 1,
        "iterations": [],
        "history": [],
    }

    with open(loop_path, "w", encoding="utf-8") as f:
        json.dump(loop, f, ensure_ascii=False, indent=2)

    print(f"✅ 循环已初始化: {loop_path}")
    print(f"   当前阶段: {STAGE_NAMES['draft']}")


def load_loop(skill_path):
    """加载循环状态"""
    loop_path = get_loop_path(skill_path)
    if not loop_path.exists():
        print(f"❌ 循环不存在，请先运行 loop-init", file=sys.stderr)
        sys.exit(1)

    with open(loop_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_loop(skill_path, loop):
    """保存循环状态"""
    loop_path = get_loop_path(skill_path)
    with open(loop_path, "w", encoding="utf-8") as f:
        json.dump(loop, f, ensure_ascii=False, indent=2)


def show_loop_status(skill_path):
    """查看当前状态"""
    loop = load_loop(skill_path)

    print("=" * 60)
    print("📊 反馈循环状态")
    print("=" * 60)
    print(f"技能: {loop['skill_path']}")
    print(f"创建时间: {loop['created_at']}")
    print(f"当前迭代: {loop['current_iteration']}")
    print(f"当前阶段: {STAGE_NAMES[loop['current_stage']]}")
    print()

    print("阶段进度:")
    for stage in STAGES:
        marker = "✅" if STAGES.index(stage) < STAGES.index(loop["current_stage"]) else "🔄" if stage == loop["current_stage"] else "⬜"
        print(f"  {marker} {STAGE_NAMES[stage]}")

    print()
    if loop["iterations"]:
        print(f"历史迭代: {len(loop['iterations'])}轮")
        for it in loop["iterations"]:
            print(f"  第{it['iteration']}轮: {it.get('summary', '无摘要')}")


def next_loop_stage(skill_path):
    """进入下一阶段"""
    loop = load_loop(skill_path)
    current_idx = STAGES.index(loop["current_stage"])

    if current_idx >= len(STAGES) - 1:
        print("✅ 已完成所有阶段")
        return

    next_idx = current_idx + 1
    next_stage_name = STAGES[next_idx]

    loop["history"].append({
        "timestamp": datetime.now().isoformat(),
        "action": "next_stage",
        "from": loop["current_stage"],
        "to": next_stage_name,
        "iteration": loop["current_iteration"],
    })

    loop["current_stage"] = next_stage_name

    if next_stage_name == "draft":
        loop["current_iteration"] += 1

    save_loop(skill_path, loop)

    print(f"✅ 进入下一阶段: {STAGE_NAMES[next_stage_name]}")
    print(f"   当前迭代: {loop['current_iteration']}")


def submit_loop_feedback(skill_path, feedback):
    """提交反馈"""
    loop = load_loop(skill_path)

    if loop["current_stage"] != "review":
        print(f"⚠️ 当前阶段是{STAGE_NAMES[loop['current_stage']]}，不是评审阶段", file=sys.stderr)
        return

    current_iter = loop["current_iteration"]
    iteration_data = None
    for it in loop["iterations"]:
        if it["iteration"] == current_iter:
            iteration_data = it
            break

    if not iteration_data:
        iteration_data = {
            "iteration": current_iter,
            "feedback": [],
            "summary": "",
        }
        loop["iterations"].append(iteration_data)

    iteration_data["feedback"].append({
        "timestamp": datetime.now().isoformat(),
        "content": feedback,
    })

    loop["history"].append({
        "timestamp": datetime.now().isoformat(),
        "action": "submit_feedback",
        "iteration": current_iter,
        "feedback": feedback,
    })

    save_loop(skill_path, loop)

    print(f"✅ 反馈已提交")
    print(f"   迭代: {current_iter}")
    print(f"   反馈: {feedback[:100]}...")


def show_loop_history(skill_path):
    """查看历史"""
    loop = load_loop(skill_path)

    print("=" * 60)
    print("📜 循环历史")
    print("=" * 60)

    for entry in loop["history"]:
        timestamp = entry.get("timestamp", "")
        action = entry.get("action", "")
        iteration = entry.get("iteration", "")

        if action == "next_stage":
            print(f"  [{timestamp}] 迭代{iteration}: {STAGE_NAMES[entry['from']]} → {STAGE_NAMES[entry['to']]}")
        elif action == "submit_feedback":
            print(f"  [{timestamp}] 迭代{iteration}: 提交反馈 - {entry.get('feedback', '')[:50]}")
        else:
            print(f"  [{timestamp}] {action}")


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="技能自进化工具（可观测性+反馈循环）")
    sub = parser.add_subparsers(dest="command")

    # --- 可观测性子命令 ---
    log_p = sub.add_parser("log", help="记录使用日志")
    log_p.add_argument("skill_name")
    log_p.add_argument("action")
    log_p.add_argument("--result", default="success", choices=["success", "fail"])
    log_p.add_argument("--detail", default="")
    log_p.add_argument("--duration", type=float, default=0)

    rep_p = sub.add_parser("report", help="生成使用报告")
    rep_p.add_argument("skill_name")

    fb_p = sub.add_parser("feedback", help="记录用户反馈")
    fb_p.add_argument("skill_name")
    fb_p.add_argument("rating", type=int, choices=[1, 2, 3, 4, 5])
    fb_p.add_argument("--comment", default="")

    imp_p = sub.add_parser("improve", help="生成改进建议")
    imp_p.add_argument("skill_name")

    eg_p = sub.add_parser("extract-gotchas", help="从日志中提取潜在Gotchas")
    eg_p.add_argument("skill_name")

    sub.add_parser("stats", help="全局统计")

    # --- 反馈循环子命令 ---
    loop_init = sub.add_parser("loop-init", help="初始化反馈循环")
    loop_init.add_argument("skill_path")

    loop_status = sub.add_parser("loop-status", help="查看循环状态")
    loop_status.add_argument("skill_path")

    loop_next = sub.add_parser("loop-next", help="进入下一阶段")
    loop_next.add_argument("skill_path")

    loop_review = sub.add_parser("loop-review", help="提交反馈")
    loop_review.add_argument("skill_path")
    loop_review.add_argument("--feedback", required=True)

    loop_history = sub.add_parser("loop-history", help="查看循环历史")
    loop_history.add_argument("skill_path")

    args = parser.parse_args()

    # 可观测性命令
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
            summary[s] = {"total": r.get("total_uses", 0), "success_rate": r.get("success_rate", 0)}
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.command == "feedback":
        entry = log_usage(args.skill_name, "user_feedback", "success" if args.rating >= 3 else "fail",
                          f"rating={args.rating}: {args.comment}")
        print(f"✅ 反馈已记录: {args.rating}/5")
    elif args.command == "improve":
        cmd_improve(args.skill_name)
    elif args.command == "extract-gotchas":
        cmd_extract_gotchas(args.skill_name)

    # 反馈循环命令
    elif args.command == "loop-init":
        init_loop(args.skill_path)
    elif args.command == "loop-status":
        show_loop_status(args.skill_path)
    elif args.command == "loop-next":
        next_loop_stage(args.skill_path)
    elif args.command == "loop-review":
        submit_loop_feedback(args.skill_path, args.feedback)
    elif args.command == "loop-history":
        show_loop_history(args.skill_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
