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
| 掌握渐进式披露 | `references/preload-design-guide.md` |
| 防止LLM偷懒 | `references/llm-anti-laziness-guide.md` |
| 设计触发路由 | `references/routing-mustread-test-cases.md` |
| 做端到端测试 | `references/e2e-testing-playbook.md` |
| 搭建自进化闭环 | `references/self-evolution-playbook.md` |
| 管理技术债 | `references/tech-debt-management.md` |
| 做安全审计 | `references/security-audit-checklist.md` |
| 做规范评审 | `references/review-process-guide.md` |

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

更多问题见 `references/faq.md`。

---

## 版本

- v1.0：快速上手指南初版
- 核心：5分钟创建流程 + 命令速查 + 三种模式对比 + 质量标准
- 2026-09-23
