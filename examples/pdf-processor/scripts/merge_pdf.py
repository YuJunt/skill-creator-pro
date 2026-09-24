#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF合并脚本（示例）

将多个PDF文件按顺序合并为一个PDF文件。

用法：
  python3 merge_pdf.py input1.pdf input2.pdf -o output.pdf
  python3 merge_pdf.py *.pdf -o merged.pdf
"""
import argparse
import os
import sys


def merge_pdfs(input_files, output_file):
    """合并多个PDF文件"""
    try:
        from PyPDF2 import PdfMerger
    except ImportError:
        print("❌ 缺少依赖：PyPDF2", file=sys.stderr)
        print("💡 安装：pip install PyPDF2", file=sys.stderr)
        sys.exit(3)

    for f in input_files:
        if not os.path.isfile(f):
            print(f"❌ 文件不存在: {f}", file=sys.stderr)
            sys.exit(2)
        if not f.lower().endswith('.pdf'):
            print(f"❌ 不是PDF文件: {f}", file=sys.stderr)
            sys.exit(2)

    merger = PdfMerger()
    try:
        for f in input_files:
            merger.append(f)
        merger.write(output_file)
    except Exception as e:
        print(f"❌ 合并失败: {e}", file=sys.stderr)
        sys.exit(3)
    finally:
        merger.close()

    if not os.path.isfile(output_file):
        print("❌ 输出文件未生成", file=sys.stderr)
        sys.exit(3)

    size = os.path.getsize(output_file)
    print(f"✅ 合并完成")
    print(f"   输入: {len(input_files)}个文件")
    print(f"   输出: {output_file}（{size/1024:.1f}KB）")


def main():
    parser = argparse.ArgumentParser(description="合并多个PDF文件")
    parser.add_argument("inputs", nargs="+", help="输入PDF文件（按顺序合并）")
    parser.add_argument("-o", "--output", required=True, help="输出PDF文件路径")
    args = parser.parse_args()
    merge_pdfs(args.inputs, args.output)


if __name__ == "__main__":
    main()
