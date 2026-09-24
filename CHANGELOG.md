# Changelog

All notable changes to **skill-creator-pro** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-24

### 正式发布

首个稳定版本，经过多轮深度开发、实战验证和全面质量测试。

### 核心功能

- **8个确定性脚本**：覆盖技能创建全生命周期
  - `init_skill_pro.py` — 模板生成（3种设计哲学：capability/process/mixed）
  - `validate_skill.py` — 规范校验（5大检查项，静态质量门）
  - `audit_skill.py` — 深度审计（36项三层分类评分，必备层/推荐层/可选层）
  - `security_scan.py` — 安全扫描（5大类39种检测模式，提示注入/危险代码/数据泄露/隐藏指令）
  - `output_validator.py` — 输出校验（硬门禁，拦截不合格输出）
  - `upgrade_skill.py` — 迁移升级（差距分析+自动迁移+备份）
  - `create_skill.py` — 编排脚本（5种模式统一入口：create/optimize/review/test/upgrade）
  - `templates.py` — 模板库（13个模板）

- **23个references文档**：全部被SKILL.md引用，无孤立文档
  - 36项检查清单、架构设计模式、最佳实践、自由度匹配、设计哲学
  - 端到端测试手册、评估方法指南、评估用例模板、评估驱动开发
  - 经验库建设、自进化闭环手册、技术债管理、常见坑集合
  - 防LLM偷懒指南、预加载设计、触发路由测试用例、安全审计清单
  - 技能组合编排、输出格式模板、模板填充指南、快速开始、FAQ、评审流程

### 设计特性

- **渐进式披露三层架构**：L1元数据（name+description）→ L2 SKILL.md（<300行）→ L3 references（按需加载）
- **触发路由**：4种模式路由表，任何输出前必须先输出路由行
- **预加载机制**：触发后自动加载关键信息，防止LLM偷懒
- **防LLM偷懒**：硬门禁+校验脚本+强制执行规则，不允许跳步
- **零第三方依赖**：全部Python标准库，用户无需pip install
- **跨平台兼容**：77处os.path.join，无硬编码路径分隔符
- **管道友好**：--json输出可被jq/python管道解析，grep可过滤

### 质量验证

- 规范校验：高=0 中=0 低=0
- 深度审计：36/36（100%），优秀
- 安全扫描：0高风险
- 边界测试：8个用例全部通过（空目录/不存在/超大2万行/特殊字符/损坏脚本/重复运行×5）
- 模式覆盖：5种模式×3种哲学全部通过
- 端到端实测：4个完整流程全部通过（创建流程/安全扫描/迁移升级/输出校验）
- 性能：50个脚本扫描<0.1秒

### 已知限制

- 仅在Linux平台验证，Windows/macOS未测试
- 无自动化测试套件（pytest），回归靠手动测试
- 无CI/CD配置

---

## [Unreleased]

### 计划中

- pytest自动化测试套件
- GitHub Actions CI/CD
- Windows/macOS兼容性测试
- 贡献指南（CONTRIBUTING.md）
