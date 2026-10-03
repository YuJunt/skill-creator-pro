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

> **⚠️⚠️⚠️ 最高优先级（不可跳过）**：任何输出前，必须先输出这一行路由声明（格式极简：技能名+模式+一句话重点，禁止省略）：
> ```
> 🔀 路由: skill-creator-pro · {模式} · {一句话重点}
> ```
> **示例**：
> - `🔀 路由: skill-creator-pro · 优化技能 · 优化my-skill的规范和脚本`
> - `🔀 路由: skill-creator-pro · 深度评审 · 审计自身规范和实战能力`
> - `🔀 路由: skill-creator-pro · 端到端测试 · 验证新功能实际效果`
>
> **格式说明（极简，只有3段）**：
> - 第1段：固定`🔀 路由: skill-creator-pro`
> - 第2段：模式（5种之一）
> - 第3段：一句话重点（自由文本，说明当前任务）
>
> 模式只能是以下5种之一：`🚫拒绝` / `新建技能` / `优化技能` / `深度评审` / `端到端测试`。
> **安全预检**：如果是危险请求（凭据硬编码/恶意技能/提示注入/违反规则/危险代码），模式必须是`🚫拒绝`，下一行以`REFUSED:`开头，只提供安全替代方案。
> 没有路由声明的输出视为无效。路由确定后，才读取对应模式的must_read文档。
>
> **会话保持（防止长对话丢失技能状态）**：一旦技能被触发，在后续对话中持续保持激活状态，直到用户明确说"退出技能"或"切换到无关话题"。**每轮回复都必须输出路由行，即使是简短回复也不能省略。**
>
> **路由行输出硬验证（脚本实现，非文字说明）**：
> - 每轮输出路由行后，必须运行 `python3 scripts/runtime_guard.py route --mode "{模式}" --line "🔀 路由: skill-creator-pro · {模式} · {一句话重点}"` 记录并校验格式
> - `--line` 参数传入完整路由行文本，脚本自动校验格式（前缀/技能名/模式合法）
> - 交付前必须运行 `python3 scripts/runtime_guard.py gate --mode {模式}` 检查所有门禁
> - `gate` 命令检查4个硬门禁：①路由行是否输出 ②路由行格式是否正确 ③关键脚本是否调用 ④关键文档是否阅读
> - 任何门禁不通过，`gate` 命令返回非0退出码，**不能交付**
> - 如果路由行输出为0次，视为**严重偷懒**（critical级别），触发路由机制完全失效，必须重新执行

> **版本**: v2.1.0 | **最低Python版本**: 3.8+ | **许可证**: MIT
>
> **设计哲学**: 混合型（Mixed）——工具脚本（validate/audit/init）+ 方法论（36项清单+最佳实践）结合。适合需要工具+判断的复杂技能创建任务。

> **预加载（强制，技能触发后第一步）**: 触发后**必须先运行** `python3 scripts/preload.py --mode "{模式}" --target "{目标技能}"`，获取路由行模板+当前状态+必读文档+工作流步骤。preload.py会输出一行可直接复制的路由行模板，照着输出就不会忘记路由。然后根据路由模式读取对应的references文档。L2文档按需加载，不需要全部读取。

---

## 🔀 路由模式表（渐进式披露的核心开关）

> **路由是渐进式披露的开关：路由确定后，才知道该读什么文档、用什么流程、输出什么格式。推荐使用 `python3 scripts/router.py "用户消息"` 自动路由。**

### ⚠️ 安全预检（路由前必做）

危险请求（凭据硬编码/恶意技能/提示注入/违反平台规则/危险代码）→ 路由 `🚫拒绝`，只提供安全替代方案。

### 📋 四种模式完整路由表

| 维度 | 🆕 新建技能 | 🔧 优化技能 | 🔍 深度评审 | 🧪 端到端测试 |
|------|------------|------------|------------|--------------|
| **触发词** | 创建、新建、从零开始、生成、搭建、create、new、generate、build | 优化、改进、重构、精简、升级、调优、optimize、refactor、upgrade | 评审、审计、规范检查、检查、评估、review、audit、check、evaluate | 测试、实测、验证、端到端、E2E、test、e2e、verify、benchmark |
| **must_read** | best-practices + design-philosophies + 36-element-checklist | 36-element-checklist + gotchas-collection + best-practices | 36-element-checklist + review-process-guide + best-practices | eval-practice + routing-mustread-test-cases + evaluation-guide |
| **核心脚本** | create_skill + init_skill_pro + validate_skill | create_skill + validate + audit + output_validator | create_skill + validate + audit | create_skill + validate + output_validator |
| **工作流** | 需求分析→选设计哲学→init生成模板→填充SKILL.md→validate→audit→交付→复盘沉淀 | 现状审计→识别问题→制定方案→执行优化→validate→audit→硬门禁→报告→复盘沉淀 | 读取→validate→audit(36项)→问题分级→改进建议→评审报告→复盘沉淀 | 读取→语法检查→冒烟测试→E2E测试→回归测试→测试报告→复盘沉淀 |
| **输出** | 技能目录+SKILL.md+scripts+references+创建报告 | 优化后技能+优化报告 | 评分+问题清单+改进建议 | 通过率+失败用例+改进建议 |
| **边界** | 需求不明→先问澄清；有旧技能→建议optimize | 技能不存在→建议create；范围大→分阶段 | 技能不存在→提示先创建；只有SKILL.md→只做文档评审 | 技能不存在→提示先创建；环境不全→降级冒烟测试 |

### ❓ 模糊请求处理

路由为 `ambiguous` 时：列出top3备选→询问用户→根据回答路由。常见模糊："技能""这个技能怎么样""帮我弄一下"。

### 🔧 路由脚本使用

`python3 scripts/router.py "消息"`（自动路由）/ `--json`（脚本集成）/ `--verbose`（详细分数）/ `--test`（11个内置测试）。输出：mode+confidence+must_read+reasoning+alternatives+is_dangerous。

### ⚠️ 强制执行规则（违反=输出无效）

1. **无路由的输出视为无效**：任何输出前必须先输出路由声明（`🔀 路由: skill-creator-pro · {模式} · target=...; scope=...; reason=...`）。`create_skill.py`运行时会自动输出路由行并记录到runtime_guard。
2. **必须运行编排脚本**：新建/优化/评审/测试**必须**通过 `python3 scripts/create_skill.py <mode> <skill-path>`，禁止直接调用validate_skill.py/audit_skill.py等单个脚本（会绕过runtime_guard记录）。
3. **must_read必须阅读并记录**：路由确定后，必须阅读对应模式的must_read文档，阅读后运行 `python3 scripts/runtime_guard.py track --step <文档名> --action doc --type doc` 记录。输出中必须引用文档具体内容，否则视为未读取。
4. **交付前必须跑门禁**：交付前必须运行 `python3 scripts/runtime_guard.py gate --mode {模式}`，4项门禁（路由行/格式/关键脚本/关键文档）全部通过才能交付。
5. **校验失败不允许继续**：create_skill.py校验失败时必须修复后重新运行，不允许绕过。

---

## 🚀 快速开始（3步上手）

> 新用户按这3步操作，5分钟内创建合格的专业技能。环境：Python 3.8+（标准库，无外部依赖）。

**第1步：生成模板**：`python3 scripts/init_skill_pro.py my-skill --path . --philosophy mixed`（三种设计哲学：capability工具包装/process方法论/mixed混合型推荐）

**第2步：编辑内容**：编辑 `SKILL.md`（description含触发词+工作流+Gotchas）、按需添加 `references/` 文档、需要确定性计算时添加 `scripts/`。

**第3步：校验发布**：`python3 scripts/create_skill.py optimize my-skill`（一键规范校验+深度审计+安全扫描），全部通过即可使用。

### 常用命令速查（🟢 核心层·必用5个，全部通过create_skill.py入口）

> **⚠️ 强制约束：优化/评审/测试必须通过create_skill.py，禁止直接调用validate_skill.py/audit_skill.py等单个脚本。** create_skill.py会自动按顺序执行所有校验，并自动记录runtime_guard。

| 操作 | 命令 | 说明 |
|------|------|------|
| 新建技能 | `python3 scripts/create_skill.py create <name> --path <dir> --philosophy mixed` | 一键创建+校验 |
| 优化校验 | `python3 scripts/create_skill.py optimize <skill-path>` | **一键完成**规范校验+深度审计+安全扫描+输出校验 |
| 深度评审 | `python3 scripts/create_skill.py review <skill-path>` | 一键评审+36项审计 |
| 端到端测试 | `python3 scripts/create_skill.py test <skill-path>` | 一键测试+冒烟+E2E |
| **交付前门禁** | `python3 scripts/runtime_guard.py gate --mode {模式}` | **必须运行**，检查路由/脚本/文档是否全部完成 |

> 完整命令表（含内部脚本说明/运行时保障9子命令/退出码）见 `references/command-reference.md`；防偷懒机制详解见 `references/anti-laziness-guide.md`。

---

## 🟡 高级层工具索引（按需使用，特定场景才需要）

| 分类 | 工具 |
|------|------|
| **安全** | security_scan.py / supply_chain_scan.py（--generate-sbom） |
| **发布** | package.sh / install.sh / release_audit.py（status/bump） |
| **测试** | multi_model_test.py / eval_runner.py（eval/grade） |
| **优化** | upgrade_skill.py / description_optimizer.py（optimize/diagnose） |
| **进化** | skill_evolution.py（反馈循环+可观测性log） |

> 💡 以上工具不需要每次都用，遇到对应场景时再看`--help`。完整用法见 `references/command-reference.md`。

---

## 🎯 评估驱动开发（EDD）核心理念（最高优先级，先于所有工作流）

> **Anthropic官方skill-creator的核心方法论：先写eval，再写技能。没有eval的技能创建是盲目的。**
>
> **RED-GREEN-REFACTOR循环**：
> 1. **RED（红）**：先写3个eval用例（正常/边界/质量），定义通过标准。此时技能还不存在，eval必然失败。
> 2. **GREEN（绿）**：写技能草稿，让eval用例通过。
> 3. **REFACTOR（重构）**：优化技能结构，保持eval通过。
> 4. **重复**：扩展eval用例，更大规模测试，持续迭代。

### EDD为什么比"先写技能再测试"好？

> 核心优势：**目标清晰**（eval先定义"什么算成功"）→ **质量设计驱动**（每个功能有对应eval，测试是设计不是事后检查）→ **回归保护**（修改即验证）→ **可量化价值**（with-skill vs baseline 对比）。详细对比见 `references/evaluation-guide.md`。

### EDD执行标准（🔴低自由度，必须执行）

**第0步（任何技能创建前）：写eval用例**
- 至少3个eval用例：1个正常场景 + 1个边界场景 + 1个质量场景
- 每个eval用例包含：`prompt`（用户真实输入）+ `expected_behavior`（期望行为列表）+ `assertions`（可验证的断言）
- eval用例保存到技能目录的 `evals/evals.json`
- **没有eval用例，不允许开始写技能**

**第7步（技能创建后）：跑eval验证**
- 运行 `python3 scripts/eval_runner.py eval --type all` 执行所有eval用例
- 做baseline对比：无技能（without_skill）vs 有技能（with_skill），量化技能的价值
- 端到端测试通过率 ≥80% 才能交付
- 每个eval用例的断言必须全部通过

> 完整EDD流程、eval用例JSON格式示例与设计指南见 `references/evaluation-guide.md`

---

## 工作流程与自由度

> **自由度说明**: 按步骤标注自由度等级——🟢高自由度（灵活调整，可根据情况变化）/ 🟡中自由度（推荐流程，建议按此执行）/ 🔴低自由度（必须严格执行，不允许跳过或变通）。脆弱步骤（出错代价高）用🔴，灵活步骤用🟢。

### 新建技能流程
0. **先写eval（EDD·RED阶段）** 🔴低自由度：按上方「评估驱动开发（EDD）核心理念」写3个eval用例（正常/边界/质量），定义通过标准，保存到 `evals/evals.json`。**没有eval用例不允许开始写技能**。详见 `references/evaluation-guide.md`
1. **需求分析** 🟢高自由度：与用户确认技能目标、触发场景、设计哲学
2. **架构设计** 🟡中自由度：选择设计哲学，规划目录结构，确定scripts/references/examples
3. **模板生成** 🔴低自由度：必须运行 `python3 scripts/init_skill_pro.py`，禁止手动创建目录结构
4. **内容编写** 🟢高自由度：编写SKILL.md、references、examples，替换TODO
5. **一键校验发布** 🔴低自由度：必须运行 `python3 scripts/create_skill.py optimize <skill-path>`，一键完成规范校验+深度审计+安全扫描+输出校验，有高优先级问题必须修复
6. **交付前门禁** 🔴低自由度：必须运行 `python3 scripts/runtime_guard.py gate --mode create`，检查路由/脚本/文档是否全部完成，不通过不能交付
7. **端到端测试** 🟡中自由度：跑eval用例验证，做baseline对比（无技能vs有技能），验证输出质量
8. **复盘沉淀（可观测性+人在环改进）** 🟡中自由度：运行 `python3 scripts/skill_evolution.py log <skill-name> <模式> --result success/fail --detail "本轮要点"` 记录结果（低成本可观测性）；改进走**定期复盘**（每月/每10次），`extract-gotchas` 提取潜在Gotchas 后**必须人工确认**再追加进 `references/gotchas-collection.md`。依据业界模式（Anthropic/Warp：base skill + improver skill + 人在环），**改进是定时/作者驱动+人工审批，不是每次任务强制修改**

### 验证循环（必须执行）
> **执行→验证→修正**：每步完成后必须验证，发现问题立即修正，不允许跳过验证直接进入下一步。模板生成后验证目录结构，内容编写后验证规范，校验后验证0高优先级，审计后验证必备层达标，测试后验证真实跑通。

### 每步通过标准（防止表面满足）
> **不是"做了没做"，而是"做得好不好"**。每步有明确通过标准，用`--quality`参数记录，gate命令自动检查。**完整标准见 `references/step-standards.md`**。

核心标准：读文档必须引用具体内容 / 规范校验0高优先级 / 深度审计必备层100% / 输出校验0问题 / 端到端测试通过率≥80%。

### 状态检查后行动
> **先检查状态，再决定行动**：优化前先review检查现状，重新生成模板前检查目录是否存在，修复后检查是否生效，交付前检查所有验证是否通过。

---

## Gotchas（最高优先级，违反=创建出不合格技能）

> 这些都是**真实踩过的坑**，不是抽象规则。完整26个（含原因分析）见 `references/gotchas-collection.md`。

| # | 坑 | 症状 | 修正 |
|---|----|------|------|
| 1 | description只写"做什么"不写"什么时候用" | 技能永远不触发，或在不相关场景错误触发 | description必须含三要素（What做什么+When什么时候用+Trigger触发词） |
| 2 | SKILL.md超过500行还不拆分 | 上下文窗口被占满，LLM只看前半部分，后半规则被忽略 | 超过300行就拆分，详细内容放references/按需加载 |
| 3 | **触发路由失效（最常见的偷懒方式）** | 多轮对话后LLM忘记输出路由行，渐进式披露失效，跳过大部分工作流 | ①简化3段式路由（技能名+模式+一句话重点）②preload.py预加载输出模板③runtime_guard.py硬门禁（输出0次=严重偷懒）④编排脚本自动记录路由行 |
| 4 | 写抽象规则"严禁偷懒" | LLM表面满足实际套模板，每次输出都一样 | 写具体Gotchas（真实失败模式+修正），用工程手段对抗（硬门禁+可验证输出） |
| 5 | 没有完整示例 | 每次输出格式不一致，遗漏关键步骤 | examples/放1-2个完整示例，LLM照着做 |
| 6 | 没有校验门禁 | 缺必要字段/格式错误也能交付 | 关键步骤前硬校验，缺字段就报错，不允许跳过 |
| 7 | 脚本不测试就交付 | 用户第一次用就报错，TypeError/KeyError满天飞 | 每个脚本必须实际运行测试，端到端跑通完整流程 |
| 8 | 没有运行时保障 | LLM说"完成了"实际只做了20%，无法验证 | runtime_guard.py（track记录+verify验证+report报告），不完成拒绝接受输出 |

---

## 技能创建最佳实践（详见references）

> 核心原则：技能创建在 `workspace/.user_skills` 目录内，网站收集默认Browser Use，禁止README/CHANGELOG等额外辅助文档，遵循6步迭代流程。详见 `references/best-practices.md`。

---

## 36项检查清单（三层分类，完整版见references）

> **三层分类**：①所有技能必备(20项，权重×2) ②复杂技能推荐(10项，权重×1) ③特定领域可选(6项，权重×0.5)

| 层级 | 项数 | 权重 | 核心检查项 |
|------|------|------|-----------|
| **必备层** | 20项 | ×2 | 规范8项 + 架构4项（设计哲学明确/单一职责/渐进式披露执行层/技能组合友好） + 内容4项（Gotchas驱动/示例驱动/输出格式文档化/自由度匹配） + 工程4项（确定性推入代码/错误处理/验证循环/状态检查后行动） |
| **推荐层** | 10项 | ×1 | 架构2项（触发路由/编排脚本） + 内容2项（决策树+候选输出/方法论知识库） + 工程2项（校验门禁/配置中心） + 质量2项（端到端实测/评估用例+多模型测试） + 进化安全2项（自进化闭环/安全考虑） |
| **可选层** | 6项 | ×0（不计入质量分） | 平台能力接入清单（职责边界/定时任务/通知推送/云端持久化/指标监控/经验回流），按适用性判定，不需要的记为N/A；**不计入技能质量分** |

**必备层全部达标是基础（硬门禁），推荐层达标率决定专业程度；质量分=必备20×2+推荐10×1=50，可选层按适用性评估（不适用=N/A，且不计入技能质量分）。**
**详细每项检查标准见 `references/36-element-checklist.md`；复杂技能（固定节奏/跨期数据/主动触达）的架构与能力路径见 `references/complex-skill-guide.md`**

---

## 输出格式

> 4种交付格式完整模板见 `references/output-and-templates-guide.md`（§1新建/§2优化/§3评审/§4测试），按需加载。

| 交付场景 | 核心字段 |
|---------|---------|
| 新建技能 | 路径/设计哲学/36项达标/必备层/待完善 |
| 优化技能 | 优化前后对比/修复问题/新增功能/待完善 |
| 评审报告 | 总体评分/三层得分/高/中/低优先级问题 |
| 端到端测试 | 测试结果汇总/失败用例详情/结论 |

**所有交付必须包含校验状态**：✅规范校验 + ✅深度审计（必备层全部达标）。

---

## 渐进式披露

### L1: 你现在知道的（SKILL.md，触发后立即加载，<5000 tokens）
触发路由 + 工作流程与自由度 + 8个核心Gotchas + 快速开始 + 36项精简清单 + 输出格式摘要

### L2: 触发后必读（must_read，根据路由模式强制加载，每模式3-5个文档，<5000 tokens）

> **must_read机制**: 路由确定后，必须读取对应模式的必读文档，不允许跳过。`python3 scripts/router.py "消息"` 会自动输出must_read列表。

| 路由模式 | must_read（必读，按顺序） |
|---------|--------------------------|
| 🆕 新建技能 | 1. `best-practices.md`（官方最佳实践）→ 2. `design-philosophies.md`（设计哲学选择）→ 3. `36-element-checklist.md`（质量标准）→ 4. `output-and-templates-guide.md`（模板填充指南） |
| 🔧 优化技能 | 1. `36-element-checklist.md`（质量标准）→ 2. `gotchas-collection.md`（30个真实坑案例）→ 3. `best-practices.md`（官方最佳实践）→ 4. `tech-debt-management.md`（技术债管理） |
| 🔍 深度评审 | 1. `36-element-checklist.md`（36项审计清单）→ 2. `review-and-security-guide.md`（7维度评审流程）→ 3. `best-practices.md`（官方最佳实践）→ 4. `review-and-security-guide.md`（安全检查清单） |
| 🧪 端到端测试 | 1. `evaluation-cases.md`（评估用例+E2E测试流程）→ 2. `advanced-testing-guide.md`（路由专项测试）→ 3. `evaluation-guide.md`（8维度评估体系）→ 4. `advanced-testing-guide.md`（多模型测试） |

### L3: 按需加载（需要时才读，不强制，按主题分组）

> **L3原则**：遇到对应场景时才读，不需要每次都加载。用 `Glob`/`Grep` 快速定位。**完整索引与检索定位见 `references/index.md`**。

| 主题 | 文档 | 什么时候读 |
|------|------|-----------|
| **实战经验** | `battle-tested-playbooks.md` | 优化/创建技能前，参考3个实战方法论 |
| **专业模板** | `data-analysis-template-guide.md` / `tool-creator-template-guide.md` / `agent-orchestrator-template-guide.md` | 创建数据分析/工具包装/Agent编排类技能时 |
| **架构设计** | `architecture-patterns.md` | 设计技能架构，需要模式参考时 |
| **复杂技能** | `complex-skill-guide.md` | 创建/优化持续运行型技能（定时/存储/推送/经验闭环）时 |
| **防LLM偷懒** | `anti-laziness-guide.md` | 技能需要防偷懒机制时（track/verify/gate/loop等9个子命令） |
| **预加载设计** | `performance-optimization-guide.md` | 设计预加载机制或优化结构降低成本时 |
| **自进化闭环** | `self-evolution-guide.md` | 技能需要经验库和自进化时 |
| **MCP集成** | `mcp-integration-guide.md` | 技能需要MCP集成时 |
| **需求发现** | `requirement-discovery-guide.md` | 用户需求不明确，需要主动发现时 |
| **自由度匹配** | `degrees-of-freedom.md` | 根据任务脆弱性调整指令严格程度时 |
| **技能组合** | `skill-composition.md` | 多技能组合，一技能一职责时 |
| **快速上手/FAQ** | `quick-start.md` | 新用户快速上手或查常见问题时 |
| **命令参考/退出码** | `command-reference.md` | 需要查脚本详细用法或退出码含义时 |

### L4: 脚本自动完成 + assets资源 + 官方权威资源
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
