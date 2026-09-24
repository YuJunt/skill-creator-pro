# skill-creator-pro 使用指南

> 详细的使用指南，帮助你充分利用skill-creator-pro的所有功能。

---

## 目录

1. [快速开始](#1-快速开始)
2. [5种模式详解](#2-5种模式详解)
3. [3种设计哲学](#3-3种设计哲学)
4. [核心脚本用法](#4-核心脚本用法)
5. [36项检查清单](#5-36项检查清单)
6. [渐进式披露最佳实践](#6-渐进式披露最佳实践)
7. [触发路由设计](#7-触发路由设计)
8. [常见问题](#8-常见问题)
9. [示例技能](#9-示例技能)

---

## 1. 快速开始

### 创建新技能
```bash
cd /path/to/workspace/.user_skills
python3 skill-creator-pro/scripts/init_skill_pro.py my-skill --path . --philosophy mixed
# 编辑 my-skill/SKILL.md 和 references/
python3 skill-creator-pro/scripts/create_skill.py optimize my-skill
```

### 优化现有技能
```bash
python3 skill-creator-pro/scripts/create_skill.py optimize /path/to/your-skill
```

### 评审技能
```bash
python3 skill-creator-pro/scripts/create_skill.py review /path/to/your-skill
```

### 测试技能
```bash
python3 skill-creator-pro/scripts/create_skill.py test /path/to/your-skill
```

### 迁移升级
```bash
python3 skill-creator-pro/scripts/upgrade_skill.py /path/to/your-skill --apply --backup
```

---

## 2. 5种模式详解

### create（新建技能）
从零创建新技能。流程：需求分析→架构设计→模板生成→内容编写→规范校验→深度审计。

```bash
python3 scripts/create_skill.py create <skill-name> --path <dir> --philosophy <type>
```

### optimize（优化技能）
优化现有技能。流程：状态检查→规范校验→深度审计→安全扫描→输出校验→优化报告。

```bash
python3 scripts/create_skill.py optimize <skill-path>
```

### review（深度评审）
对技能进行深度评审。流程：规范校验→深度审计→安全扫描→问题分级→改进建议→评审报告。

```bash
python3 scripts/create_skill.py review <skill-path>
```

### test（端到端测试）
对技能进行端到端测试。流程：状态检查→生成评估用例→规范校验→输出校验→测试报告。

```bash
python3 scripts/create_skill.py test <skill-path>
```

### upgrade（迁移升级）
将旧技能迁移到skill-creator-pro规范。流程：差距分析→迁移报告→应用迁移（可选）。

```bash
python3 scripts/create_skill.py upgrade <skill-path>
python3 scripts/upgrade_skill.py <skill-path> --apply --backup
```

---

## 3. 3种设计哲学

### Capability型（工具包装型）
- **适用**：操作类任务（PDF处理/图片处理/文件转换）
- **特点**：大部分逻辑脚本化，AI只负责选工具传参
- **SKILL.md重点**：工具列表/使用方法/常见坑
- **示例**：examples/pdf-processor

### Process型（方法论型）
- **适用**：分析类任务（代码审查/需求分析/方案评估）
- **特点**：固定流程和Checklist，AI按步骤执行，不允许跳步
- **SKILL.md重点**：工作流程/Checklist/输出模板
- **示例**：examples/code-reviewer

### Mixed型（混合型）
- **适用**：复杂任务（数据分析/决策支持/系统设计）
- **特点**：脚本做确定性计算，AI做分析判断
- **SKILL.md重点**：工作流程/脚本用法/分析方法论/输出模板
- **示例**：examples/data-analyzer

---

## 4. 核心脚本用法

### validate_skill.py（规范校验）
```bash
python3 scripts/validate_skill.py <skill-path> [--json]
```
检查项：frontmatter/description三要素/SKILL.md行数/渐进式披露/脚本完整性/references引用/无硬编码路径。
退出码：0=通过，1=有高优先级问题。

### audit_skill.py（深度审计）
```bash
python3 scripts/audit_skill.py <skill-path> [--json]
```
36项检查（3层分类：必备12/推荐12/卓越12），评分0-36分。
- 优秀：≥32分（89%）
- 良好：28-31分
- 合格：24-27分
- 不合格：<24分

### security_scan.py（安全扫描）
```bash
python3 scripts/security_scan.py <skill-path> [--json]
```
5类39种检测模式：注入攻击/危险代码/数据泄露/不安全操作/其他。
评分：0-100分，高风险问题直接扣分。

### output_validator.py（输出校验硬门禁）
```bash
python3 scripts/output_validator.py <skill-path> --mode <create|optimize|review|test>
```
校验项：目录结构/SKILL.md核心要素/references引用/脚本可运行性/无特定领域残留。
退出码：0=通过，1=校验失败。

### init_skill_pro.py（模板生成）
```bash
python3 scripts/init_skill_pro.py <skill-name> --path <dir> --philosophy <type>
```
生成：SKILL.md（带frontmatter和TODO）/references//scripts//assets/。

### upgrade_skill.py（迁移升级）
```bash
python3 scripts/upgrade_skill.py <skill-path> [--json] [--apply] [--backup] [--target <path>]
```
退出码：0=成功，1=目录不存在，3=运行时错误。

### package.sh（一键打包）
```bash
bash scripts/package.sh [--output <dir>] [--skip-validate] [--version <ver>]
```
功能：清理临时文件→规范校验→读取版本号→创建zip→验证完整性→打包报告。

---

## 5. 36项检查清单

### 必备层（12项，必须达标）
1. frontmatter规范 2. description三要素 3. SKILL.md<500行 4. 渐进式披露三层架构
5. 设计哲学明确 6. 单一职责 7. Gotchas驱动（≥5个） 8. 输出格式文档化
9. 确定性推入代码 10. 错误处理 11. 校验门禁 12. 端到端实测

### 推荐层（12项，建议达标）
13. 触发路由 14. 编排脚本 15. 决策树 16. 候选输出 17. 方法论知识库
18. 配置中心 19. 状态管理 20. 评估用例 21. 多模型测试 22. 自进化闭环
23. 安全考虑 24. 技能组合友好

### 卓越层（12项，专业级）
25. 预加载机制 26. 渐进式披露执行层 27. 自由度匹配 28. 示例驱动
29. 经验回流 30. 复盘机制 31. 指标监控 32. 通知推送 33. 云端持久化
34. 定时任务 35. 备份恢复 36. 贡献指南

---

## 6. 渐进式披露最佳实践

### 三层架构
| 层级 | 内容 | 加载时机 | 大小限制 |
|------|------|---------|---------|
| L1 元数据 | name+description | 始终在上下文 | ~100字 |
| L2 SKILL.md | 核心工作流+触发路由+Gotchas | 技能触发后 | <500行 |
| L3 references | 详细文档/模板/示例 | 需要时才读 | 无限制 |

### 什么时候拆分到references
- 文档超过100行
- 内容是特定场景的细节
- 内容不常用
- 内容是参考资料（API文档/Schema/政策）

### references引用规范
每个reference必须从SKILL.md引用，并说明什么时候读：
```markdown
## 渐进式披露
| 场景 | 文档 |
|------|------|
| 需要了解API细节 | references/api-docs.md |
```

### 常见错误
❌ SKILL.md写了500行，所有内容都在里面
✅ 核心工作流在SKILL.md（<300行），细节在references/

❌ references/有10个文档，但SKILL.md只字未提
✅ 每个reference都从SKILL.md引用，并说明什么时候读

---

## 7. 触发路由设计

### 什么是触发路由
触发路由是技能触发后，AI输出的第一行声明，用于：
1. 确认技能模式
2. 明确任务范围
3. 确定must_read文档

### 路由格式
```
🔀 路由: {模式}｜任务: {简述}｜原因: {一句话}
```

### 最佳实践
1. 路由要求放在SKILL.md最顶部（frontmatter后第一行），用醒目标记
2. 格式简化（降低AI输出成本）
3. 预加载说明强化："触发后先输出路由行"
4. 路由表只做参考

### 固有局限
触发路由是LLM软约束，无法100%保证出现。已通过顶部醒目位置+简化格式+预加载强化最大化遵守率。

---

## 8. 常见问题

### Q: skill-creator-pro和平台自带的skill-creator-for-work有什么区别？
A: skill-creator-pro是专业版，支持5种模式（创建/优化/评审/测试/升级）、36项深度审计、5类39种安全扫描、3种设计哲学、示例库、pytest测试套件、CI/CD配置。平台自带的是基础创建指南，只有1种创建模式。

### Q: 如何选择设计哲学？
A: 操作类任务选Capability型，分析类任务选Process型，复杂任务选Mixed型。不确定时选Mixed型。

### Q: SKILL.md超过500行怎么办？
A: 识别核心工作流（保留在SKILL.md），细节移到references/，在SKILL.md中添加引用表。目标：SKILL.md < 300行。

### Q: 如何验证技能质量？
A: 运行4个校验脚本：validate_skill.py（规范）+ audit_skill.py（审计，目标≥32分）+ security_scan.py（安全，目标0高风险）+ output_validator.py（输出）。

### Q: 支持哪些Python版本？
A: Python 3.7+（因为使用了dataclasses）。已在3.7-3.12上测试。

### Q: 支持Windows/macOS吗？
A: 所有Python脚本跨平台。package.sh需要bash环境（Windows上用Git Bash或WSL）。

---

## 9. 示例技能

参见examples/README.md，包含3个完整示例：
1. pdf-processor（Capability型）：7种PDF操作
2. code-reviewer（Process型）：5维度30+项Checklist
3. data-analyzer（Mixed型）：脚本做指标计算，AI做归因分析

---

## 版本

- v1.0.0：初始版本，完整使用指南
