# 命令参考手册（Command Reference）

> skill-creator-pro 所有脚本的完整用法参考。按类别分组，按需查阅。

---

## 一、核心编排脚本（5个）

### 1. create_skill.py（主入口，5种模式）

```bash
# 新建技能
python3 scripts/create_skill.py create <name> --path <dir> --philosophy mixed

# 优化校验（规范+审计+安全扫描）
python3 scripts/create_skill.py optimize <skill-path>

# 深度评审
python3 scripts/create_skill.py review <skill-path>

# 端到端测试
python3 scripts/create_skill.py test <skill-path>

# 迁移升级
python3 scripts/create_skill.py upgrade <skill-path> --apply
```

**设计哲学选项**：`capability`（工具包装型）/ `process`（方法论型）/ `mixed`（混合型，推荐）

---

### 2. init_skill_pro.py（模板生成）

```bash
python3 scripts/init_skill_pro.py <skill-name> --path <output-dir> --philosophy mixed
```

生成完整目录结构：`SKILL.md` + `scripts/` + `references/` + `examples/` + `assets/`

---

### 3. validate_skill.py（规范校验）

```bash
python3 scripts/validate_skill.py <skill-path>
python3 scripts/validate_skill.py <skill-path> --json  # JSON格式输出
```

检查项：frontmatter规范 / description三要素 / SKILL.md行数 / 渐进式披露 / 文件引用深度 / 无时间敏感信息 / 术语一致 / 示例具体

---

### 4. audit_skill.py（深度审计，36项）

```bash
python3 scripts/audit_skill.py <skill-path>
python3 scripts/audit_skill.py <skill-path> --json  # JSON格式输出
```

三层分类：必备层(20项×2) / 推荐层(10项×1) / 可选层(6项×0.5)

---

### 5. output_validator.py（输出校验硬门禁）

```bash
python3 scripts/output_validator.py <skill-path> --mode optimize
```

模式选项：`create` / `optimize` / `review` / `test`

---

## 二、安全扫描脚本（3个）

### 6. security_scan.py（安全扫描）

```bash
python3 scripts/security_scan.py <skill-path>
python3 scripts/security_scan.py <skill-path> --fail-on high  # 高风险就退出
```

检测：提示注入 / 危险代码 / 数据泄露 / 隐藏指令 / os.system() / 缺try-except

---

### 7. supply_chain_scan.py（供应链扫描）

```bash
python3 scripts/supply_chain_scan.py <skill-path>
python3 scripts/supply_chain_scan.py <skill-path> --generate-sbom  # 生成SBOM
```

检测：依赖漏洞 / 许可证合规 / 生成CycloneDX 1.4格式SBOM

---

### 8. release_audit.py（发布前审计，8大门禁）

```bash
python3 scripts/release_audit.py --skill <skill-path>
python3 scripts/release_audit.py --skill <skill-path> --skip-tests  # 跳过测试
```

8大门禁：规范校验 / 深度审计 / 安全扫描 / 供应链扫描 / 输出校验 / 自动化测试 / 打包验证 / 文档完整性

---

## 三、评估工具脚本（9个）

### 9. run_eval.py（触发/选择/边界评估）

```bash
python3 scripts/run_eval.py --type all
python3 scripts/run_eval.py --type trigger  # 只测触发
python3 scripts/run_eval.py --type selection  # 只测模式选择
python3 scripts/run_eval.py --type edge  # 只测边界
```

---

### 10. executor.py（评估流程编排）

```bash
python3 scripts/executor.py init <skill_dir>  # 初始化工作空间
python3 scripts/executor.py prompts <skill_dir>  # 生成测试提示
python3 scripts/executor.py collect <run_dir> <output_dir>  # 收集结果
python3 scripts/executor.py grade <run_dir>  # 评分
python3 scripts/executor.py compare <run_a> <run_b>  # 比较
python3 scripts/executor.py analyze <benchmark_dir>  # 分析
python3 scripts/executor.py full <skill_dir>  # 完整流程
```

---

### 11. grader.py（自动评分）

```bash
python3 scripts/grader.py <run_dir>
python3 scripts/grader.py <run_dir> --auto  # 自动评分
python3 scripts/grader.py <run_dir> --expectations <json>  # 指定断言
```

支持断言类型：`contains` / `file_exists` / `file_not_empty` / `not_contains`

---

### 12. comparator.py（盲A/B比较）

```bash
python3 scripts/comparator.py <run_a> <run_b>
python3 scripts/comparator.py <run_a> <run_b> --criteria "通过率,对话长度,完成度"
```

三维度比较：通过率 / 对话长度 / 完成度

---

### 13. analyzer.py（基准分析）

```bash
python3 scripts/analyzer.py <benchmark_dir>
python3 scripts/analyzer.py <benchmark_dir> --mode posthoc  # 事后分析
```

检测：总是通过的断言（非歧视性）/ 总是失败的断言 / 高方差断言（可能不稳定）

---

### 14. eval_framework.py（8层评估框架）

```bash
python3 scripts/eval_framework.py <run_dir>
python3 scripts/eval_framework.py <run_dir> --detailed  # 详细输出
```

8层：routing / deterministic_contract / trajectory / final_state / semantic_quality / reliability / cost / security

---

### 15. aggregate_benchmark.py（基准聚合）

```bash
python3 scripts/aggregate_benchmark.py <iteration_dir> --skill-name <name>
python3 scripts/aggregate_benchmark.py <iteration_dir> --skill-name <name> --previous <prev_iteration>
```

输出：`benchmark.json` + `benchmark.md`，包含pass_rate/time/tokens的mean±stddev和delta

---

### 16. eval_viewer.py（交互式HTML审核界面）

```bash
python3 scripts/eval_viewer.py <benchmark_dir>
python3 scripts/eval_viewer.py <benchmark_dir> --output report.html
```

生成HTML报告：Outputs标签页（测试用例+输出+评分）+ Benchmark标签页（统计摘要）

---

### 17. run_loop.py（描述优化自动循环）

```bash
python3 scripts/run_loop.py --eval-set <path> --skill-path <path>
python3 scripts/run_loop.py --eval-set <path> --skill-path <path> --suggest  # 只生成建议
python3 scripts/run_loop.py --eval-set <path> --skill-path <path> --max-iterations 5
```

流程：60%train/40%test分割 → 评估当前描述 → 生成改进建议 → 迭代优化 → 选最佳描述（基于test score）

---

## 四、优化工具脚本（3个）

### 18. description_optimizer.py（自动描述改进）

```bash
python3 scripts/description_optimizer.py <skill_dir>
python3 scripts/description_optimizer.py <skill_dir> --auto  # 自动改进模式
```

检查：三要素（What/When/Differentiator）/ 长度 / 触发词 / 不适用于

---

### 19. diagnose_trigger.py（触发诊断）

```bash
python3 scripts/diagnose_trigger.py <skill-path>
```

诊断：description质量 / 触发词有效性 / 误触发风险

---

### 20. upgrade_skill.py（迁移升级）

```bash
python3 scripts/upgrade_skill.py <skill-path>
python3 scripts/upgrade_skill.py <skill-path> --apply  # 应用升级
```

检查：frontmatter / description / 冗余文件 / 脚本错误处理 / 渐进式披露

---

## 五、运维工具脚本（5个）

### 21. release_audit.py（发布审计+版本管理，合并自version_manager.py）

```bash
# 发布前审计（8大门禁）
python3 scripts/release_audit.py audit --skill <skill-path>
python3 scripts/release_audit.py  # 默认执行audit

# 版本管理（原version_manager功能）
python3 scripts/release_audit.py status <skill-path>
python3 scripts/release_audit.py bump <skill-path> --type patch  # patch/minor/major
```

---

### 22. skill_evolution.py（使用统计）

```bash
python3 scripts/skill_evolution.py log <skill-name> --action create --result success
python3 scripts/skill_evolution.py report <skill-name>
python3 scripts/skill_evolution.py stats  # 所有技能统计
```

---

### 23. skill_evolution.py（反馈循环管理）

```bash
python3 scripts/skill_evolution.py init <skill_path>  # 初始化循环
python3 scripts/skill_evolution.py status <skill_path>  # 查看状态
python3 scripts/skill_evolution.py next <skill_path>  # 进入下一阶段
python3 scripts/skill_evolution.py review <skill_path> --feedback "..."  # 提交反馈
python3 scripts/skill_evolution.py history <skill_path>  # 查看历史
```

阶段：draft → test → review → improve → repeat

---

### 24. install.sh（一键安装）

```bash
bash scripts/install.sh <skill-path>
```

---

### 25. package.sh（打包发布）

```bash
bash scripts/package.sh --output <dir>
```

---

## 六、模板文件（1个）

### 26. templates.py（模板内容，被init_skill_pro.py导入）

不直接调用，由init_skill_pro.py内部使用。包含3种设计哲学的SKILL.md模板。

---

## 脚本分层说明

| 层级 | 脚本 | 使用频率 |
|------|------|---------|
| **核心层（常用）** | create_skill / init_skill_pro / validate_skill / audit_skill / output_validator | 每次都用 |
| **安全层（重要）** | security_scan / supply_chain_scan / release_audit | 发布前用 |
| **评估层（高级）** | run_eval / executor / grader / comparator / analyzer / eval_framework / aggregate_benchmark / eval_viewer / run_loop | 完整评估时用 |
| **优化层（按需）** | description_optimizer / diagnose_trigger / upgrade_skill | 特定需求时用 |
| **运维层（偶尔）** | release_audit(含版本管理) / skill_evolution(可观测性+反馈循环) / install.sh / package.sh | 运维时用 |

---

## 版本

- v1.0.0：初始版本
- 最后更新：2026-09-26

---

# 附录：退出码参考

# 退出码规范（Exit Codes）

> skill-creator-pro 所有脚本统一遵循的退出码规范，便于CI/CD集成和脚本链调用。
> 核心原则：**退出码必须可预测，调用方可以根据退出码判断失败类型并采取相应措施。**

---

## 退出码定义

| 退出码 | 名称 | 含义 | 调用方应采取的措施 |
|--------|------|------|-------------------|
| **0** | SUCCESS | 执行成功 | 继续后续步骤 |
| **1** | VALIDATION_FAILED | 校验失败（技能不符合规范/安全扫描发现高风险/参数校验不通过） | 修复输入后重试，不要继续后续步骤 |
| **2** | ARGUMENT_ERROR | 参数错误（无效参数/缺少必填参数/参数格式错误） | 检查命令行参数，修正后重试 |
| **3** | RUNTIME_ERROR | 运行时错误（文件读写失败/网络错误/未预期异常） | 检查环境（磁盘空间/权限/网络），可能需要手动干预 |

---

## 各脚本退出码对照

| 脚本 | exit 0 | exit 1 | exit 2 | exit 3 |
|------|--------|--------|--------|--------|
| `validate_skill.py` | 规范校验通过 | 校验不通过（有高/中/低问题） | - | - |
| `audit_skill.py` | 审计完成 | 必备层未全部达标 | - | - |
| `security_scan.py` | 扫描完成（无门禁阻断） | `--fail-on`门禁触发 | - | - |
| `output_validator.py` | 输出校验通过 | 输出校验不通过 | - | - |
| `init_skill_pro.py` | 模板生成成功 | 路径/参数校验失败 | - | - |
| `upgrade_skill.py` | 迁移完成 | 技能目录不存在 | - | 差距分析/迁移执行失败 |
| `create_skill.py` | 编排执行成功 | 校验失败/RuntimeError | - | 未预期异常 |
| `templates.py` | 模板操作成功 | 校验不通过 | - | - |

> 注：`-` 表示该脚本不使用此退出码。argparse的参数错误默认exit 2，由Python标准库处理。

---

## CI/CD 集成示例

### 示例1：创建技能后自动校验

```bash
#!/bin/bash
set -e

# 1. 创建技能
python3 scripts/init_skill_pro.py my-skill --path /path/to/.user_skills --philosophy mixed

# 2. 规范校验（exit 1 = 校验失败）
python3 scripts/validate_skill.py /path/to/.user_skills/my-skill

# 3. 安全扫描（高风险时exit 1）
python3 scripts/security_scan.py /path/to/.user_skills/my-skill --fail-on high

echo "✅ 技能创建并校验通过"
```

### 示例2：在脚本链中判断失败类型

```bash
python3 scripts/create_skill.py optimize my-skill
EXIT_CODE=$?

case $EXIT_CODE in
    0) echo "✅ 优化成功" ;;
    1) echo "❌ 校验失败，请修复技能规范问题" ;;
    2) echo "❌ 参数错误，请检查命令行参数" ;;
    3) echo "❌ 运行时错误，请检查环境（磁盘/权限/网络）" ;;
    *) echo "❌ 未知错误: $EXIT_CODE" ;;
esac

exit $EXIT_CODE
```

---

## 设计原则

1. **可预测性**：相同的失败类型总是返回相同的退出码
