# skill-creator-pro 快速上手指南

> 5分钟学会使用skill-creator-pro创建专业级技能。
> 核心结论：**选择模式 → 运行命令 → 填充内容 → 校验测试，四步创建专业技能。**

---

## 一、什么是skill-creator-pro

skill-creator-pro是专业级技能创建工具，相比平台自带的skill-creator-for-work：

| 对比项 | skill-creator-for-work | skill-creator-pro |
|--------|----------------------|-------------------|
| 定位 | 指南型（教你怎么建） | 工具型（帮你建好） |
| 脚本数量 | 2个 | 6个 |
| references文档 | 2个 | 20个 |
| 创建模式 | 1种（通用骨架） | 3种（Mixed/Process/Capability） |
| 规范校验 | 基础（frontmatter+命名） | 完整（36项三层评分） |
| 产出质量 | 基础骨架（大量TODO） | 专业可用（必备层20/20） |

---

## 二、5分钟创建第一个技能

### 第1步：选择模式（30秒）

| 如果你要创建... | 选择模式 | 特点 |
|----------------|---------|------|
| 完整的分析/决策/工作流技能 | **Mixed** | 3脚本+2references+1示例，完整工程化 |
| 方法论/流程/检查清单类技能 | **Process** | 编排脚本+校验脚本+方法论文档 |
| 简单工具/命令包装类技能 | **Capability** | 1个核心脚本，简洁高效 |

**不确定选什么？选Mixed模式**，它是最通用的完整专业模板。

### 第2步：运行创建命令（1分钟）

```bash
cd /home/user/.doubao/agent_mode/workspace/.user_skills/skill-creator-pro

# Mixed模式（推荐新手）
python3 scripts/init_skill_pro.py my-first-skill \
  --path /home/user/.doubao/agent_mode/workspace/.user_skills \
  --philosophy mixed \
  --title "我的第一个技能" \
  --description "专业技能描述。触发词："技能创建""专业模板"。"

# 查看创建结果
ls -la /home/user/.doubao/agent_mode/workspace/.user_skills/my-first-skill/
```

### 第3步：填充内容（2分钟）

创建的技能包含预置模板，需要根据你的具体领域填充：

1. **编辑SKILL.md**：替换所有`【】`占位符，填写具体的工作流程和Gotchas
2. **编辑scripts/main.py**：实现核心功能（替换TODO）
3. **编辑references/**：填写领域特定的方法论和规则
4. **编辑examples/**：填写完整的使用示例

### 第4步：校验测试（1.5分钟）

```bash
# 规范校验（必须0高优先级问题）
python3 scripts/validate_skill.py /home/user/.doubao/agent_mode/workspace/.user_skills/my-first-skill

# 深度审计（必备层必须20/20）
python3 scripts/audit_skill.py /home/user/.doubao/agent_mode/workspace/.user_skills/my-first-skill

# 输出校验（硬门禁）
python3 scripts/output_validator.py /home/user/.doubao/agent_mode/workspace/.user_skills/my-first-skill --mode create

# 端到端测试（完整流程）
python3 scripts/create_skill.py test /home/user/.doubao/agent_mode/workspace/.user_skills/my-first-skill
```

**全部通过后，你的专业技能就创建完成了！**

---

## 三、常用命令速查

### 创建技能
```bash
# Mixed模式（完整专业技能）
python3 scripts/init_skill_pro.py <skill-name> --path <output-dir> --philosophy mixed

# Process模式（方法论型）
python3 scripts/init_skill_pro.py <skill-name> --path <output-dir> --philosophy process

# Capability模式（工具包装型）
python3 scripts/init_skill_pro.py <skill-name> --path <output-dir> --philosophy capability
```

### 校验技能
```bash
# 规范校验
python3 scripts/validate_skill.py <skill-path>

# 规范校验（JSON输出）
python3 scripts/validate_skill.py <skill-path> --json

# 深度审计
python3 scripts/audit_skill.py <skill-path>

# 输出校验
python3 scripts/output_validator.py <skill-path> --mode create|optimize|review|test
```

### 编排脚本（一键完成）
```bash
# 创建技能（自动完成初始化+校验+审计）
python3 scripts/create_skill.py create <skill-name> --path <output-dir> --philosophy mixed

# 优化现有技能（自动完成审计+问题定位+修复建议）
python3 scripts/create_skill.py optimize <skill-path>

# 评审技能（自动完成36项核查+问题分级+改进建议）
python3 scripts/create_skill.py review <skill-path>

# 测试技能（自动完成触发测试+模式测试+边界测试+回归测试）
python3 scripts/create_skill.py test <skill-path>
```

---

## 四、三种模式详细对比

| 维度 | Mixed（混合型） | Process（方法论型） | Capability（工具包装型） |
|------|----------------|-------------------|------------------------|
| **适用场景** | 分析/决策/完整工作流 | 方法论/流程/检查清单 | 简单工具/命令包装 |
| **脚本数量** | 3个（main+orchestrator+validator） | 2个（orchestrator+validator） | 1个（main） |
| **references** | 2个（最佳实践+评估用例） | 2个（工作流指南+检查清单+评估用例） | 1个（评估用例） |
| **examples** | 1个（使用示例） | 1个（工作流示例） | 1个（使用示例） |
| **触发路由** | ✅ 完整（3种模式） | ✅ 完整（3种模式） | ✅ 简化（3种模式） |
| **编排脚本** | ✅ 多阶段管道 | ✅ 多阶段管道 | ❌ 单命令调用 |
| **校验脚本** | ✅ 硬门禁 | ✅ 硬门禁 | ❌ 错误处理在脚本内 |
| **SKILL.md行数** | ~240行 | ~260行 | ~180行 |
| **文件总数** | 8个 | 8个 | 6个 |
| **深度审计（初始）** | 28/36 | 26/36 | 22/36 |
| **必备层（初始）** | 20/20 | 20/20 | 20/20 |

### 模式选择决策树

```
你的技能是否有明确的多步骤工作流？
├── 是 → 工作流是否需要编排脚本强制顺序？
│   ├── 是 → 选择Mixed模式（完整工程化）
│   └── 否 → 选择Process模式（方法论驱动）
└── 否 → 你的技能是否主要是单命令调用？
    ├── 是 → 选择Capability模式（简洁高效）
    └── 否 → 选择Mixed模式（最通用）
```

---

## 五、质量标准

创建的技能必须达到以下标准才能发布：

### 必须达标（发布前检查）
- [ ] 规范校验：0高优先级问题
- [ ] 深度审计：必备层20/20
- [ ] 输出校验：0必须修复问题
- [ ] 所有脚本：语法正确，可正常运行
- [ ] 所有占位符：已替换为具体内容
- [ ] 端到端测试：完整流程跑通

### 建议达标（专业级）
- [ ] 深度审计：总分≥28/36
- [ ] 有完整的examples示例
- [ ] 有具体的Gotchas（≥5个）
- [ ] 有评估用例并通过测试
- [ ] 有自进化闭环设计

---

## 六、下一步学习资源

创建完第一个技能后，深入学习以下文档提升技能质量：

| 如果你想... | 阅读 |
|------------|------|
| 理解三种设计哲学的区别 | `references/design-philosophies.md` |
| 学习架构设计模式 | `references/architecture-patterns.md` |
| 掌握渐进式披露 | `references/performance-optimization-guide.md` |
| 防止LLM偷懒 | `references/anti-laziness-guide.md` |
| 设计触发路由 | `references/advanced-testing-guide.md` |
| 做端到端测试 | `references/e2e-testing-playbook.md` |
| 搭建自进化闭环 | `references/self-evolution-guide.md` |
| 管理技术债 | `references/tech-debt-management.md` |
| 做安全审计 | `references/review-and-security-guide.md` |
| 做规范评审 | `references/review-and-security-guide.md` |

---

## 七、常见问题快速解答

**Q: 创建的技能有很多TODO占位符，正常吗？**
A: 正常。模板预置了占位符提示你需要填充的内容，填充后删除所有TODO。

**Q: 三种模式创建的技能初始审计分数不同，是不是Capability模式最差？**
A: 不是。初始分数不同是因为脚本数量不同，填充内容后都可以达到36/36。Capability模式适合简单工具，不需要编排脚本。

**Q: 我可以混合使用三种模式的元素吗？**
A: 可以。创建后可以手动添加/删除脚本和文档，模式只是初始配置，不是限制。

**Q: 创建的技能和skill-creator-for-work创建的有什么区别？**
A: skill-creator-pro创建的是专业级可用技能（必备层20/20，无TODO），skill-creator-for-work创建的是基础骨架（必备层8/20，大量TODO）。

更多问题见 `references/quick-start.md`。

---

## 版本

- v1.0：快速上手指南初版
- 核心：5分钟创建流程 + 命令速查 + 三种模式对比 + 质量标准
- 2026-09-23

---

# 附录：常见问题解答（FAQ）

# skill-creator-pro 常见问题解答（FAQ）

> 收集自多轮开发实战中的真实问题，按类别整理。
> 核心结论：**90%的问题都有明确答案，遇到问题先查FAQ，再查references，最后问AI。**

---

## 一、基础概念

### Q1: skill-creator-pro是什么？和skill-creator-for-work有什么区别？

**A:** skill-creator-pro是专业级技能创建工具，skill-creator-for-work是平台自带的入门指南。

| 对比项 | skill-creator-for-work | skill-creator-pro |
|--------|----------------------|-------------------|
| 定位 | 指南型（教你怎么建） | 工具型（帮你建好） |
| 脚本 | 2个 | 6个 |
| references | 2个 | 20个 |
| 创建模式 | 1种 | 3种 |
| 规范校验 | 基础 | 完整（36项） |
| 产出质量 | 基础骨架（大量TODO） | 专业可用（必备层20/20） |

简单说：for-work是"入门教材"，pro是"专业工厂"。

### Q2: 什么是三种设计哲学（Mixed/Process/Capability）？

**A:** 三种模式对应不同类型的技能：

- **Mixed（混合型）**：完整工程化技能，有编排脚本+校验脚本+核心工具，适合分析/决策/复杂工作流
- **Process（方法论型）**：流程驱动技能，有编排脚本+校验脚本+方法论文档，适合方法论/检查清单/审批流程
- **Capability（工具包装型）**：简洁工具技能，只有1个核心脚本，适合简单工具/命令包装/格式转换

**不确定选什么？选Mixed模式**，它是最通用的完整专业模板。

### Q3: 什么是渐进式披露？

**A:** 渐进式披露是技能的三层加载架构：
- **L1 元数据**（name+description）：始终在上下文，~100词
- **L2 SKILL.md**：技能触发后加载，<500行
- **L3 references/scripts**：按需加载，不受上下文限制

目的是避免上下文窗口被无关内容占满，只在需要时加载详细信息。

### Q4: 什么是触发路由？

**A:** 触发路由是SKILL.md开头的强制路由声明，告诉AI当前用户请求属于哪种模式，应该走哪条流程。

例如：
```
🔀 路由: 完整分析｜任务：深度分析｜命令：orchestrator.py start｜原因：用户要求完整分析
```

作用是防止LLM跳步、偷懒、走错流程。

---

## 二、创建技能

### Q5: 技能名有什么格式要求？

**A:** 技能名必须满足以下条件：
1. 只允许小写字母、数字、连字符（`-`）
2. 不能以连字符开头或结尾
3. 不能只有连字符
4. 不能包含路径分隔符（`/`或`\`）
5. 不能包含`..`
6. 长度不超过64字符
7. 不能为空

**正确示例**：`my-skill`、`pdf-editor`、`data-analyzer-v2`

**错误示例**：`My Skill`（大写+空格）、`-bad`（开头连字符）、`bad-`（结尾连字符）、`../attack`（路径遍历）

### Q6: 技能创建在哪个目录？

**A:** 默认创建在 `workspace/.user_skills` 目录内。完整路径是：
```
/home/user/.doubao/agent_mode/workspace/.user_skills/<skill-name>/
```

必须用`--path`参数指定输出目录，脚本不会自动解析。

### Q7: 创建的技能有很多TODO占位符，正常吗？

**A:** 正常。模板预置了`【】`占位符提示你需要填充的内容。**发布前必须替换所有占位符为具体内容**，否则规范校验会报"发现TODO占位符"问题。

### Q8: 可以修改创建后的技能吗？

**A:** 可以。创建后的技能是普通目录，可以自由修改：
- 添加/删除脚本
- 添加/删除references文档
- 修改SKILL.md内容
- 修改模板内容

模式只是初始配置，不是限制。修改后重新运行校验和审计即可。

### Q9: 如何删除不需要的脚本/文档？

**A:** 直接删除文件即可，但要注意：
1. 删除脚本后，检查SKILL.md中是否还有对该脚本的引用
2. 删除references后，检查SKILL.md的渐进式披露引用表是否还有该文档
3. 删除后重新运行`output_validator.py`，确保没有"引用不存在的文件"问题

---

## 三、质量校验

### Q10: 规范校验、深度审计、输出校验有什么区别？

**A:** 三个校验工具各有侧重：

| 工具 | 侧重 | 检查项 | 通过标准 |
|------|------|--------|---------|
| `validate_skill.py` | 规范合规 | frontmatter/body/目录/脚本/内容质量 | 0高优先级问题 |
| `audit_skill.py` | 质量评估 | 36项三层评分（必备/推荐/可选） | 必备层20/20 |
| `output_validator.py` | 硬门禁 | 触发路由/渐进式披露/Gotchas/特定领域残留 | 0必须修复问题 |

**建议三个都运行**，确保技能从规范、质量、门禁三个维度都达标。

### Q11: 深度审计的分数怎么算？多少分算合格？

**A:** 深度审计采用加权评分：
- 必备层（20项）：权重×2，满分40分
- 推荐层（10项）：权重×1，满分10分
- 可选层（6项）：权重×0.5，满分3分
- **总分**：53分（加权），对应36项（未加权）

**评级标准**：
- 优秀：≥30/36（加权≥45/53）
- 良好：25-29/36（加权35-44/53）
- 及格：20-24/36（加权28-34/53）
- 不及格：<20/36（加权<28/53）

**发布最低标准**：必备层20/20（这是硬要求，推荐层和可选层根据技能复杂度评估）。

### Q12: 规范校验报"description可能缺少触发词"怎么办？

**A:** 这是medium级别警告，建议在description中用引号标注触发词。

**修改前**：
```
description: PDF处理技能。支持PDF旋转、合并、拆分。
```

**修改后**：
```
description: PDF处理技能。支持PDF旋转、合并、拆分。触发词："PDF处理""PDF旋转""PDF合并"。
```

### Q13: 输出校验报"缺少触发路由章节"怎么办？

**A:** 在SKILL.md的开头（frontmatter之后，第一个章节之前）添加触发路由章节。

参考模板：
```markdown
## 触发路由（强制执行，任何操作前先声明）

| 模式 | 触发词 | 流程 | 必读 |
|------|--------|------|------|
| 完整模式 | "完整""详细""深度" | 完整工作流 | references/workflow-guide.md |
| 快速模式 | "快速""简单""直接" | 简化流程 | 无 |
| 单步执行 | "只做XX""仅XX" | 单一步骤 | 对应步骤文档 |

路由声明格式：🔀 路由: 【模式】｜任务：【具体任务】｜命令：【运行的命令】｜原因：【为什么选这个模式】
```

---

## 四、错误处理

### Q14: 运行init_skill_pro.py报"技能名格式错误"怎么办？

**A:** 检查技能名是否符合格式要求（见Q5）。常见错误：
- 包含大写字母 → 改为小写
- 包含空格 → 改为连字符
- 包含下划线 → 改为连字符
- 以连字符开头/结尾 → 去掉首尾连字符

### Q15: 运行init_skill_pro.py报"目录已存在"怎么办？

**A:** 有两种解决方案：
1. **换一个技能名**：`python3 scripts/init_skill_pro.py new-name --path ...`
2. **删除已有目录后重新创建**：`rm -rf /path/to/existing-skill`，然后重新运行

**注意**：删除前确认目录中没有需要保留的内容。

### Q16: 运行validate_skill.py报"路径不存在"怎么办？

**A:** 检查传入的路径是否正确：
1. 路径是否存在
2. 路径是否是目录（不是文件）
3. 路径中是否包含SKILL.md文件
4. 相对路径是否基于当前工作目录

**建议使用绝对路径**，避免相对路径的歧义。

### Q17: 脚本运行报UnicodeDecodeError怎么办？

**A:** 这通常是因为读取了二进制文件或非UTF-8编码的文件。

skill-creator-pro的脚本已经修复了这个问题（使用`errors="replace"`参数）。如果你创建的技能中的脚本遇到这个问题，修改文件读取代码：

```python
# 修改前（可能崩溃）
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 修改后（安全处理）
with open(path, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()
```

---

## 五、进阶问题

### Q18: 编排脚本、校验脚本、自进化是必须的吗？

**A:** 对skill-creator-pro自身是必须的，但对创建的技能不是一刀切：

| 技能类型 | 编排脚本 | 校验脚本 | 自进化 |
|---------|---------|---------|--------|
| 复杂工作流型 | ✅ 必须 | ✅ 必须 | ✅ 建议 |
| 决策支持型 | ✅ 必须 | ✅ 必须 | ✅ 必须 |
| 持续运行型 | ✅ 建议 | ✅ 必须 | ✅ 必须 |
| 工具包装型 | ❌ 不需要 | ⚠️ 可选 | ❌ 不需要 |
| 一次性任务型 | ❌ 不需要 | ⚠️ 可选 | ❌ 不需要 |

**核心原则：功能匹配需求，不过度设计。** 三种模式已经体现了这种差异化。

### Q19: 多模型测试是必须的吗？

**A:** 不是必须的。多模型测试是指在不同能力的AI模型（Haiku/Sonnet/Opus）上分别测试技能，确保跨模型兼容性。

- **生产级技能，面向多模型环境发布**：建议做
- **个人使用，固定模型环境**：不是必须

skill-creator-pro通过设计层面的防偷懒机制（触发路由/Gotchas/硬门禁/编排脚本），已经在很大程度上解决了跨模型兼容性问题。

### Q20: 如何优化创建的技能？

**A:** 使用`create_skill.py optimize`命令一键优化：
```bash
python3 scripts/create_skill.py optimize <skill-path>
```

优化流程：
1. 现状审计（规范校验+深度审计+输出校验）
2. 问题定位（按严重程度分类）
3. 修复建议（每个问题给出具体修改方案）
4. 回归测试（修复后重新校验）

也可以手动优化，参考`references/tech-debt-management.md`。

### Q21: 如何做端到端测试？

**A:** 使用`create_skill.py test`命令：
```bash
python3 scripts/create_skill.py test <skill-path>
```

测试覆盖：
1. 触发测试（should_trigger/should_not_trigger）
2. 模式测试（每种模式的路由选择）
3. 边界测试（空输入/超长输入/特殊字符）
4. 回归测试（修改后不破坏现有功能）

详细测试方法见`references/e2e-testing-playbook.md`。

### Q22: 创建的技能如何发布？

**A:** 发布前检查清单：
- [ ] 规范校验：0高优先级问题
- [ ] 深度审计：必备层20/20
- [ ] 输出校验：0必须修复问题
- [ ] 所有脚本：语法正确，可正常运行
- [ ] 所有占位符：已替换为具体内容
- [ ] 端到端测试：完整流程跑通
- [ ] 示例：有1-2个完整示例
- [ ] Gotchas：有≥5个具体失败模式

全部通过后，技能目录就是最终交付物，放在`workspace/.user_skills`目录中即可被系统加载。

---

## 六、与其他工具的关系

### Q23: skill-creator-pro和其他分析类技能是什么关系？

**A:** skill-creator-pro是从多个特定领域技能（数据分析/内容生成/决策支持等）多轮开发经验中提炼出来的通用工具。

- 特定领域技能：针对具体领域的分析/处理技能
- skill-creator-pro：通用的技能创建工具，不包含任何特定领域内容

skill-creator-pro已经完成了特定领域残留清理（0残留），可以用于创建任何类型的技能。

### Q24: 可以用skill-creator-pro创建skill-creator-pro吗？

**A:** 理论上可以，但不建议。skill-creator-pro自身是经过多轮优化的专业工具，用模板重新创建会丢失很多优化细节。

如果需要创建类似的技能创建工具，建议：
1. 复制skill-creator-pro目录
2. 修改名称和description
3. 根据具体需求调整模板和脚本

---

## 七、检查清单：你的问题是否在FAQ中

- [ ] 基础概念问题（Q1-Q4）
- [ ] 创建技能问题（Q5-Q9）
- [ ] 质量校验问题（Q10-Q13）
- [ ] 错误处理问题（Q14-Q17）
- [ ] 进阶问题（Q18-Q22）
- [ ] 与其他工具关系（Q23-Q24）

**如果你的问题不在FAQ中**：
1. 查看相关的references文档
2. 运行脚本的`--help`查看参数说明
