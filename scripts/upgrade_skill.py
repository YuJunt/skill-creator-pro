#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本: v1.0.0 | 许可证: MIT | 最低Python: 3.8+

upgrade_skill.py - 技能迁移升级脚本

将简单技能（只有SKILL.md）自动升级到skill-creator-pro专业标准：
  - 分析差距（对照36项检查清单）
  - 自动创建缺失的目录和文件
  - 补充缺失的SKILL.md section
  - 生成references文档骨架

用法：
  python3 upgrade_skill.py <skill-path>              # 仅分析差距
  python3 upgrade_skill.py <skill-path> --apply       # 应用迁移
  python3 upgrade_skill.py <skill-path> --apply --backup  # 迁移前备份
"""

import argparse
import datetime
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any


# ============================================================
# 数据结构
# ============================================================

@dataclass
class GapItem:
    """差距项"""
    category: str          # 类别：structure/content/engineering/quality
    item: str              # 检查项名称
    status: str            # 状态：missing/partial/present
    severity: str          # 严重度：high/medium/low
    description: str       # 描述
    fix_suggestion: str    # 修复建议


@dataclass
class GapAnalysis:
    """差距分析结果"""
    skill_path: str
    skill_name: str = ""
    total_checks: int = 0
    present_count: int = 0
    partial_count: int = 0
    missing_count: int = 0
    gaps: List[GapItem] = field(default_factory=list)
    current_score: int = 0
    target_score: int = 36

    @property
    def completeness_pct(self):
        if self.total_checks == 0:
            return 0
        return round((self.present_count + self.partial_count * 0.5) / self.total_checks * 100, 1)


# ============================================================
# 差距分析
# ============================================================

def analyze_gap(skill_path: str) -> GapAnalysis:
    """分析技能与专业标准的差距"""
    analysis = GapAnalysis(skill_path=os.path.abspath(skill_path))

    if not os.path.isdir(skill_path):
        analysis.gaps.append(GapItem(
            category="structure", item="技能目录", status="missing",
            severity="high", description="技能目录不存在",
            fix_suggestion="确认技能目录路径正确"
        ))
        return analysis

    skill_md_path = os.path.join(skill_path, "SKILL.md")
    has_skill_md = os.path.isfile(skill_md_path)
    skill_md_content = ""
    if has_skill_md:
        try:
            with open(skill_md_path, 'r', encoding='utf-8', errors='replace') as f:
                skill_md_content = f.read()
        except Exception:
            pass

    # 提取技能名称
    for line in skill_md_content.split('\n'):
        if line.startswith('name:'):
            analysis.skill_name = line.split(':', 1)[1].strip().strip('"')
            break

    # ===== 结构层检查 =====
    checks = [
        # (category, item, check_function, severity, description, fix_suggestion)
        ("structure", "SKILL.md存在", lambda: has_skill_md, "high",
         "技能入口文件", "创建SKILL.md"),
        ("structure", "frontmatter规范", lambda: _check_frontmatter(skill_md_content), "high",
         "YAML frontmatter包含name和description", "添加标准frontmatter"),
        ("structure", "description三要素", lambda: _check_description(skill_md_content), "high",
         "description包含What/When/触发词", "完善description"),
        ("structure", "SKILL.md <500行", lambda: len(skill_md_content.split('\n')) < 500, "medium",
         "渐进式披露要求SKILL.md精简", "拆分内容到references"),
        ("structure", "references目录", lambda: os.path.isdir(os.path.join(skill_path, "references")), "medium",
         "渐进式披露L3层", "创建references目录"),
        ("structure", "scripts目录", lambda: os.path.isdir(os.path.join(skill_path, "scripts")), "low",
         "确定性计算脚本", "创建scripts目录（如需要）"),
        ("structure", "无冗余文件", lambda: _check_no_redundant(skill_path), "low",
         "无README/CHANGELOG/__pycache__", "清理冗余文件"),

        # ===== 内容层检查 =====
        ("content", "Gotchas section", lambda: "gotcha" in skill_md_content.lower() or "坑" in skill_md_content, "high",
         "常见失败模式与修正方法", "添加Gotchas section"),
        ("content", "示例驱动", lambda: "示例" in skill_md_content or "example" in skill_md_content.lower(), "medium",
         "完整示例覆盖正常流程", "添加示例"),
        ("content", "输出格式文档化", lambda: "输出" in skill_md_content or "output" in skill_md_content.lower(), "medium",
         "明确输出格式（简洁版+完整版）", "添加输出格式说明"),
        ("content", "触发路由", lambda: "路由" in skill_md_content or "routing" in skill_md_content.lower(), "medium",
         "多模式路由表", "添加触发路由"),
        ("content", "预加载机制", lambda: "预加载" in skill_md_content or "preload" in skill_md_content.lower(), "low",
         "触发后自动加载关键信息", "添加预加载说明"),
        ("content", "渐进式披露引用表", lambda: "references/" in skill_md_content, "medium",
         "明确什么时候读什么reference", "添加references引用表"),

        # ===== 工程层检查 =====
        ("engineering", "错误处理", lambda: _check_script_error_handling(skill_path), "medium",
         "脚本有try-except错误处理", "添加错误处理"),
        ("engineering", "校验门禁", lambda: _check_validator(skill_path), "low",
         "关键操作前硬校验", "添加校验脚本（如需要）"),
        ("engineering", "配置外置", lambda: _check_config(skill_path), "low",
         "凭据不硬编码", "使用环境变量或配置文件"),

        # ===== 质量层检查 =====
        ("quality", "端到端测试", lambda: _check_e2e_test(skill_path), "low",
         "有测试用例和测试结果", "添加端到端测试"),
        ("quality", "评估用例", lambda: _check_evaluation(skill_path), "low",
         "触发/行为/质量评估用例", "添加评估用例"),
    ]

    for category, item, check_fn, severity, description, fix_suggestion in checks:
        analysis.total_checks += 1
        try:
            result = check_fn()
        except Exception:
            result = False

        if result is True:
            analysis.present_count += 1
            status = "present"
        elif result == "partial":
            analysis.partial_count += 1
            status = "partial"
        else:
            analysis.missing_count += 1
            status = "missing"
            analysis.gaps.append(GapItem(
                category=category, item=item, status=status,
                severity=severity, description=description,
                fix_suggestion=fix_suggestion
            ))

    analysis.current_score = analysis.present_count
    return analysis


def _check_frontmatter(content: str) -> bool:
    if not content.startswith('---'):
        return False
    end = content.find('---', 3)
    if end == -1:
        return False
    fm = content[3:end]
    return 'name:' in fm and 'description:' in fm


def _check_description(content: str) -> str:
    if not _check_frontmatter(content):
        return False
    end = content.find('---', 3)
    fm = content[3:end]
    lines = fm.split('\n')
    # 找到description起始行（支持 description: / description: > / description: |）
    desc_start = -1
    for i, l in enumerate(lines):
        if l.strip().startswith('description:'):
            desc_start = i
            break
    if desc_start == -1:
        return False
    # 提取description完整内容（支持YAML折叠标量>/|）
    first_line = lines[desc_start].strip()
    if first_line.endswith('>') or first_line.endswith('|') or first_line.endswith('>-') or first_line.endswith('|-'):
        # 折叠标量：继续读取缩进行，直到遇到非缩进行或frontmatter结束
        desc_parts = []
        for j in range(desc_start + 1, len(lines)):
            if lines[j].strip() == '':
                continue
            if lines[j].startswith(' ') or lines[j].startswith('\t'):
                desc_parts.append(lines[j].strip())
            else:
                break
        desc = ' '.join(desc_parts).lower()
    else:
        # 单行description
        desc = first_line[len('description:'):].strip().lower()
    has_what = len(desc) > 30
    has_when = any(w in desc for w in ['when', 'use', '触发', '适用于', '场景'])
    has_trigger = any(w in desc for w in ['触发', 'trigger', '"'])
    if has_what and has_when and has_trigger:
        return True
    elif has_what or has_when:
        return "partial"
    return False


def _check_no_redundant(skill_path: str) -> bool:
    redundant = ['README.md', 'CHANGELOG.md', 'INSTALLATION_GUIDE.md', 'QUICK_REFERENCE.md']
    for f in redundant:
        if os.path.isfile(os.path.join(skill_path, f)):
            return False
    if os.path.isdir(os.path.join(skill_path, '__pycache__')):
        return False
    return True


def _check_script_error_handling(skill_path: str) -> bool:
    scripts_dir = os.path.join(skill_path, "scripts")
    if not os.path.isdir(scripts_dir):
        return "partial"  # 没有脚本，不适用
    py_files = [f for f in os.listdir(scripts_dir) if f.endswith('.py')]
    if not py_files:
        return "partial"
    has_try = False
    for f in py_files:
        try:
            with open(os.path.join(scripts_dir, f), 'r') as fh:
                if 'try:' in fh.read():
                    has_try = True
                    break
        except Exception:
            pass
    return has_try


def _check_validator(skill_path: str) -> bool:
    scripts_dir = os.path.join(skill_path, "scripts")
    if not os.path.isdir(scripts_dir):
        return False
    return any('valid' in f.lower() for f in os.listdir(scripts_dir))


def _check_config(skill_path: str) -> bool:
    scripts_dir = os.path.join(skill_path, "scripts")
    if not os.path.isdir(scripts_dir):
        return "partial"
    has_config = any('config' in f.lower() for f in os.listdir(scripts_dir))
    # 检查是否有硬编码凭据
    for f in os.listdir(scripts_dir):
        if f.endswith('.py'):
            try:
                with open(os.path.join(scripts_dir, f), 'r') as fh:
                    content = fh.read()
                    if 'api_key' in content.lower() and '=' in content and 'os.environ' not in content:
                        return False
            except Exception:
                pass
    return has_config or "partial"


def _check_e2e_test(skill_path: str) -> bool:
    refs_dir = os.path.join(skill_path, "references")
    if os.path.isdir(refs_dir):
        return any('test' in f.lower() or 'e2e' in f.lower() for f in os.listdir(refs_dir))
    return False


def _check_evaluation(skill_path: str) -> bool:
    refs_dir = os.path.join(skill_path, "references")
    if os.path.isdir(refs_dir):
        return any('evaluat' in f.lower() for f in os.listdir(refs_dir))
    return False


# ============================================================
# 迁移应用
# ============================================================

def apply_migration(skill_path: str, analysis: GapAnalysis,
                     target_path: str = None, backup: bool = False) -> Dict[str, Any]:
    """应用迁移方案，创建缺失的专业版结构"""
    target = target_path or skill_path
    created_files = []
    created_dirs = []

    # 备份
    if backup:
        backup_path = f"{skill_path}-backup-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copytree(skill_path, backup_path)
        print(f"  ✅ 备份原技能到: {backup_path}")

    # 如果目标不同，先复制
    if target_path and target_path != skill_path:
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(skill_path, target)
        print(f"  ✅ 复制技能到: {target}")

    # 创建缺失的目录
    missing_items = {g.item for g in analysis.gaps}

    if "references目录" in missing_items:
        refs_dir = os.path.join(target, "references")
        os.makedirs(refs_dir, exist_ok=True)
        created_dirs.append("references/")
        print(f"  ✅ 创建 references/ 目录")

    if "scripts目录" in missing_items:
        scripts_dir = os.path.join(target, "scripts")
        os.makedirs(scripts_dir, exist_ok=True)
        created_dirs.append("scripts/")
        print(f"  ✅ 创建 scripts/ 目录")

    # 创建references文档骨架
    if os.path.isdir(os.path.join(target, "references")):
        refs_to_create = [
            ("gotchas.md", "# 常见坑与解决方案\n\n> 记录使用本技能时常见的失败模式和修正方法。\n\n## 坑1：[描述]\n**症状**：\n**根因**：\n**修正**：\n"),
            ("best-practices.md", "# 最佳实践\n\n> 本技能的最佳实践和使用建议。\n\n## 1. [实践名称]\n[描述]\n"),
        ]
        for filename, content in refs_to_create:
            filepath = os.path.join(target, "references", filename)
            if not os.path.isfile(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                created_files.append(f"references/{filename}")
                print(f"  ✅ 创建 references/{filename}")

    # 更新SKILL.md（添加缺失的section）
    skill_md_path = os.path.join(target, "SKILL.md")
    if os.path.isfile(skill_md_path):
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        additions = []
        if "Gotchas section" in missing_items and "## Gotchas" not in content and "## 常见坑" not in content:
            additions.append("\n## Gotchas（常见坑）\n\n> 记录使用本技能时常见的失败模式和修正方法。\n\n1. **[坑1描述]** - [修正方法]\n")
        if "渐进式披露引用表" in missing_items and "references/" not in content:
            additions.append("\n## References（按需加载）\n\n| 场景 | 文档 |\n|------|------|\n| [场景1] | `references/gotchas.md` |\n")
        if "输出格式文档化" in missing_items and "## 输出" not in content and "## Output" not in content:
            additions.append("\n## 输出格式\n\n### 简洁版\n[简洁输出格式]\n\n### 完整版\n[完整输出格式]\n")

        if additions:
            content = content.rstrip() + '\n' + ''.join(additions)
            with open(skill_md_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ 更新 SKILL.md（添加 {len(additions)} 个section）")

    # 清理冗余文件
    if "无冗余文件" in missing_items:
        for f in ['README.md', 'CHANGELOG.md']:
            fp = os.path.join(target, f)
            if os.path.isfile(fp):
                os.remove(fp)
                print(f"  🗑️  删除冗余文件: {f}")
        pycache = os.path.join(target, '__pycache__')
        if os.path.isdir(pycache):
            shutil.rmtree(pycache, ignore_errors=True)

    return {
        "success": True,
        "skill_path": target,
        "mode": "upgrade",
        "created_dirs": created_dirs,
        "created_files": created_files,
        "note": f"迁移完成：创建{len(created_dirs)}个目录，{len(created_files)}个文件"
    }


# ============================================================
# 报告输出
# ============================================================

def print_migration_report(analysis: GapAnalysis):
    """打印迁移报告"""
    print(f"\n{'='*60}")
    print(f"🔄 技能迁移升级分析报告")
    print(f"{'='*60}")
    print(f"  技能路径: {analysis.skill_path}")
    print(f"  技能名称: {analysis.skill_name or '(未检测到)'}")
    print(f"{'='*60}")

    print(f"\n📊 当前完整度: {analysis.completeness_pct}%")
    print(f"  已达标: {analysis.present_count}/{analysis.total_checks}")
    print(f"  部分达标: {analysis.partial_count}")
    print(f"  缺失: {analysis.missing_count}")

    if not analysis.gaps:
        print(f"\n✅ 技能已达到专业标准，无需迁移！")
        print(f"{'='*60}\n")
        return

    # 按严重度分组
    high_gaps = [g for g in analysis.gaps if g.severity == "high"]
    medium_gaps = [g for g in analysis.gaps if g.severity == "medium"]
    low_gaps = [g for g in analysis.gaps if g.severity == "low"]

    for label, gaps in [("🔴 高优先级（必须修复）", high_gaps),
                          ("🟡 中优先级（建议修复）", medium_gaps),
                          ("🔵 低优先级（可选修复）", low_gaps)]:
        if not gaps:
            continue
        print(f"\n{label} ({len(gaps)}项):")
        for g in gaps:
            print(f"  - [{g.category}] {g.item}: {g.description}")
            print(f"    修复: {g.fix_suggestion}")

    print(f"\n💡 使用 --apply 参数自动应用迁移方案")
    print(f"💡 使用 --backup 参数在迁移前自动备份")
    print(f"{'='*60}\n")


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="技能迁移升级脚本（将简单技能升级到专业标准）")
    parser.add_argument("skill_path", help="技能目录路径")
    parser.add_argument("--apply", action="store_true", help="应用迁移方案（创建缺失文件）")
    parser.add_argument("--backup", action="store_true", help="迁移前自动备份")
    parser.add_argument("--target", help="迁移到新目录（不修改原技能）")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    # 校验输入
    if not os.path.isdir(args.skill_path):
        print(f"❌ 技能目录不存在: {args.skill_path}", file=sys.stderr)
        sys.exit(1)

    try:
        analysis = analyze_gap(args.skill_path)
    except Exception as e:
        print(f"❌ 差距分析失败: {e}", file=sys.stderr)
        sys.exit(3)

    if args.json:
        output = {
            "skill_path": analysis.skill_path,
            "skill_name": analysis.skill_name,
            "completeness_pct": analysis.completeness_pct,
            "total_checks": analysis.total_checks,
            "present": analysis.present_count,
            "partial": analysis.partial_count,
            "missing": analysis.missing_count,
            "gaps": [{"category": g.category, "item": g.item, "severity": g.severity,
                       "description": g.description, "fix_suggestion": g.fix_suggestion}
                      for g in analysis.gaps],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_migration_report(analysis)

    if args.apply:
        try:
            result = apply_migration(args.skill_path, analysis,
                                     target_path=args.target, backup=args.backup)
        except Exception as e:
            print(f"❌ 迁移失败: {e}", file=sys.stderr)
            sys.exit(3)
        if not args.json:
            print(f"\n✅ 迁移完成: {result['note']}")
            for f in result.get('created_files', []):
                print(f"  - {f}")

    sys.exit(0)


if __name__ == "__main__":
    main()
