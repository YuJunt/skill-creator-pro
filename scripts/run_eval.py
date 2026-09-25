#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-creator-pro 评估脚本（借鉴agent-plugin-creator的评估体系）

支持3种评估类型：
  - trigger: 触发评估（should_trigger/should_not_trigger/adversarial）
  - selection: 选择评估（模式选择正确性）
  - edge: 边界评估（异常输入处理）
  - all: 运行全部评估

用法：
  python3 scripts/run_eval.py --type trigger
  python3 scripts/run_eval.py --type selection
  python3 scripts/run_eval.py --type edge
  python3 scripts/run_eval.py --type all
  python3 scripts/run_eval.py --type all --json  # JSON格式输出
"""
import argparse
import json
import os
import sys
import contextlib

# 技能根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVALS_FILE = os.path.join(SKILL_ROOT, "evals", "evals.json")


def load_evals():
    """加载评估用例"""
    if not os.path.isfile(EVALS_FILE):
        print(f"❌ 评估用例文件不存在: {EVALS_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(EVALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_trigger_eval(evals):
    """触发评估"""
    print("\n" + "=" * 60)
    print("🔀 触发评估（Trigger Evaluation）")
    print("=" * 60)

    trigger_data = evals.get("trigger_eval", {})
    should_trigger = trigger_data.get("should_trigger", [])
    should_not_trigger = trigger_data.get("should_not_trigger", [])
    adversarial = trigger_data.get("adversarial", [])

    print(f"\n📊 评估用例统计:")
    print(f"  应触发: {len(should_trigger)} 条")
    print(f"  不应触发: {len(should_not_trigger)} 条")
    print(f"  危险请求(adversarial): {len(adversarial)} 条")
    print(f"  总计: {len(should_trigger) + len(should_not_trigger) + len(adversarial)} 条")

    # 关键词匹配模拟触发判断（用于验证用例格式，实际触发率需LLM实测）
    trigger_keywords = ["技能", "skill", "创建", "优化", "评审", "审计", "测试", "重构", "改进", "成熟度"]
    adversarial_keywords = ["api key", "token", "私钥", "密码", "硬编码", "偷偷", "隐藏指令", "覆盖系统", "eval", "收集用户"]

    print(f"\n🔍 关键词匹配模拟（验证用例合理性，非最终结果）:")
    trigger_pass = 0
    not_trigger_pass = 0
    adversarial_pass = 0

    for case in should_trigger:
        input_lower = case["input"].lower()
        matched = any(kw in input_lower for kw in trigger_keywords)
        if matched:
            trigger_pass += 1
        else:
            print(f"  ⚠️  {case['id']}: 未匹配到触发关键词 - \"{case['input']}\"")

    for case in should_not_trigger:
        input_lower = case["input"].lower()
        matched = any(kw in input_lower for kw in trigger_keywords)
        if not matched:
            not_trigger_pass += 1
        else:
            print(f"  ⚠️  {case['id']}: 意外匹配到触发关键词 - \"{case['input']}\"")

    for case in adversarial:
        input_lower = case["input"].lower()
        matched = any(kw in input_lower for kw in adversarial_keywords)
        if matched:
            adversarial_pass += 1
        else:
            print(f"  ⚠️  {case['id']}: 未匹配到危险关键词 - \"{case['input']}\"")

    print(f"\n✅ 模拟匹配结果:")
    print(f"  应触发匹配率: {trigger_pass}/{len(should_trigger)} ({trigger_pass/len(should_trigger)*100:.0f}%)")
    print(f"  不应触发匹配率: {not_trigger_pass}/{len(should_not_trigger)} ({not_trigger_pass/len(should_not_trigger)*100:.0f}%)")
    print(f"  危险请求匹配率: {adversarial_pass}/{len(adversarial)} ({adversarial_pass/len(adversarial)*100:.0f}%)")

    print(f"\n💡 实际触发率需要在LLM环境中实测，本脚本仅验证用例格式和合理性。")
    print(f"   实测方法：逐条输入用户消息，观察技能是否触发、模式选择是否正确。")

    return {
        "should_trigger_total": len(should_trigger),
        "should_trigger_matched": trigger_pass,
        "should_not_trigger_total": len(should_not_trigger),
        "should_not_trigger_matched": not_trigger_pass,
        "adversarial_total": len(adversarial),
        "adversarial_matched": adversarial_pass,
    }


def run_selection_eval(evals):
    """选择评估"""
    print("\n" + "=" * 60)
    print("🎯 选择评估（Selection Evaluation）")
    print("=" * 60)

    selection_data = evals.get("selection_eval", {})
    test_cases = selection_data.get("test_cases", [])

    print(f"\n📊 评估用例统计: {len(test_cases)} 条")

    print(f"\n📋 用例列表:")
    for case in test_cases:
        print(f"  {case['id']}: \"{case['input']}\"")
        print(f"       预期模式: {case['expected_mode']}")
        print(f"       必读文档: {', '.join(case.get('must_read', []))}")

    print(f"\n💡 模式选择正确率需要在LLM环境中实测。")
    print(f"   通过标准：模式选择准确率 ≥ 85%，must_read引用率 100%。")

    return {
        "total": len(test_cases),
        "test_cases": [{"id": c["id"], "input": c["input"], "expected_mode": c["expected_mode"]} for c in test_cases],
    }


def run_edge_eval(evals):
    """边界评估"""
    print("\n" + "=" * 60)
    print("🔲 边界评估（Edge Evaluation）")
    print("=" * 60)

    edge_data = evals.get("edge_eval", {})
    test_cases = edge_data.get("test_cases", [])

    print(f"\n📊 评估用例统计: {len(test_cases)} 条")

    print(f"\n📋 用例列表:")
    for case in test_cases:
        print(f"  {case['id']}: [{case['description']}]")
        print(f"       输入: \"{case['input']}\"")
        print(f"       预期行为: {case['expected_behavior']}")

    print(f"\n💡 边界处理正确率需要在LLM环境中实测。")
    print(f"   通过标准：边界情况处理正确率 ≥ 80%，不崩溃/不输出无效内容。")

    return {
        "total": len(test_cases),
        "test_cases": [{"id": c["id"], "description": c["description"], "input": c["input"]} for c in test_cases],
    }


def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 评估脚本（触发/选择/边界评估）"
    )
    parser.add_argument("--type", choices=["trigger", "selection", "edge", "all"],
                        default="all", help="评估类型（默认all）")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    evals = load_evals()
    results = {}

    # --json模式：抑制所有普通文本输出，只输出纯JSON
    if args.json:
        try:
            with open(os.devnull, "w") as devnull:
                with contextlib.redirect_stdout(devnull):
                    if args.type in ("trigger", "all"):
                        results["trigger"] = run_trigger_eval(evals)
                    if args.type in ("selection", "all"):
                        results["selection"] = run_selection_eval(evals)
                    if args.type in ("edge", "all"):
                        results["edge"] = run_edge_eval(evals)
        except Exception as e:
            print(json.dumps({"error": f"评估执行失败: {str(e)}"}, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        # 只输出纯JSON，不带任何前缀文本
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if args.type in ("trigger", "all"):
        results["trigger"] = run_trigger_eval(evals)
    if args.type in ("selection", "all"):
        results["selection"] = run_selection_eval(evals)
    if args.type in ("edge", "all"):
        results["edge"] = run_edge_eval(evals)

    print("\n" + "=" * 60)
    print("✅ 评估完成")
    print("=" * 60)
    print(f"\n📌 评估用例文件: {EVALS_FILE}")
    print(f"📌 实际LLM实测指南: 逐条输入用例，观察触发/选择/边界处理是否正确")
    print(f"📌 通过标准: 触发率≥90%，模式选择≥85%，边界处理≥80%")


if __name__ == "__main__":
    main()
