#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型测试自动化模板（multi_model_test.py）

skill-creator-pro 跨模型鲁棒性测试工具。帮助用户落地多模型测试，
验证技能在不同模型下的触发率、路由输出率、流程完整性和输出质量是否一致。

用法：
  # 初始化测试模板
  python3 scripts/multi_model_test.py init --skill-path <skill> --models "Claude,GPT-4,Gemini"

  # 记录测试结果
  python3 scripts/multi_model_test.py record --test-dir <dir> --model Claude --case T1 --triggered yes --routed yes --completed yes --quality 85

  # 生成跨模型对比报告
  python3 scripts/multi_model_test.py report --test-dir <dir>

  # 查看测试状态
  python3 scripts/multi_model_test.py status --test-dir <dir>
"""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime


# 默认测试用例模板（从multi-model-testing-guide.md提取）
DEFAULT_TEST_CASES = [
    # 触发率测试（应触发）
    {"id": "T1", "category": "trigger", "input": "帮我创建一个技能", "expected_trigger": True, "style": "直接明确"},
    {"id": "T2", "category": "trigger", "input": "这个技能有什么问题", "expected_trigger": True, "style": "口语化"},
    {"id": "T3", "category": "trigger", "input": "优化一下我的skill", "expected_trigger": True, "style": "中英混合"},
    {"id": "T4", "category": "trigger", "input": "帮我看看这个技能还能怎么改进", "expected_trigger": True, "style": "长句口语"},
    {"id": "T5", "category": "trigger", "input": "技能审计", "expected_trigger": True, "style": "极简关键词"},
    {"id": "T6", "category": "trigger", "input": "review my skill", "expected_trigger": True, "style": "英文"},
    {"id": "T7", "category": "trigger", "input": "测试一下这个技能的质量", "expected_trigger": True, "style": "间接表达"},
    {"id": "T8", "category": "trigger", "input": "我想做一个自定义技能", "expected_trigger": True, "style": "意图表达"},
    # 触发率测试（不应触发）
    {"id": "T9", "category": "trigger", "input": "今天天气怎么样", "expected_trigger": False, "style": "无关对话"},
    {"id": "T10", "category": "trigger", "input": "帮我写个prompt", "expected_trigger": False, "style": "相关但不匹配"},
    # 路由输出率测试
    {"id": "R1", "category": "routing", "input": "帮我优化这个技能", "expected_route": "优化技能"},
    {"id": "R2", "category": "routing", "input": "创建一个新技能", "expected_route": "新建技能"},
    {"id": "R3", "category": "routing", "input": "评审一下这个技能", "expected_route": "深度评审"},
    {"id": "R4", "category": "routing", "input": "测试技能效果", "expected_route": "端到端测试"},
    # 流程完整性测试
    {"id": "F1", "category": "flow", "input": "完整优化这个技能，包括规范校验和安全扫描", "expected_steps": ["路由", "需求分析", "规范校验", "深度审计", "安全扫描", "输出报告"]},
    {"id": "F2", "category": "flow", "input": "创建一个新技能，然后测试它", "expected_steps": ["路由", "模板生成", "内容编写", "规范校验", "端到端测试"]},
    # 输出质量测试
    {"id": "Q1", "category": "quality", "input": "优化这个技能，给出详细报告", "expected_quality": "包含问题清单+改进建议+验证结果"},
    {"id": "Q2", "category": "quality", "input": "创建一个数据分析技能", "expected_quality": "包含完整SKILL.md+脚本+references"},
]


def init_test(skill_path, models):
    """初始化多模型测试目录"""
    try:
        skill_name = os.path.basename(skill_path)
        test_dir = Path(skill_path) / "multi_model_test"
        test_dir.mkdir(exist_ok=True)

        # 解析模型列表
        model_list = [m.strip() for m in models.split(",") if m.strip()]

        # 创建测试配置
        config = {
            "skill_name": skill_name,
            "skill_path": skill_path,
            "created_at": datetime.now().isoformat(),
            "models": model_list,
            "test_cases": DEFAULT_TEST_CASES,
            "pass_criteria": {
                "trigger_rate_min": 0.90,
                "false_trigger_rate_max": 0.10,
                "trigger_rate_diff_max": 0.10,
                "routing_rate_min": 0.90,
                "flow_completion_min": 0.85,
                "quality_diff_max": 0.15,
                "error_recovery_min": 0.80,
            }
        }

        config_path = test_dir / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # 为每个模型创建结果文件
        for model in model_list:
            model_file = test_dir / f"results_{model.replace(' ', '_').replace('/', '_')}.json"
            if not model_file.exists():
                with open(model_file, "w", encoding="utf-8") as f:
                    json.dump({"model": model, "results": {}}, f, ensure_ascii=False, indent=2)

        print(f"✅ 多模型测试已初始化: {test_dir}")
        print(f"   技能: {skill_name}")
        print(f"   模型: {', '.join(model_list)}")
        print(f"   测试用例: {len(DEFAULT_TEST_CASES)}个")
        print(f"   配置文件: {config_path}")
        print()
        print("📋 下一步：")
        print("  1. 在每个模型下运行测试用例")
        print("  2. 用 record 命令记录结果")
        print("  3. 用 report 命令生成对比报告")
        return test_dir
    except Exception as e:
        print(f"❌ 初始化失败: {e}", file=sys.stderr)
        sys.exit(1)


def record_result(test_dir, model, case_id, triggered=None, routed=None, completed=None, quality=None, route=None, notes=None):
    """记录单个测试用例的结果"""
    try:
        test_dir = Path(test_dir)
        model_file = test_dir / f"results_{model.replace(' ', '_').replace('/', '_')}.json"

        if not model_file.exists():
            print(f"❌ 模型结果文件不存在: {model_file}", file=sys.stderr)
            print("   请先运行 init 命令初始化测试", file=sys.stderr)
            sys.exit(1)

        with open(model_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        result = {
            "case_id": case_id,
            "recorded_at": datetime.now().isoformat(),
        }

        if triggered is not None:
            result["triggered"] = triggered.lower() in ["yes", "true", "1", "y"]
        if routed is not None:
            result["routed"] = routed.lower() in ["yes", "true", "1", "y"]
        if completed is not None:
            result["completed"] = completed.lower() in ["yes", "true", "1", "y"]
        if quality is not None:
            result["quality_score"] = float(quality)
        if route is not None:
            result["route"] = route
        if notes is not None:
            result["notes"] = notes

        data["results"][case_id] = result

        with open(model_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 已记录: {model} / {case_id}")
        if triggered is not None:
            print(f"   触发: {'✅' if result['triggered'] else '❌'}")
        if routed is not None:
            print(f"   路由: {'✅' if result['routed'] else '❌'}")
        if completed is not None:
            print(f"   完成: {'✅' if result['completed'] else '❌'}")
        if quality is not None:
            print(f"   质量: {quality}/100")
    except Exception as e:
        print(f"❌ 记录失败: {e}", file=sys.stderr)
        sys.exit(1)


def generate_report(test_dir):
    """生成跨模型对比报告"""
    test_dir = Path(test_dir)
    config_file = test_dir / "config.json"

    if not config_file.exists():
        print(f"❌ 测试配置不存在: {config_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 读取配置失败: {e}", file=sys.stderr)
        sys.exit(1)

    models = config["models"]
    test_cases = config["test_cases"]
    pass_criteria = config["pass_criteria"]

    # 加载所有模型的结果
    all_results = {}
    for model in models:
        model_file = test_dir / f"results_{model.replace(' ', '_').replace('/', '_')}.json"
        if model_file.exists():
            with open(model_file, "r", encoding="utf-8") as f:
                all_results[model] = json.load(f).get("results", {})
        else:
            all_results[model] = {}

    # 计算各模型的指标
    model_metrics = {}
    for model in models:
        results = all_results[model]
        metrics = {
            "total_cases": len(test_cases),
            "tested_cases": len(results),
            "trigger_should": 0,
            "trigger_should_pass": 0,
            "trigger_should_not": 0,
            "trigger_should_not_pass": 0,
            "routing_cases": 0,
            "routing_pass": 0,
            "flow_cases": 0,
            "flow_pass": 0,
            "quality_scores": [],
        }

        for case in test_cases:
            case_id = case["id"]
            if case_id not in results:
                continue

            result = results[case_id]
            category = case["category"]

            if category == "trigger":
                if case["expected_trigger"]:
                    metrics["trigger_should"] += 1
                    if result.get("triggered", False):
                        metrics["trigger_should_pass"] += 1
                else:
                    metrics["trigger_should_not"] += 1
                    if not result.get("triggered", False):
                        metrics["trigger_should_not_pass"] += 1

            elif category == "routing":
                metrics["routing_cases"] += 1
                if result.get("routed", False):
                    metrics["routing_pass"] += 1

            elif category == "flow":
                metrics["flow_cases"] += 1
                if result.get("completed", False):
                    metrics["flow_pass"] += 1

            elif category == "quality":
                if "quality_score" in result:
                    metrics["quality_scores"].append(result["quality_score"])

        # 计算比率
        metrics["trigger_rate"] = metrics["trigger_should_pass"] / metrics["trigger_should"] if metrics["trigger_should"] > 0 else 0
        metrics["false_trigger_rate"] = 1 - (metrics["trigger_should_not_pass"] / metrics["trigger_should_not"]) if metrics["trigger_should_not"] > 0 else 0
        metrics["routing_rate"] = metrics["routing_pass"] / metrics["routing_cases"] if metrics["routing_cases"] > 0 else 0
        metrics["flow_completion"] = metrics["flow_pass"] / metrics["flow_cases"] if metrics["flow_cases"] > 0 else 0
        metrics["quality_mean"] = sum(metrics["quality_scores"]) / len(metrics["quality_scores"]) if metrics["quality_scores"] else 0

        model_metrics[model] = metrics

    # 生成Markdown报告
    lines = []
    lines.append(f"# 多模型测试报告：{config['skill_name']}")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 测试概览")
    lines.append("")
    lines.append(f"- 技能：{config['skill_name']}")
    lines.append(f"- 测试模型：{', '.join(models)}")
    lines.append(f"- 测试用例：{len(test_cases)}个")
    lines.append("")

    lines.append("## 各模型指标对比")
    lines.append("")
    lines.append("| 模型 | 已测试 | 触发率 | 误触发率 | 路由输出率 | 流程完成率 | 质量均分 |")
    lines.append("|------|--------|--------|----------|-----------|-----------|---------|")

    for model in models:
        m = model_metrics[model]
        lines.append(
            f"| {model} | {m['tested_cases']}/{m['total_cases']} | "
            f"{m['trigger_rate']*100:.0f}% | {m['false_trigger_rate']*100:.0f}% | "
            f"{m['routing_rate']*100:.0f}% | {m['flow_completion']*100:.0f}% | "
            f"{m['quality_mean']:.0f}/100 |"
        )

    lines.append("")
    lines.append("## 通过标准检查")
    lines.append("")
    lines.append("| 指标 | 标准 | 状态 |")
    lines.append("|------|------|------|")

    # 检查各模型是否达标
    all_pass = True
    for model in models:
        m = model_metrics[model]
        checks = [
            ("触发率≥90%", m["trigger_rate"] >= pass_criteria["trigger_rate_min"]),
            ("误触发率≤10%", m["false_trigger_rate"] <= pass_criteria["false_trigger_rate_max"]),
            ("路由输出率≥90%", m["routing_rate"] >= pass_criteria["routing_rate_min"]),
            ("流程完成率≥85%", m["flow_completion"] >= pass_criteria["flow_completion_min"]),
        ]
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            lines.append(f"| {model} - {check_name} | {status} |")
            if not passed:
                all_pass = False

    # 检查模型间差异
    if len(models) >= 2:
        trigger_rates = [model_metrics[m]["trigger_rate"] for m in models]
        trigger_diff = max(trigger_rates) - min(trigger_rates)
        diff_pass = trigger_diff <= pass_criteria["trigger_rate_diff_max"]
        lines.append(f"| 模型间触发率差异≤10% | 实际{trigger_diff*100:.0f}% | {'✅' if diff_pass else '❌'} |")
        if not diff_pass:
            all_pass = False

        quality_means = [model_metrics[m]["quality_mean"] for m in models if model_metrics[m]["quality_mean"] > 0]
        if len(quality_means) >= 2:
            quality_diff = (max(quality_means) - min(quality_means)) / 100
            q_diff_pass = quality_diff <= pass_criteria["quality_diff_max"]
            lines.append(f"| 模型间质量差异≤15% | 实际{quality_diff*100:.0f}% | {'✅' if q_diff_pass else '❌'} |")
            if not q_diff_pass:
                all_pass = False

    lines.append("")
    lines.append(f"## 最终结论")
    lines.append("")
    if all_pass:
        lines.append("✅ **全部通过**：技能在所有测试模型下表现一致，达到跨模型鲁棒性标准。")
    else:
        lines.append("⚠️ **部分未通过**：技能在某些模型或指标上未达标，建议优化提示词和工作流设计。")
        lines.append("")
        lines.append("### 优化建议")
        lines.append("- 触发率低：优化description，添加更多触发词")
        lines.append("- 误触发率高：在description中明确「不适用于」场景")
        lines.append("- 路由输出率低：在SKILL.md开头加强制路由输出要求")
        lines.append("- 流程完成率低：添加编排脚本强制流程，添加校验门禁")
        lines.append("- 模型间差异大：简化提示词，减少模型特性依赖，使用更通用的表达")

    lines.append("")
    lines.append("## 详细测试用例结果")
    lines.append("")

    for model in models:
        lines.append(f"### {model}")
        lines.append("")
        lines.append("| 用例 | 类别 | 输入 | 触发 | 路由 | 完成 | 质量 |")
        lines.append("|------|------|------|------|------|------|------|")

        results = all_results[model]
        for case in test_cases:
            case_id = case["id"]
            if case_id not in results:
                lines.append(f"| {case_id} | {case['category']} | {case['input'][:20]}... | ⏳ | ⏳ | ⏳ | ⏳ |")
                continue

            result = results[case_id]
            triggered = "✅" if result.get("triggered", False) else "❌" if "triggered" in result else "-"
            routed = "✅" if result.get("routed", False) else "❌" if "routed" in result else "-"
            completed = "✅" if result.get("completed", False) else "❌" if "completed" in result else "-"
            quality = f"{result['quality_score']:.0f}" if "quality_score" in result else "-"

            lines.append(f"| {case_id} | {case['category']} | {case['input'][:20]}... | {triggered} | {routed} | {completed} | {quality} |")

        lines.append("")

    report_content = "\n".join(lines)
    report_path = test_dir / "multi_model_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"✅ 多模型测试报告已生成: {report_path}")
    print()
    print("=" * 60)
    print("📊 测试摘要")
    print("=" * 60)
    for model in models:
        m = model_metrics[model]
        print(f"  {model}: 触发率={m['trigger_rate']*100:.0f}%, 路由率={m['routing_rate']*100:.0f}%, 完成率={m['flow_completion']*100:.0f}%, 质量={m['quality_mean']:.0f}/100")
    print()
    print(f"最终结论: {'✅ 全部通过' if all_pass else '⚠️ 部分未通过'}")


def show_status(test_dir):
    """显示测试状态"""
    test_dir = Path(test_dir)
    config_file = test_dir / "config.json"

    if not config_file.exists():
        print(f"❌ 测试配置不存在: {config_file}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 读取配置失败: {e}", file=sys.stderr)
        sys.exit(1)

    if not config_file.exists():
        print(f"❌ 测试配置不存在: {config_file}", file=sys.stderr)
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    models = config["models"]
    total_cases = len(config["test_cases"])

    print("=" * 60)
    print(f"📊 多模型测试状态：{config['skill_name']}")
    print("=" * 60)
    print(f"  测试用例总数: {total_cases}")
    print(f"  测试模型: {', '.join(models)}")
    print()

    for model in models:
        model_file = test_dir / f"results_{model.replace(' ', '_').replace('/', '_')}.json"
        if model_file.exists():
            with open(model_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            tested = len(data.get("results", {}))
            progress = tested / total_cases * 100
            print(f"  {model}: {tested}/{total_cases} ({progress:.0f}%)")
        else:
            print(f"  {model}: 0/{total_cases} (0%) - 未开始")

    print()
    print("📋 命令：")
    print("  record - 记录测试结果")
    print("  report - 生成对比报告")


def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 多模型测试自动化模板（跨模型鲁棒性测试）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="初始化多模型测试")
    p_init.add_argument("--skill-path", required=True, help="技能目录路径")
    p_init.add_argument("--models", required=True, help="测试模型列表，逗号分隔（如：Claude,GPT-4,Gemini）")

    # record
    p_record = sub.add_parser("record", help="记录测试结果")
    p_record.add_argument("--test-dir", required=True, help="测试目录路径")
    p_record.add_argument("--model", required=True, help="模型名称")
    p_record.add_argument("--case", required=True, help="测试用例ID（如T1）")
    p_record.add_argument("--triggered", help="是否触发（yes/no）")
    p_record.add_argument("--routed", help="是否输出路由行（yes/no）")
    p_record.add_argument("--completed", help="是否完整执行流程（yes/no）")
    p_record.add_argument("--quality", help="质量评分（0-100）")
    p_record.add_argument("--route", help="实际路由模式")
    p_record.add_argument("--notes", help="备注")

    # report
    p_report = sub.add_parser("report", help="生成跨模型对比报告")
    p_report.add_argument("--test-dir", required=True, help="测试目录路径")

    # status
    p_status = sub.add_parser("status", help="显示测试状态")
    p_status.add_argument("--test-dir", required=True, help="测试目录路径")

    args = parser.parse_args()

    if args.command == "init":
        init_test(args.skill_path, args.models)
    elif args.command == "record":
        record_result(
            args.test_dir, args.model, args.case,
            triggered=args.triggered, routed=args.routed,
            completed=args.completed, quality=args.quality,
            route=args.route, notes=args.notes
        )
    elif args.command == "report":
        generate_report(args.test_dir)
    elif args.command == "status":
        show_status(args.test_dir)


if __name__ == "__main__":
    main()
