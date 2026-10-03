#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description Optimizer（自动描述改进脚本）

分析SKILL.md的description字段，给出改进建议：
- 检查三要素（What/When/Differentiator）
- 检查触发词是否明确
- 检查长度是否合适（100-200词最佳）
- 给出改进后的description建议

用法：
  python3 description_optimizer.py <skill_dir>
  python3 description_optimizer.py <skill_dir> --auto  # 自动改进
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path


def extract_description(skill_md_path):
    """从SKILL.md提取description"""
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取frontmatter
        if not content.startswith("---"):
            return None, "没有frontmatter"

        end = content.find("---", 3)
        if end == -1:
            return None, "frontmatter未闭合"

        fm_text = content[3:end]

        # 提取description
        desc_match = re.search(r"^description:\s*(.+?)(?=\n[a-z_]+:|\Z)", fm_text, re.DOTALL | re.MULTILINE)
        if not desc_match:
            return None, "缺少description字段"

        desc = desc_match.group(1).strip().strip('"').strip("'")
        # 去除折叠符号 >
        desc = desc.lstrip(">").strip()

        return desc, None
    except Exception as e:
        return None, f"读取失败: {e}"


def analyze_description(desc):
    """分析description质量"""
    issues = []
    suggestions = []
    score = 100

    # 1. 长度检查
    word_count = len(desc.split())
    char_count = len(desc)

    if char_count > 1024:
        issues.append(f"过长: {char_count}字符（max 1024）")
        score -= 20
    elif char_count < 50:
        issues.append(f"过短: {char_count}字符（建议100-200词）")
        score -= 15
    elif 100 <= word_count <= 200:
        suggestions.append(f"✅ 长度合适: {word_count}词")
    else:
        suggestions.append(f"⚠️ 长度: {word_count}词（建议100-200词）")

    # 2. 三要素检查
    has_what = len(desc) > 30
    has_when = any(w in desc for w in ["when", "use", "触发", "适用于", "场景", "当"])
    has_trigger = any(w in desc for w in ["触发", "trigger", '"', "“"])

    if not has_what:
        issues.append("缺少What（做什么）")
        score -= 15
    else:
        suggestions.append("✅ 有What")

    if not has_when:
        issues.append("缺少When（什么时候用）")
        score -= 15
    else:
        suggestions.append("✅ 有When")

    if not has_trigger:
        issues.append("缺少触发词（建议用引号标注）")
        score -= 10
    else:
        suggestions.append("✅ 有触发词")

    # 3. 检查是否有"不适用于"
    has_not_for = "不适用于" in desc or "not for" in desc.lower()
    if has_not_for:
        suggestions.append("✅ 有不适用于（避免误触发）")
    else:
        suggestions.append("⚠️ 建议加'不适用于'（避免误触发）")

    # 4. 检查是否有具体场景
    has_specific = any(w in desc for w in ["具体", "例如", "比如", "场景"])
    if has_specific:
        suggestions.append("✅ 有具体场景")
    else:
        suggestions.append("⚠️ 建议加具体场景示例")

    return {
        "score": score,
        "char_count": char_count,
        "word_count": word_count,
        "issues": issues,
        "suggestions": suggestions,
    }


def generate_improved_description(skill_name, desc, analysis):
    """生成改进后的description建议"""
    # 简单模板
    improved = f"""{skill_name}。{desc}
触发词："{skill_name}"。
不适用于：其他不相关的任务。"""

    return improved




# ============================================================
# 触发诊断功能（从diagnose_trigger.py合并）
# ============================================================

def read_skill_md(skill_path):
    """读取SKILL.md并解析frontmatter"""
    md_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(md_path):
        return None, "SKILL.md不存在"

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析frontmatter
    if not content.startswith("---"):
        return None, "frontmatter未找到（必须以---开头）"

    end = content.find("---", 3)
    if end == -1:
        return None, "frontmatter未正确闭合"

    fm_text = content[3:end]
    fm = {}
    current_key = None
    for line in fm_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # 新key（非缩进行）
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val in (">", "|", ">-", "|-"):
                current_key = key
                fm[key] = ""
            else:
                fm[key] = val.strip('"').strip("'")
                current_key = None
        elif current_key and (line.startswith(" ") or line.startswith("\t")):
            fm[current_key] += " " + stripped

    body = content[end + 3:]
    return {"frontmatter": fm, "body": body, "raw": content}, None



def diagnose_description(fm):
    """诊断description质量"""
    desc = fm.get("description", "")
    name = fm.get("name", "")
    issues = []
    suggestions = []
    score = 100

    # 1. 长度检查
    desc_len = len(desc)
    if desc_len < 50:
        issues.append(f"description太短（{desc_len}字符），LLM无法判断何时使用")
        suggestions.append("增加具体场景和触发词，目标100-300字符")
        score -= 20
    elif desc_len > 500:
        issues.append(f"description太长（{desc_len}字符），可能被截断")
        suggestions.append("精简到200字符以内，详细信息放body")
        score -= 10

    # 2. 三要素检查
    has_what = len(desc) > 30
    has_when = any(w in desc for w in ["当", "使用", "用于", "场景", "when", "use", "trigger", "触发"])
    has_trigger = any(w in desc for w in ["\"", "触发词", "trigger", "关键词"])

    if not has_what:
        issues.append("缺少What（做什么）描述")
        suggestions.append("明确说明技能的核心功能")
        score -= 15

    if not has_when:
        issues.append("缺少When（什么时候用）描述")
        suggestions.append("说明具体使用场景，如'当用户说XX时使用'")
        score -= 15

    if not has_trigger:
        issues.append("缺少触发词列表")
        suggestions.append("在description中列出具体触发词，如触发词：\"XX\"\"YY\"")
        score -= 10

    # 3. 模糊词检查
    vague_words = ["帮助", "处理", "支持", "工具", "助手", "万能", "各种", "所有"]
    vague_found = [w for w in vague_words if w in desc and len(desc) < 200]
    if vague_found and len(desc) < 200:
        issues.append(f"description使用了模糊词：{vague_found}")
        suggestions.append("替换为具体描述，如'帮助处理文档'→'从PDF提取文本和表格'")
        score -= 10

    # 4. 第三人称检查
    first_person = any(p in desc for p in ["我可以", "我能", "你可以用我", "I can", "I help"])
    if first_person:
        issues.append("description使用第一人称，应改为第三人称")
        suggestions.append("改为'Processes X and generates Y'而非'I can help you'")
        score -= 10

    # 5. 否定检查（不适用于）
    has_not_for = "不适用于" in desc or "不用于" in desc or "not for" in desc.lower()
    if not has_not_for:
        suggestions.append("建议在description末尾加'不适用于：XXX'，避免误触发")
        score -= 5

    # 6. name检查
    if not name:
        issues.append("缺少name字段")
        score -= 20
    elif not re.match(r'^[a-z][a-z0-9-]*$', name):
        issues.append(f"name '{name}' 不符合规范（小写+连字符）")
        suggestions.append("改为kebab-case，如'pdf-processing'")
        score -= 10

    return {
        "score": max(0, score),
        "length": desc_len,
        "has_what": has_what,
        "has_when": has_when,
        "has_trigger": has_trigger,
        "has_not_for": has_not_for,
        "issues": issues,
        "suggestions": suggestions,
        "description": desc,
    }



def diagnose_body(body):
    """诊断body内容"""
    issues = []
    suggestions = []

    lines = body.count("\n") + 1

    if lines > 500:
        issues.append(f"SKILL.md body {lines}行，超过500行限制")
        suggestions.append("拆分到references/")
    elif lines > 300:
        suggestions.append(f"SKILL.md {lines}行，建议考虑拆分到references/")

    # 检查是否有路由
    has_router = "路由" in body or "router" in body.lower() or "route" in body.lower()
    if not has_router:
        suggestions.append("建议在SKILL.md开头加触发路由（多模式技能）")

    # 检查是否有Gotchas
    has_gotchas = "Gotchas" in body or "常见坑" in body or "坑" in body
    if not has_gotchas:
        suggestions.append("建议加Gotchas章节（真实失败模式+修正）")

    # 检查是否有输出格式
    has_output = "输出" in body and ("格式" in body or "格式" in body)
    if not has_output:
        suggestions.append("建议明确输出格式")

    return {
        "body_lines": lines,
        "has_router": has_router,
        "has_gotchas": has_gotchas,
        "has_output_format": has_output,
        "issues": issues,
        "suggestions": suggestions,
    }



def diagnose_directory(skill_path):
    """诊断目录结构"""
    issues = []
    suggestions = []

    expected_dirs = ["scripts", "references", "examples"]
    existing = [d for d in expected_dirs if os.path.isdir(os.path.join(skill_path, d))]

    if not os.path.isdir(os.path.join(skill_path, "references")):
        suggestions.append("建议创建references/目录存放详细文档")

    if not os.path.isdir(os.path.join(skill_path, "examples")):
        suggestions.append("建议创建examples/目录存放完整示例")

    # 检查文件命名
    ref_dir = os.path.join(skill_path, "references")
    if os.path.isdir(ref_dir):
        bad_names = [f for f in os.listdir(ref_dir)
                     if f.startswith("doc") or f.startswith("untitled") or f == "readme.md"]
        if bad_names:
            issues.append(f"references/中有不描述性的文件名：{bad_names}")
            suggestions.append("改为描述性文件名，如'form-validation.md'")

    return {
        "existing_dirs": existing,
        "issues": issues,
        "suggestions": suggestions,
    }





def load_eval_set(eval_set_path):
    """加载触发测试用例集（eval set）
    
    eval set格式：JSON数组，每个元素包含query和should_trigger
    [{"query": "用户输入", "should_trigger": true}, ...]
    """
    if not os.path.isfile(eval_set_path):
        return None, f"eval set文件不存在: {eval_set_path}"
    try:
        with open(eval_set_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return None, "eval set必须是JSON数组"
        return data, None
    except Exception as e:
        return None, f"读取eval set失败: {e}"


def split_eval_set(eval_set, train_ratio=0.6):
    """分割eval set为训练集和测试集（60%训练+40%测试）
    
    为了可复现，使用确定性分割（按索引奇偶）
    """
    train = []
    test = []
    for i, item in enumerate(eval_set):
        if i % 10 < 6:  # 前60%为训练集
            train.append(item)
        else:
            test.append(item)
    return train, test


def generate_description_candidates(skill_name, current_desc, analysis, num_candidates=5):
    """生成多个候选description（基于规则和模板变体）
    
    对齐官方skill-creator：每次迭代生成多个候选，然后评估选择最佳
    """
    candidates = []
    
    # 候选1：基于当前分析的标准改进
    improved = generate_improved_description(skill_name, current_desc, analysis)
    candidates.append({"variant": "standard", "description": improved})
    
    # 候选2：更强调触发词（用引号明确标注）
    trigger_words = extract_trigger_words(current_desc)
    if trigger_words:
        trigger_str = "、".join([f'"{w}"' for w in trigger_words[:5]])
        candidate2 = f"{skill_name}技能。当用户提到{trigger_str}时使用。"
        what = extract_what(current_desc)
        if what:
            candidate2 += f"核心能力：{what}。"
        candidates.append({"variant": "trigger-focused", "description": candidate2})
    
    # 候选3：更简洁（只保留核心三要素）
    what = extract_what(current_desc)
    when = extract_when(current_desc)
    if what and when:
        candidate3 = f"{what}。{when}"
        candidates.append({"variant": "concise", "description": candidate3})
    
    # 候选4：更详细（增加适用场景和边界说明）
    if what:
        candidate4 = f"{what}。适用于需要专业{skill_name}的场景。触发词：{trigger_str if trigger_words else '相关关键词'}。不适用于简单任务或非{skill_name}场景。"
        candidates.append({"variant": "detailed", "description": candidate4})
    
    # 候选5：第三人称+动作导向
    if what:
        candidate5 = f"处理{skill_name}相关任务，{what}。当用户需要{skill_name}时触发。"
        candidates.append({"variant": "action-oriented", "description": candidate5})
    
    return candidates[:num_candidates]


def extract_trigger_words(desc):
    """从description中提取触发词"""
    # 匹配引号中的词
    quoted = re.findall(r'[""](.+?)["""]', desc)
    if quoted:
        return quoted
    # 匹配"触发词："后面的内容
    trigger_match = re.search(r'触发词[：:]\s*(.+)', desc)
    if trigger_match:
        return [w.strip() for w in re.split(r'[、,，]', trigger_match.group(1)) if w.strip()]
    return []


def extract_what(desc):
    """提取What（做什么）"""
    # 简单提取：取第一句或前50个字符
    sentences = re.split(r'[。.！!？?]', desc)
    if sentences and sentences[0].strip():
        return sentences[0].strip()[:80]
    return desc[:80]


def extract_when(desc):
    """提取When（什么时候用）"""
    when_match = re.search(r'(当|在|适用于|use when|when)\s*(.+?)[。.；;]', desc)
    if when_match:
        return when_match.group(0).strip()[:80]
    return None


def evaluate_description_quality(desc, eval_set=None):
    """评估description质量分数（基于规则）
    
    如果提供eval_set，模拟触发率评估（基于关键词匹配）
    """
    analysis = analyze_description(desc)
    base_score = analysis.get("score", 50)
    
    # 如果有eval_set，模拟触发率
    trigger_rate = None
    if eval_set:
        triggered = 0
        trigger_words = extract_trigger_words(desc)
        for item in eval_set:
            query = item.get("query", "")
            should_trigger = item.get("should_trigger", True)
            # 简单模拟：如果query包含任何触发词，认为触发
            query_triggered = any(w in query for w in trigger_words) if trigger_words else False
            if query_triggered == should_trigger:
                triggered += 1
        trigger_rate = triggered / len(eval_set) * 100 if eval_set else 0
        # 触发率占40%权重
        final_score = base_score * 0.6 + trigger_rate * 0.4
    else:
        final_score = base_score
    
    return {
        "score": round(final_score, 1),
        "base_score": base_score,
        "trigger_rate": round(trigger_rate, 1) if trigger_rate is not None else None,
        "analysis": analysis,
    }


def run_optimization_loop(skill_path, eval_set_path=None, max_iterations=5, num_candidates=5):
    """运行描述优化自动循环（对齐官方skill-creator的run_loop）
    
    核心流程：
    1. 加载eval set，60%训练+40%测试分割
    2. 评估当前description（训练集+测试集）
    3. 迭代：生成候选→训练集评估→测试集验证→选择最佳
    4. 最多max_iterations次迭代
    5. 用测试集分数选择最佳description（防过拟合）
    """
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        return {"success": False, "error": f"SKILL.md不存在: {skill_md}"}
    
    current_desc, error = extract_description(skill_md)
    if error:
        return {"success": False, "error": error}
    
    skill_name = os.path.basename(skill_path)
    analysis = analyze_description(current_desc)
    
    # 加载eval set
    eval_set = None
    train_set = None
    test_set = None
    if eval_set_path:
        eval_set, error = load_eval_set(eval_set_path)
        if error:
            return {"success": False, "error": error}
        train_set, test_set = split_eval_set(eval_set, train_ratio=0.6)
    
    # 初始评估
    initial_eval = evaluate_description_quality(current_desc, train_set)
    initial_test_eval = evaluate_description_quality(current_desc, test_set) if test_set else None
    
    iterations = []
    best_description = current_desc
    best_test_score = initial_test_eval["score"] if initial_test_eval else initial_eval["score"]
    best_iteration = 0
    
    print("\n" + "="*70)
    print("🔄 描述优化自动循环（run_loop）")
    print("="*70)
    print(f"\n技能: {skill_name}")
    print(f"最大迭代次数: {max_iterations}")
    print(f"每轮候选数: {num_candidates}")
    if eval_set:
        print(f"eval set: {len(eval_set)}个用例（训练{len(train_set)}+测试{len(test_set)}）")
    print(f"\n初始description: {current_desc[:100]}...")
    print(f"初始训练集分数: {initial_eval['score']}")
    if initial_test_eval:
        print(f"初始测试集分数: {initial_test_eval['score']}")
    
    # 迭代循环
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- 第{iteration}轮迭代 ---")
        
        # 生成候选
        candidates = generate_description_candidates(skill_name, best_description, analysis, num_candidates)
        print(f"生成{len(candidates)}个候选description")
        
        # 训练集评估每个候选
        candidate_results = []
        for cand in candidates:
            train_eval = evaluate_description_quality(cand["description"], train_set)
            candidate_results.append({
                "variant": cand["variant"],
                "description": cand["description"],
                "train_score": train_eval["score"],
                "train_trigger_rate": train_eval["trigger_rate"],
            })
        
        # 按训练集分数排序
        candidate_results.sort(key=lambda x: x["train_score"], reverse=True)
        
        # 取top3在测试集上验证
        top3 = candidate_results[:3]
        for cand in top3:
            test_eval = evaluate_description_quality(cand["description"], test_set) if test_set else None
            cand["test_score"] = test_eval["score"] if test_eval else cand["train_score"]
            cand["test_trigger_rate"] = test_eval["trigger_rate"] if test_eval else None
        
        # 用测试集分数选择最佳（防过拟合）
        top3.sort(key=lambda x: x["test_score"], reverse=True)
        winner = top3[0]
        
        print(f"训练集TOP3: {[(c['variant'], c['train_score']) for c in candidate_results[:3]]}")
        print(f"测试集验证TOP3: {[(c['variant'], c['test_score']) for c in top3]}")
        print(f"本轮最佳: {winner['variant']} (训练{winner['train_score']}, 测试{winner['test_score']})")
        
        # 记录迭代
        iteration_record = {
            "iteration": iteration,
            "candidates": candidate_results,
            "winner": winner,
        }
        iterations.append(iteration_record)
        
        # 如果测试集分数提升，更新最佳
        if winner["test_score"] > best_test_score:
            best_description = winner["description"]
            best_test_score = winner["test_score"]
            best_iteration = iteration
            print(f"✅ 测试集分数提升！新最佳: {best_test_score}")
        else:
            print(f"⚠️ 测试集分数未提升，保持当前最佳")
            # 连续2轮无提升，提前停止
            if iteration >= 2 and iterations[-1]["winner"]["test_score"] <= best_test_score:
                if iterations[-2]["winner"]["test_score"] <= best_test_score:
                    print(f"\n⏹️ 连续2轮无提升，提前停止")
                    break
    
    # 最终结果
    print("\n" + "="*70)
    print("🏆 优化循环完成")
    print("="*70)
    print(f"\n最佳迭代: 第{best_iteration}轮")
    print(f"最佳测试集分数: {best_test_score}")
    print(f"初始测试集分数: {initial_test_eval['score'] if initial_test_eval else initial_eval['score']}")
    print(f"提升: {round(best_test_score - (initial_test_eval['score'] if initial_test_eval else initial_eval['score']), 1)}分")
    print(f"\n最佳description:")
    print(best_description)
    
    return {
        "success": True,
        "skill_name": skill_name,
        "initial_description": current_desc,
        "best_description": best_description,
        "initial_train_score": initial_eval["score"],
        "initial_test_score": initial_test_eval["score"] if initial_test_eval else None,
        "best_train_score": iterations[best_iteration-1]["winner"]["train_score"] if iterations else initial_eval["score"],
        "best_test_score": best_test_score,
        "best_iteration": best_iteration,
        "total_iterations": len(iterations),
        "iterations": iterations,
    }


def main():
    parser = argparse.ArgumentParser(description="技能描述优化与触发诊断工具")
    sub = parser.add_subparsers(dest="command")
    
    # optimize子命令
    opt_p = sub.add_parser("optimize", help="优化description")
    opt_p.add_argument("skill_path", help="技能目录路径")
    
    # diagnose子命令
    diag_p = sub.add_parser("diagnose", help="诊断触发问题")
    diag_p.add_argument("skill_path", help="技能目录路径")
    diag_p.add_argument("--json", action="store_true", help="JSON格式输出")
    
    # run_loop子命令（描述优化自动循环，对齐官方skill-creator）
    loop_p = sub.add_parser("run-loop", help="描述优化自动循环（60%训练+40%测试，最多5次迭代，防过拟合）")
    loop_p.add_argument("skill_path", help="技能目录路径")
    loop_p.add_argument("--eval-set", default="", help="触发测试用例集路径（JSON数组，含query和should_trigger）")
    loop_p.add_argument("--max-iterations", type=int, default=5, help="最大迭代次数（默认5）")
    loop_p.add_argument("--num-candidates", type=int, default=5, help="每轮候选description数量（默认5）")
    loop_p.add_argument("--apply", action="store_true", help="自动应用最佳description到SKILL.md")
    loop_p.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    if args.command == "optimize":
        # 原description_optimizer的逻辑
        skill_md = os.path.join(args.skill_path, "SKILL.md")
        if not os.path.isfile(skill_md):
            print(f"❌ SKILL.md不存在: {skill_md}", file=sys.stderr)
            sys.exit(1)
        
        desc, error = extract_description(skill_md)
        if error:
            print(f"❌ {error}", file=sys.stderr)
            sys.exit(1)
        
        analysis = analyze_description(desc)
        improved = generate_improved_description(os.path.basename(args.skill_path), desc, analysis)
        
        print("\n" + "="*60)
        print("📝 Description分析报告")
        print("="*60)
        print(f"\n当前描述: {desc[:100]}...")
        print(f"\n分析结果:")
        for k, v in analysis.items():
            print(f"  - {k}: {v}")
        print(f"\n建议改进:")
        print(improved)
        
    elif args.command == "diagnose":
        # 原diagnose_trigger的逻辑
        result, error = read_skill_md(args.skill_path)
        if error:
            print(f"❌ {error}", file=sys.stderr)
            sys.exit(1)
        
        fm = result["frontmatter"]
        body = result["body"]
        
        desc_diag = diagnose_description(fm)
        body_diag = diagnose_body(body)
        dir_diag = diagnose_directory(args.skill_path)
        
        if args.json:
            print(json.dumps({
                "description": desc_diag,
                "body": body_diag,
                "directory": dir_diag,
            }, ensure_ascii=False, indent=2))
        else:
            print("\n" + "="*60)
            print("🔍 技能触发诊断报告")
            print("="*60)
            print(f"\n技能: {fm.get('name', '未知')}")
            print(f"\n--- Description诊断 ---")
            print(f"  得分: {desc_diag.get('score', 0)}/100")
            for issue in desc_diag.get('issues', []):
                print(f"  ⚠️  {issue}")
            for sug in desc_diag.get('suggestions', []):
                print(f"  💡 {sug}")
            
            print(f"\n--- 正文诊断 ---")
            for issue in body_diag.get('issues', []):
                print(f"  ⚠️  {issue}")
            
            print(f"\n--- 目录诊断 ---")
            for issue in dir_diag.get('issues', []):
                print(f"  ⚠️  {issue}")
    
    elif args.command == "run-loop":
        # 描述优化自动循环（对齐官方skill-creator的run_loop）
        result = run_optimization_loop(
            skill_path=args.skill_path,
            eval_set_path=args.eval_set if args.eval_set else None,
            max_iterations=args.max_iterations,
            num_candidates=args.num_candidates,
        )
        
        if not result["success"]:
            print(f"❌ {result['error']}", file=sys.stderr)
            sys.exit(1)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 如果--apply，自动应用最佳description到SKILL.md
        if args.apply and result["best_description"] != result["initial_description"]:
            skill_md = os.path.join(args.skill_path, "SKILL.md")
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 替换description字段
            new_content = re.sub(
                r'^(description:\s*)(.+?)(?=\n[a-z_]+:|\Z)',
                lambda m: m.group(1) + result["best_description"],
                content,
                flags=re.DOTALL | re.MULTILINE,
                count=1,
            )
            
            with open(skill_md, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            print(f"\n✅ 已自动应用最佳description到SKILL.md")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
