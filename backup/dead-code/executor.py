#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executor Agent（评估流程编排脚本）

编排完整的评估流程：
  1. 读取评估用例
  2. 生成测试提示（with-skill vs baseline）
  3. 收集运行结果
  4. 调用grader.py评分
  5. 调用comparator.py比较
  6. 调用analyzer.py分析

用法：
  python3 executor.py init <skill_dir>  # 初始化评估工作空间
  python3 executor.py prompts <skill_dir>  # 生成测试提示
  python3 executor.py collect <run_dir> <output_dir>  # 收集运行结果
  python3 executor.py grade <run_dir>  # 评分
  python3 executor.py compare <run_a> <run_b>  # 比较
  python3 executor.py analyze <benchmark_dir>  # 分析
  python3 executor.py full <skill_dir>  # 完整流程（init→prompts→collect→grade→compare→analyze）
"""
import argparse
import json
import os
import sys
from pathlib import Path


def init_workspace(skill_dir):
    """初始化评估工作空间"""
    try:
        skill_path = Path(skill_dir)
        if not skill_path.exists():
            print(f"❌ 技能目录不存在: {skill_dir}", file=sys.stderr)
            sys.exit(1)

        # 创建工作空间
        workspace = skill_path / "eval_workspace"
        workspace.mkdir(exist_ok=True)

        # 创建子目录
        (workspace / "with_skill").mkdir(exist_ok=True)
        (workspace / "baseline").mkdir(exist_ok=True)
        (workspace / "results").mkdir(exist_ok=True)

        print(f"✅ 评估工作空间已创建: {workspace}")
        print(f"   with_skill/: 使用技能的运行")
        print(f"   baseline/: 不使用技能的基线运行")
        print(f"   results/: 评分/比较/分析结果")

        return str(workspace)
    except Exception as e:
        print(f"❌ 初始化失败: {e}", file=sys.stderr)
        sys.exit(1)


def generate_prompts(skill_dir):
    """生成测试提示"""
    workspace = Path(skill_dir) / "eval_workspace"
    if not workspace.exists():
        print("❌ 工作空间不存在，请先运行 init", file=sys.stderr)
        sys.exit(1)

    # 读取evals.json
    evals_file = workspace / "evals.json"
    if not evals_file.exists():
        # 创建默认evals.json
        default_evals = {
            "skill_dir": str(skill_dir),
            "test_cases": [
                {
                    "id": "test-001",
                    "name": "基本触发",
                    "prompt": "帮我做一个XX任务",
                    "expectations": [
                        {"text": "技能被触发", "type": "contains", "keywords": ["路由"]},
                        {"text": "输出格式正确", "type": "contains", "keywords": ["结论"]}
                    ]
                }
            ]
        }
        with open(evals_file, "w", encoding="utf-8") as f:
            json.dump(default_evals, f, ensure_ascii=False, indent=2)
        print(f"⚠️ 未找到evals.json，已创建模板: {evals_file}")
        print(f"   请编辑此文件，添加你的测试用例")
        return

    with open(evals_file, "r", encoding="utf-8") as f:
        evals = json.load(f)

    # 生成测试提示
    prompts = []
    for case in evals.get("test_cases", []):
        prompts.append({
            "id": case["id"],
            "name": case["name"],
            "prompt": case["prompt"],
            "mode": "with_skill"  # 第一个是with-skill
        })
        prompts.append({
            "id": case["id"],
            "name": case["name"],
            "prompt": case["prompt"],
            "mode": "baseline"  # 第二个是baseline
        })

    # 保存提示列表
    prompts_file = workspace / "prompts.json"
    with open(prompts_file, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

    print(f"✅ 生成{len(prompts)}个测试提示")
    print(f"   with_skill: {len([p for p in prompts if p['mode'] == 'with_skill'])}个")
    print(f"   baseline: {len([p for p in prompts if p['mode'] == 'baseline'])}个")
    print(f"   📄 提示列表: {prompts_file}")
    print(f"   💡 请手动运行这些提示，把结果放到对应的run目录")


def collect_results(run_dir, output_dir):
    """收集运行结果"""
    run_path = Path(run_dir)
    output_path = Path(output_dir)

    if not run_path.exists():
        print(f"❌ 运行目录不存在: {run_dir}", file=sys.stderr)
        sys.exit(1)

    # 复制输出文件到run目录
    output_target = run_path / "output"
    output_target.mkdir(exist_ok=True)

    if output_path.exists():
        for f in output_path.glob("**/*"):
            if f.is_file():
                rel_path = f.relative_to(output_path)
                target = output_target / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(f.read_bytes())
        print(f"✅ 已收集{len(list(output_target.glob('**/*')))}个文件到{run_path}")


def grade_run(run_dir):
    """对单次运行评分"""
    import subprocess
    grader_script = Path(__file__).parent / "grader.py"
    subprocess.run([sys.executable, str(grader_script), run_dir], check=False)


def compare_runs(run_a, run_b):
    """比较两个运行"""
    import subprocess
    comparator_script = Path(__file__).parent / "comparator.py"
    subprocess.run([sys.executable, str(comparator_script), run_a, run_b], check=False)


def analyze_benchmark(benchmark_dir):
    """分析基准"""
    import subprocess
    analyzer_script = Path(__file__).parent / "analyzer.py"
    subprocess.run([sys.executable, str(analyzer_script), benchmark_dir], check=False)


def main():
    parser = argparse.ArgumentParser(description="Executor Agent：评估流程编排")
    sub = parser.add_subparsers(dest="command")

    # init
    sub_init = sub.add_parser("init", help="初始化评估工作空间")
    sub_init.add_argument("skill_dir", help="技能目录")

    # prompts
    sub_prompts = sub.add_parser("prompts", help="生成测试提示")
    sub_prompts.add_argument("skill_dir", help="技能目录")

    # collect
    sub_collect = sub.add_parser("collect", help="收集运行结果")
    sub_collect.add_argument("run_dir", help="运行目录")
    sub_collect.add_argument("output_dir", help="输出目录")

    # grade
    sub_grade = sub.add_parser("grade", help="评分")
    sub_grade.add_argument("run_dir", help="运行目录")

    # compare
    sub_compare = sub.add_parser("compare", help="比较")
    sub_compare.add_argument("run_a", help="运行A目录")
    sub_compare.add_argument("run_b", help="运行B目录")

    # analyze
    sub_analyze = sub.add_parser("analyze", help="分析")
    sub_analyze.add_argument("benchmark_dir", help="基准目录")

    # full
    sub_full = sub.add_parser("full", help="完整流程")
    sub_full.add_argument("skill_dir", help="技能目录")

    args = parser.parse_args()

    if args.command == "init":
        init_workspace(args.skill_dir)
    elif args.command == "prompts":
        generate_prompts(args.skill_dir)
    elif args.command == "collect":
        collect_results(args.run_dir, args.output_dir)
    elif args.command == "grade":
        grade_run(args.run_dir)
    elif args.command == "compare":
        compare_runs(args.run_a, args.run_b)
    elif args.command == "analyze":
        analyze_benchmark(args.benchmark_dir)
    elif args.command == "full":
        print("=" * 60)
        print("完整评估流程")
        print("=" * 60)
        workspace = init_workspace(args.skill_dir)
        generate_prompts(args.skill_dir)
        print("\n📋 下一步：")
        print("  1. 手动运行测试提示，把结果放到eval_workspace/with_skill/和baseline/")
        print("  2. 运行 grade 评分")
        print("  3. 运行 compare 比较")
        print("  4. 运行 analyze 分析")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
