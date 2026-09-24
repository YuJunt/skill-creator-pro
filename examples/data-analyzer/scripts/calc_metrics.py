#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指标计算脚本（示例）

从CSV数据计算核心指标，支持按维度分组。

用法：
  python3 calc_metrics.py data.csv --metrics "pv,uv,conversion_rate" --group-by "date" -o metrics.json
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict


def load_csv(filepath):
    """加载CSV文件"""
    if not os.path.isfile(filepath):
        print(f"❌ 文件不存在: {filepath}", file=sys.stderr)
        sys.exit(2)
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def calc_metric(rows, metric):
    """计算单个指标"""
    if not rows:
        return 0
    if metric == "pv":
        return len(rows)
    elif metric == "uv":
        return len(set(r.get("user_id", "") for r in rows if r.get("user_id")))
    elif metric == "conversion_rate":
        total = len(rows)
        converted = sum(1 for r in rows if r.get("converted", "0") in ("1", "true", "True"))
        return round(converted / total * 100, 2) if total > 0 else 0
    elif metric == "revenue":
        return round(sum(float(r.get("amount", 0) or 0) for r in rows), 2)
    elif metric == "orders":
        return sum(1 for r in rows if r.get("order_id"))
    elif metric == "aov":
        orders = sum(1 for r in rows if r.get("order_id"))
        revenue = sum(float(r.get("amount", 0) or 0) for r in rows)
        return round(revenue / orders, 2) if orders > 0 else 0
    else:
        try:
            return round(sum(float(r.get(metric, 0) or 0) for r in rows), 2)
        except (ValueError, TypeError):
            return None


def analyze(data, metrics, group_by=None):
    """分析数据"""
    results = {}
    if group_by:
        groups = defaultdict(list)
        for row in data:
            key = "|".join(str(row.get(d, "")) for d in group_by)
            groups[key].append(row)
        for key, rows in sorted(groups.items()):
            group_result = {}
            for metric in metrics:
                value = calc_metric(rows, metric)
                if value is not None:
                    group_result[metric] = value
            results[key] = group_result
    else:
        total = {}
        for metric in metrics:
            value = calc_metric(data, metric)
            if value is not None:
                total[metric] = value
        results["total"] = total
    return results


def main():
    parser = argparse.ArgumentParser(description="计算核心指标")
    parser.add_argument("input", help="输入CSV文件路径")
    parser.add_argument("--metrics", required=True, help="指标列表，逗号分隔")
    parser.add_argument("--group-by", help="分组维度，逗号分隔")
    parser.add_argument("-o", "--output", help="输出JSON文件路径")
    args = parser.parse_args()

    data = load_csv(args.input)
    if not data:
        print("❌ 数据为空", file=sys.stderr)
        sys.exit(1)

    metrics = [m.strip() for m in args.metrics.split(",")]
    group_by = [g.strip() for g in args.group_by.split(",")] if args.group_by else None
    results = analyze(data, metrics, group_by)

    output = {
        "input": args.input,
        "row_count": len(data),
        "metrics": metrics,
        "group_by": group_by,
        "results": results,
    }

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"✅ 指标计算完成: {args.output}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
