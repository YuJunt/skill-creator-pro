#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-creator-pro 模板库

包含所有技能模板字符串，与init_skill_pro.py逻辑分离。
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业版技能模板生成脚本（Skill Initializer Pro）

基于三层分类36要素最佳实践，生成通用专业级技能模板。
支持三种设计哲学：capability（工具包装型）/ process（方法论型）/ mixed（混合型）。

用法：
  python3 init_skill_pro.py <skill-name> --path <output-dir> --philosophy mixed
  python3 init_skill_pro.py my-skill --path /path/to/workspace/.user_skills
"""
import argparse
import os
import re
import sys


# ============================================================
# Mixed 模式模板（混合型）
# 特点：完整SKILL.md + 编排脚本 + 校验脚本 + 核心工具脚本 + references + examples
# ============================================================

SKILL_MD_MIXED_TEMPLATE = '''---
name: {skill_name}
description: >
  {skill_description}
  触发词："{trigger_words}"。
  不适用于：{not_for}。
---

<!--
模板填充指南（创建技能后请删除此注释）：
- name: 技能名称，小写+连字符，与目录名一致
- description: 三要素（What做什么+When什么时候用+Differentiator区别），包含触发词，50-200字
- trigger_words: 具体触发词列表，用逗号分隔
- not_for: 明确说明不适用的场景（避免误触发）
- skill_title: 中文标题
完整填充指南见 skill-creator-pro/references/template-filling-guide.md
-->

# {skill_title}

> **设计哲学**: 混合型（Mixed）——工具脚本（确定性操作）+ 方法论（工作流+检查清单）结合。适合需要工具+判断的复杂任务。

> **预加载**: 本技能触发后，先执行触发路由（见下方），再根据路由模式读取对应的references文档。

---

## 🔀 触发路由（不可跳过，任何输出前必须先输出这一行）

**格式固定：**
```
🔀 路由: {{模式}}｜任务: {{简述}}｜管道: {{几段}}｜原因: {{一句话}}
```

**模式路由表：**

| 模式 | 触发词 | 管道 | 必读文档 | 输出详略 |
|------|--------|------|----------|----------|
| **完整模式** | "完整""详细""全面""深度" | 完整工作流 | references/best-practices.md | 完整版 |
| **快速模式** | "快速""简单""直接""简要" | 简化流程 | 无 | 极简版 |
| **单步执行** | "只做XX""仅XX""第一步" | 单一步骤 | 对应步骤文档 | 单步结果 |

**路由是渐进式披露的开关：路由确定后，才知道该读什么文档、用什么流程。**

### ⚠️ 强制执行规则

1. **无路由的输出视为无效**：任何输出前必须先输出路由声明
2. **必须运行编排脚本**：完整模式必须运行 `python3 scripts/orchestrator.py run`，按顺序执行所有阶段
3. **必须运行输出校验**：最终输出前必须运行 `python3 scripts/validator.py --input <结果文件>`
4. **校验失败不允许继续**：校验失败时必须修复问题后重新运行，不允许绕过

---

## 工作流程（必须按顺序执行）

### Step 1: 需求确认（高自由度）
- **做什么**: 确认任务目标、输入输出、约束条件
- **检查清单**:
  - [ ] 任务目标明确
  - [ ] 输入数据/文件已就绪
  - [ ] 输出格式已确认
  - [ ] 约束条件（时间/预算/质量）已明确
- **通过标准**: 能用一句话清晰描述任务目标

### Step 2: 方案设计（中自由度）
- **做什么**: 选择方法、规划步骤、确定工具
- **检查清单**:
  - [ ] 方法选择有依据（参考references/best-practices.md）
  - [ ] 步骤分解合理（每步有明确输入输出）
  - [ ] 工具选择正确（脚本/手动/混合）
- **通过标准**: 方案文档完整，包含方法/步骤/工具

### Step 3: 执行（低自由度，必须用脚本）
- **做什么**: 运行编排脚本，按方案执行
- **命令**: `python3 scripts/orchestrator.py run --plan <方案文件>`
- **检查清单**:
  - [ ] 编排脚本运行成功
  - [ ] 每个阶段输出符合预期
  - [ ] 无错误或异常
- **通过标准**: 编排脚本输出 `success: true`

### Step 4: 校验（低自由度，必须用脚本）
- **做什么**: 运行校验脚本，验证输出质量
- **命令**: `python3 scripts/validator.py --input <结果文件>`
- **检查清单**:
  - [ ] 校验脚本运行成功
  - [ ] 无必须修复的问题
  - [ ] 警告项已评估
- **通过标准**: 校验输出 `0 个必须修复的问题`

### Step 5: 交付（高自由度）
- **做什么**: 整理输出、撰写说明、交付结果
- **检查清单**:
  - [ ] 输出格式符合模板
  - [ ] 包含必要的说明和风险提示
  - [ ] 文件命名规范
- **通过标准**: 用户能直接使用交付结果

---

## 状态检查后行动（必须遵守）

> **先检查状态，再决定行动**，防止重复执行/跳过步骤/状态混乱。

| 行动前 | 必须检查 | 检查方法 |
|--------|---------|---------|
| 重新执行前 | 当前状态是否为idle/done | `python3 scripts/orchestrator.py status` |
| 继续执行前 | 当前状态是否为对应阶段 | 查看state.json或orchestrator.py status |
| 修复后重试 | 修复是否生效 | 重新运行校验，确认问题已解决 |
| 交付前 | 所有验证是否通过 | 确认validator.py 0个必须修复问题 |
| 重置前 | 是否真的需要重置 | 确认当前状态异常，无法继续 |

**禁止**: 不检查状态直接执行、跳过状态检查、状态异常时继续执行。

---

## 工程原则

### 确定性推入代码
- 能脚本化的就脚本化，不让LLM凭感觉做确定性计算
- 校验、转换、统计等操作必须用脚本
- LLM只做判断和决策，不做确定性计算

### 错误处理
- 所有脚本必须有try-except，不静默失败
- 错误信息必须明确指出问题和修复建议
- 有降级机制：主路径失败时，有备选方案
- SKILL.md中说明常见错误和处理方法

---

## Gotchas（最高优先级，违反=输出错误结果）

> 这些都是**真实踩过的坑**，不是抽象规则。遇到对应情况必须按修正做。

### 流程相关

1. **跳过触发路由直接开始执行**
   - 症状：用户说"快速"却走了完整流程，用户说"只做第一步"却做了全部
   - 修正：任何输出前必须先输出路由声明，路由确定后才开始执行

2. **跳过编排脚本手动执行**
   - 症状：不运行orchestrator.py，自己手动执行步骤，遗漏关键环节
   - 修正：完整模式必须运行编排脚本，不允许手动执行

3. **校验失败后绕过继续**
   - 症状：validator.py报错，但说"问题不大"继续交付
   - 修正：校验失败必须修复，不允许绕过；必须修复的问题=交付阻断

### 质量相关

4. **输出格式不统一**
   - 症状：每次输出格式都不一样，遗漏关键字段
   - 修正：严格按照"输出格式"模板输出，不允许自由发挥

5. **没有风险提示**
   - 症状：只说结果好，不说局限性和风险
   - 修正：每次交付必须包含风险提示和局限性说明

6. **引用文档但不说明具体章节**
   - 症状：说"参考了best-practices.md"但不说具体哪一章
   - 修正：引用文档必须指定具体章节或页码，不允许笼统引用

### 工程相关

7. **脚本不测试就交付**
   - 症状：写了脚本但没运行过，用户第一次用就报错
   - 修正：每个脚本必须实际运行测试，端到端跑通完整流程

8. **硬编码路径或凭据**
   - 症状：脚本里写死了本地路径或API key，换环境就失效
   - 修正：路径用相对路径或环境变量，凭据用环境变量或配置文件

---

## 快速开始

```bash
cd {scripts_path}

# 1. 查看编排脚本帮助
python3 orchestrator.py --help

# 2. 运行完整流程
python3 orchestrator.py run --input <输入文件> --output <输出文件>

# 3. 校验输出
python3 validator.py --input <输出文件>

# 4. 查看核心工具帮助
python3 main.py --help
```

**脚本目录**：`{scripts_path}`
**3个脚本**：orchestrator.py（编排）/ validator.py（校验）/ main.py（核心工具）

---

## 输出格式

```
## {skill_title}结果

**状态**: ✅成功 / ❌失败
**任务**: 一句话描述任务目标
**方法**: 简述使用的方法和工具

---

**核心输出**:
<主要结果，按格式要求呈现>

**关键发现**:
- 发现1
- 发现2
- 发现3

**风险提示**: 一句话说明局限性和风险
**后续建议**: 一句话说明下一步可以做什么

✅ 已通过校验（validator.py 0个必须修复问题）
```

---

## 渐进式披露

### L1: 你现在知道的（SKILL.md）
触发路由 + 工作流程 + Gotchas + 快速开始 + 输出格式

### L2: 需要时才读
| 什么时候 | 读什么 |
|---------|--------|
| 需要最佳实践和方法论 | `references/best-practices.md` |
| 验证技能质量（评估用例） | `references/evaluation-cases.md` |
| 看完整使用示例 | `examples/example-usage.md` |
| 需要输出资源模板 | `assets/` 目录 |

### L3: 脚本自动完成
编排执行/输出校验/核心工具——全部脚本做，你不用关心实现细节。

**assets/ 目录**：存放不加载到上下文、但在输出中使用的文件（模板、图片、图标、字体、示例文档等）。

---

## 版本

- v1.0.0（Mixed模式）
- 基于：skill-creator-pro 通用专业模板
- 设计哲学：混合型（工具脚本+方法论）
- {date}
'''


# ============================================================
# Capability 模式模板（工具包装型）
# 特点：简洁SKILL.md + 核心工具脚本，逻辑活在代码里
# ============================================================

SKILL_MD_CAPABILITY_TEMPLATE = '''---
name: {skill_name}
description: >
  {skill_description}
  触发词："{trigger_words}"。
  不适用于：{not_for}。
---

<!--
模板填充指南（创建技能后请删除此注释）：
- name: 技能名称，小写+连字符，与目录名一致
- description: 三要素（What做什么+When什么时候用+Differentiator区别），包含触发词，50-200字
- trigger_words: 具体触发词列表，用逗号分隔
- not_for: 明确说明不适用的场景（避免误触发）
- skill_title: 中文标题
完整填充指南见 skill-creator-pro/references/template-filling-guide.md
-->

# {skill_title}

> **设计哲学**: Capability（工具包装型）——逻辑活在代码里，SKILL.md教agent怎么调用脚本。适合确定性操作、工具封装类任务。

---

## 🔀 触发路由（不可跳过，任何输出前必须先输出这一行）

> 任何操作前，先输出路由声明，防止跳步/错模式。

🔀 路由: 工具调用｜任务: {{简述}}｜命令: {{命令名}}｜原因: {{一句话}}

### 路由模式

| 用户说什么 | 路由模式 | 怎么做 |
|-----------|---------|--------|
| "执行/运行/处理/转换" | 工具调用 | 查看命令列表→选择命令→检查输入→执行→校验输出 |
| "帮助/怎么用/用法" | 帮助查询 | 读快速开始+命令列表，输出用法说明 |
| "出错了/报错/失败" | 错误排查 | 读Gotchas+错误处理→定位问题→修复→重试 |

### ⚠️ 强制执行规则
1. 必须先输出路由声明，再执行任何操作
2. 必须先检查输入文件是否存在，再执行命令
3. 必须校验输出文件非空，再交付
4. 禁止：不检查输入直接执行、输出为空就交付、跳过路由声明

---

## 快速开始

```bash
cd {scripts_path}

# 查看帮助
python3 main.py --help

# 执行核心功能
python3 main.py --input <输入文件> --output <输出文件>
```

**脚本目录**：`{scripts_path}`

---

## 命令列表

### 1. 【命令1名称】
- **用法**: `python3 main.py command1 --param <值>`
- **参数**:
  - `--param`: 【参数说明】（必填）
  - `--option`: 【选项说明】（可选，默认值）
- **输出**: 【输出格式说明】
- **错误处理**:
  - 文件不存在 → 报错"输入文件不存在"
  - 参数错误 → 报错"参数格式错误"

### 2. 【命令2名称】
- **用法**: `python3 main.py command2 --input <输入>`
- **参数**: 【参数说明】
- **输出**: 【输出说明】

---

## 状态检查后行动（必须遵守）

> **先检查状态，再决定行动**，防止重复执行/参数错误。

| 行动前 | 必须检查 | 检查方法 |
|--------|---------|---------|
| 执行命令前 | 输入文件是否存在 | `ls <输入文件>` 或脚本自动校验 |
| 重复执行前 | 输出文件是否已存在 | 确认是否需要覆盖或备份 |
| 修复后重试 | 修复是否生效 | 重新运行命令，确认错误已解决 |
| 交付前 | 输出文件是否生成且非空 | 检查文件大小和内容 |

**禁止**: 不检查输入直接执行、覆盖已有文件不提示、输出为空就交付。

---

## 错误处理

- 所有脚本必须有try-except，不静默失败
- 错误信息必须明确指出问题和修复建议
- 常见错误在Gotchas中说明
- 输入校验：文件不存在/格式错误/参数缺失必须明确报错
- 退出码：成功返回0，失败返回非0

---

## Gotchas（常见坑）

1. **【坑1名称】**
   - 症状：【具体表现】
   - 修正：【具体做法】

2. **【坑2名称】**
   - 症状：【具体表现】
   - 修正：【具体做法】

3. **【坑3名称】**
   - 症状：【具体表现】
   - 修正：【具体做法】

---

## 输出格式

```
## {skill_title}结果

**状态**: ✅成功 / ❌失败
**输出文件**: <路径>
**摘要**: 一句话总结
```

---

## 渐进式披露

- **L1**: frontmatter（始终加载）
- **L2**: 本文件（触发后加载，命令说明+Gotchas）
- **L3**: scripts/（执行时调用，不需要读入上下文）

### 什么时候读什么文件

| 场景 | 读什么 |
|------|--------|
| 不知道怎么用 | 先读「快速开始」和「命令列表」 |
| 遇到错误 | 读「Gotchas」和「错误处理」 |
| 需要完整示例 | 读 `examples/example-usage.md` |
| 验证技能质量（评估用例） | 读 `references/evaluation-cases.md` |
| 需要输出资源 | 查看 `assets/` 目录 |

**examples/**：完整使用示例，照着做。
**assets/**：输出资源文件（模板、图片等），不加载到上下文。

---

## 验证循环（必须执行）

> **执行→验证→修正**：每个命令执行后必须验证，发现问题立即修正，不允许执行完就完事。

| 步骤 | 验证内容 | 验证方法 |
|------|---------|---------|
| 执行命令后 | 命令是否成功（退出码0） | 检查退出码和输出 |
| 生成文件后 | 文件是否存在且非空 | `ls -la <文件>` 检查大小 |
| 输出结果后 | 结果是否符合预期 | 对比输入输出，检查关键字段 |
| 发现问题后 | 修复是否生效 | 重新执行命令，确认错误已解决 |

**禁止**: 不验证就交付、验证不通过就继续、发现问题不修复。

---

## 版本

- v1.0.0（Capability模式）
- 基于：skill-creator-pro 通用专业模板
- 设计哲学：工具包装型
- {date}
'''


# ============================================================
# Process 模式模板（方法论型）
# 特点：完整SKILL.md流程/checklist + references方法论文档，逻辑活在prompt里
# ============================================================

SKILL_MD_PROCESS_TEMPLATE = '''---
name: {skill_name}
description: >
  {skill_description}
  触发词："{trigger_words}"。
  不适用于：{not_for}。
---

<!--
模板填充指南（创建技能后请删除此注释）：
- name: 技能名称，小写+连字符，与目录名一致
- description: 三要素（What做什么+When什么时候用+Differentiator区别），包含触发词，50-200字
- trigger_words: 具体触发词列表，用逗号分隔
- not_for: 明确说明不适用的场景（避免误触发）
- skill_title: 中文标题
完整填充指南见 skill-creator-pro/references/template-filling-guide.md
-->

# {skill_title}

> **设计哲学**: Process（方法论型）——逻辑活在prompt里，SKILL.md编码工作流和checklist。适合需要判断、分析、决策的复杂任务。

---

## 🔀 触发路由（不可跳过，任何输出前必须先输出这一行）

**格式固定：**
```
🔀 路由: {{模式}}｜任务: {{简述}}｜管道: {{几段}}｜原因: {{一句话}}
```

**模式路由表：**

| 模式 | 触发词 | 管道 | 必读文档 | 输出详略 |
|------|--------|------|----------|----------|
| **完整模式** | "完整""详细""全面""深度" | 完整工作流 | references/workflow-guide.md | 完整版 |
| **快速模式** | "快速""简单""直接""简要" | 简化流程 | 无 | 极简版 |
| **单步执行** | "只做XX""仅XX""第一步" | 单一步骤 | 对应步骤文档 | 单步结果 |

---

## 工作流程（必须按顺序执行）

> **编排脚本强制顺序**：完整模式必须运行 `scripts/orchestrator.py`，按阶段顺序执行，防止跳步。快速模式/单步执行可跳过编排脚本，直接按对应步骤执行。

```bash
# 查看编排脚本帮助
python3 scripts/orchestrator.py --help

# 完整执行（init→execute→validate→review）
python3 scripts/orchestrator.py run --input <输入文件> --output <输出文件>

# 查看当前状态
python3 scripts/orchestrator.py status

# 重置状态（重新执行前）
python3 scripts/orchestrator.py reset
```

**阶段对应关系**：orchestrator.py的init→Step 1，execute→Step 2-3，validate→Step 4，review→交付。

### Step 1: 【步骤1名称】（高自由度）
- **做什么**: 【具体说明】
- **检查清单**:
  - [ ] 【检查项1】
  - [ ] 【检查项2】
- **必读**: references/workflow-guide.md（第X章）
- **通过标准**: 【明确的完成标准】

### Step 2: 【步骤2名称】（中自由度）
- **做什么**: 【具体说明】
- **检查清单**:
  - [ ] 【检查项1】
  - [ ] 【检查项2】
- **必读**: references/checklist.md（第X节）
- **通过标准**: 【明确的完成标准】

### Step 3: 【步骤3名称】（低自由度）
- **做什么**: 【具体说明】
- **检查清单**:
  - [ ] 【检查项1】
- **通过标准**: 【明确的完成标准】

### Step 4: 验证与修正（必须执行）
- **做什么**: 验证输出质量，发现问题则修正
- **检查清单**:
  - [ ] 输出是否符合格式模板？
  - [ ] 所有检查项是否都完成？
  - [ ] 有没有遗漏的步骤？
  - [ ] 风险提示是否包含？
- **不通过则回到对应步骤修正**

---

## 状态检查后行动（必须遵守）

> **先检查状态，再决定行动**，防止重复执行/跳过步骤/状态混乱。

| 行动前 | 必须检查 | 检查方法 |
|--------|---------|---------|
| 重新执行前 | 上一步是否已完成 | `python3 scripts/orchestrator.py status` 查看当前阶段 |
| 继续执行前 | 当前步骤的前置条件是否满足 | 确认输入数据/文件已就绪 |
| 修复后重试 | 修复是否生效 | 重新验证，确认问题已解决 |
| 交付前 | 所有验证是否通过 | 确认Step 4检查清单全部完成 + orchestrator.py状态为done |

**禁止**: 不检查状态直接执行、跳过验证、验证不通过就交付。

---

## 工程原则

### 确定性推入代码
- 能脚本化的就脚本化，不让LLM凭感觉做确定性计算
- 校验、转换、统计等操作建议用脚本
- 本技能提供 `scripts/orchestrator.py` 用于工作流编排（强制顺序+状态管理）
- 本技能提供 `scripts/validator.py` 用于输出格式校验
- 如果没有脚本，必须在检查清单中明确验证方法
- LLM只做判断和决策，不做确定性计算

### 校验脚本用法
```bash
# 校验输出文件
python3 scripts/validator.py --input <结果文件>

# JSON格式输出
python3 scripts/validator.py --input <结果文件> --json
```
- 校验不通过（退出码非0）= 交付阻断，必须修复
- 必须修复的问题：缺少必填字段（状态/任务/核心输出）
- 警告项：建议包含风险提示/后续建议

### 错误处理
- 每个步骤必须说明常见错误和处理方法
- 错误信息必须明确指出问题和修复建议
- 有降级机制：主路径失败时，有备选方案
- 不静默失败：遇到错误必须明确告知用户

---

## Gotchas（最高优先级，违反=输出错误结果）

### 流程相关

1. **跳过触发路由直接开始执行**
   - 症状：用户说"快速"却走了完整流程
   - 修正：任何输出前必须先输出路由声明

2. **跳步执行**
   - 症状：跳过Step 2直接到Step 3，遗漏关键环节
   - 修正：必须按顺序执行，每步完成后验证再进入下一步

3. **验证环节走过场**
   - 症状：Step 4只说"已验证"但实际没检查
   - 修正：Step 4必须逐项检查，发现问题必须回到对应步骤修正

### 质量相关

4. **输出格式不统一**
   - 症状：每次输出格式都不一样，遗漏关键字段
   - 修正：严格按照"输出格式"模板输出

5. **没有风险提示**
   - 症状：只说结果好，不说局限性
   - 修正：每次交付必须包含风险提示和局限性说明

---

## 输出格式

```
## {skill_title}结果

**状态**: ✅成功 / ❌失败
**任务**: 一句话描述任务目标
**方法**: 简述使用的方法

---

**核心输出**:
<主要结果>

**关键发现**:
- 发现1
- 发现2

**风险提示**: 一句话说明局限性
**后续建议**: 一句话说明下一步

✅ 已通过验证（Step 4逐项检查完成）
```

---

## 渐进式披露

### L1: 你现在知道的（SKILL.md）
触发路由 + 工作流程 + Gotchas + 输出格式

### L2: 需要时才读
| 什么时候 | 读什么 |
|---------|--------|
| 需要详细工作流指导 | `references/workflow-guide.md` |
| 需要检查清单模板 | `references/checklist.md` |
| 验证技能质量（评估用例） | `references/evaluation-cases.md` |
| 看完整工作流示例 | `examples/example-workflow.md` |

### L3: 工具和资源
- **scripts/orchestrator.py**：工作流编排脚本（强制顺序+状态管理），完整模式必须运行
- **scripts/validator.py**：输出校验脚本（硬门禁），交付前必须运行
- **examples/**：完整工作流示例，照着做
- **assets/**：输出资源文件，不加载到上下文

---

## 版本

- v1.0.0（Process模式）
- 基于：skill-creator-pro 通用专业模板
- 设计哲学：方法论型
- {date}
'''


# ============================================================
# 通用脚本模板
# ============================================================

ORCHESTRATOR_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{skill_title} 编排脚本（Orchestrator）

多阶段管道：init → execute → validate → review
强制顺序执行，状态管理，防止跳步。

用法：
  python3 orchestrator.py run --input <输入文件> --output <输出文件>
  python3 orchestrator.py status
  python3 orchestrator.py reset
"""
import argparse
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
SKILL_NAME = os.path.basename(SKILL_DIR)
DATA_DIR = os.path.expanduser(f"~/.{SKILL_NAME}_state")
STATE_FILE = os.path.join(DATA_DIR, "state.json")

# 管道阶段定义（通用多阶段，不是特定领域的三段式）
PIPELINE_STAGES = [
    {"id": "init", "name": "初始化", "description": "加载配置、校验输入、准备环境"},
    {"id": "execute", "name": "执行", "description": "按方案执行核心任务"},
    {"id": "validate", "name": "校验", "description": "验证输出质量，检查必须修复的问题"},
    {"id": "review", "name": "复盘", "description": "总结经验、记录结果、准备交付"},
]


def load_state():
    """加载运行状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"stage": "idle", "history": []}


def save_state(state):
    """保存运行状态"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def cmd_run(args):
    """运行完整管道"""
    state = load_state()
    if state.get("stage") not in ("idle", "done"):
        print(json.dumps({
            "success": False,
            "error": f"当前状态为{state.get('stage')}，请先reset或等待完成"
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    # 初始化
    state["stage"] = "init"
    state["start_time"] = datetime.now().isoformat()
    state["input"] = args.input
    state["output"] = args.output
    save_state(state)

    # TODO: 实现各阶段逻辑
    # init阶段：校验输入文件存在、加载配置
    # execute阶段：调用main.py执行核心任务
    # validate阶段：调用validator.py校验输出
    # review阶段：总结经验、记录结果

    result = {
        "success": True,
        "stage": "done",
        "pipeline": [s["id"] for s in PIPELINE_STAGES],
        "input": args.input,
        "output": args.output,
        "message": "管道框架已就绪，请实现各阶段逻辑",
        "mandatory_steps": [
            "路由模式声明",
            "需求确认",
            "方案设计",
            "执行（编排脚本）",
            "校验（validator.py）",
            "交付（输出格式+风险提示）",
        ],
        "must_read": [
            "references/best-practices.md（最佳实践）",
        ],
    }

    state["stage"] = "done"
    state["end_time"] = datetime.now().isoformat()
    state["result"] = result
    save_state(state)

    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_status(args):
    """查看当前状态"""
    state = load_state()
    print(json.dumps({
        "stage": state.get("stage", "idle"),
        "start_time": state.get("start_time"),
        "end_time": state.get("end_time"),
        "input": state.get("input"),
        "output": state.get("output"),
    }, ensure_ascii=False, indent=2))


def cmd_reset(args):
    """重置状态"""
    state = load_state()
    state["stage"] = "idle"
    state.pop("start_time", None)
    state.pop("end_time", None)
    state.pop("input", None)
    state.pop("output", None)
    state.pop("result", None)
    save_state(state)
    print(json.dumps({"success": True, "message": "状态已重置"}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="{skill_title} 编排脚本")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="运行完整管道")
    p_run.add_argument("--input", required=True, help="输入文件路径")
    p_run.add_argument("--output", required=True, help="输出文件路径")
    p_run.set_defaults(func=cmd_run)

    p_status = sub.add_parser("status", help="查看当前状态")
    p_status.set_defaults(func=cmd_status)

    p_reset = sub.add_parser("reset", help="重置状态")
    p_reset.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
'''


VALIDATOR_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{skill_title} 输出校验脚本（Validator）

通用输出校验：检查完整性、规范性、一致性。
硬门禁：必须修复的问题=交付阻断。

用法：
  python3 validator.py --input <结果文件>
  python3 validator.py --input <结果文件> --json
"""
import argparse
import json
import os
import sys


def validate_file(filepath):
    """校验输出文件（通用校验，不是特定领域的字段校验）"""
    issues = []
    warnings = []

    # 检查1：文件存在
    if not os.path.exists(filepath):
        issues.append({"level": "error", "field": "file_exists", "message": f"文件不存在: {filepath}"})
        return issues, warnings

    # 检查2：文件非空
    if os.path.getsize(filepath) == 0:
        issues.append({"level": "error", "field": "file_empty", "message": "文件为空"})
        return issues, warnings

    # 检查3：读取文件内容
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        issues.append({"level": "error", "field": "file_read", "message": f"文件读取失败: {e}"})
        return issues, warnings

    # 检查4：完整性（通用关键字段，不是特定领域的字段）
    mandatory_fields = ["状态", "任务", "核心输出"]
    for field in mandatory_fields:
        if field not in content:
            issues.append({
                "level": "error",
                "field": f"missing_{field}",
                "message": f"缺少必填字段: {field}"
            })

    # 检查5：风险提示（质量要求）
    if "风险提示" not in content and "风险" not in content:
        warnings.append({
            "level": "warning",
            "field": "missing_risk",
            "message": "建议包含风险提示和局限性说明"
        })

    # 检查6：格式规范性（Markdown标题）
    if not content.startswith("#") and not content.startswith("```"):
        warnings.append({
            "level": "warning",
            "field": "format",
            "message": "建议使用Markdown格式，以标题开头"
        })

    return issues, warnings


def main():
    parser = argparse.ArgumentParser(description="{skill_title} 输出校验")
    parser.add_argument("--input", required=True, help="待校验的结果文件")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    args = parser.parse_args()

    issues, warnings = validate_file(args.input)

    result = {
        "success": len(issues) == 0,
        "input": args.input,
        "errors": len(issues),
        "warnings": len(warnings),
        "issues": issues,
        "warnings_list": warnings,
        "message": "校验通过" if len(issues) == 0 else f"发现{len(issues)}个必须修复的问题",
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print(f"校验结果: {'✅ 通过' if result['success'] else '❌ 失败'}")
        print(f"必须修复的问题: {result['errors']}")
        print(f"警告（建议修复）: {result['warnings']}")
        print("=" * 60)
        if issues:
            print("\\n必须修复的问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. [{issue['field']}] {issue['message']}")
        if warnings:
            print("\\n警告（建议修复）:")
            for i, w in enumerate(warnings, 1):
                print(f"  {i}. [{w['field']}] {w['message']}")

    # 有必须修复的问题时，退出码为1
    sys.exit(0 if len(issues) == 0 else 1)


if __name__ == "__main__":
    main()
'''


# ============================================================
# 通用文档模板
# ============================================================

BEST_PRACTICES_TEMPLATE = '''# {skill_title} 最佳实践

> 本文档包含{skill_title}的最佳实践和方法论，按需加载。

## 一、核心原则

### 1.1 确定性优先
- 能脚本化的就脚本化，不要让LLM凭感觉做确定性计算
- 校验、转换、统计等操作必须用脚本
- LLM只做判断和决策，不做确定性计算

### 1.2 渐进式披露
- L1: frontmatter（始终加载）
- L2: SKILL.md（触发后加载）
- L3: references/scripts（按需加载）
- 大文件必须有目录索引，方便快速定位

### 1.3 可验证输出
- 每个输出都必须能被校验
- 校验只检查"有没有"，不检查"好不好"
- 校验失败必须阻断，不允许警告后继续

## 二、工作流最佳实践

### 2.1 需求确认
- 必须明确任务目标、输入输出、约束条件
- 不确定时主动询问，不要凭假设执行
- 需求确认后用一句话复述，确保理解一致

### 2.2 方案设计
- 方法选择必须有依据，不要凭感觉
- 步骤分解必须合理，每步有明确输入输出
- 复杂任务必须拆成小步骤，不要一步到位

### 2.3 执行与校验
- 执行必须用编排脚本，不允许手动跳步
- 校验必须用校验脚本，不允许凭感觉判断
- 校验失败必须修复，不允许绕过

### 2.4 交付
- 输出格式必须统一，严格按照模板
- 必须包含风险提示和局限性说明
- 必须包含后续建议

## 三、常见错误与避免方法

| 错误 | 症状 | 避免方法 |
|------|------|---------|
| 跳步执行 | 跳过关键步骤直接给结果 | 用编排脚本强制顺序 |
| 校验走过场 | 说"已校验"但实际没检查 | 用校验脚本，输出可验证 |
| 输出格式混乱 | 每次格式不一样 | 严格按照输出模板 |
| 没有风险提示 | 只说好不说坏 | 交付模板强制包含风险提示 |
| 硬编码路径 | 换环境就失效 | 用相对路径或环境变量 |

## 四、质量检查清单

- [ ] 任务目标明确
- [ ] 方法选择有依据
- [ ] 步骤分解合理
- [ ] 编排脚本运行成功
- [ ] 校验脚本0个必须修复问题
- [ ] 输出格式符合模板
- [ ] 包含风险提示
- [ ] 包含后续建议

---

**版本**: v1.0
**基于**: skill-creator-pro 通用最佳实践模板
'''


WORKFLOW_GUIDE_TEMPLATE = '''# {skill_title} 工作流指南

> 本文档包含{skill_title}的详细工作流指导，按需加载。

## 一、工作流总览

```
需求确认 → 方案设计 → 执行 → 校验 → 交付
    ↓          ↓        ↓      ↓      ↓
  明确目标   选择方法  脚本执行 质量检查 整理输出
```

## 二、各阶段详细指导

### 阶段1: 需求确认

**目标**: 明确任务目标、输入输出、约束条件

**步骤**:
1. 阅读用户输入，提取关键信息
2. 确认任务目标（用一句话描述）
3. 确认输入数据/文件
4. 确认输出格式和要求
5. 确认约束条件（时间/预算/质量）

**检查清单**:
- [ ] 任务目标能用一句话描述
- [ ] 输入数据已就绪
- [ ] 输出格式已确认
- [ ] 约束条件已明确

**常见问题**:
- 需求不明确时怎么办？→ 主动询问，不要凭假设执行
- 需求冲突时怎么办？→ 列出冲突点，请用户决策

### 阶段2: 方案设计

**目标**: 选择方法、规划步骤、确定工具

**步骤**:
1. 分析任务特点，选择合适的方法
2. 分解任务为可执行的步骤
3. 确定每个步骤使用的工具（脚本/手动/混合）
4. 预估时间和资源

**检查清单**:
- [ ] 方法选择有依据
- [ ] 步骤分解合理（每步有明确输入输出）
- [ ] 工具选择正确
- [ ] 时间预估合理

**方法选择指南**:
| 任务特点 | 推荐方法 | 推荐工具 |
|---------|---------|---------|
| 确定性操作 | 脚本化 | orchestrator.py + main.py |
| 需要判断 | 方法论+检查清单 | workflow-guide.md + checklist.md |
| 复杂任务 | 分阶段执行 | orchestrator.py 多阶段管道 |

### 阶段3: 执行

**目标**: 按方案执行核心任务

**步骤**:
1. 运行编排脚本：`python3 orchestrator.py run --input <输入> --output <输出>`
2. 监控执行过程，确保每阶段成功
3. 遇到错误时，查看错误信息，修复后重试

**检查清单**:
- [ ] 编排脚本运行成功
- [ ] 每个阶段输出符合预期
- [ ] 无错误或异常

### 阶段4: 校验

**目标**: 验证输出质量

**步骤**:
1. 运行校验脚本：`python3 validator.py --input <输出文件>`
2. 查看校验结果
3. 必须修复的问题：立即修复，重新校验
4. 警告项：评估是否需要修复

**检查清单**:
- [ ] 校验脚本运行成功
- [ ] 0个必须修复的问题
- [ ] 警告项已评估

### 阶段5: 交付

**目标**: 整理输出、撰写说明、交付结果

**步骤**:
1. 整理输出文件，确保命名规范
2. 撰写交付说明（状态/任务/方法/结果/风险/建议）
3. 按照输出格式模板呈现

**检查清单**:
- [ ] 输出格式符合模板
- [ ] 包含风险提示
- [ ] 包含后续建议
- [ ] 文件命名规范

## 三、异常处理

| 异常 | 处理方法 |
|------|---------|
| 编排脚本失败 | 查看错误信息，修复输入或配置，重新运行 |
| 校验发现必须修复问题 | 修复问题，重新运行校验，直到0个必须修复 |
| 输出不符合预期 | 回到方案设计阶段，调整方法，重新执行 |
| 时间不够 | 优先保证核心功能，非核心功能标注为"待完善" |

---

**版本**: v1.0
**基于**: skill-creator-pro 通用工作流指南模板
'''


# ============================================================
# Process 模式校验脚本模板
# ============================================================

PROCESS_VALIDATOR_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{skill_title} 输出校验脚本

验证输出格式完整性，硬门禁：缺少必填字段=交付阻断。

用法：
  python3 validator.py --input <结果文件>
  python3 validator.py --input <结果文件> --json
"""
import argparse
import json
import os
import sys


def validate_output(filepath):
    """校验输出文件完整性"""
    issues = []
    warnings = []

    # 检查1：文件存在
    if not os.path.exists(filepath):
        issues.append({{"level": "error", "field": "file_exists", "message": f"文件不存在: {{filepath}}"}})
        return issues, warnings

    # 检查2：文件非空
    if os.path.getsize(filepath) == 0:
        issues.append({{"level": "error", "field": "file_empty", "message": "文件为空"}})
        return issues, warnings

    # 检查3：读取内容
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        issues.append({{"level": "error", "field": "file_read", "message": f"文件读取失败: {{e}}"}})
        return issues, warnings

    # 检查4：必填字段（通用输出格式）
    mandatory_fields = ["状态", "任务", "核心输出"]
    for field in mandatory_fields:
        if field not in content:
            issues.append({{
                "level": "error",
                "field": f"missing_{{field}}",
                "message": f"缺少必填字段: {{field}}"
            }})

    # 检查5：质量字段（建议包含）
    quality_fields = ["风险提示", "后续建议"]
    for field in quality_fields:
        if field not in content:
            warnings.append({{
                "level": "warning",
                "field": f"missing_{{field}}",
                "message": f"建议包含: {{field}}"
            }})

    return issues, warnings


def main():
    parser = argparse.ArgumentParser(description="{skill_title} 输出校验")
    parser.add_argument("--input", required=True, help="待校验的结果文件")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    args = parser.parse_args()

    issues, warnings = validate_output(args.input)

    result = {{
        "success": len(issues) == 0,
        "input": args.input,
        "errors": len(issues),
        "warnings": len(warnings),
        "issues": issues,
        "warnings_list": warnings,
    }}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print(f"校验结果: {{'✅ 通过' if result['success'] else '❌ 失败'}}")
        print(f"必须修复的问题: {{result['errors']}}")
        print(f"警告（建议修复）: {{result['warnings']}}")
        print("=" * 60)
        if issues:
            print("\\n必须修复的问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {{i}}. [{{issue['field']}}] {{issue['message']}}")

    sys.exit(0 if len(issues) == 0 else 1)


if __name__ == "__main__":
    main()
'''


CHECKLIST_TEMPLATE = '''# {skill_title} 检查清单

> 本文档包含{skill_title}的各阶段检查清单，按需加载。

## 一、需求确认检查清单

- [ ] 任务目标明确（能用一句话描述）
- [ ] 输入数据/文件已就绪
- [ ] 输出格式已确认
- [ ] 约束条件（时间/预算/质量）已明确
- [ ] 不确定的点已询问用户

## 二、方案设计检查清单

- [ ] 方法选择有依据（参考best-practices.md）
- [ ] 步骤分解合理（每步有明确输入输出）
- [ ] 工具选择正确（脚本/手动/混合）
- [ ] 时间预估合理
- [ ] 风险点已识别

## 三、执行检查清单

- [ ] 编排脚本运行成功（orchestrator.py run）
- [ ] init阶段成功（输入校验通过）
- [ ] execute阶段成功（核心任务执行完成）
- [ ] validate阶段成功（输出校验通过）
- [ ] review阶段成功（复盘完成）
- [ ] 无错误或异常

## 四、校验检查清单

- [ ] 校验脚本运行成功（validator.py）
- [ ] 0个必须修复的问题
- [ ] 警告项已评估
- [ ] 输出文件存在且非空
- [ ] 输出格式符合规范

## 五、交付检查清单

- [ ] 输出格式符合模板
- [ ] 包含状态（成功/失败）
- [ ] 包含任务描述
- [ ] 包含方法说明
- [ ] 包含核心输出
- [ ] 包含关键发现
- [ ] 包含风险提示
- [ ] 包含后续建议
- [ ] 文件命名规范

## 六、质量保证检查清单

- [ ] 所有步骤都有验证
- [ ] 校验失败都已修复
- [ ] 没有跳过的步骤
- [ ] 没有硬编码的路径或凭据
- [ ] 脚本都经过测试
- [ ] 文档都已更新

---

**使用方法**: 每个阶段完成后，对照检查清单逐项确认。不允许跳过检查直接进入下一阶段。
**版本**: v1.0
'''


# ============================================================
# 通用示例模板
# ============================================================

EXAMPLE_USAGE_TEMPLATE = '''# {skill_title} 使用示例

> 完整使用示例，照着做。

## 示例1: 完整流程执行

### 任务
对输入文件进行完整处理，输出结果文件。

### 步骤

**Step 1: 需求确认**
- 任务目标：处理输入文件，生成结构化输出
- 输入：input.csv
- 输出：output.json
- 约束：5分钟内完成

**Step 2: 方案设计**
- 方法：使用编排脚本多阶段管道
- 步骤：init → execute → validate → review
- 工具：orchestrator.py + main.py + validator.py

**Step 3: 执行**
```bash
cd scripts
python3 orchestrator.py run --input ../input.csv --output ../output.json
```

预期输出：
```json
{{
  "success": true,
  "stage": "done",
  "pipeline": ["init", "execute", "validate", "review"]
}}
```

**Step 4: 校验**
```bash
python3 validator.py --input ../output.json
```

预期输出：
```
============================================================
校验结果: ✅ 通过
必须修复的问题: 0
警告（建议修复）: 0
============================================================
```

**Step 5: 交付**
```
## 处理结果

**状态**: ✅成功
**任务**: 处理input.csv，生成结构化输出output.json
**方法**: 编排脚本多阶段管道（init→execute→validate→review）

---

**核心输出**:
output.json（包含处理后的结构化数据）

**关键发现**:
- 数据完整性100%
- 处理耗时2分30秒
- 无异常数据

**风险提示**: 输入文件中包含少量缺失值，已按默认值处理
**后续建议**: 可以增加数据清洗步骤，提升数据质量

✅ 已通过校验（validator.py 0个必须修复问题）
```

---

## 示例2: 快速模式（简化流程）

### 任务
快速处理输入，只需要核心结果。

### 步骤
```bash
cd scripts
python3 main.py --input ../input.csv --output ../output.json --quick
```

---

## 常见问题

**Q: 编排脚本失败怎么办？**
A: 查看错误信息，修复输入或配置，运行 `python3 orchestrator.py reset` 后重新运行。

**Q: 校验发现必须修复的问题怎么办？**
A: 修复问题，重新运行校验，直到0个必须修复的问题。不允许绕过校验。

**Q: 输出不符合预期怎么办？**
A: 回到方案设计阶段，调整方法，重新执行。

---

**版本**: v1.0
**基于**: skill-creator-pro 通用使用示例模板
'''


EXAMPLE_WORKFLOW_TEMPLATE = '''# {skill_title} 工作流示例

> 完整工作流示例，照着做。

## 示例: 完整工作流执行

### 任务
对输入数据进行深度分析，输出分析报告。

### 工作流执行

**Step 1: 需求确认**
- 任务目标：分析输入数据的趋势和异常
- 输入：data.csv
- 输出：report.md
- 约束：包含趋势分析+异常检测+建议

**Step 2: 方案设计**
- 方法：分阶段分析（数据清洗→趋势分析→异常检测→报告生成）
- 工具：手动分析+脚本辅助
- 参考：references/workflow-guide.md（第二章）

**Step 3: 执行**
- 3.1 数据清洗：检查缺失值、异常值、重复值
- 3.2 趋势分析：计算增长率、移动平均、季节性
- 3.3 异常检测：识别离群点、突变点
- 3.4 报告生成：整理分析结果，撰写报告

**Step 4: 验证与修正**
- [ ] 报告包含趋势分析
- [ ] 报告包含异常检测
- [ ] 报告包含建议
- [ ] 数据引用准确
- [ ] 格式符合模板

**Step 5: 交付**
```
## 数据分析报告

**状态**: ✅成功
**任务**: 分析data.csv的趋势和异常
**方法**: 分阶段分析（清洗→趋势→异常→报告）

---

**核心输出**:
report.md（完整分析报告）

**关键发现**:
- 整体趋势：增长15%
- 异常点：第3周数据突降
- 建议：关注第3周异常原因

**风险提示**: 数据仅覆盖3个月，趋势判断可能受短期波动影响
**后续建议**: 收集更多数据，做长期趋势分析

✅ 已通过验证（Step 4逐项检查完成）
```

---

**版本**: v1.0
**基于**: skill-creator-pro 通用工作流示例模板
'''


ASSETS_README_TEMPLATE = '''# Assets 目录说明

本目录存放不加载到上下文、但在输出中使用的文件。

## 适合放在这里的文件

- 模板文件（.docx, .xlsx, .pptx, .html等）
- 图片资源（.png, .jpg, .svg等）
- 字体文件（.ttf, .woff2等）
- 示例数据（.csv, .json等）
- 代码模板（前端模板、后端模板等）

## 不适合放在这里的文件

- 需要LLM阅读的文档（应该放在 references/）
- 需要执行的脚本（应该放在 scripts/）
- 使用示例（应该放在 examples/）

## 使用方法

1. 将资源文件放入本目录
2. 在SKILL.md或references中引用这些文件
3. LLM在生成输出时，可以直接使用这些文件，不需要加载到上下文

## 注意事项

- 不要放入大文件（>10MB），会影响技能加载速度
- 不要放入敏感信息（API key、密码等）
- 定期清理不需要的文件

---

**当前状态**: 空目录，请按需放入资源文件
'''


# ============================================================
# 通用评估用例模板（三种模式都预置）
# ============================================================

EVALUATION_CASES_TEMPLATE = '''# {skill_title} 评估用例

> 本文件包含3类通用评估用例，用于验证技能的触发准确性、输出完整性和错误处理能力。
> 使用方法：根据技能的具体领域，修改每个用例的输入和预期输出，然后实际运行测试。
> 核心原则：**没有评估用例的技能不能发布——评估用例是质量的可验证标准。**

---

## 一、触发准确性测试（Trigger Accuracy）

**目的**：验证技能在正确的场景下被触发，不在错误的场景下被触发。

**通过标准**：
- should_trigger用例触发率 ≥ 90%
- should_not_trigger用例误触发率 ≤ 10%

### 1.1 应该触发的用例（should_trigger）

```
用例1.1.1：核心功能触发
  - 输入："[请替换为用户会说的触发语，例如：帮我处理这个文件]"
  - 预期：技能被触发，开始执行核心流程
  - 验证点：
    - 技能确实被加载（不是其他技能）
    - 输出包含技能的核心功能相关内容

用例1.1.2：关键词触发
  - 输入："[请替换为领域关键词，例如：这个数据需要清洗]"
  - 预期：技能被触发
  - 验证点：
    - description中的关键词被正确匹配
    - 技能开始执行相关流程

用例1.1.3：复杂场景触发
  - 输入："[请替换为复杂场景，例如：帮我把这个PDF转成Word然后提取表格]"
  - 预期：技能被触发，并且能处理多步骤任务
  - 验证点：
    - 技能被触发
    - 能正确分解多步骤任务
    - 每步都有明确输出
```

### 1.2 不应该触发的用例（should_not_trigger）

```
用例1.2.1：无关任务不触发
  - 输入："[请替换为无关任务，例如：今天天气怎么样]"
  - 预期：技能不被触发
  - 验证点：
    - 技能没有被加载
    - 系统用通用能力回答，而不是本技能

用例1.2.2：其他技能领域不触发
  - 输入："[请替换为其他技能领域的任务，例如：帮我写一封邮件]"
  - 预期：技能不被触发（如果有邮件技能，应该触发邮件技能）
  - 验证点：
    - 本技能没有被加载
    - 没有输出本技能的相关内容

用例1.2.3：模糊需求不误触发
  - 输入："[请替换为模糊需求，例如：帮我处理一下这个]"
  - 预期：技能不盲目触发，应该先询问用户具体需求
  - 验证点：
    - 没有直接开始执行本技能的流程
    - 输出了澄清问题
```

---

## 二、输出完整性测试（Output Completeness）

**目的**：验证技能的输出包含所有必需字段，格式正确。

**通过标准**：
- 输出完整率 = 100%（不允许遗漏关键字段）
- 格式符合技能定义的输出规范

### 2.1 正常场景输出完整性

```
用例2.1.1：核心功能输出完整
  - 输入："[请替换为核心功能的标准输入]"
  - 预期：输出包含所有必需字段
  - 必需字段清单（根据技能具体情况修改）：
    - [ ] 一句话结论（核心结果）
    - [ ] 执行步骤（做了什么）
    - [ ] 输出结果（具体数据/文件）
    - [ ] 注意事项（风险/限制）
    - [ ] 下一步建议（后续操作）
  - 验证点：
    - 所有必需字段都存在
    - 字段内容具体（不是"已完成"这种空泛描述）
    - 格式一致（每次输出结构相同）

用例2.1.2：多步骤任务输出完整
  - 输入："[请替换为多步骤任务输入]"
  - 预期：每一步都有明确输出，最终结果完整
  - 验证点：
    - 每一步都有进度提示
    - 中间结果可追溯
    - 最终结果包含所有步骤的汇总
    - 没有跳过任何步骤
```

### 2.2 输出格式一致性

```
用例2.2.1：多次输出格式一致
  - 构造：连续运行3次相同的核心功能
  - 预期：3次输出的结构和格式一致
  - 验证点：
    - 必需字段的顺序一致
    - 标题/小标题格式一致
    - 没有遗漏字段
    - 内容随输入变化（不是模板复制）

用例2.2.2：边界输入输出格式不变
  - 构造：输入边界数据（空/最小/最大）
  - 预期：输出格式仍然完整，不因输入特殊而崩溃
  - 验证点：
    - 输出仍然包含所有必需字段
    - 没有报错或崩溃
    - 对边界情况有明确说明
```

---

## 三、错误处理测试（Error Handling）

**目的**：验证技能在边界条件和异常场景下的行为。

**通过标准**：
- 不崩溃（所有异常场景都有明确输出）
- 错误信息明确（指出问题+修复建议）
- 有降级机制（主路径失败时有备选方案）

### 3.1 边界场景

```
用例3.1.1：输入不完整
  - 构造：用户只提供了部分必需信息
  - 预期：主动询问缺失信息，不盲目执行
  - 验证点：
    - 输出了澄清问题（至少1个关键问题）
    - 没有直接执行（避免错误结果）
    - 问题具体（不是"请提供更多信息"这种空泛描述）

用例3.1.2：输入格式错误
  - 构造：用户提供了错误格式的输入（如应该是数字却给了文字）
  - 预期：检测到格式错误，提示用户修正
  - 验证点：
    - 明确指出哪个字段格式错误
    - 给出正确格式的示例
    - 不崩溃，不产生错误结果

用例3.1.3：超出能力范围
  - 构造：用户要求技能做它不支持的事情
  - 预期：明确说明不支持，给出替代方案
  - 验证点：
    - 明确说明"本技能不支持XXX"
    - 给出替代方案（如"建议使用XXX技能"或"可以手动XXX"）
    - 不强行执行（避免错误结果）
```

### 3.2 异常场景

```
用例3.2.1：脚本执行失败
  - 构造：模拟脚本执行失败（如依赖缺失、文件不存在）
  - 预期：捕获错误，给出明确的错误信息和修复建议
  - 验证点：
    - 错误信息明确（指出哪个脚本失败，为什么失败）
    - 给出修复建议（如"请安装XXX依赖"）
    - 有降级机制（如"可以手动执行XXX"）
    - 不崩溃，不静默失败

用例3.2.2：外部依赖不可用
  - 构造：模拟外部API/服务不可用
  - 预期：检测到不可用，给出降级方案
  - 验证点：
    - 明确说明外部依赖不可用
    - 给出降级方案（如使用缓存/手动输入）
    - 不无限重试
    - 不崩溃

用例3.2.3：大文件/大数据处理
  - 构造：输入超出常规大小的文件/数据
  - 预期：能处理或明确说明限制
  - 验证点：
    - 如果能处理：有进度提示，不超时
    - 如果不能处理：明确说明大小限制，给出替代方案
    - 不崩溃，不内存溢出
```

---

## 四、评估执行指南

### 4.1 如何执行评估

```
步骤1：根据技能具体领域，修改上述用例的输入和预期输出
步骤2：实际运行每个用例，记录实际输出
步骤3：对照预期输出，检查验证点是否全部通过
步骤4：记录失败用例，分析原因，修复技能
步骤5：重新运行失败用例，直到全部通过
```

### 4.2 评估报告模板

```
# {skill_title} 评估报告

## 评估时间：YYYY-MM-DD
## 评估人：XXX

## 一、触发准确性测试
| 用例ID | 描述 | 预期 | 实际 | 结果 |
|--------|------|------|------|------|
| 1.1.1 | 核心功能触发 | 触发 | | ✅/❌ |
| 1.1.2 | 关键词触发 | 触发 | | ✅/❌ |
| ... | ... | ... | ... | ... |

触发率：XX%（标准≥90%）
误触发率：XX%（标准≤10%）

## 二、输出完整性测试
| 用例ID | 描述 | 必需字段数 | 实际字段数 | 结果 |
|--------|------|-----------|-----------|------|
| 2.1.1 | 核心功能输出完整 | 5 | | ✅/❌ |
| ... | ... | ... | ... | ... |

输出完整率：XX%（标准=100%）

## 三、错误处理测试
| 用例ID | 描述 | 预期 | 实际 | 结果 |
|--------|------|------|------|------|
| 3.1.1 | 输入不完整 | 询问缺失信息 | | ✅/❌ |
| ... | ... | ... | ... | ... |

错误处理通过率：XX%（标准=100%不崩溃）

## 四、总结
- 总用例数：XX
- 通过数：XX
- 失败数：XX
- 通过率：XX%

## 五、失败用例分析与修复计划
| 用例ID | 失败原因 | 修复方案 | 优先级 | 状态 |
|--------|---------|---------|--------|------|
| | | | | |
```

---

## 五、检查清单：你的评估用例是否完整

- [ ] 是否有至少3个should_trigger用例？
- [ ] 是否有至少3个should_not_trigger用例？
- [ ] 是否有输出完整性测试（必需字段清单）？
- [ ] 是否有输出格式一致性测试（多次运行对比）？
- [ ] 是否有边界场景测试（输入不完整/格式错误/超出范围）？
- [ ] 是否有异常场景测试（脚本失败/外部依赖不可用/大数据）？
- [ ] 每个用例是否有明确的通过标准？
- [ ] 是否实际运行了所有用例并记录结果？
- [ ] 失败用例是否有修复计划？

**0-4项**：评估用例严重不足，技能质量没有保障
**5-7项**：评估用例基本完整，但有遗漏场景
**8-9项**：评估用例完整，技能质量有保障
**10项**：评估用例完美，技能质量可验证

---

**版本**: v1.0
**基于**: skill-creator-pro 通用评估用例模板
**更新**: 2026-09-23
'''


# ============================================================
# Capability 模式核心工具脚本
# ============================================================

