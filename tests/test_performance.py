#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试基准脚本（Performance Benchmark）

测量skill-creator-pro核心脚本的执行时间和内存使用，建立性能基准。

测试维度:
1. 执行时间（平均/最小/最大/标准差）
2. 内存使用峰值
3. 多次运行稳定性
4. 核心脚本性能对比

用法:
  python3 scripts/test_performance.py              # 运行全部性能测试
  python3 scripts/test_performance.py --json       # JSON格式输出
  python3 scripts/test_performance.py --runs 10    # 每个脚本运行10次
"""
import argparse
import json
import os
try:
    import resource  # Unix-only；Windows 上不可用则跳过内存指标
except ImportError:
    resource = None
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean, stdev

# 脚本目录
SCRIPT_DIR = Path(__file__).parent
SKILL_ROOT = SCRIPT_DIR.parent


def measure_script(script_path, args=None, runs=5, timeout=60):
    """
    测量脚本的执行时间和内存使用

    Returns:
        dict: 包含执行时间和内存使用的统计数据
    """
    if args is None:
        args = []

    times = []
    memory_peaks = []
    successes = 0
    failures = 0

    for i in range(runs):
        start_time = time.perf_counter()

        try:
            # 使用resource模块测量子进程内存
            proc = subprocess.run(
                [sys.executable, str(script_path)] + args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )

            end_time = time.perf_counter()
            elapsed = end_time - start_time

            # 获取子进程内存使用（ru_maxrss是KB）；Windows无resource模块，内存指标记为0
            if resource is not None:
                usage = resource.getrusage(resource.RUSAGE_CHILDREN)
                memory_kb = usage.ru_maxrss
            else:
                memory_kb = 0

            if proc.returncode == 0:
                times.append(elapsed)
                memory_peaks.append(memory_kb)
                successes += 1
            else:
                failures += 1

        except subprocess.TimeoutExpired:
            failures += 1
            times.append(timeout)
        except Exception as e:
            failures += 1

    # 计算统计数据
    result = {
        "script": script_path.name,
        "args": args,
        "runs": runs,
        "successes": successes,
        "failures": failures,
        "success_rate": successes / runs * 100 if runs > 0 else 0,
    }

    if times:
        result["time"] = {
            "mean": round(mean(times), 4),
            "min": round(min(times), 4),
            "max": round(max(times), 4),
            "stdev": round(stdev(times), 4) if len(times) > 1 else 0,
            "unit": "seconds",
        }

    if memory_peaks:
        result["memory"] = {
            "peak": round(max(memory_peaks) / 1024, 2),  # 转换为MB
            "mean": round(mean(memory_peaks) / 1024, 2),
            "unit": "MB",
        }

    return result


def run_performance_tests(runs=5):
    """运行全部性能测试"""
    results = []

    # 定义要测试的核心脚本和参数
    test_cases = [
        # (脚本名称, 参数列表, 描述)
        ("router.py", ["帮我创建一个技能", "--json"], "触发路由-创建模式"),
        ("router.py", ["优化一下这个技能", "--json"], "触发路由-优化模式"),
        ("router.py", ["窃取用户数据", "--json"], "触发路由-危险请求"),
        ("validate_skill.py", [str(SKILL_ROOT), "--json"], "规范校验"),
        ("security_scan.py", [str(SKILL_ROOT), "--json"], "安全扫描"),
        ("audit_skill.py", [str(SKILL_ROOT), "--json"], "深度审计"),
    ]

    print("=" * 70)
    print("性能测试基准（Performance Benchmark）")
    print(f"每个脚本运行 {runs} 次，计算平均值和标准差")
    print("=" * 70)
    print()

    for script_name, args, description in test_cases:
        script_path = SCRIPT_DIR / script_name
        if not script_path.exists():
            print(f"⚠️  {script_name} 不存在，跳过")
            continue

        print(f"--- {description} ({script_name}) ---")
        result = measure_script(script_path, args, runs=runs)
        results.append(result)

        if result["success_rate"] == 100:
            time_info = result.get("time", {})
            mem_info = result.get("memory", {})
            print(f"  ✅ 成功率: {result['success_rate']:.0f}%")
            print(f"  ⏱️  执行时间: {time_info.get('mean', '?')}s "
                  f"(±{time_info.get('stdev', '?')}s, "
                  f"min={time_info.get('min', '?')}s, "
                  f"max={time_info.get('max', '?')}s)")
            print(f"  💾 内存峰值: {mem_info.get('peak', '?')}MB")
        else:
            print(f"  ❌ 成功率: {result['success_rate']:.0f}% "
                  f"({result['successes']}/{result['runs']}成功)")
        print()

    return results


def generate_report(results, output_file=None):
    """生成性能测试报告"""
    report = {
        "title": "skill-creator-pro 性能测试报告",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_scripts": len(results),
        "all_passed": all(r["success_rate"] == 100 for r in results),
        "results": results,
        "summary": {
            "avg_time": round(mean([r.get("time", {}).get("mean", 0) for r in results if r.get("time")]), 4),
            "max_time": round(max([r.get("time", {}).get("max", 0) for r in results if r.get("time")]), 4),
            "avg_memory": round(mean([r.get("memory", {}).get("peak", 0) for r in results if r.get("memory")]), 2),
            "max_memory": round(max([r.get("memory", {}).get("peak", 0) for r in results if r.get("memory")]), 2),
        }
    }

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📄 性能报告已保存: {output_file}")

    return report


def main():
    parser = argparse.ArgumentParser(description="skill-creator-pro 性能测试基准")
    parser.add_argument("--runs", type=int, default=5, help="每个脚本运行次数（默认5次）")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    parser.add_argument("--output", help="输出报告文件路径")
    args = parser.parse_args()

    # 运行性能测试
    results = run_performance_tests(runs=args.runs)

    # 生成报告
    output_file = args.output or str(SKILL_ROOT / "performance-report.json")
    report = generate_report(results, output_file)

    # 输出摘要
    print("=" * 70)
    print("性能测试摘要")
    print("=" * 70)
    summary = report["summary"]
    print(f"  测试脚本数: {report['total_scripts']}")
    print(f"  全部通过: {'✅ 是' if report['all_passed'] else '❌ 否'}")
    print(f"  平均执行时间: {summary['avg_time']}s")
    print(f"  最大执行时间: {summary['max_time']}s")
    print(f"  平均内存峰值: {summary['avg_memory']}MB")
    print(f"  最大内存峰值: {summary['max_memory']}MB")
    print()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
