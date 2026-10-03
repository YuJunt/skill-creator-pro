# 参考文档完整索引

> 本文档是skill-creator-pro所有references文档的完整索引，按主题分类。SKILL.md的L3层只保留精简说明，完整索引见本文档。

---

## L2: 触发后必读（must_read，按路由模式）

| 路由模式 | must_read（必读，按顺序） |
|---------|--------------------------|
| 🆕 新建技能 | 1. best-practices.md → 2. design-philosophies.md → 3. 36-element-checklist.md → 4. output-and-templates-guide.md |
| 🔧 优化技能 | 1. 36-element-checklist.md → 2. gotchas-collection.md → 3. best-practices.md → 4. tech-debt-management.md |
| 🔍 深度评审 | 1. 36-element-checklist.md → 2. review-and-security-guide.md → 3. best-practices.md → 4. review-and-security-guide.md（安全检查清单） |
| 🧪 端到端测试 | 1. evaluation-cases.md → 2. advanced-testing-guide.md → 3. evaluation-guide.md → 4. advanced-testing-guide.md（多模型测试） |

---

## L3: 按需加载（按主题分组）

| 主题 | 文档 | 什么时候读 |
|------|------|-----------|
| **实战经验** | battle-tested-playbooks.md | 优化/创建技能前，参考3个实战验证过的方法论 |
| **专业模板** | data-analysis-template-guide.md / tool-creator-template-guide.md / agent-orchestrator-template-guide.md | 创建特定类型技能时，参考对应专业模板 |
| **架构设计** | architecture-patterns.md | 设计技能架构，需要模式参考时 |
| **防LLM偷懒** | anti-laziness-guide.md | 技能需要防偷懒机制时（track/verify/gate/loop等9个子命令） |
| **预加载设计** | performance-optimization-guide.md | 设计预加载机制时 |
| **自进化闭环** | self-evolution-guide.md | 技能需要经验库和自进化时 |
| **Prompt Caching** | performance-optimization-guide.md | 优化技能结构降低成本时 |
| **MCP集成** | mcp-integration-guide.md | 技能需要MCP集成时 |
| **需求发现** | requirement-discovery-guide.md | 用户需求不明确，需要主动发现时 |
| **自由度匹配** | degrees-of-freedom.md | 根据任务脆弱性调整指令严格程度时 |
| **技能组合** | skill-composition.md | 多技能组合，一技能一职责时 |
| **快速上手/FAQ** | quick-start.md / examples/ | 新用户快速上手或查常见问题时 |
| **命令参考** | command-reference.md | 需要查脚本详细用法时 |
| **退出码** | command-reference.md | 需要查脚本退出码含义时 |
| **评估体系** | evaluation-guide.md / evaluation-cases.md / eval-grader-design.md | 设计评估用例和评估体系时 |
| **测试指南** | advanced-testing-guide.md / e2e-testing-playbook.md | 设计端到端测试和多模型测试时 |
| **自进化** | self-evolution-playbook.md / experience-library-guide.md | 设计经验库和自进化闭环时 |
| **技术债管理** | tech-debt-management.md | 管理技术债和优化优先级时 |
| **评审流程** | review-and-security-guide.md | 设计7维度评审流程和安全检查时 |

---

## L4: 脚本自动完成 + assets资源 + 官方权威资源

- 规范校验/深度审计/模板生成——全部脚本做
- assets/存放输出用资源文件
- official/内置官方skill-creator-for-work作为只读权威参考

---

## 版本

- v1.0.0：初始版本，完整文档索引
- 2026-09-28
