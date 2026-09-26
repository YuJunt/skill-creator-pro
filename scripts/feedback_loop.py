#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反馈循环管理器（feedback_loop.py）

管理技能优化的完整迭代循环：
  draft → test → review → improve → repeat

用法：
  python3 feedback_loop.py init <skill_path>  # 初始化循环
  python3 feedback_loop.py status <skill_path>  # 查看当前状态
  python3 feedback_loop.py next <skill_path>  # 进入下一步
  python3 feedback_loop.py review <skill_path> --feedback "..."  # 提交反馈
  python3 feedback_loop.py history <skill_path>  # 查看历史
"""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime


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

    # 确保目录存在
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
        print(f"❌ 循环不存在，请先运行 init", file=sys.stderr)
        sys.exit(1)

    with open(loop_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_loop(skill_path, loop):
    """保存循环状态"""
    loop_path = get_loop_path(skill_path)
    with open(loop_path, "w", encoding="utf-8") as f:
        json.dump(loop, f, ensure_ascii=False, indent=2)


def show_status(skill_path):
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

    # 阶段进度
    print("阶段进度:")
    for stage in STAGES:
        marker = "✅" if STAGES.index(stage) < STAGES.index(loop["current_stage"]) else "🔄" if stage == loop["current_stage"] else "⬜"
        print(f"  {marker} {STAGE_NAMES[stage]}")

    print()
    if loop["iterations"]:
        print(f"历史迭代: {len(loop['iterations'])}轮")
        for it in loop["iterations"]:
            print(f"  第{it['iteration']}轮: {it.get('summary', '无摘要')}")


def next_stage(skill_path):
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

    # 如果回到draft，增加迭代次数
    if next_stage_name == "draft":
        loop["current_iteration"] += 1

    save_loop(skill_path, loop)

    print(f"✅ 进入下一阶段: {STAGE_NAMES[next_stage_name]}")
    print(f"   当前迭代: {loop['current_iteration']}")


def submit_feedback(skill_path, feedback):
    """提交反馈"""
    loop = load_loop(skill_path)

    if loop["current_stage"] != "review":
        print(f"⚠️ 当前阶段是{STAGE_NAMES[loop['current_stage']]}，不是评审阶段", file=sys.stderr)
        return

    # 找到当前迭代
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


def show_history(skill_path):
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


def main():
    parser = argparse.ArgumentParser(description="反馈循环管理器")
    sub = parser.add_subparsers(dest="command")

    # init
    sub_init = sub.add_parser("init", help="初始化循环")
    sub_init.add_argument("skill_path", help="技能目录")

    # status
    sub_status = sub.add_parser("status", help="查看状态")
    sub_status.add_argument("skill_path", help="技能目录")

    # next
    sub_next = sub.add_parser("next", help="进入下一阶段")
    sub_next.add_argument("skill_path", help="技能目录")

    # review
    sub_review = sub.add_parser("review", help="提交反馈")
    sub_review.add_argument("skill_path", help="技能目录")
    sub_review.add_argument("--feedback", required=True, help="反馈内容")

    # history
    sub_history = sub.add_parser("history", help="查看历史")
    sub_history.add_argument("skill_path", help="技能目录")

    args = parser.parse_args()

    if args.command == "init":
        init_loop(args.skill_path)
    elif args.command == "status":
        show_status(args.skill_path)
    elif args.command == "next":
        next_stage(args.skill_path)
    elif args.command == "review":
        submit_feedback(args.skill_path, args.feedback)
    elif args.command == "history":
        show_history(args.skill_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
