#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-creator-pro 路由脚本（Router）

混合路由三层架构：
  1. 确定性匹配（关键词/正则）—— 快速处理80%明确请求
  2. 规则引擎（信号评分）—— 处理模糊请求，计算置信度
  3. 危险请求检测 —— 拦截恶意/越权请求

核心价值：
  - Claude的自动触发是概率性的（45%-84%准确率），必须用确定性路由弥补
  - 路由是渐进式披露的开关——路由确定后，才知道读什么文档、走什么流程、输出什么格式
  - 让激活可预测、可测试、可优化

用法：
  python3 router.py "用户消息"
  python3 router.py "创建一个技能" --json
  python3 router.py --test  # 运行内置测试用例
"""
import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional


# ============================================================
# 路由模式定义
# ============================================================

MODES = {
    "create": {
        "name": "新建技能",
        "triggers": [
            # 中文
            "创建", "新建", "从零开始", "生成", "搭建", "初始化", "做一个",
            "开发一个", "写一个", "造一个", "搞一个", "建一个",
            # 英文
            "create", "new", "generate", "build", "init", "initialize",
            "scaffold", "make a", "develop a",
        ],
        "must_read": [
            "references/best-practices.md",
            "references/design-philosophies.md",
            "references/36-element-checklist.md",
        ],
        "workflow": "create_skill.py create → init_skill_pro.py → validate → audit",
        "output": "完整版（技能目录+SKILL.md+scripts+references）",
    },
    "optimize": {
        "name": "优化技能",
        "triggers": [
            # 中文
            "优化", "改进", "重构", "精简", "升级", "调优", "完善",
            "修改", "调整", "改造", "进化", "迭代", "修补", "修复",
            # 英文
            "optimize", "refactor", "upgrade", "improve", "enhance",
            "tune", "polish", "modify", "adjust", "evolve",
        ],
        "must_read": [
            "references/36-element-checklist.md",
            "references/gotchas-collection.md",
            "references/best-practices.md",
        ],
        "workflow": "create_skill.py optimize → validate → audit → output_validator",
        "output": "完整版（优化后的技能+优化报告）",
    },
    "review": {
        "name": "深度评审",
        "triggers": [
            # 中文
            "评审", "审计", "规范检查", "检查", "审查", "评估", "评测",
            "诊断", "分析", "深度审计", "代码审查", "规范评审",
            # 英文
            "review", "audit", "check", "inspect", "evaluate", "assess",
            "diagnose", "analyze", "code review",
        ],
        "must_read": [
            "references/36-element-checklist.md",
            "references/review-process-guide.md",
            "references/best-practices.md",
        ],
        "workflow": "create_skill.py review → validate → audit → 评审报告",
        "output": "评审报告（评分+问题清单+改进建议）",
    },
    "test": {
        "name": "端到端测试",
        "triggers": [
            # 中文
            "测试", "实测", "验证", "压力测试", "端到端", "E2E",
            "回归测试", "单元测试", "集成测试", "跑测试", "做测试",
            # 英文
            "test", "e2e", "testing", "verify", "validation", "regression",
            "stress test", "benchmark",
        ],
        "must_read": [
            "references/eval-practice.md",
            "references/routing-mustread-test-cases.md",
            "references/evaluation-guide.md",
        ],
        "workflow": "create_skill.py test → validate → 冒烟测试 → 端到端测试",
        "output": "测试报告（通过率+失败用例+改进建议）",
    },
}

# 危险请求关键词
DANGEROUS_PATTERNS = [
    r"删除.*系统", r"删除.*所有", r"rm\s+-rf\s+/",
    r"窃取", r"破解", r"入侵", r"攻击",
    r"绕过.*权限", r"越权", r"提权",
    r"生成.*病毒", r"生成.*木马", r"生成.*恶意",
]

# 模糊阈值（低于此分数标记为模糊）
AMBIGUOUS_THRESHOLD = 0.3


# ============================================================
# 路由决策数据结构
# ============================================================

@dataclass
class RoutingDecision:
    """路由决策结果"""
    mode: str  # create/optimize/review/test/refuse/ambiguous
    confidence: str  # high/medium/low
    must_read: List[str] = field(default_factory=list)
    reasoning: str = ""
    alternatives: List[str] = field(default_factory=list)
    is_dangerous: bool = False
    scores: Dict[str, float] = field(default_factory=dict)
    matched_keywords: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


# ============================================================
# 第一层：确定性匹配
# ============================================================

def deterministic_match(user_input: str) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
    """
    第一层：确定性匹配（关键词匹配）
    
    返回：
      - scores: 每个模式的匹配分数
      - matched_keywords: 每个模式匹配到的关键词
    """
    scores = {}
    matched_keywords = {}
    input_lower = user_input.lower()

    for mode, config in MODES.items():
        score = 0.0
        matched = []

        for trigger in config["triggers"]:
            trigger_lower = trigger.lower()
            # 精确匹配（权重高）
            if trigger_lower in input_lower:
                score += 0.2
                matched.append(trigger)
            # 模糊匹配（权重低）
            elif len(trigger_lower) >= 2 and trigger_lower[:2] in input_lower:
                score += 0.05
                matched.append(f"{trigger}（模糊）")

        # 归一化（最多1.0）
        scores[mode] = min(score, 1.0)
        matched_keywords[mode] = matched

    return scores, matched_keywords


# ============================================================
# 第二层：规则引擎（信号评分）
# ============================================================

def rule_engine_scoring(user_input: str, base_scores: Dict[str, float]) -> Dict[str, float]:
    """
    第二层：规则引擎（信号评分）
    
    基于上下文信号调整分数：
      - 技能相关词汇加分
      - 明确的动作动词加分
      - 否定词减分
      - 多模式冲突时降低置信度
    """
    scores = base_scores.copy()
    input_lower = user_input.lower()

    # 信号1：技能相关词汇（所有模式都加分）
    skill_keywords = ["技能", "skill", "SKILL.md", "脚本", "文档", "工作流"]
    has_skill_context = any(kw in input_lower for kw in skill_keywords)
    if has_skill_context:
        for mode in scores:
            scores[mode] += 0.1

    # 信号2：明确的动作动词（对应模式加分）
    action_signals = {
        "create": ["新的", "一个新", "从零", "空白", "模板"],
        "optimize": ["现有", "已经", "当前", "这个技能", "我的技能"],
        "review": ["怎么样", "如何", "质量", "规范", "标准"],
        "test": ["能不能", "是否", "通过", "跑通", "效果"],
    }
    for mode, signals in action_signals.items():
        for signal in signals:
            if signal in input_lower:
                scores[mode] += 0.1
                break

    # 信号3：否定词（对应模式减分）
    negation_patterns = [
        (r"不(要|用|需要)创建", "create"),
        (r"不(要|用|需要)优化", "optimize"),
        (r"不(要|用|需要)评审", "review"),
        (r"不(要|用|需要)测试", "test"),
    ]
    for pattern, mode in negation_patterns:
        if re.search(pattern, input_lower):
            scores[mode] -= 0.3

    # 信号4：多模式冲突检测
    high_score_modes = [m for m, s in scores.items() if s >= 0.5]
    if len(high_score_modes) >= 2:
        # 多模式冲突，降低所有模式的分数
        for mode in high_score_modes:
            scores[mode] -= 0.1

    # 归一化
    for mode in scores:
        scores[mode] = max(0.0, min(scores[mode], 1.0))

    return scores


# ============================================================
# 第三层：危险请求检测
# ============================================================

def detect_dangerous(user_input: str) -> Tuple[bool, List[str]]:
    """
    第三层：危险请求检测
    
    返回：
      - is_dangerous: 是否危险
      - matched_patterns: 匹配到的危险模式
    """
    matched = []
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            matched.append(pattern)

    return len(matched) > 0, matched


# ============================================================
# 路由决策
# ============================================================

def make_decision(
    scores: Dict[str, float],
    matched_keywords: Dict[str, List[str]],
    is_dangerous: bool,
    dangerous_patterns: List[str],
) -> RoutingDecision:
    """根据三层路由结果，做出最终路由决策"""

    # 危险请求优先处理
    if is_dangerous:
        return RoutingDecision(
            mode="refuse",
            confidence="high",
            must_read=[],
            reasoning=f"检测到危险请求关键词: {', '.join(dangerous_patterns)}",
            alternatives=[],
            is_dangerous=True,
            scores=scores,
            matched_keywords=matched_keywords,
        )

    # 按分数排序
    sorted_modes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_mode, best_score = sorted_modes[0]
    second_mode, second_score = sorted_modes[1] if len(sorted_modes) > 1 else ("", 0)

    # 判断置信度
    if best_score >= 0.6:
        confidence = "high"
    elif best_score >= 0.4:
        confidence = "medium"
    else:
        confidence = "low"

    # 判断是否模糊
    is_ambiguous = (
        best_score < AMBIGUOUS_THRESHOLD
        or (best_score - second_score < 0.1 and second_score > 0.2)
    )

    if is_ambiguous:
        # 模糊请求：返回ambiguous模式，列出备选
        alternatives = [m for m, s in sorted_modes[:3] if s > 0.1]
        return RoutingDecision(
            mode="ambiguous",
            confidence=confidence,
            must_read=[],
            reasoning=f"请求模糊，最高匹配模式'{best_mode}'分数{best_score:.2f}，与第二名'{second_mode}'差距{best_score-second_score:.2f}",
            alternatives=alternatives,
            is_dangerous=False,
            scores=scores,
            matched_keywords=matched_keywords,
        )

    # 明确路由
    config = MODES[best_mode]
    matched = matched_keywords.get(best_mode, [])
    reasoning = f"匹配到{len(matched)}个关键词: {', '.join(matched[:5])}" if matched else "基于上下文信号匹配"

    return RoutingDecision(
        mode=best_mode,
        confidence=confidence,
        must_read=config["must_read"],
        reasoning=reasoning,
        alternatives=[m for m, s in sorted_modes[1:3] if s > 0.1],
        is_dangerous=False,
        scores=scores,
        matched_keywords=matched_keywords,
    )


# ============================================================
# 主路由函数
# ============================================================

def route(user_input: str) -> RoutingDecision:
    """
    完整路由流程：三层混合路由
    
    1. 确定性匹配（关键词）
    2. 规则引擎（信号评分）
    3. 危险请求检测
    4. 做出决策
    """
    # 第一层：确定性匹配
    base_scores, matched_keywords = deterministic_match(user_input)

    # 第二层：规则引擎
    final_scores = rule_engine_scoring(user_input, base_scores)

    # 第三层：危险请求检测
    is_dangerous, dangerous_patterns = detect_dangerous(user_input)

    # 做出决策
    decision = make_decision(final_scores, matched_keywords, is_dangerous, dangerous_patterns)

    return decision


# ============================================================
# 内置测试用例
# ============================================================

TEST_CASES = [
    # (输入, 预期模式, 描述)
    ("帮我创建一个技能", "create", "明确创建"),
    ("从零开始做一个新技能", "create", "从零开始"),
    ("优化一下我的技能", "optimize", "明确优化"),
    ("重构这个技能", "optimize", "重构"),
    ("帮我评审一下这个技能", "review", "明确评审"),
    ("深度审计技能现状", "review", "深度审计"),
    ("测试一下技能能不能跑通", "test", "明确测试"),
    ("端到端实测", "test", "端到端"),
    ("这个技能怎么样", "review", "模糊-评审"),
    ("技能", "ambiguous", "只有关键词，模糊"),
    ("帮我删除系统文件", "refuse", "危险请求"),
]


def run_tests() -> Dict:
    """运行内置测试用例"""
    results = []
    passed = 0
    total = len(TEST_CASES)

    for user_input, expected, desc in TEST_CASES:
        decision = route(user_input)
        is_pass = decision.mode == expected
        if is_pass:
            passed += 1

        results.append({
            "input": user_input,
            "expected": expected,
            "actual": decision.mode,
            "confidence": decision.confidence,
            "passed": is_pass,
            "desc": desc,
        })

    return {
        "total": total,
        "passed": passed,
        "pass_rate": f"{passed/total*100:.1f}%",
        "results": results,
    }


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 路由脚本（混合路由三层架构）"
    )
    parser.add_argument("input", nargs="?", help="用户输入消息")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    parser.add_argument("--test", action="store_true", help="运行内置测试用例")
    parser.add_argument("--verbose", action="store_true", help="详细输出（包含分数和匹配关键词）")

    args = parser.parse_args()

    if args.test:
        # 运行测试
        test_result = run_tests()
        if args.json:
            print(json.dumps(test_result, ensure_ascii=False, indent=2))
        else:
            print("\n" + "=" * 60)
            print("🔀 路由测试结果")
            print("=" * 60)
            print(f"\n通过率: {test_result['passed']}/{test_result['total']} ({test_result['pass_rate']})")
            print()
            for r in test_result["results"]:
                icon = "✅" if r["passed"] else "❌"
                print(f"  {icon} [{r['desc']}] '{r['input']}'")
                print(f"     预期: {r['expected']} → 实际: {r['actual']} ({r['confidence']})")
            print()
        return

    if not args.input:
        parser.error("请提供用户输入消息，或使用 --test 运行测试")

    # 路由
    decision = route(args.input)

    if args.json:
        output = decision.to_dict()
        if not args.verbose:
            # 简洁模式，去掉详细字段
            output.pop("scores", None)
            output.pop("matched_keywords", None)
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("\n" + "=" * 60)
        print("🔀 路由决策结果")
        print("=" * 60)
        print(f"\n📥 输入: {args.input}")
        print(f"\n🎯 模式: {decision.mode}")
        mode_name = MODES.get(decision.mode, {}).get("name", decision.mode)
        print(f"   ({mode_name})")
        print(f"\n📊 置信度: {decision.confidence}")
        print(f"\n💡 理由: {decision.reasoning}")

        if decision.must_read:
            print(f"\n📚 必读文档 ({len(decision.must_read)}个):")
            for doc in decision.must_read:
                print(f"   - {doc}")

        if decision.alternatives:
            print(f"\n🔄 备选模式: {', '.join(decision.alternatives)}")

        if decision.is_dangerous:
            print(f"\n🚫 危险请求: 已拦截")

        if args.verbose:
            print(f"\n📈 各模式分数:")
            for mode, score in sorted(decision.scores.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * int(score * 20)
                print(f"   {mode:10s} |{bar}| {score:.2f}")

            print(f"\n🔑 匹配关键词:")
            for mode, keywords in decision.matched_keywords.items():
                if keywords:
                    print(f"   {mode}: {', '.join(keywords[:5])}")

        print()


if __name__ == "__main__":
    main()
