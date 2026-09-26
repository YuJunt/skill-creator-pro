#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基准聚合脚本（aggregate_benchmark.py）

聚合多轮评估结果，计算：
- 每个配置的pass_rate、time、tokens
- mean ± stddev
- delta（与baseline的差值）

用法：
  python3 aggregate_benchmark.py <workspace>/iteration-N --skill-name <name>
  python3 aggregate_benchmark.py <workspace>/iteration-N --skill-name <name> --previous <prev_iteration>
"""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def load_grading(run_dir):
    """加载单次运行的grading.json"""
    grading_file = Path(run_dir) / "grading.json"
    if not grading_file.exists():
        return None
    try:
        with open(grading_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_timing(run_dir):
    """加载单次运行的timing.json"""
    timing_file = Path(run_dir) / "timing.json"
    if not timing_file.exists():
        return None
    try:
        with open(timing_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def find_runs(iteration_dir):
    """查找所有运行目录"""
    iteration_path = Path(iteration_dir)
    runs = []

    for eval_dir in sorted(iteration_path.iterdir()):
        if not eval_dir.is_dir():
            continue

        # 查找with_skill和baseline目录
        for config_name in ["with_skill", "without_skill", "old_skill", "baseline"]:
            run_dir = eval_dir / config_name
            if run_dir.exists():
                runs.append({
                    "eval_id": eval_dir.name,
                    "config": config_name,
                    "run_dir": str(run_dir),
                })

    return runs


def aggregate_runs(runs):
    """聚合所有运行"""
    configs = {}

    for run in runs:
        config = run["config"]
        if config not in configs:
            configs[config] = {
                "config": config,
                "runs": [],
                "pass_rates": [],
                "durations": [],
                "tokens": [],
            }

        grading = load_grading(run["run_dir"])
        timing = load_timing(run["run_dir"])

        run_data = {
            "eval_id": run["eval_id"],
            "run_dir": run["run_dir"],
        }

        if grading:
            pass_rate = grading.get("pass_rate", 0)
            run_data["pass_rate"] = pass_rate
            run_data["passed"] = grading.get("passed", 0)
            run_data["total_expectations"] = grading.get("total_expectations", 0)
            configs[config]["pass_rates"].append(pass_rate)

        if timing:
            duration = timing.get("total_duration_seconds", 0)
            tokens = timing.get("total_tokens", 0)
            run_data["duration_seconds"] = duration
            run_data["total_tokens"] = tokens
            configs[config]["durations"].append(duration)
            configs[config]["tokens"].append(tokens)

        configs[config]["runs"].append(run_data)

    # 计算统计
    for config_name, config_data in configs.items():
        pass_rates = config_data["pass_rates"]
        durations = config_data["durations"]
        tokens = config_data["tokens"]

        if pass_rates:
            mean_pass = sum(pass_rates) / len(pass_rates)
            variance = sum((p - mean_pass) ** 2 for p in pass_rates) / len(pass_rates)
            std_pass = variance ** 0.5
            config_data["pass_rate_mean"] = round(mean_pass, 4)
            config_data["pass_rate_std"] = round(std_pass, 4)

        if durations:
            mean_duration = sum(durations) / len(durations)
            config_data["duration_mean"] = round(mean_duration, 2)

        if tokens:
            mean_tokens = sum(tokens) / len(tokens)
            config_data["tokens_mean"] = int(mean_tokens)

    return configs


def calculate_deltas(configs):
    """计算与baseline的delta"""
    # 找baseline配置
    baseline_config = None
    for name in ["without_skill", "old_skill", "baseline"]:
        if name in configs:
            baseline_config = name
            break

    if not baseline_config:
        return configs

    baseline = configs[baseline_config]

    for config_name, config_data in configs.items():
        if config_name == baseline_config:
            continue

        if "pass_rate_mean" in config_data and "pass_rate_mean" in baseline:
            config_data["pass_rate_delta"] = round(
                config_data["pass_rate_mean"] - baseline["pass_rate_mean"], 4
            )

        if "duration_mean" in config_data and "duration_mean" in baseline:
            config_data["duration_delta"] = round(
                config_data["duration_mean"] - baseline["duration_mean"], 2
            )

        if "tokens_mean" in config_data and "tokens_mean" in baseline:
            config_data["tokens_delta"] = config_data["tokens_mean"] - baseline["tokens_mean"]

    return configs


def generate_markdown(configs, skill_name, previous_configs=None):
    """生成Markdown报告"""
    lines = []
    lines.append(f"# 基准测试报告：{skill_name}")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 配置对比")
    lines.append("")
    lines.append("| 配置 | 通过率(mean±std) | 耗时(mean) | Tokens(mean) | Δ通过率 | Δ耗时 | ΔTokens |")
    lines.append("|------|-----------------|-----------|-------------|--------|------|---------|")

    for config_name, config_data in configs.items():
        pass_rate = f"{config_data.get('pass_rate_mean', 'N/A')}±{config_data.get('pass_rate_std', 'N/A')}"
        duration = f"{config_data.get('duration_mean', 'N/A')}s"
        tokens = f"{config_data.get('tokens_mean', 'N/A')}"
        delta_pass = f"{config_data.get('pass_rate_delta', '-')}"
        delta_duration = f"{config_data.get('duration_delta', '-')}s"
        delta_tokens = f"{config_data.get('tokens_delta', '-')}"

        lines.append(f"| {config_name} | {pass_rate} | {duration} | {tokens} | {delta_pass} | {delta_duration} | {delta_tokens} |")

    lines.append("")
    lines.append("## 各测试用例详情")
    lines.append("")

    for config_name, config_data in configs.items():
        lines.append(f"### {config_name}")
        lines.append("")
        lines.append("| 测试用例 | 通过率 | 通过/总数 | 耗时 | Tokens |")
        lines.append("|---------|--------|----------|------|--------|")

        for run in config_data["runs"]:
            pass_rate = f"{run.get('pass_rate', 'N/A')*100:.0f}%" if run.get('pass_rate') is not None else "N/A"
            passed = f"{run.get('passed', 'N/A')}/{run.get('total_expectations', 'N/A')}"
            duration = f"{run.get('duration_seconds', 'N/A')}s"
            tokens = f"{run.get('total_tokens', 'N/A')}"
            lines.append(f"| {run['eval_id']} | {pass_rate} | {passed} | {duration} | {tokens} |")

        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="基准聚合脚本")
    parser.add_argument("iteration_dir", help="迭代目录")
    parser.add_argument("--skill-name", required=True, help="技能名称")
    parser.add_argument("--previous", help="上一轮迭代目录（用于对比）")
    args = parser.parse_args()

    if not os.path.isdir(args.iteration_dir):
        print(f"❌ 目录不存在: {args.iteration_dir}", file=sys.stderr)
        sys.exit(1)

    # 查找所有运行
    runs = find_runs(args.iteration_dir)
    if not runs:
        print(f"❌ 未找到运行目录", file=sys.stderr)
        sys.exit(1)

    print(f"✅ 找到{len(runs)}个运行")

    # 聚合
    configs = aggregate_runs(runs)
    configs = calculate_deltas(configs)

    # 生成benchmark.json
    benchmark = {
        "skill_name": args.skill_name,
        "iteration": os.path.basename(args.iteration_dir),
        "generated_at": datetime.now().isoformat(),
        "configs": configs,
    }

    benchmark_path = os.path.join(args.iteration_dir, "benchmark.json")
    with open(benchmark_path, "w", encoding="utf-8") as f:
        json.dump(benchmark, f, ensure_ascii=False, indent=2)
    print(f"✅ benchmark.json已生成: {benchmark_path}")

    # 生成benchmark.md
    markdown = generate_markdown(configs, args.skill_name)
    markdown_path = os.path.join(args.iteration_dir, "benchmark.md")
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"✅ benchmark.md已生成: {markdown_path}")

    # 打印摘要
    print()
    print("=" * 60)
    print("📊 基准测试摘要")
    print("=" * 60)
    for config_name, config_data in configs.items():
        pass_rate = config_data.get("pass_rate_mean", "N/A")
        duration = config_data.get("duration_mean", "N/A")
        tokens = config_data.get("tokens_mean", "N/A")
        print(f"  {config_name}: 通过率={pass_rate}, 耗时={duration}s, Tokens={tokens}")


if __name__ == "__main__":
    main()
