#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本: v1.0.0 | 许可证: MIT | 最低Python: 3.7+

技能规范校验脚本（Skill Validator）

基于Anthropic官方规范 + 36项检查清单，校验技能是否符合规范。

用法：
  python3 validate_skill.py <skill-path>
  python3 validate_skill.py <skill-path> --json  # JSON格式输出
"""
import argparse
import json
import os
import re
import sys

# === 常量定义（避免魔法数字）===
MAX_SKILL_NAME_LENGTH = 64          # 技能名最大字符数
MAX_DESCRIPTION_LENGTH = 1024       # description最大字符数
MAX_SKILL_MD_LINES = 500            # SKILL.md行数上限（超过必须拆分）
WARN_SKILL_MD_LINES = 300           # SKILL.md行数警告阈值（超过建议拆分）
MAX_SCRIPT_CHECK_COUNT = 5          # 最多检查的脚本数量
MAX_READ_FIRST_LINES = 5            # 读取脚本前N行检查docstring
MAX_FILE_SIZE_BYTES = 2_000_000    # 最大读取文件大小（2MB）


def check_frontmatter(skill_md_path):
    """检查frontmatter规范"""
    issues = []
    try:
        with open(skill_md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        issues.append({"level": "high", "item": "frontmatter", "message": f"SKILL.md读取失败: {e}"})
        return issues

    # 检查是否有frontmatter
    if not content.startswith("---"):
        issues.append({"level": "high", "item": "frontmatter", "message": "缺少YAML frontmatter"})
        return issues

    # 提取frontmatter
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        issues.append({"level": "high", "item": "frontmatter", "message": "frontmatter格式错误"})
        return issues

    fm = match.group(1)

    # 检查name字段
    name_match = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
    if not name_match:
        issues.append({"level": "high", "item": "frontmatter.name", "message": "缺少name字段"})
    else:
        name = name_match.group(1).strip().strip('"').strip("'")
        if not re.match(r"^[a-z0-9-]+$", name):
            issues.append({"level": "high", "item": "frontmatter.name", "message": f"name格式错误: {name}（只允许小写字母、数字、连字符）"})
        if len(name) > MAX_SKILL_NAME_LENGTH:
            issues.append({"level": "medium", "item": "frontmatter.name", "message": f"name过长: {len(name)}字符（max {MAX_SKILL_NAME_LENGTH}）"})

    # 检查description字段
    desc_match = re.search(r"^description:\s*(.+?)(?=\n[a-z_]+:|\Z)", fm, re.DOTALL | re.MULTILINE)
    if not desc_match:
        issues.append({"level": "high", "item": "frontmatter.description", "message": "缺少description字段"})
    else:
        desc = desc_match.group(1).strip().strip('"').strip("'")
        # 去除折叠符号 >
        desc = desc.lstrip(">").strip()
        if len(desc) > MAX_DESCRIPTION_LENGTH:
            issues.append({"level": "high", "item": "frontmatter.description", "message": f"description过长: {len(desc)}字符（max {MAX_DESCRIPTION_LENGTH}）"})
        # 检查是否包含触发词
        if not re.search(r"[“\"'](.+?)[”\"']", desc) and "触发" not in desc and "when" not in desc.lower():
            issues.append({"level": "medium", "item": "frontmatter.description", "message": "description可能缺少触发词（建议用引号标注触发词）"})

    # 检查白名单字段
    allowed_fields = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
    field_names = re.findall(r"^([a-z_]+):", fm, re.MULTILINE)
    for field in field_names:
        if field not in allowed_fields:
            issues.append({"level": "medium", "item": f"frontmatter.{field}", "message": f"非白名单字段: {field}（允许: name/description/license/compatibility/metadata/allowed-tools）"})

    return issues


def check_skill_md_body(skill_md_path):
    """检查SKILL.md body规范"""
    issues = []
    try:
        with open(skill_md_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        issues.append({"level": "high", "item": "SKILL.md.body", "message": f"SKILL.md读取失败: {e}"})
        return issues

    # 检查行数
    line_count = len(lines)
    if line_count > MAX_SKILL_MD_LINES:
        issues.append({"level": "high", "item": "SKILL.md行数", "message": f"SKILL.md过长: {line_count}行（建议<{MAX_SKILL_MD_LINES}行，详细内容放references/）"})
    elif line_count > WARN_SKILL_MD_LINES:
        issues.append({"level": "low", "item": "SKILL.md行数", "message": f"SKILL.md {line_count}行，接近上限，建议考虑拆分"})

    content = "".join(lines)

    # 检查是否有"什么时候使用"在body里（应该只在description里）
    if re.search(r"##\s*(什么时候使用|使用场景|何时使用|When to Use)", content):
        issues.append({"level": "medium", "item": "body触发信息", "message": "body里有'什么时候使用'章节，触发信息应该只放frontmatter的description里"})

    # 检查是否有Gotchas
    if not re.search(r"##\s*(Gotchas|踩坑|常见坑|坑)", content):
        issues.append({"level": "low", "item": "Gotchas", "message": "建议添加Gotchas章节（具体失败模式+修正方法）"})

    # 检查是否有示例
    if not re.search(r"##\s*(示例|Examples|完整示例)", content) and "examples/" not in content:
        issues.append({"level": "low", "item": "示例", "message": "建议添加示例（examples/目录或SKILL.md里的示例章节）"})

    return issues


def check_content_quality(skill_md_path):
    """检查SKILL.md内容质量（TODO占位符/模板残留/明显无关内容）"""
    issues = []
    content, err = safe_read_file(skill_md_path)
    if err or not content:
        return issues

    # 检查TODO占位符未替换
    todo_patterns = [
        (r"TODO[:：]", "包含TODO占位符，发布前应替换为实际内容"),
        (r"FIXME[:：]", "包含FIXME标记，发布前应修复"),
        (r"XXX[:：]", "包含XXX标记，发布前应替换"),
        (r"\[待填写\]|\[待补充\]|\[占位\]", "包含占位标记，发布前应填充"),
    ]
    for pattern, message in todo_patterns:
        if re.search(pattern, content):
            issues.append({"level": "medium", "item": "内容质量", "message": message})

    # 检查模板残留（init_skill生成的默认内容未修改）
    template_residues = [
        (r"技能标题", "可能包含模板默认标题，建议修改为实际标题"),
        (r"这里写.*描述", "可能包含模板默认描述，建议修改为实际描述"),
        (r"示例脚本.*替换", "可能包含模板示例脚本说明，建议删除或替换"),
    ]
    for pattern, message in template_residues:
        if re.search(pattern, content):
            issues.append({"level": "low", "item": "内容质量", "message": message})

    # 检查是否有明显的乱码或控制字符
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", content):
        issues.append({"level": "medium", "item": "内容质量", "message": "包含不可见控制字符，可能是编码问题"})

    # 检查frontmatter之后是否有内容（不是空文件）
    body = re.sub(r"^---\n.*?\n---", "", content, flags=re.DOTALL).strip()
    if not body:
        issues.append({"level": "high", "item": "内容质量", "message": "SKILL.md body为空，只有frontmatter"})

    return issues


def detect_module_files(scripts_dir):
    """
    检测哪些脚本是被其他脚本import的模块文件。
    模块文件不需要main入口（因为它们是被import的，不是独立运行的）。
    返回：被import的脚本文件名集合（不含.py后缀）。
    """
    if not os.path.exists(scripts_dir):
        return set()

    scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]
    imported_modules = set()

    # 读取所有脚本内容，分析import语句
    for script in scripts:
        script_path = os.path.join(scripts_dir, script)
        content, _ = safe_read_file(script_path)
        if not content:
            continue
        # 分析 from xxx import 语句
        for match in re.finditer(r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import', content, re.MULTILINE):
            mod_name = match.group(1)
            if mod_name + ".py" in scripts:
                imported_modules.add(mod_name)
        # 分析 import xxx 语句（只取第一个模块名）
        for match in re.finditer(r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE):
            mod_name = match.group(1)
            if mod_name + ".py" in scripts:
                imported_modules.add(mod_name)

    # 常见模块文件命名模式（即使没被import也视为模块）
    module_patterns = ['config', 'utils', 'constants', 'helpers', 'types', 'models', 'schemas']
    for script in scripts:
        base = script[:-3]  # 去掉.py
        if base in module_patterns or base.startswith('indicators_') or base.startswith('utils_'):
            imported_modules.add(base)

    return imported_modules


def check_scripts_integrity(skill_path):
    """检查脚本完整性（语法错误/main入口/docstring）"""
    issues = []
    scripts_dir = os.path.join(skill_path, "scripts")
    if not os.path.exists(scripts_dir):
        return issues

    # 检测模块文件（被其他脚本import的，不需要main入口）
    module_files = detect_module_files(scripts_dir)

    scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]
    for script in scripts:
        script_path = os.path.join(scripts_dir, script)

        # 检查语法错误（用py_compile）
        import py_compile
        try:
            py_compile.compile(script_path, doraise=True)
        except py_compile.PyCompileError as e:
            issues.append({"level": "high", "item": f"scripts/{script}", "message": f"脚本语法错误: {str(e)[:100]}"})
            continue  # 语法错误就不继续检查其他项了
        except Exception as e:
            issues.append({"level": "medium", "item": f"scripts/{script}", "message": f"脚本编译异常: {str(e)[:100]}"})
            continue

        # 检查文件大小（空脚本）
        if os.path.getsize(script_path) < 10:
            issues.append({"level": "medium", "item": f"scripts/{script}", "message": "脚本文件过小（<10字节），可能是空文件"})
            continue

        # 检查main入口（模块文件不需要main入口）
        script_content, _ = safe_read_file(script_path)
        if script_content:
            script_base = script[:-3]  # 去掉.py
            is_module = script_base in module_files
            if not is_module and 'if __name__ == "__main__"' not in script_content and "def main()" not in script_content:
                issues.append({"level": "low", "item": f"scripts/{script}", "message": "脚本可能缺少main入口（建议添加if __name__ == '__main__'）"})

            # 检查docstring
            first_lines = "\n".join(script_content.split("\n")[:MAX_READ_FIRST_LINES])
            if '"""' not in first_lines and "'''" not in first_lines:
                issues.append({"level": "low", "item": f"scripts/{script}", "message": "脚本建议添加模块docstring（说明用途和用法）"})

    return issues


def safe_read_file(path, max_bytes=MAX_FILE_SIZE_BYTES):
    """安全读取文件，处理非UTF-8编码。返回(内容, 错误信息)。"""
    try:
        if os.path.getsize(path) > max_bytes:
            return "", f"文件过大（>{max_bytes//1000}K），跳过"
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), None
    except Exception as e:
        return "", str(e)


def check_directory_structure(skill_path, has_skill_md=True):
    """检查目录结构"""
    issues = []
    skill_md = os.path.join(skill_path, "SKILL.md")

    # 缺SKILL.md时，只检查目录结构，不做需要读SKILL.md的检查
    if not has_skill_md:
        # 检查scripts目录（不需要读SKILL.md）
        scripts_dir = os.path.join(skill_path, "scripts")
        if os.path.exists(scripts_dir):
            module_files = detect_module_files(scripts_dir)
            scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]
            for script in scripts[:MAX_SCRIPT_CHECK_COUNT]:
                script_base = script[:-3]
                if script_base in module_files:
                    continue  # 模块文件不需要main入口
                script_path = os.path.join(scripts_dir, script)
                script_content, _ = safe_read_file(script_path)
                if script_content and 'if __name__ == "__main__"' not in script_content and "def main()" not in script_content:
                    issues.append({"level": "low", "item": f"scripts/{script}", "message": "脚本可能缺少main入口"})
        return issues

    # 检查目录名与name是否一致
    # 处理"."或相对路径的情况，获取实际目录名
    abs_path = os.path.abspath(skill_path)
    dir_name = os.path.basename(abs_path)
    content, _ = safe_read_file(skill_md)
    if content:
        name_match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip('"').strip("'")
            if name != dir_name:
                issues.append({"level": "medium", "item": "目录名", "message": f"目录名({dir_name})与name({name})不一致"})

    # 检查scripts目录
    scripts_dir = os.path.join(skill_path, "scripts")
    if os.path.exists(scripts_dir):
        module_files = detect_module_files(scripts_dir)
        scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]
        if scripts:
            for script in scripts[:MAX_SCRIPT_CHECK_COUNT]:
                script_base = script[:-3]
                if script_base in module_files:
                    continue  # 模块文件不需要main入口
                script_path = os.path.join(scripts_dir, script)
                script_content, _ = safe_read_file(script_path)
                if not script_content:
                    continue
                if 'if __name__ == "__main__"' not in script_content and "def main()" not in script_content:
                    issues.append({"level": "low", "item": f"scripts/{script}", "message": "脚本可能缺少main入口"})
                first_lines = "\n".join(script_content.split("\n")[:MAX_READ_FIRST_LINES])
                if '"""' not in first_lines and "'''" not in first_lines:
                    issues.append({"level": "low", "item": f"scripts/{script}", "message": "脚本建议添加模块docstring"})

    # 检查references目录
    refs_dir = os.path.join(skill_path, "references")
    if os.path.exists(refs_dir):
        refs = [f for f in os.listdir(refs_dir) if f.endswith(".md")]
        if refs and content:
            for ref in refs:
                if ref not in content:
                    issues.append({"level": "low", "item": f"references/{ref}", "message": "references文件未在SKILL.md中引用（建议说明什么时候读）"})

    return issues


def validate_skill(skill_path):
    """校验技能规范"""
    result = {
        "skill_path": skill_path,
        "success": True,
        "issues": [],
        "summary": {"high": 0, "medium": 0, "low": 0},
    }

    # 检查路径是否存在
    if not os.path.exists(skill_path):
        result["success"] = False
        result["issues"].append({"level": "high", "item": "路径", "message": f"路径不存在: {skill_path}"})
        # 统计后再返回
        for issue in result["issues"]:
            result["summary"][issue["level"]] += 1
        return result

    # 检查SKILL.md
    skill_md = os.path.join(skill_path, "SKILL.md")
    has_skill_md = os.path.exists(skill_md)
    if has_skill_md:
        result["issues"].extend(check_frontmatter(skill_md))
        result["issues"].extend(check_skill_md_body(skill_md))
        result["issues"].extend(check_content_quality(skill_md))
    else:
        result["issues"].append({"level": "high", "item": "SKILL.md", "message": "缺少SKILL.md文件"})

    # 检查目录结构（缺SKILL.md时跳过需要读SKILL.md的检查）
    result["issues"].extend(check_directory_structure(skill_path, has_skill_md=has_skill_md))

    # 检查脚本完整性（语法错误等，不需要SKILL.md）
    result["issues"].extend(check_scripts_integrity(skill_path))

    # 统计
    for issue in result["issues"]:
        result["summary"][issue["level"]] += 1

    # 判断是否成功（没有high级别问题）
    result["success"] = result["summary"]["high"] == 0

    return result


def print_result(result, output_json=False):
    """输出校验结果"""
    if output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"\n{'='*60}")
    print(f"技能规范校验报告: {result['skill_path']}")
    print(f"{'='*60}")

    if result["success"]:
        print(f"\n✅ 校验通过（无高优先级问题）")
    else:
        print(f"\n❌ 校验未通过（有高优先级问题）")

    print(f"\n问题统计: 高={result['summary']['high']}  中={result['summary']['medium']}  低={result['summary']['low']}")

    if result["issues"]:
        print(f"\n问题详情:")
        for i, issue in enumerate(result["issues"], 1):
            level_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[issue["level"]]
            print(f"  {i}. {level_icon} [{issue['level'].upper()}] {issue['item']}: {issue['message']}")

    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="技能规范校验")
    parser.add_argument("skill_path", help="技能目录路径")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    result = validate_skill(args.skill_path)
    print_result(result, output_json=args.json)

    # 有高优先级问题时返回非0退出码
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
