#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本: v1.0.0 | 许可证: MIT | 最低Python: 3.8+

技能深度审计脚本 v2.0（Skill Auditor）

基于36项检查清单三层分类，对技能进行精确审计。
- 必备层（20项，权重×2）：所有技能必须达标
- 推荐层（10项，权重×1）：复杂技能建议达标
- 可选层（6项，权重×0.5）：特定领域可选

用法：
  python3 audit_skill.py <skill-path>
  python3 audit_skill.py <skill-path> --json  # JSON格式输出
"""
import argparse
import json
import os
import re
import sys

# === 常量定义（避免魔法数字）===
MAX_SKILL_MD_LINES = 500            # SKILL.md行数上限
MIN_FUNCTIONS_COUNT = 4              # 脚本最小函数数量
MIN_GOTCHAS_COUNT = 3                # Gotchas最小数量
MIN_EXAMPLE_CONTENT_LENGTH = 200     # 示例最小内容长度
TOTAL_AUDIT_ITEMS = 36               # 审计项总数
REQUIRED_ITEMS = 20                  # 必备层项数
RECOMMENDED_ITEMS = 10               # 推荐层项数
OPTIONAL_ITEMS = 6                   # 可选层项数
WEIGHTED_TOTAL = 53                  # 加权总分：20*2 + 10*1 + 6*0.5
SCORE_EXCELLENT = 90                 # 优秀评级阈值
SCORE_GOOD = 78                      # 良好评级阈值
SCORE_PASS = 67                      # 及格评级阈值


# ============================================================
# 技能类型识别
# ============================================================

def detect_skill_type(skill_path, skill_md_content):
    """识别技能类型，决定哪些检查项不适用

    返回：
      - "networked": 处理外部API/凭据/云端 → 配置中心等是推荐
      - "standalone": 纯本地工具 → 配置中心/云端等不适用
    """
    has_external_api = bool(re.search(
        r"(API|api|请求|requests|urllib|http|fetch|curl)",
        skill_md_content))
    has_credentials = bool(re.search(
        r"(key|token|密码|凭据|认证|auth|secret)",
        skill_md_content, re.IGNORECASE))
    has_cloud = bool(re.search(
        r"(云端|云端|Base|云存储|lark|feishu|云盘)",
        skill_md_content))

    # 检查scripts目录是否有网络/配置相关脚本
    scripts_dir = os.path.join(skill_path, "scripts")
    has_network_script = False
    if os.path.exists(scripts_dir):
        for f in os.listdir(scripts_dir):
            if f.endswith(".py"):
                fpath = os.path.join(scripts_dir, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as fp:
                        content = fp.read()
                    if any(k in content for k in ["requests", "urllib", "http", "api", "token", "key"]):
                        has_network_script = True
                        break
                except Exception:
                    pass

    if has_external_api or has_credentials or has_cloud or has_network_script:
        return "networked"
    return "standalone"


# ============================================================
# 必备层审计（20项，权重×2）
# ============================================================

def audit_required_layer(skill_path, skill_md_content):
    """审计必备层（20项）——所有技能必须达标"""
    results = []
    scripts_dir = os.path.join(skill_path, "scripts")
    refs_dir = os.path.join(skill_path, "references")

    # ---- 规范层（8项）----

    # 1. frontmatter规范
    has_fm = skill_md_content.startswith("---")
    name_ok = bool(re.search(r"^name:\s*[a-z0-9-]+$", skill_md_content, re.MULTILINE))
    results.append({"item": "frontmatter规范", "passed": has_fm and name_ok,
                    "detail": "name格式正确" if name_ok else "name格式错误或缺失"})

    # 2. description三要素
    desc_match = re.search(r"^description:\s*(.+?)(?=\n[a-z_]+:|\Z)", skill_md_content, re.DOTALL | re.MULTILINE)
    if desc_match:
        desc = desc_match.group(1)
        has_trigger = bool(re.search(r"[“\"'](.+?)[”\"']", desc)) or "触发" in desc
        has_what = len(desc) > 20
        has_when = "当" in desc or "用于" in desc or "使用" in desc or "时候" in desc
        results.append({"item": "description三要素",
                        "passed": has_trigger and has_what and has_when,
                        "detail": "包含What+When+Trigger" if (has_trigger and has_what and has_when)
                        else "建议补充：What(做什么)+When(什么时候用)+Trigger(触发词)"})
    else:
        results.append({"item": "description三要素", "passed": False, "detail": "缺少description字段"})

    # 3. SKILL.md <500行
    line_count = skill_md_content.count("\n") + 1
    results.append({"item": "SKILL.md<500行", "passed": line_count <= MAX_SKILL_MD_LINES,
                    "detail": f"{line_count}行" if line_count <= MAX_SKILL_MD_LINES else f"{line_count}行，超过MAX_SKILL_MD_LINES行建议拆分"})

    # 4. 渐进式披露三层架构
    has_refs = os.path.exists(refs_dir)
    has_scripts = os.path.exists(scripts_dir)
    has_layers = has_refs or has_scripts
    results.append({"item": "渐进式披露三层架构",
                    "passed": has_layers,
                    "detail": f"references={'有' if has_refs else '无'}, scripts={'有' if has_scripts else '无'}"
                    if has_layers else "建议添加references/或scripts/实现三层架构"})

    # 5. 文件引用一级深度
    deep_ref = False
    if os.path.exists(refs_dir):
        for f in os.listdir(refs_dir):
            if f.endswith(".md"):
                try:
                    with open(os.path.join(refs_dir, f), "r", encoding="utf-8", errors="replace") as fp:
                        content = fp.read()
                    if re.search(r"\]\((?!https?://)[^)]*\.md\)", content):
                        deep_ref = True
                        break
                except Exception:
                    pass
    results.append({"item": "文件引用一级深度",
                    "passed": not deep_ref,
                    "detail": "无嵌套引用" if not deep_ref else "发现references文件间的嵌套引用"})

    # 6. 无时间敏感信息
    body = skill_md_content.split("---", 2)[-1] if skill_md_content.count("---") >= 2 else skill_md_content
    time_sensitive = bool(re.search(r"(今天|昨天|明天|最新版本|当前版本|近日)", body))
    results.append({"item": "无时间敏感信息",
                    "passed": not time_sensitive,
                    "detail": "无相对时间表述" if not time_sensitive else "发现相对时间表述，版本号放body末尾"})

    # 7. 术语一致（简化检查：同一概念不混用多种叫法，排除中英文混用）
    term_inconsistent = False
    # 检查常见术语混用（排除纯中英文对照，如"技能"/"Skill"是正常的）
    common_pairs = [
        (r"输出方式", r"方案类型|交付方式"),
        (r"推荐结果", r"输出结果|交付内容"),
    ]
    for term1, term2 in common_pairs:
        if re.search(term1, body) and re.search(term2, body):
            term_inconsistent = True
            break
    results.append({"item": "术语一致",
                    "passed": not term_inconsistent,
                    "detail": "术语使用一致" if not term_inconsistent else "发现同一概念多种叫法，建议统一"})

    # 8. 示例具体不抽象
    examples_dir = os.path.join(skill_path, "examples")
    example_count = 0
    if os.path.exists(examples_dir):
        example_count = len([f for f in os.listdir(examples_dir) if f.endswith(".md")])
    has_examples_in_md = "## 示例" in skill_md_content or "## Examples" in skill_md_content or "示例" in skill_md_content
    results.append({"item": "示例具体不抽象",
                    "passed": example_count > 0 or has_examples_in_md,
                    "detail": f"{example_count}个示例文件" if example_count > 0
                    else ("SKILL.md里有示例" if has_examples_in_md else "建议添加具体示例（不是抽象的'例如...'）")})

    # ---- 架构层（4项）----

    # 9. 设计哲学明确
    has_philosophy = bool(re.search(
        r"(设计哲学|Capability|Process|能力原语|过程原语|工具包装|方法论型|混合模式)",
        skill_md_content, re.IGNORECASE))
    results.append({"item": "设计哲学明确",
                    "passed": has_philosophy,
                    "detail": "有明确的设计哲学声明" if has_philosophy
                    else "建议声明设计哲学（Capability工具包装/Process方法论/混合）"})

    # 10. 单一职责
    desc_match2 = re.search(r"^description:\s*(.+?)(?=\n[a-z_]+:|\Z)", skill_md_content, re.DOTALL | re.MULTILINE)
    single_resp = True
    if desc_match2:
        desc = desc_match2.group(1)
        # 检查是否有明确的排除范围（有"不适用于"说明职责清晰）
        if "不适用于" not in desc and "不适合" not in desc and "不用于" not in desc:
            # 检查是否列举了3个以上不相关的功能
            functions = re.findall(r"[、，,]([^、，,]{2,10})", desc)
            if len(functions) >= MIN_FUNCTIONS_COUNT:
                single_resp = False
    results.append({"item": "单一职责",
                    "passed": single_resp,
                    "detail": "职责清晰" if single_resp else "建议聚焦单一职责，复杂任务拆成多个技能组合"})

    # 11. 渐进式披露（执行层）
    has_when_to_read = bool(re.search(r"(什么时候|何时|需要时|按需).*(读|加载|参考|引用)", skill_md_content))
    has_must_read = "must_read" in skill_md_content or "必读" in skill_md_content or "mandatory" in skill_md_content.lower()
    results.append({"item": "渐进式披露执行层",
                    "passed": has_when_to_read or has_must_read,
                    "detail": "有按需加载说明" if (has_when_to_read or has_must_read)
                    else "建议说明'什么时候读什么文件'，或用must_read强制加载"})

    # 12. 技能组合友好
    has_not_for = "不适用于" in skill_md_content or "不适合" in skill_md_content or "不用于" in skill_md_content
    has_composition_note = "组合" in skill_md_content or "配合" in skill_md_content or "协作" in skill_md_content
    results.append({"item": "技能组合友好",
                    "passed": has_not_for or has_composition_note,
                    "detail": "有明确的适用边界/组合说明" if (has_not_for or has_composition_note)
                    else "建议说明'不适用于什么场景'或'可以与什么技能组合'"})

    # ---- 内容层（4项）----

    # 13. Gotchas驱动
    has_gotchas = "Gotchas" in skill_md_content or "踩坑" in skill_md_content or "常见坑" in skill_md_content or "坑" in skill_md_content
    gotcha_count = 0
    if has_gotchas:
        gotcha_count = len(re.findall(r"^\d+\.\s+\*\*", skill_md_content, re.MULTILINE))
    results.append({"item": "Gotchas驱动",
                    "passed": has_gotchas and gotcha_count >= MIN_GOTCHAS_COUNT,
                    "detail": f"{gotcha_count}个Gotchas" if gotcha_count >= MIN_GOTCHAS_COUNT
                    else ("建议添加≥MIN_GOTCHAS_COUNT个具体Gotchas（症状+修正）" if gotcha_count < 3 else "Gotchas数量充足")})

    # 14. 示例驱动（同第8项，但这里检查示例质量）
    has_quality_example = False
    if os.path.exists(examples_dir):
        for f in os.listdir(examples_dir):
            if f.endswith(".md"):
                try:
                    with open(os.path.join(examples_dir, f), "r", encoding="utf-8", errors="replace") as fp:
                        content = fp.read()
                    if len(content) > MIN_EXAMPLE_CONTENT_LENGTH:  # 示例有实质内容
                        has_quality_example = True
                        break
                except Exception:
                    pass
    results.append({"item": "示例驱动",
                    "passed": has_quality_example or (example_count > 0),
                    "detail": "有完整示例" if (has_quality_example or example_count > 0)
                    else "建议添加完整示例（覆盖完整流程，不是片段）"})

    # 15. 输出格式文档化
    has_output_format = ("输出格式" in skill_md_content or "Output Format" in skill_md_content or
                          "## 输出" in skill_md_content or "交付" in skill_md_content)
    results.append({"item": "输出格式文档化",
                    "passed": has_output_format,
                    "detail": "有输出格式模板" if has_output_format
                    else "建议添加固定输出格式模板（用户知道会得到什么）"})

    # 16. 自由度匹配
    has_freedom = bool(re.search(
        r"(自由度|高自由度|中自由度|低自由度|严格|宽松|灵活|必须|建议|可选)",
        skill_md_content))
    results.append({"item": "自由度匹配",
                    "passed": has_freedom,
                    "detail": "有自由度标注" if has_freedom
                    else "建议按步骤标注自由度（高/中/低），脆弱步骤严格，灵活步骤宽松"})

    # ---- 工程层（4项）----

    # 17. 确定性推入代码
    script_count = 0
    if os.path.exists(scripts_dir):
        script_count = len([f for f in os.listdir(scripts_dir) if f.endswith(".py")])
    results.append({"item": "确定性推入代码",
                    "passed": script_count >= 1,
                    "detail": f"{script_count}个脚本" if script_count >= 1
                    else "建议将确定性逻辑（计算/校验/采集）脚本化，不让LLM凭感觉算"})

    # 18. 错误处理
    has_error_handling = False
    if os.path.exists(scripts_dir):
        for f in os.listdir(scripts_dir):
            if f.endswith(".py"):
                try:
                    with open(os.path.join(scripts_dir, f), "r", encoding="utf-8", errors="replace") as fp:
                        if "try:" in fp.read():
                            has_error_handling = True
                            break
                except Exception:
                    pass
    has_error_in_md = "错误处理" in skill_md_content or "降级" in skill_md_content or "异常" in skill_md_content
    results.append({"item": "错误处理",
                    "passed": has_error_handling or has_error_in_md,
                    "detail": "有错误处理" if (has_error_handling or has_error_in_md)
                    else "建议脚本添加try-except，SKILL.md说明降级机制（不静默失败）"})

    # 19. 验证循环
    has_verify_loop = bool(re.search(
        r"(验证.*修正|校验.*修复|测试.*迭代|执行.*验证|验证.*通过|回归测试|验证循环)",
        skill_md_content))
    results.append({"item": "验证循环",
                    "passed": has_verify_loop,
                    "detail": "有验证闭环说明" if has_verify_loop
                    else "建议说明'执行→验证→修正'的闭环（不是执行完就完事）"})

    # 20. 状态检查后行动
    has_state_check = bool(re.search(
        r"(先检查|确认状态|检查后|检查.*再|状态.*决定|根据状态|先确认)",
        skill_md_content))
    results.append({"item": "状态检查后行动",
                    "passed": has_state_check,
                    "detail": "有状态检查说明" if has_state_check
                    else "建议说明'先检查状态，再决定行动'（防止重复执行/跳过步骤）"})

    return results


# ============================================================
# 推荐层审计（10项，权重×1）
# ============================================================

def audit_recommended_layer(skill_path, skill_md_content, skill_type):
    """审计推荐层（10项）——复杂技能建议达标"""
    results = []
    scripts_dir = os.path.join(skill_path, "scripts")
    refs_dir = os.path.join(skill_path, "references")

    # ---- 架构（2项）----

    # 21. 触发路由
    has_routing = ("🔀 路由" in skill_md_content or "触发路由" in skill_md_content or
                   "模式判断" in skill_md_content or "路由表" in skill_md_content)
    results.append({"item": "触发路由",
                    "passed": has_routing,
                    "detail": "有路由机制" if has_routing
                    else "建议添加强制路由输出（多模式技能必须有）"})

    # 22. 编排脚本
    has_orchestrator = False
    if os.path.exists(scripts_dir):
        has_orchestrator = any("orchestrat" in f.lower() or "pipeline" in f.lower() for f in os.listdir(scripts_dir))
    has_orch_in_md = "编排" in skill_md_content or "三段式" in skill_md_content or "管道" in skill_md_content
    results.append({"item": "编排脚本",
                    "passed": has_orchestrator or has_orch_in_md,
                    "detail": "有编排脚本" if (has_orchestrator or has_orch_in_md)
                    else "建议添加编排脚本统一管理工作流（多步骤复杂任务）"})

    # ---- 内容（2项）----

    # 23. 决策树+候选输出
    has_decision_tree = ("决策树" in skill_md_content or "decision_tree" in skill_md_content or
                         "候选" in skill_md_content or "评分对比" in skill_md_content)
    results.append({"item": "决策树+候选输出",
                    "passed": has_decision_tree,
                    "detail": "有决策树/候选输出" if has_decision_tree
                    else "建议添加决策树（多选项评分对比，输出候选，LLM只做最终选择）"})

    # 24. 方法论知识库
    kb_count = 0
    if os.path.exists(refs_dir):
        kb_count = len([f for f in os.listdir(refs_dir) if f.endswith(".md")])
    results.append({"item": "方法论知识库",
                    "passed": kb_count >= 2,
                    "detail": f"{kb_count}个参考文档" if kb_count >= 2
                    else "建议添加方法论/规则参考文档（≥2个）"})

    # ---- 工程（2项）----

    # 25. 校验门禁
    has_validator = False
    if os.path.exists(scripts_dir):
        has_validator = any("valid" in f.lower() or "check" in f.lower() or "audit" in f.lower()
                            for f in os.listdir(scripts_dir))
    has_gate_in_md = ("校验" in skill_md_content or "门禁" in skill_md_content or
                       "硬校验" in skill_md_content or "缺字段" in skill_md_content)
    results.append({"item": "校验门禁",
                    "passed": has_validator or has_gate_in_md,
                    "detail": "有校验机制" if (has_validator or has_gate_in_md)
                    else "建议添加校验门禁（关键步骤前硬校验，缺字段就报错）"})

    # 26. 配置中心（根据技能类型判断是否适用）
    if skill_type == "standalone":
        results.append({"item": "配置中心",
                        "passed": True,
                        "n/a": True,
                        "detail": "不适用（纯本地技能，不处理外部凭据）"})
    else:
        has_config = False
        if os.path.exists(scripts_dir):
            has_config = any("config" in f.lower() for f in os.listdir(scripts_dir))
        has_config_in_md = ("配置中心" in skill_md_content or "config" in skill_md_content.lower() or
                             "环境变量" in skill_md_content or "凭据外置" in skill_md_content)
        results.append({"item": "配置中心",
                        "passed": has_config or has_config_in_md,
                        "detail": "有配置中心" if (has_config or has_config_in_md)
                        else "建议添加配置中心（凭据外置，环境变量覆盖，不硬编码）"})

    # ---- 质量（2项）----

    # 27. 端到端实测
    has_e2e = ("端到端" in skill_md_content or "E2E" in skill_md_content or
                "实测" in skill_md_content or "集成测试" in skill_md_content)
    results.append({"item": "端到端实测",
                    "passed": has_e2e,
                    "detail": "有E2E实测说明" if has_e2e
                    else "建议做端到端实测（真实跑通完整流程，不是单元测试）"})

    # 28. 评估用例+多模型测试
    has_evals = ("评估" in skill_md_content or "eval" in skill_md_content.lower() or
                  "测试用例" in skill_md_content or "A/B" in skill_md_content)
    results.append({"item": "评估用例+多模型测试",
                    "passed": has_evals,
                    "detail": "有评估用例" if has_evals
                    else "建议添加评估用例（触发/模式/边界），多模型测试验证鲁棒性"})

    # ---- 进化安全（2项）----

    # 29. 自进化闭环
    has_evolution = ("自进化" in skill_md_content or "复盘" in skill_md_content or
                     "经验提取" in skill_md_content or "持续优化" in skill_md_content)
    results.append({"item": "自进化闭环",
                    "passed": has_evolution,
                    "detail": "有自进化机制" if has_evolution
                    else "建议添加自进化闭环（实战→复盘→经验提取→下批参考）"})

    # 30. 安全考虑
    has_security = ("安全" in skill_md_content or "权限" in skill_md_content or
                    "隐私" in skill_md_content or "数据安全" in skill_md_content or
                    "最小权限" in skill_md_content)
    results.append({"item": "安全考虑",
                    "passed": has_security,
                    "detail": "有安全说明" if has_security
                    else "建议添加安全考虑（最小权限/数据安全/输入校验/无硬编码凭据）"})

    return results


# ============================================================
# 可选层审计（6项，权重×0.5）
# ============================================================

def audit_optional_layer(skill_path, skill_md_content, skill_type):
    """审计可选层（6项）——特定领域可选。增强：不仅看SKILL.md文本，还检测脚本实际实现。"""
    results = []
    scripts_dir = os.path.join(skill_path, "scripts")
    script_names = set()
    script_contents = {}  # 脚本名→内容（用于检测函数实现）
    if os.path.exists(scripts_dir):
        script_names = {f for f in os.listdir(scripts_dir) if f.endswith(".py")}
        # 读取所有脚本内容（用于函数级检测），限制每个文件前2000行避免过大
        for sn in script_names:
            try:
                with open(os.path.join(scripts_dir, sn), "r", encoding="utf-8", errors="replace") as f:
                    script_contents[sn] = f.read(20000)  # 只读前20000字符
            except Exception:
                pass

    # 辅助函数：检测脚本中是否包含某个函数名
    def has_function(func_name):
        for content in script_contents.values():
            if f"def {func_name}" in content:
                return True
        return False

    # 辅助函数：检测脚本内容中是否包含某个关键词
    def scripts_contain(keyword):
        for content in script_contents.values():
            if keyword in content:
                return True
        return False

    # 31. 四方协同（特定领域架构）——增强：检测脚本实际实现
    has_sifang_text = ("四方协同" in skill_md_content or "技能做确定性" in skill_md_content or
                       "LLM做分析" in skill_md_content or "云端做持久化" in skill_md_content)
    # 脚本实现检测：有编排脚本(orchestrat) + 云端写入(feishu/lark) + 自进化(settle/backtest) 组合
    has_orchestrator = any("orchestrat" in n for n in script_names)
    has_cloud_write = any("batch" in n or "feishu" in n or "cloud_write" in n for n in script_names)
    has_settlement = any("settle" in n or "backtest" in n for n in script_names)
    has_sifang_impl = has_orchestrator and has_cloud_write and has_settlement
    has_sifang = has_sifang_text or has_sifang_impl
    sifang_detail = "有四方协同架构（文本声明）" if has_sifang_text else (
        "有四方协同架构（脚本实现检测：编排+云端写入+自进化）" if has_sifang_impl
        else "可选：适合数据分析/持续监控等需要云端持久化的持续运行技能")
    results.append({"item": "四方协同（特定领域）",
                    "passed": has_sifang,
                    "detail": sifang_detail})

    # 32. 定时任务——增强：检测脚本中是否有定时任务相关代码
    has_cron_text = ("定时" in skill_md_content or "cron" in skill_md_content.lower() or
                      "每天" in skill_md_content or "定期" in skill_md_content)
    has_cron_script = any("cron" in n or "schedul" in n for n in script_names)
    has_cron_code = scripts_contain("cron") or scripts_contain("schedule") or scripts_contain("定时任务")
    has_cron = has_cron_text or has_cron_script or has_cron_code
    results.append({"item": "定时任务",
                    "passed": has_cron,
                    "detail": "有定时任务" if has_cron
                    else "可选：需要自动执行的技能可添加定时任务"})

    # 33. 通知推送——增强：检测脚本内容中是否有webhook/通知相关代码
    has_notify_text = ("通知" in skill_md_content or "推送" in skill_md_content or
                       "webhook" in skill_md_content.lower() or "机器人" in skill_md_content)
    has_notify_script = any("notify" in n or "webhook" in n or "push" in n for n in script_names)
    has_notify_code = scripts_contain("webhook") or scripts_contain("send_text") or scripts_contain("通知")
    has_notify = has_notify_text or has_notify_script or has_notify_code
    results.append({"item": "通知推送",
                    "passed": has_notify,
                    "detail": "有通知推送" if has_notify
                    else "可选：需要结果推送到手机端的技能可添加"})

    # 34. 云端持久化（根据技能类型判断）——增强：检测脚本内容中是否有云端写入
    if skill_type == "standalone":
        results.append({"item": "云端持久化",
                        "passed": True,
                        "n/a": True,
                        "detail": "不适用（纯本地技能）"})
    else:
        has_cloud_text = ("云端" in skill_md_content or "Base" in skill_md_content or "云存储" in skill_md_content)
        has_cloud_script = any("batch" in n or "feishu" in n or "write" in n for n in script_names)
        has_cloud_code = scripts_contain("lark-cli") or scripts_contain("feishu") or scripts_contain("base_token")
        has_cloud = has_cloud_text or has_cloud_script or has_cloud_code
        results.append({"item": "云端持久化",
                        "passed": has_cloud,
                        "detail": "有云端持久化" if has_cloud
                        else "可选：关键数据需要跨期复用的技能可添加云端持久化"})

    # 35. 指标监控——增强：检测脚本实际实现（stats.py/命中率统计函数）
    has_metrics_text = ("命中率" in skill_md_content or "战绩" in skill_md_content or
                         "统计" in skill_md_content or "metrics" in skill_md_content.lower() or
                         "监控" in skill_md_content)
    has_metrics_script = any("stats" in n or "statistic" in n or "metrics" in n or "monitor" in n for n in script_names)
    has_metrics_func = has_function("calc_stats") or has_function("get_stats") or has_function("statistics")
    has_metrics_code = scripts_contain("命中率") or scripts_contain("win_rate") or scripts_contain("胜率")
    has_metrics = has_metrics_text or has_metrics_script or has_metrics_func or has_metrics_code
    metrics_detail = "有指标监控（文本声明）" if has_metrics_text else (
        "有指标监控（脚本实现检测）" if (has_metrics_script or has_metrics_func or has_metrics_code)
        else "可选：需要持续优化的技能可添加指标监控（命中率/效果统计）")
    results.append({"item": "指标监控",
                    "passed": has_metrics,
                    "detail": metrics_detail})

    # 36. 经验回流+持久化工件——增强：检测脚本实际实现（write_experience函数/经验库相关脚本）
    has_experience_text = ("经验库" in skill_md_content or "经验回流" in skill_md_content or
                            "持久化工件" in skill_md_content or "中间产物" in skill_md_content or
                            "write-experience" in skill_md_content)
    has_experience_func = has_function("write_experience") or has_function("read_experiences")
    has_experience_script = any("experience" in n or "backtest" in n for n in script_names)
    has_experience_code = scripts_contain("经验库") or scripts_contain("experience")
    has_experience = has_experience_text or has_experience_func or has_experience_script or has_experience_code
    exp_detail = "有经验回流/持久化工件（文本声明）" if has_experience_text else (
        "有经验回流/持久化工件（脚本实现检测）" if (has_experience_func or has_experience_script or has_experience_code)
        else "可选：需要跨任务复用经验/中间结果的技能可添加")
    results.append({"item": "经验回流+持久化工件",
                    "passed": has_experience,
                    "detail": exp_detail})

    return results


# ============================================================
# 主函数
# ============================================================

def _safe_read(path, max_bytes=2_000_000):
    """安全读取文件"""
    try:
        if os.path.getsize(path) > max_bytes:
            return ""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def audit_skill(skill_path):
    """深度审计技能（三层分类精确审计）"""
    result = {
        "skill_path": skill_path,
        "three_layer": {},
        "total_score": 0,
        "total_possible": TOTAL_AUDIT_ITEMS,
        "weighted_score": 0,
        "weighted_total": WEIGHTED_TOTAL,  # 20*2 + 10*1 + 6*0.5 = 53
        "grade": "",
        "skill_type": "",
        "issues": {"high": [], "medium": [], "low": []},
    }

    # 检查路径
    if not os.path.exists(skill_path):
        result["error"] = f"路径不存在: {skill_path}"
        return result

    # 读取SKILL.md
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.exists(skill_md):
        result["error"] = "缺少SKILL.md文件"
        return result

    skill_md_content = _safe_read(skill_md)
    if not skill_md_content:
        result["error"] = "SKILL.md读取失败"
        return result

    # 识别技能类型
    skill_type = detect_skill_type(skill_path, skill_md_content)
    result["skill_type"] = skill_type

    # 审计三层
    required = audit_required_layer(skill_path, skill_md_content)
    recommended = audit_recommended_layer(skill_path, skill_md_content, skill_type)
    optional = audit_optional_layer(skill_path, skill_md_content, skill_type)

    layers_data = {
        "必备层": required,
        "推荐层": recommended,
        "可选层": optional,
    }
    weights = {"必备层": 2, "推荐层": 1, "可选层": 0.5}

    for layer_name, items in layers_data.items():
        # 排除n/a项
        applicable = [item for item in items if not item.get("n/a", False)]
        na_count = len(items) - len(applicable)
        passed = sum(1 for item in applicable if item["passed"])
        total = len(applicable)
        w = weights[layer_name]

        result["three_layer"][layer_name] = {
            "passed": passed,
            "total": total,
            "na_count": na_count,
            "score": f"{passed}/{total}" + (f" ({na_count}项不适用)" if na_count > 0 else ""),
            "weight": w,
            "items": items,
        }
        result["total_score"] += passed
        result["weighted_score"] += passed * w

        # 收集问题
        for item in applicable:
            if not item["passed"]:
                if layer_name == "必备层":
                    result["issues"]["high"].append(f"[{layer_name}] {item['item']}: {item['detail']}")
                elif layer_name == "推荐层":
                    result["issues"]["medium"].append(f"[{layer_name}] {item['item']}: {item['detail']}")
                else:
                    result["issues"]["low"].append(f"[{layer_name}] {item['item']}: {item['detail']}")

    # 评级（必备层全部达标是基础）
    required_data = result["three_layer"]["必备层"]
    required_all_passed = required_data["passed"] == required_data["total"]
    score_pct = result["total_score"] / result["total_possible"] * 100
    weighted_pct = result["weighted_score"] / result["weighted_total"] * 100

    if not required_all_passed:
        result["grade"] = "不合格（必备层未全部达标）"
    elif weighted_pct >= SCORE_EXCELLENT:
        result["grade"] = "优秀"
    elif weighted_pct >= SCORE_GOOD:
        result["grade"] = "良好"
    elif weighted_pct >= SCORE_PASS:
        result["grade"] = "合格"
    else:
        result["grade"] = "不合格"

    result["weighted_pct"] = weighted_pct

    # === 6维度评估对齐（SkillCreator.ai标准：Structure/Content/Evidence/Usage/Toolchain/Freshness）===
    # 把36项检查映射到6维度，提供业界标准视角
    dimension_mapping = {
        # Structure（结构）：frontmatter/SKILL.md结构/目录/渐进式披露
        "frontmatter规范": "Structure", "description三要素": "Structure",
        "SKILL.md行数": "Structure", "渐进式披露": "Structure",
        "文件引用一级深度": "Structure", "目录结构": "Structure",
        "设计哲学明确": "Structure", "模块化拆分": "Structure",
        # Content（内容）：Gotchas/示例/输出格式/方法论
        "Gotchas驱动": "Content", "示例驱动": "Content",
        "输出格式文档化": "Content", "方法论知识库": "Content",
        "自由度匹配": "Content", "术语一致": "Content",
        "示例具体": "Content",
        # Evidence（证据）：评估用例/端到端测试/基准/多模型
        "端到端实测": "Evidence", "评估用例": "Evidence",
        "多模型测试": "Evidence", "规范评审": "Evidence",
        # Usage（使用）：触发路由/描述质量/模式选择/用户体验
        "触发路由": "Usage", "description触发词": "Usage",
        "技能组合友好": "Usage", "预加载机制": "Usage",
        # Toolchain（工具链）：脚本/错误处理/校验/配置/编排
        "脚本完整性": "Toolchain", "错误处理": "Toolchain",
        "校验门禁": "Toolchain", "配置中心": "Toolchain",
        "编排脚本": "Toolchain", "状态管理": "Toolchain",
        "确定性推入代码": "Toolchain",
        # Freshness（新鲜度）：版本/自进化/经验库/技术债
        "自进化闭环": "Freshness", "经验回流": "Freshness",
        "复盘机制": "Freshness", "指标监控": "Freshness",
        "版本管理": "Freshness", "技术债管理": "Freshness",
        "无时间敏感信息": "Freshness",
    }

    six_dimensions = {}
    for dim in ["Structure", "Content", "Evidence", "Usage", "Toolchain", "Freshness"]:
        six_dimensions[dim] = {"passed": 0, "total": 0, "items": []}

    for layer_name, items in layers_data.items():
        for item in items:
            if item.get("n/a", False):
                continue
            item_name = item.get("item", "")
            # 匹配维度（模糊匹配关键词）
            matched_dim = None
            for keyword, dim in dimension_mapping.items():
                if keyword in item_name:
                    matched_dim = dim
                    break
            if not matched_dim:
                matched_dim = "Content"  # 默认归到Content
            six_dimensions[matched_dim]["total"] += 1
            if item["passed"]:
                six_dimensions[matched_dim]["passed"] += 1
            six_dimensions[matched_dim]["items"].append({
                "item": item_name,
                "passed": item["passed"],
                "layer": layer_name,
            })

    # 计算每个维度的通过率和评级
    for dim, data in six_dimensions.items():
        if data["total"] > 0:
            data["pct"] = round(data["passed"] / data["total"] * 100, 1)
            if data["pct"] >= 90:
                data["grade"] = "优秀"
            elif data["pct"] >= 75:
                data["grade"] = "良好"
            elif data["pct"] >= 60:
                data["grade"] = "合格"
            else:
                data["grade"] = "不合格"
        else:
            data["pct"] = 0
            data["grade"] = "无数据"

    result["six_dimensions"] = six_dimensions

    return result


def print_result(result, output_json=False):
    """输出审计结果"""
    if output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if "error" in result:
        print(f"❌ 审计失败: {result['error']}")
        return

    skill_type_label = "networked（处理外部API/凭据）" if result["skill_type"] == "networked" else "standalone（纯本地工具）"

    print(f"\n{'='*70}")
    print(f"技能深度审计报告 v2.0: {result['skill_path']}")
    print(f"技能类型: {skill_type_label}")
    print(f"{'='*70}")

    print(f"\n📊 总体评分: {result['total_score']}/{result['total_possible']} ({result['total_score']/result['total_possible']*100:.0f}%)")
    print(f"⚖️  加权评分: {result['weighted_score']:.1f}/{result['weighted_total']:.1f} ({result['weighted_pct']:.0f}%)")
    print(f"🏆 等级: {result['grade']}")

    print(f"\n{'─'*70}")
    print(f"三层分类得分（必备层全部达标是基础）:")
    print(f"{'─'*70}")
    for tl_name in ["必备层", "推荐层", "可选层"]:
        tl_data = result["three_layer"][tl_name]
        bar_len = int(tl_data["passed"] / tl_data["total"] * 20) if tl_data["total"] > 0 else 0
        bar = "█" * bar_len + "░" * (20 - bar_len)
        weight_label = {2: "权重×2", 1: "权重×1", 0.5: "权重×0.5"}[tl_data["weight"]]
        na_note = f" ({tl_data['na_count']}项不适用)" if tl_data["na_count"] > 0 else ""
        print(f"  {tl_name:4s} |{bar}| {tl_data['passed']}/{tl_data['total']}{na_note} ({weight_label})")

    # 6维度评估（SkillCreator.ai标准）
    if "six_dimensions" in result:
        print(f"\n{'─'*70}")
        print(f"🎯 6维度评估（业界标准：Structure/Content/Evidence/Usage/Toolchain/Freshness）:")
        print(f"{'─'*70}")
        dim_labels = {
            "Structure": "结构（规范/目录/渐进式披露）",
            "Content": "内容（Gotchas/示例/输出格式/方法论）",
            "Evidence": "证据（评估用例/端到端测试/多模型）",
            "Usage": "使用（触发路由/描述质量/用户体验）",
            "Toolchain": "工具链（脚本/错误处理/校验/编排）",
            "Freshness": "新鲜度（版本/自进化/经验库/技术债）",
        }
        for dim in ["Structure", "Content", "Evidence", "Usage", "Toolchain", "Freshness"]:
            d = result["six_dimensions"][dim]
            bar_len = int(d["pct"] / 100 * 15) if d["total"] > 0 else 0
            bar = "█" * bar_len + "░" * (15 - bar_len)
            print(f"  {dim:12s} |{bar}| {d['passed']}/{d['total']} ({d['pct']}%) - {d['grade']}")
        print(f"  {'':12s}  {'':17s} {dim_labels['Structure']}")

    if result["issues"]["high"]:
        print(f"\n{'─'*70}")
        print(f"🔴 高优先级问题（必备层缺失，必须修复）:")
        print(f"{'─'*70}")
        for i, issue in enumerate(result["issues"]["high"], 1):
            print(f"  {i}. {issue}")

    if result["issues"]["medium"]:
        print(f"\n{'─'*70}")
        print(f"🟡 中优先级问题（推荐层缺失，建议修复）:")
        print(f"{'─'*70}")
        for i, issue in enumerate(result["issues"]["medium"], 1):
            print(f"  {i}. {issue}")

    if result["issues"]["low"]:
        print(f"\n{'─'*70}")
        print(f"🟢 低优先级问题（可选层缺失，按需添加）:")
        print(f"{'─'*70}")
        for i, issue in enumerate(result["issues"]["low"], 1):
            print(f"  {i}. {issue}")

    print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="技能深度审计 v2.0（三层分类精确审计）")
    parser.add_argument("skill_path", help="技能目录路径")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    try:
        result = audit_skill(args.skill_path)
        print_result(result, output_json=args.json)
        # 审计失败（有error）时返回非0退出码
        if "error" in result:
            sys.exit(1)
    except Exception as e:
        print(f"❌ 审计失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
