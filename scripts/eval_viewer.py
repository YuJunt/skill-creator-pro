#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eval Viewer（交互式HTML审核界面）

生成HTML报告，包含：
- Outputs标签页：测试用例+输出文件+评分详情
- Benchmark标签页：统计摘要+通过率+计时+token使用

用法：
  python3 eval_viewer.py <benchmark_dir>
  python3 eval_viewer.py <benchmark_dir> --output report.html
"""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def load_gradings(benchmark_dir):
    """加载所有grading.json"""
    try:
        gradings = []
        bench_path = Path(benchmark_dir)
        for g in bench_path.glob("**/grading.json"):
            with open(g, "r", encoding="utf-8") as f:
                grading = json.load(f)
                grading["file"] = str(g)
                grading["run_dir"] = str(g.parent)
                gradings.append(grading)
        return gradings
    except Exception as e:
        print(f"⚠️ 加载grading.json失败: {e}", file=sys.stderr)
        return []


def load_comparison(benchmark_dir):
    """加载comparison.json"""
    comp_file = Path(benchmark_dir) / "comparison.json"
    if comp_file.exists():
        with open(comp_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_analysis(benchmark_dir):
    """加载analysis.json"""
    analysis_file = Path(benchmark_dir) / "analysis.json"
    if analysis_file.exists():
        with open(analysis_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def generate_html(benchmark_dir):
    """生成HTML报告"""
    gradings = load_gradings(benchmark_dir)
    comparison = load_comparison(benchmark_dir)
    analysis = load_analysis(benchmark_dir)

    # 计算统计
    total_runs = len(gradings)
    total_passed = sum(g.get("passed", 0) for g in gradings)
    total_expectations = sum(g.get("total_expectations", 0) for g in gradings)
    overall_rate = total_passed / total_expectations if total_expectations > 0 else 0

    # 生成HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eval Viewer - 技能评估报告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #4CAF50; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .run-item {{ border: 1px solid #ddd; margin: 10px 0; border-radius: 6px; overflow: hidden; }}
        .run-header {{ background: #f8f9fa; padding: 10px 15px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
        .run-header:hover {{ background: #e9ecef; }}
        .run-content {{ padding: 15px; display: none; }}
        .run-content.active {{ display: block; }}
        .pass {{ color: #4CAF50; font-weight: bold; }}
        .fail {{ color: #f44336; font-weight: bold; }}
        .expectation {{ margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 4px; }}
        .comparison {{ background: #e3f2fd; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .analysis {{ background: #fff3e0; padding: 15px; border-radius: 6px; margin: 20px 0; }}
        .winner {{ font-size: 1.5em; font-weight: bold; color: #4CAF50; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Eval Viewer - 技能评估报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>评估目录: {benchmark_dir}</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_runs}</div>
                <div class="stat-label">总运行次数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{overall_rate*100:.0f}%</div>
                <div class="stat-label">总体通过率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_passed}/{total_expectations}</div>
                <div class="stat-label">通过/总断言</div>
            </div>
        </div>
"""

    # 比较结果
    if comparison:
        winner = comparison.get("overall_winner", "tie")
        html += f"""
        <div class="comparison">
            <h2>🔄 盲A/B比较结果</h2>
            <p>胜者: <span class="winner">{winner}</span></p>
            <p>A得分: {comparison['scores']['A']:.2f} | B得分: {comparison['scores']['B']:.2f}</p>
        </div>
"""

    # 分析结果
    if analysis:
        html += f"""
        <div class="analysis">
            <h2>📈 基准分析</h2>
            <p>模式: {analysis.get('mode', 'unknown')}</p>
"""
        if "notes" in analysis:
            for note in analysis["notes"]:
                html += f"            <p>{note}</p>\n"
        html += "        </div>\n"

    # 各运行详情
    html += """
        <h2>📋 各运行详情</h2>
"""
    for i, g in enumerate(gradings):
        pass_rate = g.get("pass_rate", 0)
        passed = g.get("passed", 0)
        total = g.get("total_expectations", 0)
        run_dir = g.get("run_dir", "unknown")

        html += f"""
        <div class="run-item">
            <div class="run-header" onclick="toggleRun({i})">
                <span>运行 {i+1}: {run_dir.split('/')[-2] if '/' in run_dir else run_dir}</span>
                <span class="{'pass' if pass_rate >= 0.8 else 'fail'}">{passed}/{total} ({pass_rate*100:.0f}%)</span>
            </div>
            <div class="run-content" id="run-{i}">
"""
        for r in g.get("results", []):
            status = "✅" if r["passed"] else "❌"
            html += f"""
                <div class="expectation">
                    <strong>{status} {r['text']}</strong>
                    <br><small>{r['evidence']}</small>
                </div>
"""
        html += """
            </div>
        </div>
"""

    html += """
    </div>

    <script>
        function toggleRun(id) {
            const content = document.getElementById('run-' + id);
            content.classList.toggle('active');
        }
    </script>
</body>
</html>
"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Eval Viewer：交互式HTML审核界面")
    parser.add_argument("benchmark_dir", help="基准测试目录")
    parser.add_argument("--output", help="输出HTML文件路径")
    args = parser.parse_args()

    if not os.path.isdir(args.benchmark_dir):
        print(f"❌ 目录不存在: {args.benchmark_dir}", file=sys.stderr)
        sys.exit(1)

    html = generate_html(args.benchmark_dir)

    output_path = args.output or os.path.join(args.benchmark_dir, "eval_viewer.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Eval Viewer已生成: {output_path}")
    print(f"   在浏览器中打开此文件查看报告")


if __name__ == "__main__":
    main()
