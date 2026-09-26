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




# ============================================================
# 评分功能（从grader.py合并）
# ============================================================

def load_run_outputs(run_dir):
    """加载运行目录下的所有输出文件"""
    outputs = {}
    run_path = Path(run_dir)
    if not run_path.exists():
        return outputs

    # 读取对话记录
    conversation = run_path / "conversation.txt"
    if conversation.exists():
        outputs["conversation"] = conversation.read_text(encoding="utf-8", errors="replace")

    # 读取输出文件
    output_dir = run_path / "output"
    if output_dir.exists():
        for f in output_dir.glob("**/*"):
            if f.is_file():
                rel_path = str(f.relative_to(output_dir))
                try:
                    outputs[f"output:{rel_path}"] = f.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    outputs[f"output:{rel_path}"] = f"[binary file: {rel_path}]"

    return outputs



def evaluate_expectation(expectation, outputs):
    """评估单个断言"""
    text = expectation.get("text", "")
    check_type = expectation.get("type", "contains")

    # 合并所有输出用于搜索
    all_content = "\n".join(outputs.values())

    if check_type == "contains":
        # 检查是否包含关键词
        keywords = expectation.get("keywords", [])
        if isinstance(keywords, str):
            keywords = [keywords]
        found = all(kw in all_content for kw in keywords)
        return {
            "text": text,
            "passed": found,
            "evidence": f"检查关键词: {keywords}",
            "type": "contains"
        }

    elif check_type == "file_exists":
        # 检查文件是否存在
        filename = expectation.get("filename", "")
        file_key = f"output:{filename}"
        exists = file_key in outputs
        return {
            "text": text,
            "passed": exists,
            "evidence": f"文件 {filename} {'存在' if exists else '不存在'}",
            "type": "file_exists"
        }

    elif check_type == "file_not_empty":
        # 检查文件是否非空
        filename = expectation.get("filename", "")
        file_key = f"output:{filename}"
        content = outputs.get(file_key, "")
        not_empty = len(content.strip()) > 0
        return {
            "text": text,
            "passed": not_empty,
            "evidence": f"文件 {filename} 长度: {len(content)} 字符",
            "type": "file_not_empty"
        }

    elif check_type == "not_contains":
        # 检查不包含敏感词
        forbidden = expectation.get("keywords", [])
        if isinstance(forbidden, str):
            forbidden = [forbidden]
        not_found = all(kw not in all_content for kw in forbidden)
        return {
            "text": text,
            "passed": not_found,
            "evidence": f"检查禁用词: {forbidden}",
            "type": "not_contains"
        }

    elif check_type == "execution":
        # 检查是否执行了正确的动作（官方4种断言之一）
        # 检查输出中是否包含特定的命令/脚本执行痕迹
        actions = expectation.get("actions", [])
        if isinstance(actions, str):
            actions = [actions]
        # 支持多种执行痕迹：命令行调用、脚本名、特定输出标记
        executed = all(
            any(action in content for content in outputs.values())
            for action in actions
        )
        return {
            "text": text,
            "passed": executed,
            "evidence": f"检查执行动作: {actions}",
            "type": "execution"
        }

    elif check_type == "output_quality":
        # 检查输出质量（官方4种断言之一，contains的别名）
        # 检查输出是否包含期望的数据/结构
        requirements = expectation.get("requirements", [])
        if isinstance(requirements, str):
            requirements = [requirements]
        quality_ok = all(req in all_content for req in requirements)
        return {
            "text": text,
            "passed": quality_ok,
            "evidence": f"检查输出质量要求: {requirements}",
            "type": "output_quality"
        }

    else:
        return {
            "text": text,
            "passed": False,
            "evidence": f"未知检查类型: {check_type}",
            "type": "unknown"
        }



def grade_run(run_dir, expectations=None):
    """对单次运行进行评分"""
    outputs = load_run_outputs(run_dir)

    if expectations is None:
        # 自动模式：基本检查
        expectations = [
            {"text": "对话记录存在", "type": "file_exists", "filename": "conversation.txt"},
            {"text": "有输出文件", "type": "contains", "keywords": ["output:"]},
        ]

    results = []
    passed_count = 0
    for exp in expectations:
        result = evaluate_expectation(exp, outputs)
        results.append(result)
        if result["passed"]:
            passed_count += 1

    total = len(results)
    pass_rate = passed_count / total if total > 0 else 0

    grading = {
        "run_dir": str(run_dir),
        "total_expectations": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "pass_rate": round(pass_rate, 2),
        "results": results,
    }

    return grading





def main():
    parser = argparse.ArgumentParser(description="技能评估运行与评分工具")
    sub = parser.add_subparsers(dest="command")
    
    # eval子命令（原run_eval）
    eval_p = sub.add_parser("eval", help="运行评估（触发/选择/边界）")
    eval_p.add_argument("--type", choices=["trigger", "selection", "edge", "all"],
                        default="all", help="评估类型（默认all）")
    eval_p.add_argument("--json", action="store_true", help="JSON格式输出")
    
    # grade子命令（原grader）
    grade_p = sub.add_parser("grade", help="评分单次运行")
    grade_p.add_argument("run_dir", help="运行目录")
    grade_p.add_argument("--expectations", help="期望文件路径")
    grade_p.add_argument("--auto", action="store_true", help="自动模式")
    grade_p.add_argument("--output", help="输出文件")
    
    args = parser.parse_args()
    
    if args.command == "eval":
        # 原run_eval的逻辑
        evals = load_evals()
        results = {}
        
        if args.type in ("trigger", "all"):
            results["trigger"] = run_trigger_eval(evals)
        if args.type in ("selection", "all"):
            results["selection"] = run_selection_eval(evals)
        if args.type in ("edge", "all"):
            results["edge"] = run_edge_eval(evals)
        
        if args.json:
            print("\n" + json.dumps(results, ensure_ascii=False, indent=2))
        
        print("\n" + "=" * 60)
        print("✅ 评估完成")
        print("=" * 60)
        print(f"\n📌 评估用例文件: {EVALS_FILE}")
        print(f"📌 实际LLM实测指南: 逐条输入用例，观察触发/选择/边界处理是否正确")
        print(f"📌 通过标准: 触发率≥90%，模式选择≥85%，边界处理≥80%")
        
    elif args.command == "grade":
        # 原grader的逻辑
        expectations = None
        if args.expectations:
            with open(args.expectations, 'r', encoding='utf-8') as f:
                expectations = json.load(f)
        
        result = grade_run(args.run_dir, expectations)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ 评分结果已写入: {args.output}")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
