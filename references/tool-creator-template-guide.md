# 工具创建型技能模板指南（Tool-Creator Skill Template）

> 适用于：插件创建/技能创建/MCP服务器创建/代码生成器等需要创建工具/脚本/模板的技能。
> 实战参考：agent-plugin-creator（插件创建技能）

---

## 一、核心特点

| 维度 | 说明 |
|------|------|
| **设计哲学** | 工具包装型（Capability）——逻辑活在脚本里，SKILL.md编码触发条件和使用说明。适合需要确定性创建/校验/打包的任务 |
| **核心挑战** | 模板质量不稳定（生成的技能缺路由/缺Gotchas）、规范校验不严格（特定领域残留）、多产物协同（Skill+MCP+Plugin） |
| **关键能力** | 模板生成（包含完整最佳实践）、规范校验（硬门禁）、多产物协同（Skill/MCP/Plugin统一创建）、渐进式披露（模板/脚本/文档按需加载） |

---

## 二、目录结构

```
my-tool-creator-skill/
├── SKILL.md                          # 核心入口（触发路由+使用说明+Gotchas）
├── scripts/
│   ├── orchestrator.py               # 编排脚本（统一入口，create/validate/package）
│   ├── init_skill.py                 # Skill脚手架生成（目录结构+SKILL.md模板+脚本模板）
│   ├── create_mcp_server.py          # MCP服务器脚手架生成（server.py+tools/配置）
│   ├── skill_template.py             # SKILL.md模板生成器（中英文模板，包含完整最佳实践）
│   ├── validate_skill.py             # Skill规范校验（frontmatter/结构/脚本/特定领域残留）
│   ├── validate_plugin.py            # Plugin规范校验（plugin.json/skills/mcp/打包）
│   ├── audit_skill.py                # Skill深度审计（36项检查清单）
│   ├── security_scan.py              # 安全扫描（硬编码凭据/危险代码/依赖漏洞）
│   ├── output_validator.py           # 输出校验（生成的SKILL.md是否包含完整路由配置）
│   ├── runtime_guard.py              # 运行时保障（track/verify/gate/route）
│   ├── package.py                    # 打包发布（zip/tar.gz+校验+版本管理）
│   ├── wizard.py                     # 交互式创建向导（一步步引导用户创建）
│   └── template_manager.py           # 模板管理（列出/查看/应用专业模板）
├── references/
│   ├── best-practices.md             # 最佳实践（官方规范+行业共识）
│   ├── skill-specification.md        # Skill规范详解（frontmatter/结构/触发/渐进式披露）
│   ├── mcp-specification.md          # MCP规范详解（server/tools/transport/安全）
│   ├── plugin-specification.md       # Plugin规范详解（plugin.json/打包/发布）
│   ├── template-design-guide.md      # 模板设计指南（如何设计高质量模板）
│   ├── validation-rules.md           # 校验规则详解（每项检查的标准和修复方法）
│   ├── gotchas-collection.md         # Gotchas集合（30个真实坑+原因分析+修正方法）
│   └── command-reference.md          # 命令参考（所有脚本的详细用法）
├── templates/
│   ├── skill/                        # Skill模板（通用/数据分析/工具创建/Agent编排）
│   │   ├── generic/                  # 通用模板
│   │   ├── data-analysis/            # 数据分析型模板
│   │   └── agent-orchestrator/       # Agent编排型模板
│   ├── mcp/                          # MCP服务器模板（python/nodejs/go）
│   └── plugin/                       # Plugin模板（含Skill+MCP的完整插件）
├── examples/
│   ├── simple-skill/                 # 简单Skill示例
│   ├── skill-with-mcp/               # 含MCP的Skill示例
│   └── complete-plugin/              # 完整Plugin示例
└── assets/
    └── (输出用资源文件)
```

---

## 三、工作流设计

### 模式1：创建Skill

```bash
# 方式1：一键创建（推荐）
python3 orchestrator.py create-skill my-skill --path . --template generic

# 方式2：交互式向导
python3 wizard.py

# 方式3：手动分步
python3 init_skill.py my-skill --path .
# 编辑SKILL.md和scripts/
python3 validate_skill.py ./my-skill
python3 audit_skill.py ./my-skill
```

**步骤**：
1. 生成脚手架（init_skill.py，目录结构+SKILL.md模板+脚本模板）
2. 填充内容（编辑SKILL.md/references/scripts，替换TODO）
3. 规范校验（validate_skill.py，frontmatter/结构/脚本/特定领域残留）
4. 深度审计（audit_skill.py，36项检查清单）
5. 安全扫描（security_scan.py，硬编码凭据/危险代码）
6. 输出校验（output_validator.py，生成的SKILL.md是否包含完整路由配置）
7. 交付前门禁（runtime_guard.py gate，检查所有步骤是否完成）

### 模式2：创建MCP服务器

```bash
python3 orchestrator.py create-mcp my-mcp --path . --language python
```

**步骤**：
1. 生成脚手架（create_mcp_server.py，server.py+tools/配置）
2. 实现工具（编辑tools/，实现具体的工具逻辑）
3. 规范校验（MCP规范检查，server/tools/transport/安全）
4. 测试运行（启动服务器，测试工具调用）
5. 打包发布（package.py，生成可分发的包）

### 模式3：创建Plugin（Skill+MCP组合）

```bash
python3 orchestrator.py create-plugin my-plugin --path . --with-skill --with-mcp
```

**步骤**：
1. 生成Plugin脚手架（目录结构+plugin.json+skills/+mcp/）
2. 创建Skill（init_skill.py，在skills/目录下）
3. 创建MCP（create_mcp_server.py，在mcp/目录下）
4. 配置plugin.json（名称/版本/描述/skills/mcp/入口）
5. 规范校验（validate_plugin.py，plugin.json/skills/mcp/打包）
6. 打包发布（package.py，生成可分发的Plugin包）

### 模式4：校验/审计/打包

```bash
# 校验
python3 orchestrator.py validate ./my-skill

# 审计
python3 orchestrator.py audit ./my-skill

# 打包
python3 orchestrator.py package ./my-skill --format zip
```

---

## 四、脚本职责清单

| 脚本 | 职责 | 调用方 |
|------|------|--------|
| **orchestrator.py** | 统一入口（create-skill/create-mcp/create-plugin/validate/audit/package） | LLM直接调用 |
| **init_skill.py** | Skill脚手架生成（目录结构+SKILL.md模板+脚本模板） | orchestrator调用 |
| **create_mcp_server.py** | MCP服务器脚手架生成（server.py+tools/配置） | orchestrator调用 |
| **skill_template.py** | SKILL.md模板生成器（中英文模板，包含完整最佳实践） | init_skill调用 |
| **validate_skill.py** | Skill规范校验（frontmatter/结构/脚本/特定领域残留） | orchestrator调用 |
| **validate_plugin.py** | Plugin规范校验（plugin.json/skills/mcp/打包） | orchestrator调用 |
| **audit_skill.py** | Skill深度审计（36项检查清单，三层分类） | orchestrator调用 |
| **security_scan.py** | 安全扫描（硬编码凭据/危险代码/依赖漏洞） | orchestrator调用 |
| **output_validator.py** | 输出校验（生成的SKILL.md是否包含完整路由配置） | orchestrator调用 |
| **runtime_guard.py** | 运行时保障（track/verify/gate/route） | LLM直接调用 |
| **package.py** | 打包发布（zip/tar.gz+校验+版本管理） | orchestrator调用 |
| **wizard.py** | 交互式创建向导（一步步引导用户创建） | LLM/用户直接调用 |
| **template_manager.py** | 模板管理（列出/查看/应用专业模板） | LLM/用户直接调用 |

---

## 五、模板设计原则

### 原则1：模板必须包含完整最佳实践

**生成的SKILL.md必须包含**：
- 触发路由配置（统一前缀+结构化字段+runtime_guard使用说明+强制执行规则）
- 渐进式披露索引（L1/L2/L3三层，明确什么时候读什么文档）
- Gotchas section（至少8个核心Gotchas，真实失败模式+修正方法）
- 工作流程与自由度（按步骤标注自由度等级🟢/🟡/🔴）
- 验证循环（执行→验证→修正，每个步骤完成后必须验证）
- 状态检查后行动（先检查状态，再决定行动）
- 输出格式（明确的交付格式模板）

**禁止**：
- 模板中只有TODO占位符，没有实际内容
- 模板中缺少触发路由配置
- 模板中缺少Gotchas section
- 模板中有特定领域残留（如业务专有名词/特定技能缩写/特定场景词汇）

### 原则2：模板分层（通用+专业）

| 模板类型 | 适用场景 | 核心特点 |
|---------|---------|---------|
| **通用模板** | 所有技能 | 触发路由+渐进式披露+Gotchas+工作流+校验 |
| **数据分析型** | 彩票/股票/数据分析 | 数据采集+指标分层+决策树+编排三段式+结算复盘 |
| **工具创建型** | 插件/技能/MCP创建 | 模板生成+规范校验+多产物协同+打包发布 |
| **Agent编排型** | Agent创建/编排 | 身份定义+工作流模板+记忆配置+边界设置+验证测试 |

### 原则3：模板可验证

**output_validator.py必须检查**：
1. 生成的SKILL.md是否包含触发路由配置（统一前缀+结构化字段）
2. 生成的SKILL.md是否包含runtime_guard使用说明
3. 生成的SKILL.md是否包含Gotchas section（至少8个）
4. 生成的SKILL.md是否包含渐进式披露索引
5. 检查模板中是否有特定领域残留（业务专有名词/特定技能缩写）

---

## 六、校验规则设计

### validate_skill.py检查项

| 检查项 | 级别 | 说明 |
|--------|------|------|
| frontmatter完整 | 高 | name/description/version必须存在 |
| description三要素 | 高 | 必须包含What做什么+When什么时候用+Trigger phrases触发词 |
| 目录结构完整 | 高 | SKILL.md/scripts/references必须存在 |
| 脚本语法正确 | 高 | 所有.py文件必须通过py_compile |
| 触发路由配置 | 高 | 必须包含`🔀 路由:`前缀+模式+结构化字段 |
| Gotchas section | 高 | 必须包含至少8个Gotchas |
| 渐进式披露 | 中 | 必须包含L1/L2/L3三层索引 |
| 特定领域残留 | 高 | 模板中不能有特定领域词汇（业务专有名词/特定技能缩写/特定场景词汇） |
| 脚本可执行 | 中 | 核心脚本必须有可执行权限 |
| 无死代码 | 低 | 脚本中不能有未使用的函数/变量 |

### output_validator.py检查项（生成的SKILL.md）

| 检查项 | 级别 | 说明 |
|--------|------|------|
| 触发路由完整 | 高 | 必须包含统一前缀+结构化字段+runtime_guard使用说明+强制执行规则 |
| 渐进式披露完整 | 高 | 必须包含L1/L2/L3三层索引 |
| Gotchas数量 | 高 | 至少8个核心Gotchas |
| 工作流完整 | 中 | 必须包含步骤+自由度标注+验证循环 |
| 输出格式 | 中 | 必须包含明确的交付格式模板 |
| 特定领域残留 | 高 | 不能有特定领域词汇 |

---

## 七、Gotchas（工具创建型特有）

### 坑1：生成的SKILL.md缺少触发路由
- **症状**：用户用模板创建的技能，SKILL.md中没有触发路由配置，LLM使用时直接跳到结论
- **修正**：skill_template.py的模板必须包含完整的触发路由配置（统一前缀+结构化字段+runtime_guard使用说明+强制执行规则），output_validator.py检查生成的SKILL.md是否包含
- **原因**：早期模板只包含基本结构，没有触发路由，用户创建的技能都没有路由

### 坑2：模板中有特定领域残留
- **症状**：模板生成的SKILL.md中有业务专有名词/特定技能缩写等特定领域词汇，被output_validator检测到
- **修正**：模板中使用通用词汇（如"编号""目标"），不使用特定领域词汇；output_validator.py检测特定领域残留
- **原因**：模板是从特定技能复制修改的，忘记清理特定领域词汇

### 坑3：规范校验只做语法检查，不做内容检查
- **症状**：validate_skill.py只检查脚本语法，不检查SKILL.md的内容（触发路由/Gotchas/渐进式披露）
- **修正**：validate_skill.py必须检查SKILL.md的内容（frontmatter/description三要素/触发路由/Gotchas/渐进式披露/特定领域残留）
- **原因**：早期校验脚本只做语法检查，认为内容检查是LLM的事，但LLM会偷懒

### 坑4：多产物协同混乱（Skill+MCP+Plugin）
- **症状**：创建Plugin时，Skill和MCP的目录结构混乱，plugin.json配置错误
- **修正**：orchestrator.py create-plugin统一生成目录结构（plugin.json+skills/+mcp/），validate_plugin.py检查plugin.json和目录结构
- **原因**：早期让用户手动创建目录结构，容易出错

### 坑5：模板质量不稳定，每次生成的都不一样
- **症状**：用同一个模板生成的SKILL.md，有时包含触发路由有时不包含，Gotchas数量不一致
- **修正**：skill_template.py使用固定的模板字符串，不使用LLM生成模板内容；模板版本化，每次更新模板都升级版本号
- **原因**：早期让LLM生成模板内容，质量不稳定

### 坑6：打包时遗漏文件
- **症状**：package.py打包时遗漏references/或scripts/中的文件，用户解压后发现缺文件
- **修正**：package.py使用清单文件（MANIFEST），明确列出需要打包的文件；打包后自动校验（解压检查文件完整性）
- **原因**：早期使用通配符打包，容易遗漏隐藏文件或空目录

### 坑7：版本管理混乱
- **症状**：模板更新后，用户不知道用的是哪个版本，旧版本的bug还在
- **修正**：每个模板都有版本号（TEMPLATE_VERSION），生成的SKILL.md中标注模板版本；template_manager.py可以查看模板版本和更新日志
- **原因**：早期模板没有版本号，更新后用户不知道

---

## 八、检查清单

### 创建时

- [ ] 有编排脚本（统一入口create/validate/package）
- [ ] Skill脚手架生成脚本（init_skill.py，目录结构+SKILL.md模板+脚本模板）
- [ ] MCP服务器脚手架生成脚本（create_mcp_server.py）
- [ ] SKILL.md模板生成器（skill_template.py，中英文模板，包含完整最佳实践）
- [ ] Skill规范校验（validate_skill.py，frontmatter/结构/脚本/特定领域残留）
- [ ] Plugin规范校验（validate_plugin.py，plugin.json/skills/mcp/打包）
- [ ] 深度审计（audit_skill.py，36项检查清单）
- [ ] 安全扫描（security_scan.py，硬编码凭据/危险代码）
- [ ] 输出校验（output_validator.py，生成的SKILL.md是否包含完整路由配置）
- [ ] runtime_guard（track/verify/gate/route）
- [ ] 打包发布（package.py，zip/tar.gz+校验+版本管理）
- [ ] 交互式向导（wizard.py，一步步引导用户创建）
- [ ] 模板管理（template_manager.py，列出/查看/应用专业模板）
- [ ] references包含：最佳实践/Skill规范/MCP规范/Plugin规范/模板设计/校验规则/Gotchas/命令参考
- [ ] templates包含：Skill模板（通用/数据分析/Agent编排）+MCP模板+Plugin模板
- [ ] examples包含：简单Skill/含MCP的Skill/完整Plugin
- [ ] 触发路由结构化（技能名+模式+分类+布尔值+reason）
- [ ] 渐进式披露四层（L1/L2/L3/L4）

### 优化时

- [ ] 检查skill_template.py的模板是否包含完整最佳实践（触发路由/渐进式披露/Gotchas/工作流）
- [ ] 检查模板中是否有特定领域残留（output_validator.py检测）
- [ ] 检查validate_skill.py的检查项是否完整（frontmatter/description/触发路由/Gotchas/渐进式披露）
- [ ] 检查output_validator.py是否检查生成的SKILL.md的完整性
- [ ] 端到端实测：用模板生成一个Skill，校验是否完整
- [ ] 端到端实测：创建一个Plugin（Skill+MCP），校验是否完整
- [ ] 规范校验（create_skill.py optimize）
- [ ] 深度审计（36项检查清单）

---

## 九、实战参考

- **agent-plugin-creator**：插件创建技能，完整实现了本模板的所有设计
  - 模板生成：skill_template.py（中英文模板，包含完整最佳实践）
  - 规范校验：validate_skill.py（frontmatter/结构/脚本/特定领域残留）
  - 多产物协同：init_skill.py+create_mcp_server.py+wizard.py
  - 渐进式披露：L1/L2/L3三层，明确什么时候读什么文档
  - 触发路由：`🔀 路由: agent-plugin-creator · ROUTE class=...; plugin=...; skill=...; mcp=...; reason=...`
  - runtime_guard：route命令（路由行记录+格式校验）

---

## 版本

- v1.0.0（2026-09-28）：初始版本，基于agent-plugin-creator实战经验沉淀
