---
name: skill-creator-pro
description: >
  专业级Agent Skill创建与优化工具。基于三层分类36要素最佳实践，支持新建技能、优化现有技能、深度评审、端到端测试四种模式。
  当用户需要创建新技能、优化现有技能、评审技能规范、测试技能质量时使用。
  触发词："创建技能""优化技能""评审技能""技能审计""技能测试""skill creator""skill review"。
  不适用于：简单prompt编写、非Skill格式的提示词优化。
---

# 专业级技能创建器（Skill Creator Pro）

> **⚠️ 触发后第一步（不可跳过）**：任何输出前，必须先输出这一行路由声明：
> ```
> 🔀 路由: {模式}｜任务: {简述}｜原因: {一句话}
> ```
> 没有路由声明的输出视为无效。路由确定后，才读取对应模式的must_read文档。

> **版本**: v1.0.0 | **最低Python版本**: 3.8+ | **许可证**: MIT
>
> **设计哲学**: 混合型（Mixed）——工具脚本（validate/audit/init）+ 方法论（36项清单+最佳实践）结合。适合需要工具+判断的复杂技能创建任务。

> **预加载**: 触发后先输出路由行（见上方⚠️），再根据路由模式读取对应的references文档。L2文档按需加载，不需要全部读取。

---

## 🔀 路由模式表（顶部已要求先输出路由行，此处为模式选择参考）

| 模式 | 触发词 | must_read（必读文档+脚本） | 输出详略 |
|------|--------|---------------------------|----------|
| **新建技能** | "创建技能""新建skill""从零开始" | `references/best-practices.md` + `references/design-philosophies.md` + `references/36-element-checklist.md` + `scripts/create_skill.py` | 完整版 |
| **优化技能** | "优化技能""改进skill""重构" | `references/36-element-checklist.md` + `references/gotchas-collection.md` + `scripts/create_skill.py` + `scripts/output_validator.py` | 完整版 |
| **深度评审** | "评审技能""技能审计""规范检查" | `references/36-element-checklist.md` + `references/review-process-guide.md` + `scripts/create_skill.py` + `scripts/output_validator.py` | 评审报告 |
| **端到端测试** | "测试技能""技能实测""E2E测试" | `references/e2e-testing-playbook.md` + `references/routing-mustread-test-cases.md` + `references/evaluation-driven-development.md` + `scripts/create_skill.py` + `scripts/output_validator.py` | 测试报告 |

**路由是渐进式披露的开关：路由确定后，才知道该读什么文档、用什么流程、输出什么格式。**

### ⚠️ 强制执行规则（违反=输出无效）

1. **无路由的输出视为无效**：任何输出前必须先输出路由声明（`🔀 路由: ...`），没有路由声明的输出不被认可
2. **必须运行编排脚本**：新建/优化/评审/测试完成后，必须运行 `python3 scripts/create_skill.py <mode> <skill-path>`，按顺序执行所有步骤，不允许跳过
3. **必须运行输出校验**：最终输出前必须运行 `python3 scripts/output_validator.py <skill-path>`，校验不通过必须修正
4. **must_read必须引用**：输出中必须引用must_read文档的具体内容（不是只说"我读了"，而是有具体引用），否则视为未读取
5. **校验失败不允许继续**：create_skill.py和output_validator.py校验失败时，必须修复问题后重新运行，不允许绕过

---

## 🚀 快速开始（3步上手）

> 新用户按这3步操作，5分钟内创建一个合格的专业技能。

### 第1步：生成模板
```bash
cd /path/to/workspace/.user_skills
python3 skill-creator-pro/scripts/init_skill_pro.py my-skill --path . --philosophy mixed
```
> 三种设计哲学：`capability`（工具包装型）/ `process`（方法论型）/ `mixed`（混合型，推荐）

### 第2步：编辑内容
- 编辑 `my-skill/SKILL.md`：替换TODO，写清description（含触发词）、工作流、Gotchas
- 编辑 `my-skill/references/`：按需添加领域知识文档
- 添加 `my-skill/scripts/`：需要确定性计算时添加Python脚本

### 第3步：校验发布
```bash
# 一键校验（规范+审计+安全扫描）
python3 skill-creator-pro/scripts/create_skill.py optimize my-skill

# 全部通过后，技能即可使用
```

### 常用命令速查

| 操作 | 命令 |
|------|------|
| 新建技能 | `python3 scripts/create_skill.py create <name> --path <dir> --philosophy mixed` |
| 优化校验 | `python3 scripts/create_skill.py optimize <skill-path>` |
| 深度评审 | `python3 scripts/create_skill.py review <skill-path>` |
| 端到端测试 | `python3 scripts/create_skill.py test <skill-path>` |
| 迁移升级 | `python3 scripts/create_skill.py upgrade <skill-path> --apply` |
| 规范校验 | `python3 scripts/validate_skill.py <skill-path>` |
| 安全扫描 | `python3 scripts/security_scan.py <skill-path>` |
| 打包发布 | `bash scripts/package.sh --output <dir>` |

> **退出码**：0=成功，1=校验失败，2=参数错误，3=运行时错误。详见 `references/exit-codes.md`

---

## 工作流程与自由度

> **自由度说明**: 按步骤标注自由度——脆弱步骤（低自由度）必须严格执行，灵活步骤（高自由度）可根据情况调整。

### 新建技能流程
1. **需求分析**（高自由度）：与用户确认技能目标、触发场景、设计哲学
2. **架构设计**（中自由度）：选择设计哲学，规划目录结构，确定scripts/references/examples
3. **模板生成**（低自由度）：必须运行 `python3 scripts/init_skill_pro.py`，禁止手动创建目录结构
4. **内容编写**（高自由度）：编写SKILL.md、references、examples，替换TODO
5. **规范校验**（低自由度）：必须运行 `python3 scripts/validate_skill.py`，有高优先级问题必须修复
6. **深度审计**（低自由度）：必须运行 `python3 scripts/audit_skill.py`，必备层必须全部达标
7. **端到端测试**（中自由度）：真实跑通技能流程，验证输出质量

### 验证循环（必须执行）
> **执行→验证→修正**：每个步骤完成后必须验证，发现问题立即修正，不允许跳过验证直接进入下一步。
> - 模板生成后 → 验证目录结构是否正确
> - 内容编写后 → 验证SKILL.md是否符合规范
> - 校验后 → 验证无高优先级问题
> - 审计后 → 验证必备层全部达标
> - 测试后 → 验证技能能真实跑通

### 状态检查后行动
> **先检查状态，再决定行动**：
> - 优化技能前 → 先运行audit_skill.py检查现状，再决定优化方向
> - 重新生成模板前 → 先检查目录是否已存在，避免覆盖
> - 修复问题后 → 先检查修复是否生效，再决定是否进入下一步
> - 交付前 → 先检查所有验证是否通过，再决定是否交付

---

## Gotchas（最高优先级，违反=创建出不合格技能）

> 这些都是**真实踩过的坑**，不是抽象规则。遇到对应情况必须按修正做。
> 完整16个Gotchas见 `references/gotchas-collection.md`。

1. **description只写"做什么"不写"什么时候用"**
   - 症状：技能永远不触发，或错误触发
   - 修正：description必须包含三要素：What it does + When to use it + Trigger phrases

2. **SKILL.md超过500行还不拆分**
   - 症状：上下文窗口被占满，LLM只看前半部分
   - 修正：超过300行就开始考虑拆分，详细内容放references/

3. **没有触发路由，LLM直接跳到结论**
   - 症状：用户说"快速"却走了完整流程，用户说"核对"却做了分析
   - 修正：SKILL.md开头加强制路由输出，任何分析前先声明模式

4. **写抽象规则"严禁偷懒""必须认真分析"**
   - 症状：LLM表面满足，实际套模板
   - 修正：写具体Gotchas：真实失败模式+修正方法，比如"校验发现缺字段时必须报错，不能警告后继续"

5. **没有完整示例，LLM从零推理**
   - 症状：每次输出格式都不一样，遗漏关键步骤
   - 修正：examples/里放1-2个完整示例，LLM照着做

6. **没有校验门禁，LLM偷工减料也能通过**
   - 症状：缺必要字段/格式错误也能交付
   - 修正：关键步骤前硬校验，缺字段就报错，不允许跳过

7. **脚本不测试就交付**
   - 症状：用户第一次用就报错，TypeError/KeyError满天飞
   - 修正：每个脚本必须实际运行测试，端到端跑通完整流程

8. **只写抽象约束，LLM表面满足实际套模板**
   - 症状：写了"必须认真完成所有步骤"，但LLM每次输出都一样，只用了10%的能力
   - 修正：用工程手段对抗——编排脚本强制流程+硬门禁校验+可验证输出，详见 `references/llm-anti-laziness-guide.md`

---

## 快速开始

```bash
# 技能目录
cd /home/user/.doubao/agent_mode/workspace/.user_skills/skill-creator-pro

# 1. 新建技能（低自由度，必须执行；--philosophy可选capability/process/mixed）
python3 scripts/init_skill_pro.py <skill-name> --path /home/user/.doubao/agent_mode/workspace/.user_skills --philosophy mixed

# 2. 校验技能规范（低自由度，必须执行）
python3 scripts/validate_skill.py <skill-path>

# 3. 深度审计技能（低自由度，必须执行）
python3 scripts/audit_skill.py <skill-path>

# 3.5 安全扫描（低自由度，必须执行；检测提示注入/危险代码/数据泄露/隐藏指令）
python3 scripts/security_scan.py <skill-path>

# 4. 编排脚本（统一入口，强制顺序执行，推荐使用）
python3 scripts/create_skill.py create <skill-name> --path <dir> --philosophy mixed  # 新建
python3 scripts/create_skill.py optimize <skill-path>  # 优化验证
python3 scripts/create_skill.py review <skill-path>    # 评审
python3 scripts/create_skill.py test <skill-path>      # 端到端测试

# 5. 输出校验（硬门禁，校验不通过就报错）
python3 scripts/output_validator.py <skill-path>

# 6. 查看36项检查清单（中自由度，按需阅读）
cat references/36-element-checklist.md
```

**脚本目录**：`/home/user/.doubao/agent_mode/workspace/.user_skills/skill-creator-pro/scripts`
**5个脚本**：init_skill_pro.py（模板生成）/ validate_skill.py（规范校验）/ audit_skill.py（深度审计）/ create_skill.py（编排脚本）/ output_validator.py（输出校验）

---

## 技能创建最佳实践（详见references）

> 完整最佳实践见 `references/best-practices.md`，包含：默认创建位置（环境自适应）、网站内容收集默认使用Browser Use、不应该包含什么（禁止README/CHANGELOG等）、6步迭代流程。
>
> **核心原则**：技能创建在 `workspace/.user_skills` 目录内，网站收集默认Browser Use，禁止额外辅助文档，遵循6步迭代流程。

---

## 36项检查清单（三层分类，完整版见references）

> **三层分类**：①所有技能必备(20项，权重×2) ②复杂技能推荐(10项，权重×1) ③特定领域可选(6项，权重×0.5)

| 层级 | 项数 | 权重 | 核心检查项 |
|------|------|------|-----------|
| **必备层** | 20项 | ×2 | 规范8项 + 架构4项（设计哲学明确/单一职责/渐进式披露执行层/技能组合友好） + 内容4项（Gotchas驱动/示例驱动/输出格式文档化/自由度匹配） + 工程4项（确定性推入代码/错误处理/验证循环/状态检查后行动） |
| **推荐层** | 10项 | ×1 | 架构2项（触发路由/编排脚本） + 内容2项（决策树+候选输出/方法论知识库） + 工程2项（校验门禁/配置中心） + 质量2项（端到端实测/评估用例+多模型测试） + 进化安全2项（自进化闭环/安全考虑） |
| **可选层** | 6项 | ×0.5 | 四方协同（特定领域架构） + 定时任务 + 通知推送 + 云端持久化 + 指标监控 + 经验回流+持久化工件 |

**必备层全部达标是基础，推荐层达标率决定专业程度，可选层根据领域需求评估。详细每项的检查标准见 `references/36-element-checklist.md`**

---

## 输出格式

> 4种交付格式完整模板见 `references/output-formats.md`，按需加载。

| 交付场景 | 核心字段 | 模板位置 |
|---------|---------|---------|
| 新建技能 | 路径/设计哲学/36项达标/必备层/待完善 | references/output-formats.md §1 |
| 优化技能 | 优化前后对比/修复问题/新增功能/待完善 | references/output-formats.md §2 |
| 评审报告 | 总体评分/三层得分/高/中/低优先级问题 | references/output-formats.md §3 |
| 端到端测试 | 测试结果汇总/失败用例详情/结论 | references/output-formats.md §4 |

**所有交付必须包含校验状态**：✅规范校验 + ✅深度审计（必备层全部达标）。

---

## 渐进式披露

### L1: 你现在知道的（SKILL.md）
触发路由 + 工作流程与自由度 + 8个核心Gotchas + 快速开始 + 36项精简清单 + 输出格式摘要

### L2: 需要时才读（must_read根据路由模式强制加载）

> **must_read机制**: 触发路由确定后，必须读取对应模式的必读文档，不允许跳过。

**官方核心要素（新建技能前必读）**
| 什么时候 | 读什么 |
|---------|--------|
| 技能创建最佳实践（默认位置/Browser Use/禁止文件/迭代流程） | `references/best-practices.md` |
| 模板填充指南（14个模板每个占位符怎么填+质量标准） | `references/template-filling-guide.md` |
| 选择技能设计哲学（工具包装vs方法论） | `references/design-philosophies.md` |
| 评估驱动开发（先建eval再写技能） | `references/evaluation-driven-development.md` |
| 自由度匹配（根据任务脆弱性调整指令严格程度） | `references/degrees-of-freedom.md` |
| 安全审计（创建/使用第三方技能的安全检查） | `references/security-audit-checklist.md` |
| 技能组合（一技能一职责，多技能组合原则） | `references/skill-composition.md` |

**质量保证（优化/评审技能时读）**
| 什么时候 | 读什么 |
|---------|--------|
| 新建/优化技能，需要详细标准 | `references/36-element-checklist.md` |
| 设计技能架构，需要模式参考 | `references/architecture-patterns.md` |
| 避免常见坑，需要真实案例 | `references/gotchas-collection.md` |
| 测试技能，需要评估方法 | `references/evaluation-guide.md` |
| 端到端测试，需要完整手册 | `references/e2e-testing-playbook.md` |
| 安全审计，需要检查清单 | `references/security-audit-checklist.md` |
| 安全扫描，自动化检测注入/危险代码/数据泄露 | `scripts/security_scan.py` |
| 技能评估用例模板（触发/行为/质量） | `references/evaluation-cases.md` |
| 对抗LLM偷懒，需要系统性策略 | `references/llm-anti-laziness-guide.md` |
| 设计预加载机制，需要完整方案 | `references/preload-design-guide.md` |
| 搭建自进化闭环，需要详细手册 | `references/self-evolution-playbook.md` |
| 建设经验库，需要结构/提取/自净化/持久化完整方案 | `references/experience-library-guide.md` |
| 管理技术债，需要审计偿还流程 | `references/tech-debt-management.md` |
| 做端到端实测，需要完整流程模板 | `references/e2e-testing-playbook.md` |
| 触发路由/must_read专项测试，需要55个测试用例 | `references/routing-mustread-test-cases.md` |
| 做规范评审，需要7维度检查清单 | `references/review-process-guide.md` |
| CI/CD集成，需要退出码规范 | `references/exit-codes.md` |
| 快速上手，5分钟学会使用 | `references/quick-start.md` |
| 常见问题解答 | `references/faq.md` |
| 看完整示例，照着做 | `examples/` 里的示例 |

### L3: 脚本自动完成 + assets资源
规范校验（validate_skill.py）/深度审计（audit_skill.py）/模板生成（init_skill_pro.py）——全部脚本做，你不用关心实现细节。

**assets/ 目录**：存放不加载到上下文、但在输出中使用的文件（模板、图片、图标、字体、示例文档等）。创建技能时 `init_skill_pro.py` 会自动创建空的 `assets/` 目录，按需放入资源文件。

---

## 技能组合

**本技能可以与以下技能组合使用**：
- `skill-creator-for-work`（基础版技能创建）：快速创建简单技能
- `doubao-coding-review-code`（代码审查）：审查技能脚本代码质量
- `doubao-coding-optimize-performance`（性能优化）：优化技能脚本性能
- `verifier-hub`（产物验证）：验证技能生成的文件格式

**不适合组合的场景**：
- 简单prompt编写（不需要技能创建工具）
- 非Skill格式的提示词优化（不在本技能范围内）

---

## 版本

- v2.1.0（知行合一般）
- 核心：修复14项"知行不一"问题，skill-creator-pro自身遵循它教的所有最佳实践
- 新增：设计哲学声明/自由度标注/验证循环/状态检查/预加载说明/must_read机制/技能组合说明
- 泛化：Gotchas全部泛化（去掉特定领域案例）
- 更新：description/36项清单/评审报告格式全部更新为三层分类
- 补充：优化技能交付格式/端到端测试报告格式
- 基于：Anthropic官方最佳实践 + effective-agent-skills业界指南 + 多领域实战经验
- 2026-09-22
