# Agent编排型技能模板指南（Agent-Orchestrator Skill Template）

> 适用于：Agent创建/Agent编排/多Agent协作/AGENTS.md生成等需要将Skill/MCP/配置编排成完整Agent的技能。
> 实战参考：agent-creator（Agent开发与编排技能）

---

## 一、核心特点

| 维度 | 说明 |
|------|------|
| **设计哲学** | 混合型（Mixed）——工具脚本（Agent配置生成/验证/打包）+ 方法论（身份设计/工作流编排/记忆系统）结合。适合需要工具+判断的复杂Agent创建任务 |
| **核心挑战** | 单一职责模糊（容易和Skill创建/MCP创建混淆）、Agent配置不完整（缺身份/工作流/记忆/边界）、工作流模式选错（简单任务用复杂模式）、底座复用不足（重复造轮子） |
| **关键能力** | 单一职责定义（明确"做什么"和"不做什么"）、底座复用策略（复用相关技能的能力）、Agent配置结构化（agent.json完整定义）、工作流模板化（7种模式+决策树）、验证测试三级门禁（配置验证+能力测试+质量评分） |

---

## 二、目录结构

```
my-agent-creator-skill/
├── SKILL.md                          # 核心入口（触发路由+使用说明+Gotchas）
├── scripts/
│   ├── agent.py                      # 统一入口（init/validate/test/score/package/to-skill/to-plugin）
│   ├── init_agent.py                 # Agent脚手架生成（agent.json+目录结构+模板）
│   ├── generate_agent_config.py      # agent.json配置生成（结构化定义所有属性）
│   ├── generate_agents_md.py         # AGENTS.md生成（项目级配置，给Agent看的说明书）
│   ├── validate_agent.py             # Agent配置验证（完整性/合法性/一致性）
│   ├── test_agent.py                 # 完整Agent测试（配置+能力+质量）
│   ├── score_agent.py                # Agent质量评分（多维度评分，目标≥80分）
│   ├── package_agent.py              # Agent打包发布（zip+校验+版本管理）
│   ├── to_skill.py                   # Agent→Skill转化（简单Agent转化为Skill）
│   ├── to_plugin.py                  # Agent→Plugin转化（复杂Agent转化为Plugin，含MCP）
│   ├── workflow_orchestrator.py      # 工作流编排（7种模式模板+步骤生成）
│   ├── persona_designer.py           # 角色设计器（10种预设角色+自定义角色）
│   ├── memory_configurator.py        # 记忆配置器（短期/长期/上下文窗口/压缩策略）
│   ├── boundary_manager.py           # 边界管理器（Always/Ask First/Never三分类）
│   ├── runtime_guard.py              # 运行时保障（track/verify/gate/route）
│   ├── security_audit.py             # Agent安全审计（7维度安全检查）
│   ├── version_manager.py            # Agent版本管理（快照/diff/回滚）
│   ├── benchmark.py                  # Agent性能基准（标准化性能测试）
│   ├── debugger.py                   # Agent调试工具（单步调试/断点/日志）
│   ├── visualize.py                  # 多Agent可视化（Mermaid/ASCII架构图）
│   ├── ab_test.py                    # Agent A/B测试（配置对比测试）
│   └── self_evolution.py             # Agent自进化（反馈驱动优化）
├── references/
│   ├── agent-architecture.md         # Agent架构指南（完整架构+五大核心能力）
│   ├── decision-trees.md             # 决策树（Agent类型/工作流/角色选择）
│   ├── persona-design.md             # 角色设计方法论（10种预设角色+自定义方法）
│   ├── workflow-templates/           # 工作流模板（7种模式完整参考）
│   │   ├── react.md                  # ReAct模式
│   │   ├── plan-and-execute.md       # Plan-and-Execute模式
│   │   ├── reflection.md             # Reflection模式
│   │   ├── tree-of-thoughts.md       # Tree-of-Thoughts模式
│   │   ├── self-consistency.md       # Self-Consistency模式
│   │   ├── chain-of-thought.md       # Chain-of-Thought模式
│   │   └── tool-use.md               # Tool-Use模式
│   ├── workflow-orchestration.md     # 工作流编排指南
│   ├── memory-system.md              # 记忆系统设计（短期/长期/上下文窗口/压缩策略）
│   ├── multi-agent-collaboration.md  # 多Agent协作设计（5种协作模式）
│   ├── performance-monitoring.md     # 性能监控与优化（监控+自动优化）
│   ├── agents-md-guide.md            # AGENTS.md生成指南
│   ├── agent-evaluation.md           # Agent评估框架（验证+测试+评分）
│   ├── responsibility-boundary.md    # 职责边界声明（单一职责证据）
│   ├── e2e-test-record.md            # 端到端实测记录
│   └── cheatsheet.md                 # 常见错误+故障排除
├── templates/
│   ├── agent.json.template           # agent.json模板（完整配置结构）
│   ├── agents.md.template            # AGENTS.md模板
│   └── personas/                     # 角色模板（10种预设角色）
│       ├── researcher.json
│       ├── engineer.json
│       ├── assistant.json
│       └── ...
├── examples/
│   ├── simple-assistant/             # 简单问答助手（技能型）
│   ├── research-agent/               # 深度研究Agent（插件型，含MCP）
│   └── coding-agent/                 # 编程开发Agent（混合型）
└── assets/
    └── (输出用资源文件)
```

---

## 三、工作流设计

### 核心工作流：先创建标准Agent，再转化为Skill或Plugin

```bash
# 步骤1：创建标准Agent（中立格式）
agent.py init my-agent

# 步骤2：验证配置完整性
agent.py validate ./my-agent

# 步骤3：转化为Skill（简单Agent）
agent.py to-skill ./my-agent
# 或转化为Plugin（复杂Agent，含MCP）
agent.py to-plugin ./my-agent
```

### 阶段1：定义与设计

```bash
agent.py init my-agent              # 初始化Agent脚手架
# 或交互式创建
agent.py new                        # 交互式创建（推荐）
```

**完成标准**：agent.json配置完整，包含身份、能力、工作流、记忆、边界、路由

**agent.json核心字段**：
```json
{
  "name": "research-agent",
  "version": "1.0.0",
  "description": "专业研究Agent",
  "identity": {
    "role": "资深研究员",
    "goal": "提供高质量、有深度的研究报告",
    "constraints": ["不编造数据", "引用可验证来源"],
    "tone": "专业严谨",
    "capabilities_summary": "网络搜索+数据分析+报告生成"
  },
  "capabilities": {
    "skills": ["web-research", "data-analysis"],
    "mcp_servers": ["search-api"],
    "builtin_tools": []
  },
  "workflow": {
    "pattern": "plan-and-execute",
    "steps": [...]
  },
  "routing": {
    "enabled": true,
    "strategy": "hybrid",
    "entry_point": "main",
    "ambiguity_handling": "ask",
    "route_line_output": true,
    "modes": [...]
  },
  "memory": {
    "short_term": "conversation",
    "long_term": "optional",
    "context_window": 128000,
    "compression_strategy": "recent_full_early_summary"
  },
  "boundaries": {
    "always": ["引用来源", "验证数据"],
    "ask_first": ["修改核心架构", "访问敏感数据"],
    "never": ["编造数据", "泄露密钥", "绕过安全检查"]
  },
  "evaluation": {
    "test_cases": [],
    "success_criteria": "研究报告质量≥80分",
    "min_score": 80
  }
}
```

### 阶段2：验证 + 测试

```bash
agent.py validate ./my-agent        # 验证配置完整性
agent.py test ./my-agent            # 完整Agent测试（配置+能力+质量）
agent.py score ./my-agent           # 质量评分（目标≥80分）
```

**完成标准**：验证0错误 + 测试0失败 + 评分≥80

### 阶段3：打包 + 发布

```bash
agent.py docs ./my-project          # 生成文档（含AGENTS.md）
agent.py package ./my-agent         # 打包发布
```

### 其他命令

| 我想做什么 | 运行什么命令 |
|-----------|-------------|
| 创建标准Agent | `agent.py init my-agent` |
| 验证Agent配置 | `agent.py validate ./my-agent` |
| 生成AGENTS.md | `agent.py agents-md ./my-project` |
| Agent→Skill | `agent.py to-skill ./my-agent` |
| Agent→Plugin | `agent.py to-plugin ./my-agent` |
| 测试Agent能力 | `agent.py test ./my-agent` |
| 质量评分 | `agent.py score ./my-agent` |
| 安全审计 | `agent.py security-audit ./my-agent` |
| 版本快照 | `agent.py snapshot ./my-agent` |
| 性能基准 | `agent.py benchmark ./my-agent` |
| 调试Agent | `agent.py debug ./my-agent` |
| 可视化架构 | `agent.py visualize ./my-agent` |
| A/B测试 | `agent.py ab-test ./agent-a ./agent-b` |

---

## 四、Agent五大核心能力

基于中国国标 GB/Z 185-2026 和行业共识，每个 Agent 必须具备：

```
┌─────────────────────────────────────────┐
│           Agent 五大核心能力            │
├─────────────────────────────────────────┤
│ 1. 感知（Perception）                   │
│    理解用户输入、感知环境状态            │
├─────────────────────────────────────────┤
│ 2. 记忆（Memory）                       │
│    短期记忆（对话）+ 长期记忆（知识）    │
├─────────────────────────────────────────┤
│ 3. 规划（Planning）                     │
│    分解任务、制定步骤、选择策略          │
├─────────────────────────────────────────┤
│ 4. 决策（Decision）                     │
│    选择工具、决定行动、处理异常          │
├─────────────────────────────────────────┤
│ 5. 执行（Execution）                    │
│    调用工具、完成任务、返回结果          │
└─────────────────────────────────────────┘
```

**可选能力**：反思（Reflection）—— 评估结果、总结经验、自我改进

---

## 五、工作流模式（7种）

| 模式 | 核心思想 | 适用场景 | 复杂度 |
|------|---------|---------|--------|
| **ReAct** | 思考→行动→观察，循环 | 探索性任务、路径不明确 | ⭐ |
| **Plan-and-Execute** | 先规划完整计划，再执行 | 复杂多步骤任务、结构化分析 | ⭐⭐ |
| **Reflection** | 执行后反思，自我改进 | 需要持续优化的复杂任务 | ⭐⭐⭐ |
| **Tree-of-Thoughts** | 多路径探索，选择最优 | 需要创造性思维的任务 | ⭐⭐⭐ |
| **Self-Consistency** | 多次采样，投票选择 | 需要高准确性的任务 | ⭐⭐ |
| **Chain-of-Thought** | 逐步推理，链式思考 | 需要逻辑推理的任务 | ⭐ |
| **Tool-Use** | 工具调用优先 | 需要大量工具调用的任务 | ⭐ |

**决策树（选择合适的工作流模式）**：
```
任务是否需要大量工具调用？
  ├─ 是 → Tool-Use模式
  └─ 否 → 任务是否需要创造性思维？
       ├─ 是 → Tree-of-Thoughts模式
       └─ 否 → 任务是否需要高准确性？
            ├─ 是 → Self-Consistency模式
            └─ 否 → 任务是否需要逻辑推理？
                 ├─ 是 → Chain-of-Thought模式
                 └─ 否 → 任务是否复杂多步骤？
                      ├─ 是 → Plan-and-Execute模式
                      └─ 否 → 任务是否探索性？
                           ├─ 是 → ReAct模式
                           └─ 否 → 需要持续优化？
                                ├─ 是 → Reflection模式
                                └─ 否 → ReAct模式（默认）
```

---

## 六、Agent路由策略配置

Agent虽然不是Skill，但可以有**路由策略配置**（决定如何处理不同类型的用户输入）：

```json
"routing": {
  "enabled": true,
  "strategy": "hybrid",
  "entry_point": "main",
  "ambiguity_handling": "ask",
  "route_line_output": true,
  "modes": [
    {
      "name": "direct_answer",
      "trigger": "简单问题/闲聊/确认",
      "action": "直接回答，不调用工具"
    },
    {
      "name": "tool_execution",
      "trigger": "需要查询/计算/操作",
      "action": "调用对应Skill/MCP工具"
    },
    {
      "name": "task_planning",
      "trigger": "复杂多步骤任务",
      "action": "先规划完整计划，再逐步执行"
    },
    {
      "name": "clarification",
      "trigger": "需求不明确/信息不足",
      "action": "先问澄清问题，不要猜测"
    }
  ]
}
```

**字段说明**：
- `strategy`：路由策略（direct直接回答/tool_first优先工具/plan_first优先规划/hybrid混合，根据输入自动选择）
- `entry_point`：工作流入口（默认"main"）
- `ambiguity_handling`：模糊请求处理（ask主动询问/clarify给出选项/guess最佳猜测）
- `route_line_output`：是否输出路由行（用于可观测性，让用户看到Agent选择了什么路由模式）
- `modes`：4种路由模式（direct_answer/tool_execution/task_planning/clarification）

---

## 七、脚本职责清单

| 脚本 | 职责 | 调用方 |
|------|------|--------|
| **agent.py** | 统一入口（init/validate/test/score/package/to-skill/to-plugin） | LLM直接调用 |
| **init_agent.py** | Agent脚手架生成（agent.json+目录结构+模板） | agent.py调用 |
| **generate_agent_config.py** | agent.json配置生成（结构化定义所有属性） | init_agent调用 |
| **generate_agents_md.py** | AGENTS.md生成（项目级配置） | agent.py调用 |
| **validate_agent.py** | Agent配置验证（完整性/合法性/一致性） | agent.py调用 |
| **test_agent.py** | 完整Agent测试（配置+能力+质量） | agent.py调用 |
| **score_agent.py** | Agent质量评分（多维度评分） | agent.py调用 |
| **package_agent.py** | Agent打包发布（zip+校验+版本管理） | agent.py调用 |
| **to_skill.py** | Agent→Skill转化（简单Agent转化为Skill） | agent.py调用 |
| **to_plugin.py** | Agent→Plugin转化（复杂Agent转化为Plugin） | agent.py调用 |
| **workflow_orchestrator.py** | 工作流编排（7种模式模板+步骤生成） | init_agent调用 |
| **persona_designer.py** | 角色设计器（10种预设角色+自定义角色） | init_agent调用 |
| **memory_configurator.py** | 记忆配置器（短期/长期/上下文窗口/压缩策略） | init_agent调用 |
| **boundary_manager.py** | 边界管理器（Always/Ask First/Never三分类） | init_agent调用 |
| **runtime_guard.py** | 运行时保障（track/verify/gate/route） | LLM直接调用 |
| **security_audit.py** | Agent安全审计（7维度安全检查） | agent.py调用 |
| **version_manager.py** | Agent版本管理（快照/diff/回滚） | agent.py调用 |
| **benchmark.py** | Agent性能基准（标准化性能测试） | agent.py调用 |
| **debugger.py** | Agent调试工具（单步调试/断点/日志） | agent.py调用 |
| **visualize.py** | 多Agent可视化（Mermaid/ASCII架构图） | agent.py调用 |
| **ab_test.py** | Agent A/B测试（配置对比测试） | agent.py调用 |
| **self_evolution.py** | Agent自进化（反馈驱动优化） | agent.py调用 |

---

## 八、底座复用策略

### 与agent-plugin-creator的关系

| 维度 | agent-plugin-creator（底座） | agent-creator（编排器） |
|------|------------------------------|------------------------|
| **核心职责** | 创建构建块（Skill和MCP） | 将构建块组合成完整Agent |
| **创建的产物** | Skill/MCP/Plugin | Agent（中立格式） |
| **复用的脚本** | - | init_skill.py/create_mcp_server.py/validate_plugin.py/audit_plugin.py/package_plugin.py |
| **复用的模板** | - | skill_template.py（中英文SKILL.md模板） |
| **复用的文档** | - | 渐进式披露索引/触发路由方法论/Gotchas |
| **新增的能力** | - | Agent身份定义/工作流编排/记忆配置/边界设置/AGENTS.md生成/Agent验证测试 |

**复用原则**：
1. 凡是底座已经有的能力，必须复用，不重复造轮子
2. 新增的能力必须是Agent编排特有的，不是底座已经有的
3. 复用底座的脚本时，通过import调用，不复制代码
4. 复用底座的模板时，通过模板生成器调用，不复制模板内容

---

## 九、Gotchas（Agent编排型特有）

### 坑1：单一职责模糊，什么都想做
- **症状**：Agent创建技能既创建Skill，又创建MCP，还创建Agent，职责混乱
- **修正**：明确单一职责（Agent编排器只做编排，创建构建块复用底座），与底座的职责边界要清晰
- **原因**：早期想把所有功能都放进一个技能，导致职责混乱，用户不知道该用哪个

### 坑2：Agent配置不完整，缺身份/工作流/记忆/边界
- **症状**：用户创建的Agent，agent.json只有name和description，缺少身份/工作流/记忆/边界等核心配置
- **修正**：init_agent.py生成的agent.json必须包含完整的配置结构（identity/capabilities/workflow/routing/memory/boundaries/evaluation），validate_agent.py检查完整性
- **原因**：早期模板只有基本字段，用户不知道需要配置什么

### 坑3：工作流模式选错，简单任务用复杂模式
- **症状**：简单问答任务用了Plan-and-Execute，效率低下；复杂研究任务用了ReAct，质量不高
- **修正**：提供决策树帮助用户选择工作流模式（7种模式+适用场景+决策树），persona_designer.py根据角色推荐工作流
- **原因**：用户不了解不同工作流模式的适用场景，随意选择

### 坑4：底座复用不足，重复造轮子
- **症状**：Agent创建技能重新实现了Skill创建和MCP创建，大量重复代码
- **修正**：明确底座复用策略，凡是底座已经有的能力必须复用（init_skill.py/create_mcp_server.py/validate_plugin.py等），通过import调用
- **原因**：早期不知道底座有这些能力，或者觉得复用麻烦，就重新实现了

### 坑5：Agent→Skill/Plugin转化丢失配置
- **症状**：Agent转化为Skill或Plugin后，身份/工作流/记忆/边界等配置丢失，转化后的Skill质量不高
- **修正**：to_skill.py和to_plugin.py必须完整映射Agent配置到Skill/Plugin配置，转化后自动验证配置完整性
- **原因**：早期转化脚本只复制基本字段，忽略了高级配置

### 坑6：验证门禁形同虚设，不通过也能发布
- **症状**：validate_agent.py只做语法检查，不做内容检查，Agent配置不完整也能通过验证
- **修正**：validate_agent.py必须检查agent.json的完整性（identity/capabilities/workflow/routing/memory/boundaries/evaluation），缺字段就报错；三级门禁（配置验证+能力测试+质量评分）必须全部通过才能发布
- **原因**：早期验证脚本只做语法检查，认为内容检查是LLM的事

### 坑7：多Agent协作设计混乱
- **症状**：多Agent系统中，Agent之间的职责划分不清，通信协议不统一，协作效率低下
- **修正**：提供多Agent协作设计指南（5种协作模式：主从/对等/流水线/黑板/委员会），visualize.py生成架构图，ab_test.py对比不同协作模式
- **原因**：早期只关注单Agent设计，忽略了多Agent协作的复杂性

---

## 十、检查清单

### 创建时

- [ ] 单一职责定义（明确"做什么"和"不做什么"，与底座的职责边界清晰）
- [ ] 底座复用策略（复用底座的脚本/模板/文档，不重复造轮子）
- [ ] 统一入口（agent.py，init/validate/test/score/package/to-skill/to-plugin）
- [ ] Agent脚手架生成（init_agent.py，agent.json+目录结构+模板）
- [ ] agent.json配置结构化（identity/capabilities/workflow/routing/memory/boundaries/evaluation）
- [ ] AGENTS.md生成（generate_agents_md.py，项目级配置）
- [ ] 工作流模板化（7种模式模板+决策树）
- [ ] 角色设计器（10种预设角色+自定义角色）
- [ ] 记忆配置器（短期/长期/上下文窗口/压缩策略）
- [ ] 边界管理器（Always/Ask First/Never三分类）
- [ ] Agent路由策略配置（strategy/entry_point/ambiguity_handling/route_line_output/modes）
- [ ] 验证测试三级门禁（配置验证+能力测试+质量评分，全部通过才能发布）
- [ ] Agent→Skill/Plugin转化（完整映射配置，转化后自动验证）
- [ ] runtime_guard（track/verify/gate/route）
- [ ] 安全审计（7维度安全检查）
- [ ] 版本管理（快照/diff/回滚）
- [ ] 性能基准（标准化性能测试）
- [ ] 调试工具（单步调试/断点/日志）
- [ ] 多Agent可视化（Mermaid/ASCII架构图）
- [ ] A/B测试（配置对比测试）
- [ ] Agent自进化（反馈驱动优化）
- [ ] references包含：架构指南/决策树/角色设计/工作流模板/记忆系统/多Agent协作/性能监控/AGENTS.md指南/评估框架/职责边界/实测记录/故障排除
- [ ] templates包含：agent.json模板/AGENTS.md模板/角色模板
- [ ] examples包含：简单助手/研究Agent/编程Agent
- [ ] 触发路由结构化（技能名+模式+分类+布尔值+reason）
- [ ] 渐进式披露四层（L1/L2/L3/L4）

### 优化时

- [ ] 检查单一职责是否清晰（与底座的职责边界是否明确）
- [ ] 检查底座复用是否充分（是否有重复造轮子）
- [ ] 检查agent.json配置是否完整（identity/capabilities/workflow/routing/memory/boundaries/evaluation）
- [ ] 检查validate_agent.py的检查项是否完整
- [ ] 检查三级门禁是否有效（配置验证+能力测试+质量评分）
- [ ] 检查Agent→Skill/Plugin转化是否完整映射配置
- [ ] 端到端实测：创建一个Agent，验证配置完整性
- [ ] 端到端实测：Agent→Skill转化，验证转化后质量
- [ ] 端到端实测：Agent→Plugin转化，验证转化后质量
- [ ] 规范校验（create_skill.py optimize）
- [ ] 深度审计（36项检查清单）

---

## 十一、实战参考

- **agent-creator**：Agent开发与编排技能，完整实现了本模板的所有设计
  - 单一职责：专注Agent全生命周期管理，创建构建块复用底座agent-plugin-creator
  - 底座复用：init_skill.py/create_mcp_server.py/validate_plugin.py/audit_plugin.py/package_plugin.py
  - Agent配置结构化：agent.json包含identity/capabilities/workflow/routing/memory/boundaries/evaluation
  - 工作流模板化：7种模式（react/plan-and-execute/reflection/tree-of-thoughts/self-consistency/chain-of-thought/tool-use）
  - 验证测试三级门禁：配置验证（validate）+能力测试（test）+质量评分（score，≥80分）
  - Agent路由策略：routing配置块（strategy/entry_point/ambiguity_handling/route_line_output/4种modes）
  - 触发路由：`🔀 路由: agent-creator · ROUTE class=...; agent=...; skill=...; mcp=...; reason=...`
  - runtime_guard：route命令（路由行记录+格式校验）

---

## 版本

- v1.0.0（2026-09-28）：初始版本，基于agent-creator实战经验沉淀
