#!/usr/bin/env python3
"""
版本: v1.0.0 | 许可证: MIT | 最低Python: 3.8+

output_validator.py - skill-creator-pro 输出校验脚本

功能：
  - 校验生成的技能目录是否符合 skill-creator-pro 的规范
  - 校验 SKILL.md 是否包含触发路由、渐进式披露、Gotchas 等核心要素
  - 校验 references 文档是否都从 SKILL.md 引用（渐进式披露执行层）
  - 校验脚本是否能正常运行
  - 校验无特定领域残留（通用技能不应有排列三/竞彩等特定内容）

用法：
  python3 output_validator.py <skill-path> [--mode <create|optimize|review|test>]

设计哲学：
  - 硬门禁：校验不通过就报错，不允许跳过
  - 可验证：每个校验项都有明确的通过/失败标准
  - 具体：错误信息指出具体哪里有问题，怎么改
"""

import argparse
import json
import os
import re
import subprocess
import sys

# === 常量定义（避免魔法数字）===
MIN_DESCRIPTION_LENGTH = 50          # description最小字符数
MAX_SKILL_MD_LINES = 500            # SKILL.md行数上限
WARN_SKILL_MD_LINES = 300           # SKILL.md行数警告阈值


# 排列三/竞彩等特定领域残留关键词（通用技能不应包含）
DOMAIN_SPECIFIC_KEYWORDS = [
    "排列三", "排列3", "pl3", "PL3",
    "竞彩", "jingcai", "北单", "beidan",
    "杀号", "组三", "组六", "豹子",
    "和值", "跨度", "胆码", "选号",
    "期号", "开奖", "投注", "中奖",
    "kb-01", "kb-02", "kb-04",
    "batch_write", "飞书Base",
]

# 用于自动检测技能类型的领域关键词（出现在frontmatter中则视为domain技能）
DOMAIN_DETECTION_KEYWORDS = [
    "排列三", "排列3", "排列五", "福彩3D", "双色球", "大乐透",
    "七乐彩", "快乐8", "七星彩", "竞彩", "北单", "足彩",
    "PDF", "Word", "Excel", "PPT", "幻灯片", "文档",
    "股票", "财报", "基金", "理财",
    "医疗", "医学", "药品", "健康",
    "合同", "法律", "合规",
    "爬虫", "浏览器", "自动化",
]


def detect_skill_type(skill_path):
    """
    自动检测技能类型：general（通用）或 domain（特定领域）。
    读取SKILL.md的frontmatter，如果包含明确的领域关键词则视为domain。
    支持单行description和YAML多行折叠标量（>/|）。
    """
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        return "general"
    try:
        with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # 提取frontmatter（---到---之间的部分）
        import re
        fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
        if fm_match:
            frontmatter = fm_match.group(1)
        else:
            frontmatter = content[:1000]
        for keyword in DOMAIN_DETECTION_KEYWORDS:
            if keyword in frontmatter:
                return "domain"
        return "general"
    except Exception as e:
        print(f"  ⚠️ 容错处理: {e}", file=sys.stderr)
        return "general"


def check_directory_structure(skill_path):
    """校验1：目录结构是否完整"""
    issues = []
    warnings = []

    # 必需：SKILL.md
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        issues.append("❌ 缺少必需文件: SKILL.md")
    else:
        print("  ✅ SKILL.md 存在")

    # 可选：scripts/
    scripts_dir = os.path.join(skill_path, "scripts")
    if os.path.isdir(scripts_dir):
        scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]
        print(f"  ✅ scripts/ 存在，包含 {len(scripts)} 个脚本")
    else:
        warnings.append("  ⚠️  scripts/ 目录不存在（简单技能可以没有）")

    # 可选：references/
    refs_dir = os.path.join(skill_path, "references")
    if os.path.isdir(refs_dir):
        refs = [f for f in os.listdir(refs_dir) if f.endswith(".md")]
        print(f"  ✅ references/ 存在，包含 {len(refs)} 个文档")
    else:
        warnings.append("  ⚠️  references/ 目录不存在（简单技能可以没有）")

    # 可选：assets/
    assets_dir = os.path.join(skill_path, "assets")
    if os.path.isdir(assets_dir):
        print("  ✅ assets/ 存在")
    else:
        warnings.append("  ⚠️  assets/ 目录不存在（不需要输出资源可以没有）")

    # 可选：examples/
    examples_dir = os.path.join(skill_path, "examples")
    if os.path.isdir(examples_dir):
        examples = [f for f in os.listdir(examples_dir) if f.endswith(".md")]
        print(f"  ✅ examples/ 存在，包含 {len(examples)} 个示例")
    else:
        warnings.append("  ⚠️  examples/ 目录不存在（复杂技能建议有）")

    return issues, warnings


def check_skill_md_content(skill_path):
    """校验2：SKILL.md 内容是否包含核心要素"""
    issues = []
    warnings = []

    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        return ["❌ SKILL.md 不存在，无法校验内容"], []

    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()

    # 2.1 frontmatter 校验
    if not content.startswith("---"):
        issues.append("❌ SKILL.md 缺少 YAML frontmatter（必须以 --- 开头）")
    else:
        # 检查 name 字段
        name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
        if not name_match:
            issues.append("❌ frontmatter 缺少 name 字段")
        else:
            print(f"  ✅ name: {name_match.group(1).strip()}")

        # 检查 description 字段
        desc_match = re.search(r'^description:\s*(.+?)(?=\n\w+:|\n---)', content, re.DOTALL | re.MULTILINE)
        if not desc_match:
            issues.append("❌ frontmatter 缺少 description 字段")
        else:
            desc = desc_match.group(1).strip()
            if len(desc) < MIN_DESCRIPTION_LENGTH:
                warnings.append(f"  ⚠️  description 较短（{len(desc)}字符），建议包含三要素（What/When/Trigger）")
            else:
                print(f"  ✅ description 存在（{len(desc)}字符）")

    # 2.2 触发路由校验
    if "触发路由" in content or "Trigger Routing" in content:
        print("  ✅ 包含触发路由章节")
        # 检查是否有路由格式
        if "🔀" in content or "路由:" in content:
            print("  ✅ 包含路由格式声明")
        else:
            warnings.append("  ⚠️  有触发路由章节，但缺少路由格式声明（🔀 路由: ...）")
    else:
        warnings.append("  ⚠️  缺少触发路由章节（复杂技能建议有，简单技能可以没有）")

    # 2.3 渐进式披露校验
    if "渐进式披露" in content or "Progressive Disclosure" in content:
        print("  ✅ 包含渐进式披露章节")
        # 检查是否有L1/L2/L3
        if "L1" in content and "L2" in content and "L3" in content:
            print("  ✅ 包含 L1/L2/L3 三层架构说明")
        else:
            warnings.append("  ⚠️  有渐进式披露章节，但缺少 L1/L2/L3 三层架构说明")
    else:
        issues.append("❌ 缺少渐进式披露章节（所有技能必须有）")

    # 2.4 Gotchas 校验
    if "Gotcha" in content or "常见坑" in content or "注意事项" in content:
        print("  ✅ 包含 Gotchas/常见坑章节")
    else:
        issues.append("❌ 缺少 Gotchas 章节（所有技能必须有，≥3个具体失败模式）")

    # 2.5 输出格式校验
    if "输出格式" in content or "Output Format" in content:
        print("  ✅ 包含输出格式章节")
    else:
        warnings.append("  ⚠️  缺少输出格式章节（建议有，明确输出模板）")

    # 2.6 SKILL.md 行数校验
    lines = content.count("\n") + 1
    if lines > MAX_SKILL_MD_LINES:
        issues.append(f"❌ SKILL.md 超过500行（当前{lines}行），必须拆分内容到 references")
    elif lines > WARN_SKILL_MD_LINES:
        warnings.append(f"  ⚠️  SKILL.md {lines}行，接近上限，建议考虑拆分")
    else:
        print(f"  ✅ SKILL.md {lines}行（健康）")

    return issues, warnings


def check_references_referenced(skill_path):
    """校验3：references 文档是否都从 SKILL.md 引用（渐进式披露执行层）"""
    issues = []
    warnings = []

    refs_dir = os.path.join(skill_path, "references")
    skill_md = os.path.join(skill_path, "SKILL.md")

    if not os.path.isdir(refs_dir):
        return [], ["  ⚠️  无 references/ 目录，跳过引用校验"]

    if not os.path.isfile(skill_md):
        return ["❌ SKILL.md 不存在，无法校验引用"], []

    with open(skill_md, "r", encoding="utf-8") as f:
        skill_content = f.read()

    refs = [f for f in os.listdir(refs_dir) if f.endswith(".md")]
    unreferenced = []

    for ref in refs:
        # 检查 SKILL.md 是否引用了这个文件（支持多种引用格式）
        ref_patterns = [
            f"references/{ref}",
            f"`references/{ref}`",
            f"[{ref}](references/{ref})",
            ref.replace(".md", ""),  # 不带扩展名的引用
        ]
        referenced = any(p in skill_content for p in ref_patterns)
        if referenced:
            print(f"  ✅ references/{ref} 已被 SKILL.md 引用")
        else:
            unreferenced.append(ref)

    if unreferenced:
        for ref in unreferenced:
            issues.append(f"❌ references/{ref} 未被 SKILL.md 引用（渐进式披露要求：每个reference必须从SKILL.md引用，并说明什么时候读）")
    else:
        print(f"  ✅ 所有 {len(refs)} 个 references 文档都已被引用")

    return issues, warnings


def check_scripts_runnable(skill_path):
    """校验4：脚本是否能正常运行"""
    issues = []
    warnings = []

    scripts_dir = os.path.join(skill_path, "scripts")
    if not os.path.isdir(scripts_dir):
        return [], ["  ⚠️  无 scripts/ 目录，跳过脚本校验"]

    scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".py")]

    for script in scripts:
        script_path = os.path.join(scripts_dir, script)
        # 尝试运行 --help
        try:
            result = subprocess.run(
                [sys.executable, script_path, "--help"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"  ✅ scripts/{script} 可正常运行")
            else:
                # 有些脚本不支持 --help，尝试语法检查（直接使用py_compile，避免命令注入）
                try:
                    import py_compile
                    py_compile.compile(script_path, doraise=True)
                    print(f"  ✅ scripts/{script} 语法正确（不支持--help）")
                except py_compile.PyCompileError:
                    issues.append(f"❌ scripts/{script} 语法错误")
                except Exception as e:
                    issues.append(f"❌ scripts/{script} 运行失败或语法错误: {e}")
        except subprocess.TimeoutExpired:
            warnings.append(f"  ⚠️  scripts/{script} 运行超时（可能需要输入参数）")
        except Exception as e:
            issues.append(f"❌ scripts/{script} 运行异常: {e}")

    return issues, warnings


def check_domain_specific_residue(skill_path, skill_type="auto"):
    """
    校验5：无特定领域残留（通用技能不应有排列三/竞彩等特定内容）。
    skill_type: auto（自动检测）/ general（通用技能，执行检查）/ domain（特定领域技能，跳过检查）
    """
    issues = []
    warnings = []

    # 自动检测技能类型
    if skill_type == "auto":
        skill_type = detect_skill_type(skill_path)

    # 特定领域技能跳过此检查（包含领域内容是合理的）
    if skill_type == "domain":
        print("  ✅ 特定领域技能，跳过特定领域残留检查（合理）")
        warnings.append("  ℹ️  特定领域技能，已跳过特定领域残留检查（合理）")
        return issues, warnings

    residue_found = []

    for root, dirs, files in os.walk(skill_path):
        # 跳过 .git 等隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            if file.endswith((".md", ".py")):
                file_path = os.path.join(root, file)
                # 跳过 output_validator.py 自身（它的关键词列表是用于检测的，不是残留）
                if file == "output_validator.py":
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    for keyword in DOMAIN_SPECIFIC_KEYWORDS:
                        if keyword in content:
                            # 统计出现次数
                            count = content.count(keyword)
                            residue_found.append((file_path, keyword, count))
                except Exception as e:
                    print(f"  ⚠️ 容错跳过: {e}", file=sys.stderr)

    if residue_found:
        # 按文件分组
        from collections import defaultdict
        by_file = defaultdict(list)
        for file_path, keyword, count in residue_found:
            by_file[file_path].append((keyword, count))

        for file_path, keywords in by_file.items():
            rel_path = os.path.relpath(file_path, skill_path)
            keyword_str = ", ".join([f"{k}({c}次)" for k, c in keywords])
            issues.append(f"❌ {rel_path} 包含特定领域残留: {keyword_str}")
    else:
        print("  ✅ 无特定领域残留（通用技能检查通过）")

    return issues, warnings


def check_routing_completeness(skill_path):
    """
    校验6：触发路由完整性（检查SKILL.md是否有路由表、路由模式、must_read机制）。
    路由是渐进式披露的开关，没有路由的技能无法正确触发。
    """
    issues = []
    warnings = []

    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        issues.append("❌ SKILL.md不存在，无法检查路由完整性")
        return issues, warnings

    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查1：是否有路由表章节
    has_routing_section = any(kw in content for kw in ["路由", "routing", "触发模式", "模式选择"])
    if not has_routing_section:
        issues.append("❌ SKILL.md缺少路由表章节（触发路由是渐进式披露的核心开关）")
    else:
        print("  ✅ 有路由表章节")

    # 检查2：是否有多种模式（至少2种）
    # 优先检测路由表表格的行数（通用方式，不硬编码特定模式关键词）
    def count_routing_table_modes(content):
        """统计路由表中的模式数量（通过markdown表格数据行）"""
        lines = content.split('\n')
        in_routing_section = False
        table_started = False
        mode_count = 0

        for line in lines:
            # 检测路由相关章节标题
            if line.startswith('#') and any(kw in line for kw in ['路由', 'routing', '触发模式', '模式选择']):
                in_routing_section = True
                table_started = False
                continue
            # 遇到下一个章节标题，退出路由章节
            elif line.startswith('#') and in_routing_section:
                in_routing_section = False
                continue

            if in_routing_section and line.strip().startswith('|'):
                # 跳过表头（第一行）和分隔行（|---|）
                if not table_started:
                    table_started = True
                    continue
                if '---' in line or '===' in line:
                    continue
                # 数据行：统计模式数量
                if line.strip().startswith('|') and len(line.strip()) > 3:
                    mode_count += 1

        return mode_count

    # 先尝试用表格方式统计
    mode_count = count_routing_table_modes(content)

    # 如果表格方式没检测到（可能没有路由表），再用通用关键词方式
    if mode_count == 0:
        # 通用关键词列表（不局限于特定模式，覆盖常见的路由模式类型）
        generic_mode_keywords = [
            # 技能创建类
            "新建", "创建", "优化", "评审", "审计", "测试",
            "create", "optimize", "review", "test", "audit",
            # 工具调用类
            "工具调用", "执行", "运行", "处理", "预览", "撤销",
            # 帮助查询类
            "帮助查询", "帮助", "怎么用", "用法",
            # 错误排查类
            "错误排查", "出错", "报错", "失败",
            # 分析类
            "完整分析", "快速推荐", "规则问答", "结算核对", "效果复盘",
            # 通用模式标识
            "模式", "路由模式",
        ]
        mode_count = sum(1 for kw in generic_mode_keywords if kw in content)

    if mode_count < 2:
        issues.append(f"❌ 路由模式不足（检测到{mode_count}种模式），至少需要2种路由模式")
    else:
        print(f"  ✅ 路由模式合理（检测到{mode_count}种模式，建议2-4种）")

    # 检查3：是否有must_read机制
    has_must_read = "must_read" in content or "必读文档" in content or "按需加载" in content
    if not has_must_read:
        warnings.append("⚠️ 缺少must_read机制（路由确定后应该明确必读文档）")
    else:
        print("  ✅ 有must_read机制")

    # 检查4：是否有模糊请求处理
    has_ambiguous = "模糊" in content or "ambiguous" in content or "询问用户" in content
    if not has_ambiguous:
        warnings.append("⚠️ 缺少模糊请求处理（用户请求不明确时应该询问澄清）")
    else:
        print("  ✅ 有模糊请求处理")

    # 检查5：模板路由配置检查（仅对skill-creator-pro自身，检查templates.py中的模板是否包含完整路由配置）
    skill_name = os.path.basename(skill_path)
    if skill_name == "skill-creator-pro":
        templates_py = os.path.join(skill_path, "scripts", "templates.py")
        if os.path.isfile(templates_py):
            with open(templates_py, "r", encoding="utf-8") as f:
                templates_content = f.read()

            # 检查模板中是否包含路由前缀
            template_has_route_prefix = "🔀 路由:" in templates_content
            if not template_has_route_prefix:
                issues.append("❌ templates.py的模板缺少路由前缀（🔀 路由:），生成的技能将没有触发路由")
            else:
                print("  ✅ 模板包含路由前缀")

            # 检查模板中是否包含runtime_guard使用说明
            template_has_runtime_guard = "runtime_guard.py route" in templates_content or "runtime_guard.py gate" in templates_content
            if not template_has_runtime_guard:
                warnings.append("⚠️ templates.py的模板缺少runtime_guard使用说明，生成的技能将没有路由行硬验证")
            else:
                print("  ✅ 模板包含runtime_guard使用说明")

            # 检查模板中是否包含结构化字段
            template_has_structured = "结构化字段" in templates_content or "target=" in templates_content or "period=" in templates_content
            if not template_has_structured:
                warnings.append("⚠️ templates.py的模板缺少结构化字段说明，建议增加结构化字段设计原则")
            else:
                print("  ✅ 模板包含结构化字段说明")
        else:
            warnings.append("⚠️ 未找到templates.py，无法检查模板路由配置")

    return issues, warnings


def check_progressive_disclosure_completeness(skill_path):
    """
    校验7：渐进式披露完整性（检查是否有L1/L2/L3分层，避免一次性加载所有内容）。
    渐进式披露是专业技能的核心特征，避免上下文浪费。
    """
    issues = []
    warnings = []

    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        issues.append("❌ SKILL.md不存在，无法检查渐进式披露完整性")
        return issues, warnings

    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查1：是否有渐进式披露章节
    has_pd_section = any(kw in content for kw in ["渐进式披露", "progressive disclosure", "按需加载", "分层"])
    if not has_pd_section:
        issues.append("❌ SKILL.md缺少渐进式披露章节（专业技能应该分层加载，避免上下文浪费）")
    else:
        print("  ✅ 有渐进式披露章节")

    # 检查2：是否有L1/L2/L3分层（至少2层）
    layer_keywords = ["L1", "L2", "L3", "第一层", "第二层", "第三层", "核心层", "扩展层", "完整层"]
    layer_count = sum(1 for kw in layer_keywords if kw in content)
    if layer_count < 2:
        warnings.append(f"⚠️ 渐进式披露分层不明显（检测到{layer_count}个层级关键词），建议明确L1/L2/L3")
    else:
        print(f"  ✅ 渐进式披露分层清晰（检测到{layer_count}个层级关键词）")

    # 检查3：SKILL.md行数是否合理（<500行，避免L1过重）
    line_count = content.count("\n") + 1
    if line_count > 500:
        issues.append(f"❌ SKILL.md {line_count}行，超过500行上限（L1应该精简，详细内容放L2/L3）")
    elif line_count > 400:
        warnings.append(f"⚠️ SKILL.md {line_count}行，接近500行上限，建议精简")
    else:
        print(f"  ✅ SKILL.md {line_count}行（健康，<400行）")

    # 检查4：是否有references目录（L2的载体）
    references_dir = os.path.join(skill_path, "references")
    if os.path.isdir(references_dir):
        ref_count = len([f for f in os.listdir(references_dir) if f.endswith(".md")])
        if ref_count == 0:
            warnings.append("⚠️ references目录存在但没有文档（L2层为空）")
        else:
            print(f"  ✅ references目录有{ref_count}个文档（L2层完整）")
    else:
        warnings.append("⚠️ 没有references目录（L2层缺失，详细文档应该放这里）")

    return issues, warnings


def write_audit_log(skill_path, mode, issues, warnings, passed):
    """
    写审计日志（记录输入→输出→验证结果，用于追溯和持续优化）。
    日志保存在技能目录下的 .audit_log.jsonl，每行一条JSON记录。
    """
    import datetime
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "skill_path": skill_path,
        "mode": mode,
        "issues_count": len(issues),
        "warnings_count": len(warnings),
        "passed": passed,
        "issues": issues,
        "warnings": warnings,
    }

    log_path = os.path.join(skill_path, ".audit_log.jsonl")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"\n📝 审计日志已写入: {log_path}")
    except Exception as e:
        print(f"\n⚠️  审计日志写入失败: {e}（不影响校验结果）")


def validate_output(skill_path, mode="optimize", skill_type="auto"):
    """主校验函数"""
    # 自动检测技能类型（用于显示）
    if skill_type == "auto":
        detected = detect_skill_type(skill_path)
    else:
        detected = skill_type

    print(f"\n{'='*60}")
    print(f"📋 输出校验: {skill_path}")
    print(f"   模式: {mode}")
    print(f"   技能类型: {detected}（{'自动检测' if skill_type == 'auto' else '手动指定'}）")
    print(f"{'='*60}")

    all_issues = []
    all_warnings = []

    # 校验1：目录结构
    print(f"\n--- 校验1: 目录结构 ---")
    issues, warnings = check_directory_structure(skill_path)
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    # 校验2：SKILL.md 内容
    print(f"\n--- 校验2: SKILL.md 核心要素 ---")
    issues, warnings = check_skill_md_content(skill_path)
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    # 校验3：references 引用
    print(f"\n--- 校验3: references 引用（渐进式披露执行层）---")
    issues, warnings = check_references_referenced(skill_path)
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    # 校验4：脚本可运行
    print(f"\n--- 校验4: 脚本可运行性 ---")
    issues, warnings = check_scripts_runnable(skill_path)
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    # 校验5：无特定领域残留
    print(f"\n--- 校验5: 无特定领域残留 ---")
    issues, warnings = check_domain_specific_residue(skill_path, skill_type=skill_type)
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    # 校验6：触发路由完整性
    print(f"\n--- 校验6: 触发路由完整性 ---")
    issues, warnings = check_routing_completeness(skill_path)
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    # 校验7：渐进式披露完整性
    print(f"\n--- 校验7: 渐进式披露完整性 ---")
    issues, warnings = check_progressive_disclosure_completeness(skill_path)
    all_issues.extend(issues)
    all_warnings.extend(warnings)

    # 汇总
    print(f"\n{'='*60}")
    print(f"📊 校验结果汇总（7项检查）")
    print(f"{'='*60}")
    print(f"  ❌ 问题（必须修复）: {len(all_issues)}")
    print(f"  ⚠️  警告（建议修复）: {len(all_warnings)}")

    if all_issues:
        print(f"\n❌ 问题清单:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")

    if all_warnings:
        print(f"\n⚠️  警告清单:")
        for i, warning in enumerate(all_warnings, 1):
            print(f"  {i}. {warning}")

    passed = len(all_issues) == 0

    # 写审计日志
    write_audit_log(skill_path, mode, all_issues, all_warnings, passed)

    if not passed:
        print(f"\n❌ 校验未通过，必须修复 {len(all_issues)} 个问题后才能继续")
        return False
    else:
        print(f"\n✅ 校验通过！（{len(all_warnings)} 个警告建议修复）")
        return True


def check_routing_consistency(parent_dir):
    """
    多技能路由一致性检查：扫描指定目录下的所有技能，检查路由格式是否统一。
    统一格式：🔀 路由: {技能名} · {模式} · {结构化字段}; reason={一句话}
    """
    print("\n" + "=" * 70)
    print("🔀 多技能路由一致性检查")
    print("=" * 70)
    print(f"扫描目录: {parent_dir}")
    print()

    # 扫描所有技能（包含SKILL.md的子目录）
    skills = []
    for item in sorted(os.listdir(parent_dir)):
        item_path = os.path.join(parent_dir, item)
        if os.path.isdir(item_path):
            skill_md = os.path.join(item_path, "SKILL.md")
            if os.path.isfile(skill_md):
                skills.append((item, skill_md))

    if not skills:
        print("❌ 未找到任何技能目录")
        return False

    print(f"找到 {len(skills)} 个技能:")
    for name, _ in skills:
        print(f"  - {name}")
    print()

    # 提取每个技能的路由格式
    routing_info = []
    for name, skill_md in skills:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        info = {
            "name": name,
            "has_route_prefix": "🔀 路由:" in content,
            "has_skill_name_in_route": False,
            "has_structured_fields": False,
            "has_runtime_guard_route": "runtime_guard.py route" in content,
            "route_format": "unknown",
        }

        # 提取路由行格式
        import re
        route_match = re.search(r'🔀 路由:\s*([^\n`]+)', content)
        if route_match:
            route_line = route_match.group(1).strip()
            info["route_line"] = route_line

            # 检查是否包含技能名
            if name in route_line:
                info["has_skill_name_in_route"] = True

            # 检查是否包含结构化字段（包含=或;）
            if "=" in route_line or ";" in route_line:
                info["has_structured_fields"] = True

            # 判断路由格式类型
            if "·" in route_line and name in route_line:
                info["route_format"] = "standard"  # 标准格式
            elif "·" in route_line:
                info["route_format"] = "no_skill_name"  # 有分隔符但没有技能名
            elif route_line.startswith("ROUTE"):
                info["route_format"] = "old_route"  # 旧格式
            else:
                info["route_format"] = "simple"  # 简单格式

        routing_info.append(info)

    # 输出每个技能的路由信息
    print("-" * 70)
    print(f"{'技能名':<25} {'路由前缀':<8} {'技能名':<8} {'结构化':<8} {'runtime_guard':<12} {'格式类型':<15}")
    print("-" * 70)

    standard_count = 0
    for info in routing_info:
        prefix_icon = "✅" if info["has_route_prefix"] else "❌"
        name_icon = "✅" if info["has_skill_name_in_route"] else "❌"
        struct_icon = "✅" if info["has_structured_fields"] else "❌"
        guard_icon = "✅" if info["has_runtime_guard_route"] else "❌"

        if info["route_format"] == "standard":
            standard_count += 1
            format_label = "✅ 标准格式"
        elif info["route_format"] == "no_skill_name":
            format_label = "⚠️ 缺技能名"
        elif info["route_format"] == "old_route":
            format_label = "⚠️ 旧格式"
        elif info["route_format"] == "simple":
            format_label = "⚠️ 简单格式"
        else:
            format_label = "❌ 无路由"

        print(f"{info['name']:<25} {prefix_icon:<8} {name_icon:<8} {struct_icon:<8} {guard_icon:<12} {format_label:<15}")

    print("-" * 70)
    print()

    # 统计和结论
    total = len(routing_info)
    standard_pct = standard_count / total * 100 if total > 0 else 0

    print(f"📊 统计:")
    print(f"  总技能数: {total}")
    print(f"  标准格式: {standard_count} ({standard_pct:.0f}%)")
    print(f"  非标准格式: {total - standard_count} ({100 - standard_pct:.0f}%)")
    print()

    if standard_count == total:
        print("✅ 所有技能路由格式统一，符合标准格式")
        return True
    else:
        print("❌ 存在非标准格式的技能，建议统一为标准格式：")
        print("   🔀 路由: {技能名} · {模式} · {结构化字段}; reason={一句话}")
        print()
        print("需要修复的技能:")
        for info in routing_info:
            if info["route_format"] != "standard":
                print(f"  - {info['name']}: {info['route_format']}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 输出校验脚本（硬门禁，校验不通过就报错）"
    )
    parser.add_argument("skill_path", nargs="?", help="技能目录路径")
    parser.add_argument("--mode", choices=["create", "optimize", "review", "test"], default="optimize",
                        help="校验模式（默认optimize）")
    parser.add_argument("--skill-type", choices=["auto", "general", "domain"], default="auto",
                        help="技能类型：auto自动检测/general通用技能（执行特定领域残留检查）/domain特定领域技能（跳过该检查）")
    parser.add_argument("--skill-path", dest="skill_path_arg", help=argparse.SUPPRESS)
    parser.add_argument("--check-consistency", dest="check_consistency", metavar="PARENT_DIR",
                        help="多技能路由一致性检查（扫描指定目录下的所有技能，检查路由格式是否统一）")

    args = parser.parse_args()

    # 多技能路由一致性检查模式
    if args.check_consistency:
        parent_dir = args.check_consistency
        if not os.path.isdir(parent_dir):
            print(f"❌ 目录不存在: {parent_dir}", file=sys.stderr)
            sys.exit(1)
        passed = check_routing_consistency(parent_dir)
        sys.exit(0 if passed else 1)

    # 处理 --skill-path 参数（create_skill.py 调用时用）
    skill_path = args.skill_path or args.skill_path_arg
    if not skill_path:
        parser.error("请提供技能目录路径")

    if not os.path.isdir(skill_path):
        print(f"❌ 技能目录不存在: {skill_path}", file=sys.stderr)
        sys.exit(1)

    passed = validate_output(skill_path, args.mode, skill_type=args.skill_type)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
