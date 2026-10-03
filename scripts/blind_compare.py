#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blind A/B Comparison（盲比较工具）

严格比较两个版本的技能，用户不知道哪个是新版，避免确认偏误。
对齐Anthropic官方skill-creator的comparator agent设计。

核心流程：
1. 接受两个技能目录路径（版本A和版本B）
2. 随机打乱顺序（输出为"技能X"和"技能Y"，不标注哪个是新版）
3. 对两个技能进行规范校验+深度审计+安全扫描
4. 生成盲比较报告（指标对比，不标注真实身份）
5. 用户评价后，运行reveal揭示哪个是新版，统计偏好

用法：
  python3 blind_compare.py compare <skill-a> <skill-b>  # 生成盲比较报告
  python3 blind_compare.py reveal <result-json> --prefer X  # 揭示答案并统计
  python3 blind_compare.py report <result-json>  # 查看完整报告
"""
import argparse
import json
import os
import random
import subprocess
import sys
from datetime import datetime


def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=cwd)
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
        }
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}


def validate_skill(skill_path, script_dir):
    """运行规范校验"""
    result = run_command([sys.executable, os.path.join(script_dir, "validate_skill.py"), skill_path])
    output = result["stdout"]
    
    # 解析问题统计
    high = medium = low = 0
    for line in output.split("\n"):
        if "问题统计" in line or "高=" in line:
            import re
            match = re.search(r'高=(\d+).*?中=(\d+).*?低=(\d+)', line)
            if match:
                high, medium, low = int(match.group(1)), int(match.group(2)), int(match.group(3))
    
    return {
        "high": high,
        "medium": medium,
        "low": low,
        "passed": high == 0,
        "raw_output": output[:2000],
    }


def audit_skill(skill_path, script_dir):
    """运行深度审计"""
    result = run_command([sys.executable, os.path.join(script_dir, "audit_skill.py"), skill_path])
    output = result["stdout"]
    
    # 解析评分
    score = 0
    essential = recommended = optional = 0
    import re
    score_match = re.search(r'总体评分.*?(\d+)/(\d+)', output)
    if score_match:
        score = int(score_match.group(1))
    essential_match = re.search(r'必备层.*?(\d+)/(\d+)', output)
    if essential_match:
        essential = int(essential_match.group(1))
    recommended_match = re.search(r'推荐层.*?(\d+)/(\d+)', output)
    if recommended_match:
        recommended = int(recommended_match.group(1))
    optional_match = re.search(r'可选层.*?(\d+)/(\d+)', output)
    if optional_match:
        optional = int(optional_match.group(1))
    
    return {
        "score": score,
        "essential": essential,
        "recommended": recommended,
        "optional": optional,
        "raw_output": output[:2000],
    }


def security_scan(skill_path, script_dir):
    """运行安全扫描"""
    result = run_command([sys.executable, os.path.join(script_dir, "security_scan.py"), skill_path])
    output = result["stdout"]
    
    # 解析安全评分
    score = 0
    high = medium = low = 0
    import re
    score_match = re.search(r'安全评分.*?(\d+)/(\d+)', output)
    if score_match:
        score = int(score_match.group(1))
    high_match = re.search(r'高风险[:：]\s*(\d+)', output)
    if high_match:
        high = int(high_match.group(1))
    medium_match = re.search(r'中风险[:：]\s*(\d+)', output)
    if medium_match:
        medium = int(medium_match.group(1))
    low_match = re.search(r'低风险[:：]\s*(\d+)', output)
    if low_match:
        low = int(low_match.group(1))
    
    return {
        "score": score,
        "high": high,
        "medium": medium,
        "low": low,
        "passed": high == 0,
        "raw_output": output[:2000],
    }


def get_skill_info(skill_path):
    """获取技能基本信息"""
    skill_md = os.path.join(skill_path, "SKILL.md")
    info = {
        "path": skill_path,
        "name": os.path.basename(skill_path),
        "skill_md_exists": os.path.isfile(skill_md),
        "skill_md_lines": 0,
        "scripts_count": 0,
        "references_count": 0,
        "examples_count": 0,
    }
    
    if os.path.isfile(skill_md):
        with open(skill_md, "r", encoding="utf-8") as f:
            info["skill_md_lines"] = len(f.readlines())
    
    scripts_dir = os.path.join(skill_path, "scripts")
    if os.path.isdir(scripts_dir):
        info["scripts_count"] = len([f for f in os.listdir(scripts_dir) if f.endswith(".py")])
    
    refs_dir = os.path.join(skill_path, "references")
    if os.path.isdir(refs_dir):
        info["references_count"] = len([f for f in os.listdir(refs_dir) if f.endswith(".md")])
    
    examples_dir = os.path.join(skill_path, "examples")
    if os.path.isdir(examples_dir):
        info["examples_count"] = len(os.listdir(examples_dir))
    
    return info


def blind_compare(skill_a, skill_b, script_dir):
    """执行盲比较
    
    随机打乱顺序，输出为"技能X"和"技能Y"，不标注哪个是新版
    """
    # 随机打乱顺序
    skills = [skill_a, skill_b]
    random.shuffle(skills)
    x_is_a = skills[0] == skill_a  # 技能X是否是版本A
    
    print("\n" + "="*70)
    print("🔬 盲比较（Blind A/B Comparison）")
    print("="*70)
    print(f"\n版本A: {skill_a}")
    print(f"版本B: {skill_b}")
    print(f"\n⚠️  以下输出已随机打乱顺序，你不知道哪个是新版")
    print(f"   请基于指标和输出质量客观评价，避免确认偏误")
    
    # 评估两个技能
    results = {}
    for label, path in [("X", skills[0]), ("Y", skills[1])]:
        print(f"\n{'='*70}")
        print(f"📊 技能{label} 评估结果")
        print(f"{'='*70}")
        
        info = get_skill_info(path)
        validate = validate_skill(path, script_dir)
        audit = audit_skill(path, script_dir)
        security = security_scan(path, script_dir)
        
        results[label] = {
            "info": info,
            "validate": validate,
            "audit": audit,
            "security": security,
        }
        
        # 输出指标（不标注真实身份）
        print(f"\n基本信息:")
        print(f"  SKILL.md行数: {info['skill_md_lines']}")
        print(f"  脚本数量: {info['scripts_count']}")
        print(f"  参考文档数量: {info['references_count']}")
        print(f"  示例数量: {info['examples_count']}")
        
        print(f"\n规范校验:")
        print(f"  高优先级问题: {validate['high']}")
        print(f"  中优先级问题: {validate['medium']}")
        print(f"  低优先级问题: {validate['low']}")
        print(f"  通过: {'✅' if validate['passed'] else '❌'}")
        
        print(f"\n深度审计:")
        print(f"  总体评分: {audit['score']}/36")
        print(f"  必备层: {audit['essential']}/20")
        print(f"  推荐层: {audit['recommended']}/10")
        print(f"  可选层: {audit['optional']}/6")
        
        print(f"\n安全扫描:")
        print(f"  安全评分: {security['score']}/100")
        print(f"  高风险: {security['high']}")
        print(f"  中风险: {security['medium']}")
        print(f"  低风险: {security['low']}")
        print(f"  通过: {'✅' if security['passed'] else '❌'}")
    
    # 对比总结
    print(f"\n{'='*70}")
    print("📈 盲比较对比总结")
    print(f"{'='*70}")
    print(f"\n{'指标':<20} {'技能X':<15} {'技能Y':<15} {'优势方'}")
    print("-"*65)
    
    comparisons = [
        ("SKILL.md行数", results["X"]["info"]["skill_md_lines"], results["Y"]["info"]["skill_md_lines"], "less_is_better"),
        ("脚本数量", results["X"]["info"]["scripts_count"], results["Y"]["info"]["scripts_count"], "more_is_better"),
        ("参考文档数量", results["X"]["info"]["references_count"], results["Y"]["info"]["references_count"], "more_is_better"),
        ("规范校验高优先级", results["X"]["validate"]["high"], results["Y"]["validate"]["high"], "less_is_better"),
        ("规范校验中优先级", results["X"]["validate"]["medium"], results["Y"]["validate"]["medium"], "less_is_better"),
        ("深度审计总分", results["X"]["audit"]["score"], results["Y"]["audit"]["score"], "more_is_better"),
        ("必备层达标", results["X"]["audit"]["essential"], results["Y"]["audit"]["essential"], "more_is_better"),
        ("安全评分", results["X"]["security"]["score"], results["Y"]["security"]["score"], "more_is_better"),
        ("安全高风险", results["X"]["security"]["high"], results["Y"]["security"]["high"], "less_is_better"),
    ]
    
    x_wins = 0
    y_wins = 0
    ties = 0
    
    for name, x_val, y_val, direction in comparisons:
        if direction == "more_is_better":
            if x_val > y_val:
                winner = "X"
                x_wins += 1
            elif y_val > x_val:
                winner = "Y"
                y_wins += 1
            else:
                winner = "平局"
                ties += 1
        else:  # less_is_better
            if x_val < y_val:
                winner = "X"
                x_wins += 1
            elif y_val < x_val:
                winner = "Y"
                y_wins += 1
            else:
                winner = "平局"
                ties += 1
        
        print(f"{name:<20} {str(x_val):<15} {str(y_val):<15} {winner}")
    
    print(f"\n指标优势统计: 技能X胜{x_wins}项 / 技能Y胜{y_wins}项 / 平局{ties}项")
    
    # 保存结果（包含真实身份，用于reveal）
    result_data = {
        "timestamp": datetime.now().isoformat(),
        "skill_a": skill_a,
        "skill_b": skill_b,
        "x_is_a": x_is_a,
        "results": {
            "X": {k: v for k, v in results["X"].items() if k != "raw_output"},
            "Y": {k: v for k, v in results["Y"].items() if k != "raw_output"},
        },
        "comparison": {
            "x_wins": x_wins,
            "y_wins": y_wins,
            "ties": ties,
        },
        "user_preference": None,
    }
    
    # 保存到文件
    result_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                f"blind_compare_{int(datetime.now().timestamp())}.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 盲比较结果已保存: {result_file}")
    print(f"\n👉 请基于以上指标客观评价，然后运行:")
    print(f"   python3 blind_compare.py reveal {result_file} --prefer X  # 如果你认为技能X更好")
    print(f"   python3 blind_compare.py reveal {result_file} --prefer Y  # 如果你认为技能Y更好")
    print(f"   python3 blind_compare.py reveal {result_file} --prefer tie  # 如果你认为平局")
    
    return result_file


def reveal_result(result_file, prefer):
    """揭示盲比较答案并统计偏好"""
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    x_is_a = data["x_is_a"]
    skill_a = data["skill_a"]
    skill_b = data["skill_b"]
    
    # 揭示真实身份
    if x_is_a:
        x_real = "版本A"
        y_real = "版本B"
        x_path = skill_a
        y_path = skill_b
    else:
        x_real = "版本B"
        y_real = "版本A"
        x_path = skill_b
        y_path = skill_a
    
    print("\n" + "="*70)
    print("🎭 盲比较结果揭示")
    print("="*70)
    print(f"\n真实身份:")
    print(f"  技能X = {x_real} ({x_path})")
    print(f"  技能Y = {y_real} ({y_path})")
    
    print(f"\n你的偏好: {prefer}")
    
    # 判断用户是否选择了更好的版本
    x_score = data["results"]["X"]["audit"]["score"]
    y_score = data["results"]["Y"]["audit"]["score"]
    
    if x_score > y_score:
        objectively_better = "X"
    elif y_score > x_score:
        objectively_better = "Y"
    else:
        objectively_better = "tie"
    
    print(f"\n客观指标优势方: {objectively_better} (审计总分 X={x_score}, Y={y_score})")
    
    if prefer == objectively_better:
        print(f"✅ 你的偏好与客观指标一致！")
    elif prefer == "tie":
        print(f"⚠️  你选择了平局，但客观指标有差异")
    else:
        print(f"🤔 你的偏好与客观指标不一致，可能有其他考虑因素（如输出质量、易用性等）")
    
    # 保存偏好
    data["user_preference"] = prefer
    data["revealed_at"] = datetime.now().isoformat()
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 偏好已保存到: {result_file}")
    
    return data


def main():
    parser = argparse.ArgumentParser(description="盲比较工具（Blind A/B Comparison）——严格比较两个版本的技能，避免确认偏误")
    sub = parser.add_subparsers(dest="command")
    
    # compare子命令
    comp_p = sub.add_parser("compare", help="生成盲比较报告（随机打乱顺序，不标注哪个是新版）")
    comp_p.add_argument("skill_a", help="版本A技能目录路径")
    comp_p.add_argument("skill_b", help="版本B技能目录路径")
    
    # reveal子命令
    reveal_p = sub.add_parser("reveal", help="揭示答案并统计偏好")
    reveal_p.add_argument("result_file", help="盲比较结果JSON文件路径")
    reveal_p.add_argument("--prefer", choices=["X", "Y", "tie"], required=True, help="你的偏好（X/Y/tie）")
    
    # report子命令
    rep_p = sub.add_parser("report", help="查看完整盲比较报告")
    rep_p.add_argument("result_file", help="盲比较结果JSON文件路径")
    
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.command == "compare":
        # 验证两个技能目录都存在
        if not os.path.isdir(args.skill_a):
            print(f"❌ 版本A技能目录不存在: {args.skill_a}", file=sys.stderr)
            sys.exit(1)
        if not os.path.isdir(args.skill_b):
            print(f"❌ 版本B技能目录不存在: {args.skill_b}", file=sys.stderr)
            sys.exit(1)
        
        blind_compare(args.skill_a, args.skill_b, script_dir)
    
    elif args.command == "reveal":
        if not os.path.isfile(args.result_file):
            print(f"❌ 结果文件不存在: {args.result_file}", file=sys.stderr)
            sys.exit(1)
        reveal_result(args.result_file, args.prefer)
    
    elif args.command == "report":
        if not os.path.isfile(args.result_file):
            print(f"❌ 结果文件不存在: {args.result_file}", file=sys.stderr)
            sys.exit(1)
        with open(args.result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
