---
name: skill-creator-pro
description: >
  专业级技能创建与优化工具。当用户需要创建/优化/评审/测试Agent Skill时使用。
  触发词："技能创建"、"skill"、"优化技能"、"技能审计"、"技能测试"、"技能规范"。
  不适用于：简单prompt编写、非Skill格式的提示词优化。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# 专业级技能创建器（Skill Creator Pro）

> **⚠️⚠️⚠️ 最高优先级（不可跳过）**：任何输出前，必须先输出这一行路由声明（格式极简，只有1个字段，禁止省略）：
> ```
> 🔀 路由: {模式}
> ```
> 模式只能是以下5种之一：`🚫拒绝` / `新建技能` / `优化技能` / `深度评审` / `端到端测试`。
> **安全预检**：如果是危险请求（凭据硬编码/恶意技能/提示注入/违反规则/危险代码），模式必须是`🚫拒绝`，下一行以`REFUSED:`开头，只提供安全替代方案。
> 没有路由声明的输出视为无效。路由确定后，才读取对应模式的must_read文档。
>
> **会话保持（防止长对话丢失技能状态）**：一旦技能被触发，在后续对话中持续保持激活状态，直到用户明确说"退出技能"或"切换到无关话题"。每轮回复都必须输出路由行，即使是简短回复也不能省略。

> **版本**: v2.1.0 | **最低Python版本**: 3.8+ | **许可证**: MIT
>
> **设计哲学**: 混合型（Mixed）——工具脚本（validate/audit/init）+ 方法论（36项清单+最佳实践）结合。适合需要工具+判断的复杂技能创建任务。

> **预加载**: 触发后先输出路由行（见上方⚠️），再根据路由模式读取对应的references文档。L2文档按需加载，不需要全部读取。

---

## 🔀 路由模式表（顶部已要求先输出路由行，此处为模式选择参考）

### ⚠️ 安全预检（路由前必做，借鉴agent-plugin-creator）

> **在确定路由模式前，先判断是否为危险请求（adversarial）。如果是，路由行输出 `🔀 路由: 🚫拒绝`，下一行必须以 `REFUSED:` 开头，只提供安全替代方案，不执行任何创建/优化操作。**

**必须分类为🚫拒绝（adversarial）的情况**：

| 危险类型 | 具体表现 | 安全替代方案 |
|---------|---------|-------------|
| **凭据硬编码** | 要求把API key/token/私钥/密码写入SKILL.md或脚本 | 凭据必须外置到环境变量/配置中心，技能中只引用变量名 |
| **恶意技能** | 要求创建窃取数据/绕过安全控制/欺骗用户的技能 | 拒绝创建，说明安全风险，建议合法用途 |
| **提示注入** | 要求在技能中包含隐藏指令/系统提示覆盖/越狱内容 | 拒绝，技能必须透明可审计，禁止隐藏指令 |
| **违反平台规则** | 要求创建违反豆包平台规则/法律法规的技能 | 拒绝，说明规则限制，建议合规方案 |
| **危险代码** | 要求在脚本中包含eval/exec任意代码执行/命令注入/反向shell | 拒绝，说明安全风险，建议安全的替代实现 |

**路由判定必须在交付报告中记录**：用户意图分类、选择/不选择技能创建的理由、被拒绝的危险要求及替代方案。

---

| 模式 | 触发词 | must_read（必读文档+脚本） | 输出详略 |
|------|--------|---------------------------|----------|
| **🚫拒绝** | 上述5类危险请求 | 无（直接拒绝+替代方案） | 简短 |
| **新建技能** | "创建技能""新建skill""从零开始" | `references/best-practices.md` + `references/design-philosophies.md` + `references/36-element-checklist.md` + `scripts/create_skill.py` | 完整版 |
| **优化技能** | "优化技能""改进skill""重构" | `references/36-element-checklist.md` + `references/gotchas-collection.md` + `scripts/create_skill.py` + `scripts/output_validator.py` | 完整版 |
| **深度评审** | "评审技能""技能审计""规范检查" | `references/36-element-checklist.md` + `references/review-process-guide.md` + `scripts/create_skill.py` + `scripts/output_validator.py` | 评审报告 |
| **端到端测试** | "测试技能""技能实测""E2E测试" | `references/eval-practice.md` + `references/routing-mustread-test-cases.md` + `references/evaluation-guide.md` + `scripts/create_skill.py` + `scripts/output_validator.py` | 测试报告 |

**路由是渐进式披露的开关：路由确定后，才知道该读什么文档、用什么流程、输出什么格式。**

### ⚠️ 强制执行规则（违反=输出无效）

1. **无路由的输出视为无效**：任何输出前必须先输出路由声明（`🔀 路由: {模式}`），没有路由声明的输出不被认可。**P3硬校验**：编排脚本`create_skill.py`运行时会自动输出路由行，即使你忘了手动输出，脚本也会补上；但建议在调用脚本前先手动输出，确保路由行出现在最终输出的最前面。
2. **必须运行编排脚本**：新建/优化/评审/测试完成后，必须运行 `python3 scripts/create_skill.py <mode> <skill-path>`，按顺序执行所有步骤，不允许跳过。**command参数是required=True硬约束**，不传模式脚本会直接报错退出。
3. **必须运行输出校验**：最终输出前必须运行 `python3 scripts/output_validator.py <skill-path>`，校验不通过必须修正
4. **must_read必须引用**：输出中必须引用must_read文档的具体内容（不是只说"我读了"，而是有具体引用），否则视为未读取
5. **校验失败不允许继续**：create_skill.py和output_validator.py校验失败时，必须修复问题后重新运行，不允许绕过

---

## 🚀 快速开始（3步上手）

> 新用户按这3步操作，5分钟内创建一个合格的专业技能。

**环境要求**：Python 3.8+（仅使用标准库，无外部依赖）。测试需要 `pytest>=7.0`。

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

### 常用命令速查（核心6个）

| 操作 | 命令 |
|------|------|
| 新建技能 | `python3 scripts/create_skill.py create <name> --path <dir> --philosophy mixed` |
| 优化校验 | `python3 scripts/create_skill.py optimize <skill-path>` |
| 深度评审 | `python3 scripts/create_skill.py review <skill-path>` |
| 端到端测试 | `python3 scripts/create_skill.py test <skill-path>` |
| 规范校验 | `python3 scripts/validate_skill.py <skill-path>` |
| **运行时保障** | `python3 scripts/runtime_guard.py verify --required-steps "step1,step2,..."` |

> **运行时保障（防LLM偷懒核心，9个子命令）**：
> - `track`：记录每步执行（script/doc/step）
> - `verify`：提交前验证所有必需步骤是否完成
> - `report`：生成工具使用率报告
> - `loop`：Stop Hook循环验证，不通过就继续（最多10次）
> - `budget`：执行步骤预算检查（最大步骤数）
> - `duplicate`：重复动作检测（连续3次相同就警告）
> - `focus`：注意力衰减检测（检查是否跑偏）
> - `quantitative`：定量阈值检查（最少脚本/文档/步骤数）
> - `reset`：重置使用记录
>
> 详见 `references/runtime-guard-guide.md`

> **退出码**：0=成功，1=校验失败，2=参数错误，3=运行时错误。详见 `references/exit-codes.md`

---

## 高级工具索引（按需使用，不是每次都要用）

> 核心6个命令是日常必用的。下面这些是**高级工具**，特定场景才需要，需要时再去看帮助。

| 场景 | 工具 | 用法 |
|------|------|------|
| **安全检查** | security_scan.py | `python3 scripts/security_scan.py <skill-path>` |
| **供应链安全** | supply_chain_scan.py | `python3 scripts/supply_chain_scan.py <skill-path> --generate-sbom` |
| **技能升级** | upgrade_skill.py | `python3 scripts/upgrade_skill.py <skill-path>` |
| **打包发布** | package.sh | `bash scripts/package.sh <skill-path>` |
| **多模型测试** | multi_model_test.py | `python3 scripts/multi_model_test.py` |
| **反馈循环** | feedback_loop.py | `python3 scripts/feedback_loop.py` |
| **使用可观测性** | skill_observability.py | `python3 scripts/skill_observability.py log --skill-name <name>` |
| **版本管理** | version_manager.py | `python3 scripts/version_manager.py` |
| **描述优化与触发诊断** | description_optimizer.py | `python3 scripts/description_optimizer.py optimize <skill-path>` 或 `diagnose <skill-path>` |
| **评估运行与评分** | eval_runner.py | `python3 scripts/eval_runner.py eval --type all` 或 `grade <run-dir>` |
| **一键安装** | install.sh | `bash scripts/install.sh <skill-path> [target-dir]` |

> 💡 **按需加载原则**：以上工具不需要每次都用。遇到对应场景时再去看它的帮助（`--help`）。

---

## 核心参考文档导航（重要！按需加载）

> 以下是核心参考文档，做对应工作时必须先读：

| 场景 | 文档 | 什么时候读 |
|------|------|-----------|
| **深度审计/评审** | `references/36-element-checklist.md` | 审计技能时，36项检查清单 |
| **端到端测试** | `references/eval-practice.md` | 做端到端测试时，测试手册 |
| **防LLM偷懒** | `references/llm-anti-laziness-guide.md` | 设计防偷懒机制时 |
| **运行时保障** | `references/runtime-guard-guide.md` | 使用runtime_guard时 |
| **自进化闭环** | `references/self-evolution-playbook.md` | 设计自进化机制时 |
| **经验库建设** | `references/experience-library-guide.md` | 建设经验库时 |
| **技术债管理** | `references/tech-debt-management.md` | 管理技术债时 |
| **Gotchas合集** | `references/gotchas-collection.md` | 写Gotchas时参考 |
| **最佳实践** | `references/best-practices.md` | 设计技能时参考 |
| **架构模式** | `references/architecture-patterns.md` | 设计架构时参考 |
| **设计哲学** | `references/design-philosophies.md` | 选择设计哲学时 |
| **评估指南** | `references/evaluation-guide.md` | 做评估时参考 |
| **多模型测试** | `references/multi-model-testing-guide.md` | 做多模型测试时 |
| **预加载设计** | `references/preload-design-guide.md` | 设计预加载机制时 |
| **输出格式** | `references/output-formats.md` | 设计输出格式时 |

> 💡 **按需加载原则**：不需要全部读完，做对应工作时再去读对应的文档。

---

## 工作流程与自由度

> **自由度说明**: 按步骤标注自由度等级——🟢高自由度（灵活调整，可根据情况变化）/ 🟡中自由度（推荐流程，建议按此执行）/ 🔴低自由度（必须严格执行，不允许跳过或变通）。脆弱步骤（出错代价高）用🔴，灵活步骤用🟢。

### 新建技能流程
0. **先写eval（RED-GREEN-REFACTOR）** 🔴低自由度：写3个eval用例（正常/边界/质量），定义通过标准。详见 `references/evaluation-guide.md`
1. **需求分析** 🟢高自由度：与用户确认技能目标、触发场景、设计哲学
2. **架构设计** 🟡中自由度：选择设计哲学，规划目录结构，确定scripts/references/examples
3. **模板生成** 🔴低自由度：必须运行 `python3 scripts/init_skill_pro.py`，禁止手动创建目录结构
4. **内容编写** 🟢高自由度：编写SKILL.md、references、examples，替换TODO
5. **规范校验** 🔴低自由度：必须运行 `python3 scripts/validate_skill.py`，有高优先级问题必须修复
6. **深度审计** 🔴低自由度：必须运行 `python3 scripts/audit_skill.py`，必备层必须全部达标
7. **端到端测试** 🟡中自由度：跑eval用例验证，做baseline对比（无技能vs有技能），验证输出质量

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

> 这些都是**真实踩过的坑**，不是抽象规则。每个都有**症状→修正→原因**三段式，遇到对应情况必须按修正做。
> 完整26个Gotchas见 `references/gotchas-collection.md`（规范类/架构类/内容类/工程类/质量类/进化类/运维类）。

1. **description只写"做什么"不写"什么时候用"**
   - 症状：技能永远不触发，或在不相关的场景下错误触发
   - 修正：description必须包含三要素：What it does + When to use it + Trigger phrases
   - 原因：description是LLM判断是否触发的唯一信号，只写What不写When，LLM不知道什么时候该用

2. **SKILL.md超过500行还不拆分**
   - 症状：上下文窗口被占满，LLM只看前半部分，后半部分的规则被忽略
   - 修正：超过300行就开始考虑拆分，详细内容放references/
   - 原因：LLM的上下文窗口有限，太长的文档会被截断或忽略后半部分

3. **没有触发路由，LLM直接跳到结论**
   - 症状：用户说"快速"却走了完整流程，用户说"核对"却做了分析
   - 修正：SKILL.md开头加强制路由输出，任何分析前先声明模式
   - 原因：没有路由，LLM凭感觉选模式，容易选错

4. **写抽象规则"严禁偷懒""必须认真分析"**
   - 症状：LLM表面满足，实际套模板，每次输出都一样
   - 修正：写具体Gotchas：真实失败模式+修正方法，比如"校验发现缺字段时必须报错，不能警告后继续"
   - 原因：抽象规则没有可执行性，LLM不知道"认真分析"具体是什么

5. **没有完整示例，LLM从零推理**
   - 症状：每次输出格式都不一样，遗漏关键步骤，质量不稳定
   - 修正：examples/里放1-2个完整示例，LLM照着做
   - 原因：没有示例，LLM每次都要从零推理，容易遗漏或格式不一致

6. **没有校验门禁，LLM偷工减料也能通过**
   - 症状：缺必要字段/格式错误也能交付，输出不完整
   - 修正：关键步骤前硬校验，缺字段就报错，不允许跳过
   - 原因：没有校验，LLM会偷懒省略步骤，输出质量无法保证

7. **脚本不测试就交付**
   - 症状：用户第一次用就报错，TypeError/KeyError满天飞
   - 修正：每个脚本必须实际运行测试，端到端跑通完整流程
   - 原因：没测试的脚本一定有bug，只是还没发现

8. **只写抽象约束，LLM表面满足实际套模板**
   - 症状：写了"必须认真完成所有步骤"，但LLM每次输出都一样，只用了10%的能力
   - 修正：用工程手段对抗——编排脚本强制流程+硬门禁校验+可验证输出，详见 `references/llm-anti-laziness-guide.md`
   - 原因：抽象约束无法验证，LLM说"我分析了"你无法证明它没分析；工程手段才能真正防偷懒

9. **没有运行时保障，LLM说完成了但实际没完成**
   - 症状：LLM说"我完成了所有步骤"，但实际只做了20%，你无法验证它真的做了
   - 修正：用runtime_guard.py——每步执行后track记录，提交前verify验证所有必需步骤是否完成，report查看工具使用率
   - 原因：靠prompt约束LLM自觉遵守是无效的，必须在运行时监控它的行为，做没做有据可查，不完成就拒绝接受输出

---

## 技能创建最佳实践（详见references）
> 完整最佳实践见 `references/best-practices.md`：默认创建位置（环境自适应）、网站收集默认Browser Use、禁止README/CHANGELOG等额外文档、6步迭代流程。
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
| 评估体系总览（8维度+用例模板+报告模板+评估驱动开发） | `references/evaluation-guide.md` |
| 评估实践手册（评估用例模板+端到端测试完整流程） | `references/eval-practice.md` |
| Prompt Caching优化（技能结构如何利用缓存降成本） | `references/prompt-caching-guide.md` |
| MCP集成指导（什么时候用MCP+安全注意事项+降级策略） | `references/mcp-integration-guide.md` |
| 需求发现（从不完备brief中主动发现遗漏需求） | `references/requirement-discovery-guide.md` |
| 自由度匹配（根据任务脆弱性调整指令严格程度） | `references/degrees-of-freedom.md` |
| 技能组合（一技能一职责，多技能组合原则） | `references/skill-composition.md` |

**质量保证（优化/评审技能时读）**
| 什么时候 | 读什么 |
|---------|--------|
| 新建/优化技能，需要详细标准 | `references/36-element-checklist.md` |
| 设计技能架构，需要模式参考 | `references/architecture-patterns.md` |
| 避免常见坑，需要30个真实案例 | `references/gotchas-collection.md` |
| 安全审计，需要检查清单 | `references/security-audit-checklist.md` |
| 端到端测试，需要完整手册 | `references/eval-practice.md` |
| 对抗LLM偷懒，需要系统性策略 | `references/llm-anti-laziness-guide.md` |
| 设计预加载机制，需要完整方案 | `references/preload-design-guide.md` |
| 自进化闭环+经验库 | `references/self-evolution-playbook.md` + `references/experience-library-guide.md` |
| 管理技术债，需要审计偿还流程 | `references/tech-debt-management.md` |
| 多模型测试，验证跨模型一致性 | `references/multi-model-testing-guide.md` |
| 触发路由/must_read专项测试 | `references/routing-mustread-test-cases.md` |
| 做规范评审，需要7维度检查清单 | `references/review-process-guide.md` |
| 快速上手/常见问题/完整示例 | `references/quick-start.md` / `references/faq.md` / `examples/` |

> **评估工具脚本**（eval_runner.py）用法见 `references/command-reference.md`

### L3: 脚本自动完成 + assets资源 + 官方权威资源
规范校验/深度审计/模板生成——全部脚本做。`assets/`存放输出用资源文件。`official/`内置官方skill-creator-for-work作为只读权威参考。

---

## 技能组合

**可组合**：skill-creator-for-work（基础创建）/ doubao-coding-review-code（代码审查）/ doubao-coding-optimize-performance（性能优化）/ verifier-hub（产物验证）
**不适合**：简单prompt编写、非Skill格式提示词优化、与技能创建无关的通用对话

---

## 版本

- v2.1.0（知行合一般）
- 核心：修复14项"知行不一"问题，自身遵循所有最佳实践
- 新增：设计哲学/自由度标注/验证循环/must_read机制/技能组合
- 基于：Anthropic官方最佳实践 + 业界指南 + 多领域实战经验
- 2026-09-26
