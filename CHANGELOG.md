# Changelog

All notable changes to skill-creator-pro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.1.0] - 2026-09-26

### Added
- 设计哲学选择（Capability工具包装/Process方法论/Mixed混合型）
- 自由度标注（高/中/低自由度，脆弱步骤严格，灵活步骤宽松）
- 验证循环（执行→验证→修正闭环）
- must_read机制（路由确定后强制加载对应文档）
- 技能组合说明（可组合/不适合）
- 36项检查清单（必备层20项+推荐层10项+可选层6项）
- 触发路由（5种模式：拒绝/新建/优化/评审/测试）
- 编排脚本create_skill.py（统一入口，禁止直接调用单个脚本）
- 运行时保障runtime_guard.py（track/verify/gate/loop等9个子命令）
- 安全扫描security_scan.py（硬编码凭据/危险命令/提示注入检测）
- 供应链扫描supply_chain_scan.py（SBOM生成+依赖审计）
- 多模型测试multi_model_test.py（跨模型一致性测试）
- 评估框架eval_runner.py（RED-GREEN-REFACTOR流程）
- 技能进化skill_evolution.py（反馈循环+可观测性日志）
- 描述优化description_optimizer.py（触发词优化+诊断）
- 版本管理version_manager.py（semver+changelog生成）
- 发布审计release_audit.py（8大门禁，全部通过才能发布）
- 可观测性skill_observability.py（使用日志+反馈+Gotchas自动提取）
- 反馈循环feedback_loop.py（draft→test→review→improve迭代）
- 升级脚本upgrade_skill.py（旧版本技能自动升级）
- 打包脚本package.sh（可移植技能包生成）
- 安装脚本install.sh（技能安装到目标环境）
- CI/CD工作流（audit/ci/codeql/e2e/release）
- 官方参考official/（skill-creator-for-work只读权威参考）
- 26个references文档（最佳实践/方法论/Gotchas/模板指南等）

### Fixed
- MIXED模板KeyError Bug（路由格式说明花括号未转义）
- 3个缺失文档引用（battle-tested-playbooks/data-analysis-template-guide/llm-anti-laziness重复）
- self-evolution-guide.md重复引用问题
- backup目录死代码死文档清理（-21文件-228K）
- SKILL.md精简（323行→299行，L3索引移到references/index.md）

### Changed
- 路由行格式升级为结构化路由（技能名·模式·任务重点）
- 每步通过标准移到references/step-standards.md
- L3层详细索引移到references/index.md
- 渐进式披露四层架构（L1入口/L2必读/L3按需/L4脚本）

## [v2.0.0] - 2026-09-20

### Added
- 36项深度审计清单
- 输出格式校验output_validator.py
- 渐进式披露三层架构
- Gotchas section（8个核心坑）
- 触发路由机制

### Changed
- 从单脚本架构升级为编排脚本+多脚本协作
- 从文字说明升级为脚本实现的硬门禁

## [v1.0.0] - 2026-09-10

### Added
- 初始版本：技能创建基础功能
- init_skill.py模板生成
- validate_skill.py规范校验
- 基础references文档
