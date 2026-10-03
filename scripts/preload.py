#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预加载脚本（preload.py）—— 技能触发时自动运行，输出路由行模板+当前状态+必读文档

核心功能：
1. 输出路由行模板（极简格式，LLM照着输出就不会忘）
2. 输出当前状态（技能版本、脚本数量、文档数量、数据状态）
3. 输出必读文档（根据模式自动推荐）
4. 输出工作流步骤（防止跳步）
5. 输出Gotchas提醒（防止踩坑）

用法：
  python3 scripts/preload.py --mode "优化技能" --target "my-skill"
  python3 scripts/preload.py --mode "新建技能"
  python3 scripts/preload.py --mode "深度评审" --target "skill-creator-pro"
  python3 scripts/preload.py --mode "端到端测试"
  python3 scripts/preload.py --list-modes  # 列出所有支持的模式
"""
import argparse
import json
import os
import sys
from datetime import datetime

# 技能根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_skill_info():
    """获取技能基本信息"""
    skill_md = os.path.join(SKILL_ROOT, "SKILL.md")
    info = {
        "name": os.path.basename(SKILL_ROOT),
        "version": "未知",
        "skill_md_lines": 0,
        "scripts_count": 0,
        "references_count": 0,
        "examples_count": 0,
    }
    
    if os.path.isfile(skill_md):
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()
            info["skill_md_lines"] = len(content.split("\n"))
            # 提取版本号
            import re
            version_match = re.search(r'v(\d+\.\d+\.\d+)', content)
            if version_match:
                info["version"] = "v" + version_match.group(1)
    
    scripts_dir = os.path.join(SKILL_ROOT, "scripts")
    if os.path.isdir(scripts_dir):
        info["scripts_count"] = len([f for f in os.listdir(scripts_dir) if f.endswith(".py")])
    
    refs_dir = os.path.join(SKILL_ROOT, "references")
    if os.path.isdir(refs_dir):
        info["references_count"] = len([f for f in os.listdir(refs_dir) if f.endswith(".md")])
    
    examples_dir = os.path.join(SKILL_ROOT, "examples")
    if os.path.isdir(examples_dir):
        info["examples_count"] = len(os.listdir(examples_dir))
    
    return info


# 模式配置（每种模式的路由模板、必读文档、工作流步骤）
MODE_CONFIG = {
    "新建技能": {
        "route_template": "🔀 路由: {skill_name} · 新建技能 · 创建{target}技能",
        "must_read": [
            "references/36-element-checklist.md — 质量标准（创建前必读）",
            "references/best-practices.md — 官方最佳实践",
            "references/gotchas-collection.md — 真实踩坑记录",
        ],
        "workflow": [
            "第0步：写eval用例（EDD·RED阶段）",
            "第1步：需求分析（确认目标/触发场景/设计哲学）",
            "第2步：架构设计（规划目录结构/scripts/references）",
            "第3步：模板生成（运行init_skill_pro.py）",
            "第4步：内容编写（替换TODO，编写SKILL.md/references）",
            "第5步：一键校验发布（运行create_skill.py optimize）",
            "第6步：交付前门禁（运行runtime_guard.py gate）",
            "第7步：端到端测试（跑eval用例验证）",
        ],
        "gotchas": [
            "⚠️ 禁止手动创建目录结构，必须用init_skill_pro.py",
            "⚠️ description必须包含三要素（What/When/Trigger phrases）",
            "⚠️ Gotchas section是最重要的部分，必须写真实失败模式",
        ],
    },
    "优化技能": {
        "route_template": "🔀 路由: {skill_name} · 优化技能 · 优化{target}的{scope}",
        "must_read": [
            "references/36-element-checklist.md — 质量标准（优化目标）",
            "references/gotchas-collection.md — 避免重复踩坑",
            "references/tech-debt-management.md — 技术债管理（如有）",
        ],
        "workflow": [
            "第1步：全面体检（validate_skill + audit_skill + security_scan）",
            "第2步：问题分类（按优先级排序：高/中/低）",
            "第3步：制定优化方案（明确改什么/怎么改/验收标准）",
            "第4步：实施优化（按优先级逐个修复）",
            "第5步：每步验证（修复后立即验证，不积累技术债）",
            "第6步：回归测试（pytest + 端到端实测）",
            "第7步：交付前门禁（runtime_guard.py gate）",
        ],
        "gotchas": [
            "⚠️ 优化前必须先做全面体检，了解现状",
            "⚠️ 每步优化后必须验证，不积累技术债",
            "⚠️ 不要盲目做加法，先考虑是否可以精简",
        ],
    },
    "深度评审": {
        "route_template": "🔀 路由: {skill_name} · 深度评审 · 审计{target}的规范和能力",
        "must_read": [
            "references/36-element-checklist.md — 评审标准",
            "references/best-practices.md — 最佳实践对比",
            "references/gotchas-collection.md — 常见问题检查",
        ],
        "workflow": [
            "第1步：规范校验（validate_skill.py）",
            "第2步：深度审计（audit_skill.py，36项检查）",
            "第3步：安全扫描（security_scan.py）",
            "第4步：输出格式校验（output_validator.py）",
            "第5步：工作流完整性检查（runtime_guard.py verify）",
            "第6步：多维度对比（与官方最佳实践对比）",
            "第7步：输出评审报告（问题清单+优先级+改进建议）",
        ],
        "gotchas": [
            "⚠️ 评审必须客观，用数据说话，不凭感觉",
            "⚠️ 发现问题必须给出具体的改进建议，不只是批评",
            "⚠️ 评审报告必须包含优先级，方便用户决定先改什么",
        ],
    },
    "端到端测试": {
        "route_template": "🔀 路由: {skill_name} · 端到端测试 · 验证{target}实际运行效果",
        "must_read": [
            "references/e2e-testing-playbook.md — 端到端测试指南",
            "references/evaluation-guide.md — 评估用例编写指南",
        ],
        "workflow": [
            "第1步：设计测试用例（覆盖正常/边界/异常场景）",
            "第2步：准备测试环境（清理缓存/重置状态）",
            "第3步：运行测试（按用例逐个执行）",
            "第4步：记录结果（成功/失败/耗时/输出质量）",
            "第5步：分析失败原因（定位根因）",
            "第6步：修复问题（原因级补丁）",
            "第7步：回归验证（修复后重新运行全部测试）",
        ],
        "gotchas": [
            "⚠️ 测试必须覆盖边缘场景，不只是正常场景",
            "⚠️ 失败用例必须定位根因，不只是记录失败",
            "⚠️ 修复后必须回归验证，确保不引入新问题",
        ],
    },
    "🚫拒绝": {
        "route_template": "🔀 路由: {skill_name} · 🚫拒绝 · 检测到危险请求",
        "must_read": [],
        "workflow": [
            "第1步：识别危险请求类型（凭据硬编码/恶意技能/提示注入/违反规则）",
            "第2步：输出REFUSED:开头的拒绝信息",
            "第3步：提供安全替代方案",
        ],
        "gotchas": [
            "⚠️ 危险请求必须拒绝，不能妥协",
            "⚠️ 拒绝时必须提供安全替代方案，不只是说不行",
        ],
    },
}


def run_preload(mode, target=None, scope="full"):
    """运行预加载，输出路由行模板+当前状态+必读文档+工作流"""
    skill_info = get_skill_info()
    skill_name = skill_info["name"]
    
    # 检查模式是否支持
    if mode not in MODE_CONFIG:
        print(f"❌ 不支持的模式: {mode}")
        print(f"   支持的模式: {', '.join(MODE_CONFIG.keys())}")
        sys.exit(1)
    
    config = MODE_CONFIG[mode]
    
    print("\n" + "=" * 70)
    print("🚀 预加载（Preload）—— 技能触发后先运行此脚本，获取路由模板和当前状态")
    print("=" * 70)
    
    # 1. 输出路由行模板（最重要，LLM照着输出就不会忘）
    print(f"\n{'='*70}")
    print("📌 第1步：输出路由行（复制下面这行，替换重点部分）")
    print(f"{'='*70}")
    route_template = config["route_template"].format(
        skill_name=skill_name,
        target=target or "目标技能",
        scope=scope,
    )
    print(f"\n{route_template}")
    print(f"\n💡 直接复制上面这行，作为回复的第一行输出")
    
    # 2. 输出当前状态
    print(f"\n{'='*70}")
    print("📊 第2步：当前技能状态")
    print(f"{'='*70}")
    print(f"  技能名: {skill_info['name']}")
    print(f"  版本: {skill_info['version']}")
    print(f"  SKILL.md行数: {skill_info['skill_md_lines']}")
    print(f"  脚本数量: {skill_info['scripts_count']}个")
    print(f"  参考文档数量: {skill_info['references_count']}个")
    print(f"  示例数量: {skill_info['examples_count']}个")
    print(f"  当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 3. 输出必读文档
    if config["must_read"]:
        print(f"\n{'='*70}")
        print("📖 第3步：必读文档（根据当前模式推荐）")
        print(f"{'='*70}")
        for i, doc in enumerate(config["must_read"], 1):
            print(f"  {i}. {doc}")
    
    # 4. 输出工作流步骤
    print(f"\n{'='*70}")
    print(f"📋 第4步：工作流步骤（{mode}模式，共{len(config['workflow'])}步）")
    print(f"{'='*70}")
    for i, step in enumerate(config["workflow"], 1):
        print(f"  {step}")
    
    # 5. 输出Gotchas提醒
    print(f"\n{'='*70}")
    print("⚠️  第5步：Gotchas提醒（防止踩坑）")
    print(f"{'='*70}")
    for i, gotcha in enumerate(config["gotchas"], 1):
        print(f"  {gotcha}")
    
    # 6. 输出硬验证提醒
    print(f"\n{'='*70}")
    print("🔒 第6步：硬验证提醒（脚本实现，非文字说明）")
    print(f"{'='*70}")
    print(f"  1. 输出路由行后，必须运行: python3 scripts/runtime_guard.py route --mode '{mode}' --line '<路由行>'")
    print(f"  2. 每步完成后，必须运行: python3 scripts/runtime_guard.py track <step> --detail '...'")
    print(f"  3. 交付前必须运行: python3 scripts/runtime_guard.py gate --mode '{mode}'")
    print(f"  4. 任何门禁不通过，不能交付")
    
    print(f"\n{'='*70}")
    print("✅ 预加载完成。请按以上步骤执行，不要跳步，不要省略路由行。")
    print(f"{'='*70}")
    
    return {
        "skill_name": skill_name,
        "mode": mode,
        "target": target,
        "route_template": route_template,
        "skill_info": skill_info,
        "must_read": config["must_read"],
        "workflow": config["workflow"],
        "gotchas": config["gotchas"],
    }


def main():
    parser = argparse.ArgumentParser(description="预加载脚本——技能触发时自动运行，输出路由行模板+当前状态+必读文档")
    parser.add_argument("--mode", choices=list(MODE_CONFIG.keys()),
                        help="当前模式（决定路由模板/必读文档/工作流）")
    parser.add_argument("--target", default="", help="目标技能名（用于路由行模板）")
    parser.add_argument("--scope", default="full", choices=["full", "doc", "script", "config"],
                        help="优化范围（默认full）")
    parser.add_argument("--list-modes", action="store_true", help="列出所有支持的模式")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    if args.list_modes:
        print("支持的模式:")
        for mode, config in MODE_CONFIG.items():
            print(f"  - {mode}: {config['workflow'][0] if config['workflow'] else '无'}")
        return
    
    if not args.mode:
        parser.error("--mode是必填参数（除非使用--list-modes）")
    
    result = run_preload(args.mode, target=args.target or None, scope=args.scope)
    
    if args.json:
        print("\n" + json.dumps(result, ensure_ascii=False, indent=2))



# ===== UTF-8 输出兼容（Windows cp1252 无法输出 emoji，统一 UTF-8） =====
try:
    import sys as _sys
    for _s in (_sys.stdout, _sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
except Exception:
    pass

if __name__ == "__main__":
    main()
