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

### 18. description_optimizer.py（自动描述改进+优化循环）

**子命令**：

| 子命令 | 用途 | 关键参数 |
|--------|------|---------|
| `optimize` | 单次描述优化 | `skill_path`（必填） |
| `diagnose` | 触发问题诊断 | `skill_path`、`--json` |
| `run-loop` | 描述优化自动循环（对齐官方skill-creator） | `skill_path`、`--eval-set`、`--max-iterations`、`--num-candidates`、`--apply`、`--json` |

**常用命令**：

```bash
# 单次描述优化
python3 scripts/description_optimizer.py optimize <skill_dir>

# 触发问题诊断
python3 scripts/description_optimizer.py diagnose <skill-path> --json

# 描述优化自动循环（核心功能，对齐官方skill-creator的run_loop）
python3 scripts/description_optimizer.py run-loop <skill-path> \
  --eval-set evals/trigger-evals.json \  # 触发测试用例集（JSON数组，含query和should_trigger）
  --max-iterations 5 \                    # 最大迭代次数（默认5）
  --num-candidates 5 \                    # 每轮候选description数量（默认5）
  --apply                                  # 自动应用最佳description到SKILL.md

# 简化版（不指定eval-set，基于规则评估）
python3 scripts/description_optimizer.py run-loop <skill-path> --max-iterations 3
```

**run-loop核心流程**：
1. 加载eval set，**60%训练+40%测试**分割（防过拟合）
2. 评估当前description（训练集+测试集）
3. 迭代：生成5个候选→训练集评估→top3测试集验证→**用测试集分数选择最佳**
4. 最多5次迭代，连续2轮无提升提前停止
5. 输出迭代报告和最佳description，`--apply`自动应用

**检查维度**：三要素（What/When/Differentiator）/ 长度 / 触发词 / 不适用于 / 触发率模拟

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

### 20.5. blind_compare.py（盲比较·Blind A/B Comparison）

**用途**：严格比较两个版本的技能，用户不知道哪个是新版，**避免确认偏误**。对齐Anthropic官方skill-creator的comparator agent设计。

**子命令**：

| 子命令 | 用途 | 关键参数 |
|--------|------|---------|
| `compare` | 生成盲比较报告（随机打乱顺序，不标注哪个是新版） | `skill_a`、`skill_b` |
| `reveal` | 揭示答案并统计偏好 | `result_file`、`--prefer X/Y/tie` |
| `report` | 查看完整盲比较报告 | `result_file` |

**常用命令**：

```bash
# 第1步：生成盲比较报告（输出为"技能X"和"技能Y"，不标注哪个是新版）
python3 scripts/blind_compare.py compare <skill-a-path> <skill-b-path>
# 输出：9项指标对比（规范校验/深度审计/安全扫描/基本信息），指标优势统计

# 第2步：用户基于指标客观评价后，揭示答案
python3 scripts/blind_compare.py reveal <result-json> --prefer X   # 认为技能X更好
python3 scripts/blind_compare.py reveal <result-json> --prefer Y   # 认为技能Y更好
python3 scripts/blind_compare.py reveal <result-json> --prefer tie # 认为平局

# 查看完整报告
python3 scripts/blind_compare.py report <result-json>
```

**核心设计**：
- **随机打乱顺序**：每次运行随机分配X/Y身份，用户不知道哪个是新版
- **9项指标对比**：SKILL.md行数/脚本数量/参考文档数量/规范校验高优先级/规范校验中优先级/深度审计总分/必备层达标/安全评分/安全高风险
- **自动评估**：对两个技能自动运行validate_skill+audit_skill+security_scan
- **偏好统计**：reveal时判断用户偏好是否与客观指标一致，避免确认偏误
- **结果持久化**：保存为JSON文件，包含真实身份（reveal时才揭示）

**使用场景**：
- 技能优化前后对比（v1.0 vs v2.0）
- 两种设计方案对比（capability vs process哲学）
- 两个候选技能的A/B测试
- 避免"我知道哪个是新版所以觉得它更好"的确认偏误

---

### 20.8. eval_runner.py red-team（红队测试·7领域分类）

**用途**：按OWASP LLM Top 10的7个领域组织红队测试用例，检查技能的安全防护能力。

**7个测试领域**：

| 领域 | OWASP参考 | 测试用例数 | 严重度 |
|------|----------|-----------|--------|
| 直接注入（direct_injection） | LLM01 | 4条 | 高 |
| 间接注入（indirect_injection） | LLM01 | 3条 | 中 |
| 越狱（jailbreak） | LLM06 | 4条 | 高 |
| 编码攻击（encoding_attack） | LLM01 | 3条 | 中 |
| 多轮攻击（multi_turn_attack） | LLM07 | 3条 | 中 |
| 多模态攻击（multimodal_attack） | LLM01 | 3条 | 中 |
| 工具滥用（tool_misuse） | LLM06 | 4条 | 高 |

**常用命令**：

```bash
# 运行全部7个领域的红队测试（自动检查目标技能安全防护）
python3 scripts/eval_runner.py red-team --skill-path <skill-path>

# 只测试指定领域
python3 scripts/eval_runner.py red-team --skill-path <skill-path> --domain direct_injection
python3 scripts/eval_runner.py red-team --skill-path <skill-path> --domain tool_misuse

# JSON格式输出
python3 scripts/eval_runner.py red-team --skill-path <skill-path> --json
```

**核心功能**：
- 7领域24条测试用例模板（基于OWASP LLM Top 10）
- 自动检查目标技能的安全防护（安全扫描脚本/Gotchas/危险请求拒绝机制）
- 静态检测（基于关键词的防护检查）+ 风险等级评估
- 测试用例保存到`evals/red_team_test_cases.json`，供LLM实测使用
- 通过标准：恶意请求拒绝率≥95%，误报率≤10%

---

### 20.9. skill_evolution.py curator（技能贡献度计算·Curator）

**用途**：计算每个技能的贡献度（successes/total加权评分），用于自进化时判断哪些技能值得保留/优化/移除。

**贡献度指标（加权平均）**：

| 指标 | 权重 | 说明 |
|------|------|------|
| 成功率 | 30% | 成功次数/总次数 |
| 使用频率 | 20% | 总使用次数（归一化，50次即满分） |
| 平均评分 | 25% | 用户反馈平均评分（1-5分转0-100） |
| 低失败率 | 15% | 1 - 失败率 |
| 活跃度 | 10% | 最近30天使用次数占比 |

**评级标准**：
- 优秀（≥80分）：✅ 贡献度高，建议保留并作为标杆技能
- 良好（60-79分）：🟡 贡献度良好，建议持续优化
- 一般（40-59分）：⚠️ 贡献度一般，建议重点优化或合并
- 较差（<40分）：❌ 贡献度低，建议考虑移除或彻底重构

**常用命令**：

```bash
# 自动发现所有有使用记录的技能，计算贡献度并排序
python3 scripts/skill_evolution.py curator

# 指定技能列表
python3 scripts/skill_evolution.py curator --skills skill-a skill-b skill-c

# 设置最低贡献度阈值（默认40分）
python3 scripts/skill_evolution.py curator --min-contribution 50

# JSON格式输出
python3 scripts/skill_evolution.py curator --json
```

**核心功能**：
- 5维度加权评分（成功率/使用频率/平均评分/低失败率/活跃度）
- 自动发现所有有使用记录的技能（读取~/.skill_observability/*.jsonl）
- 贡献度排行榜（按分数降序）
- 4级分类统计（优秀/良好/一般/较差）
- 自进化建议（标杆技能提取最佳实践/待优化技能重点优化/低贡献度技能建议移除）
- 报告保存到`~/.skill_observability/curator_report.json`

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

### 22.5. eval_runner.py（技能评估运行与评分）

**用途**：运行技能评估用例，验证技能在触发/选择/边界场景下的表现，并对单次运行进行自动评分。

**子命令**：

| 子命令 | 用途 | 关键参数 |
|--------|------|---------|
| `eval` | 运行评估用例 | `--type {trigger,selection,edge,all}`（默认all）、`--json` |
| `grade` | 评分单次运行 | `--expectations <path>`（期望文件）、`--auto`（自动模式）、`--output <path>` |

**常用命令**：

```bash
# 运行全部评估用例（触发+选择+边界）
python3 scripts/eval_runner.py eval --type all

# 只运行触发评估（验证技能是否在正确场景触发）
python3 scripts/eval_runner.py eval --type trigger

# 只运行边界评估（验证技能在模糊/异常输入下的表现）
python3 scripts/eval_runner.py eval --type edge --json

# 对单次运行结果进行评分
python3 scripts/eval_runner.py grade <run_dir> --expectations expectations.json --auto
```

**评估类型说明**：
- `trigger`：触发评估，验证技能是否在正确的用户输入下触发
- `selection`：选择评估，验证技能是否选择了正确的路由模式和工作流
- `edge`：边界评估，验证技能在模糊输入、异常输入、边界场景下的表现
- `all`：全部评估（默认）

---

### 22.6. multi_model_test.py（多模型跨模型鲁棒性测试）

**用途**：自动化多模型测试模板，验证技能在不同LLM模型（Claude/GPT-4/Gemini等）下的表现一致性，生成跨模型对比报告。

**子命令**：

| 子命令 | 用途 | 关键参数 |
|--------|------|---------|
| `init` | 初始化多模型测试 | `--skill-path <path>`（必填）、`--models <list>`（逗号分隔，必填） |
| `record` | 记录单模型单测试用例结果 | `--test-dir <path>`、`--model <name>`、`--case <id>`、`--triggered yes/no`、`--routed yes/no`、`--completed yes/no`、`--quality 0-100`、`--route <mode>`、`--notes <text>` |
| `report` | 生成跨模型对比报告 | 无额外参数 |
| `status` | 显示测试状态 | 无额外参数 |

**常用命令**：

```bash
# 初始化多模型测试（指定技能和测试模型列表）
python3 scripts/multi_model_test.py init --skill-path /path/to/skill --models Claude,GPT-4,Gemini

# 记录某个模型在某个测试用例上的结果
python3 scripts/multi_model_test.py record \
  --test-dir /path/to/test-dir \
  --model Claude \
  --case T1 \
  --triggered yes \
  --routed yes \
  --completed yes \
  --quality 85 \
  --route "优化技能" \
  --notes "路由正确，流程完整"

# 生成跨模型对比报告
python3 scripts/multi_model_test.py report

# 查看测试状态
python3 scripts/multi_model_test.py status
```

**记录字段说明**：
- `triggered`：技能是否被正确触发（yes/no）
- `routed`：是否输出了路由行（yes/no）
- `completed`：是否完整执行了工作流（yes/no）
- `quality`：输出质量评分（0-100）
- `route`：实际路由模式
- `notes`：备注说明

**使用场景**：
- 技能发布前的跨模型兼容性验证
- 发现特定模型下的技能表现问题
- 对比不同模型对同一技能的理解差异
- 技能优化效果的跨模型验证

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

---

## 运行时保障（runtime_guard.py 9个子命令）

> 防LLM偷懒核心机制。用法：`python3 scripts/runtime_guard.py <子命令>`

| 子命令 | 功能 |
|--------|------|
| `route` | 记录路由行（--mode --line），校验格式 |
| `track` | 记录每步执行（--step --action --type [--quality]） |
| `verify` | 提交前验证所有必需步骤是否完成 |
| `report` | 生成工具使用率报告 |
| `gate` | 交付前门禁检查（--mode，4项硬门禁） |
| `loop` | Stop Hook循环验证，不通过就继续（最多10次） |
| `budget` | 执行步骤预算检查（最大步骤数） |
| `duplicate` | 重复动作检测（连续3次相同就警告） |
| `focus` | 注意力衰减检测（检查是否跑偏） |
| `quantitative` | 定量阈值检查（最少脚本/文档/步骤数） |
| `reset` | 重置使用记录 |

> 详见 `references/anti-laziness-guide.md`

---

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 校验失败 |
| 2 | 参数错误 |
| 3 | 运行时错误 |
