# 运行时保障指南（Runtime Guard）

> 核心原理：**不是靠LLM自觉遵守规则，而是在运行时监控它的行为——做没做有据可查，不完成就拒绝接受输出。**
> 基于业界最新研究（SKILL SENTRY/Runtime Assurance/Completion Verification）。

---

## 一、为什么需要运行时保障

### 1.1 纯Prompt约束的失效

| 做法 | 效果 | 为什么无效 |
|------|------|-----------|
| 写"必须做X" | ❌ 无效 | LLM可以选择不做 |
| 写"禁止做Y" | ❌ 无效 | LLM可以绕过规则 |
| 写"认真分析" | ❌ 无效 | 什么是"认真"？无法验证 |
| 写"不要偷懒" | ❌ 无效 | LLM说"我没偷懒"，你无法证明 |

**核心问题**：靠prompt约束LLM，本质上是"请求"它遵守规则，而不是"强制"它遵守规则。LLM想偷懒还是会偷懒。

### 1.2 运行时保障的原理

```
LLM执行 → 每步记录 → 完成验证 → 不完成就拒绝
     ↑                                    ↓
     └──────────── 继续执行 ←─────────────┘
```

**关键区别**：
- Prompt约束：告诉LLM"你应该做什么" → 靠它自觉
- 运行时保障：监控LLM"它实际做了什么" → 不完成就拒绝

---

## 二、三大核心功能

### 2.1 track（记录步骤/工具调用）

**作用**：记录LLM实际做了什么，有据可查。

```bash
# 记录一个脚本调用
python3 runtime_guard.py track --step "indicators.py" --action "指标计算完成" --type script

# 记录一个文档读取
python3 runtime_guard.py track --step "best-practices.md" --action "读取方法论" --type doc

# 记录一个步骤完成
python3 runtime_guard.py track --step "data_fetch" --action "数据采集完成" --type step
```

**使用时机**：
- 每调用一个脚本 → 记录一次
- 每读取一个文档 → 记录一次
- 每完成一个步骤 → 记录一次

### 2.2 verify（完成验证）

**作用**：检查所有必需步骤是否真的完成了，不完成就拒绝接受输出。

```bash
# 提交输出前，验证所有必需步骤是否完成
python3 runtime_guard.py verify --required-steps "data_fetch,indicators,decision_tree,bet_plan"
```

**输出示例**：
```json
{
  "total_required": 4,
  "completed": 1,
  "missing": ["indicators", "decision_tree", "bet_plan"],
  "passed": false,
  "message": "❌ 必需步骤未完成: ['indicators', 'decision_tree', 'bet_plan']。请继续执行后再提交。"
}
```

**使用时机**：
- 提交最终输出前，必须运行
- 返回非零退出码 = 不通过 = 不能交付

### 2.3 report（使用覆盖率报告）

**作用**：自动统计工具使用率，检测偷懒/浅用。

```bash
python3 runtime_guard.py report
```

**输出示例**：
```json
{
  "script_coverage_pct": 25.0,
  "doc_coverage_pct": 50.0,
  "unused_scripts": ["main", "orchestrator", "runtime_guard", "validator"],
  "deviations": ["⚠️ 脚本使用率仅25%，低于30%，可能存在严重偷懒"],
  "health": "🟡 可能偷懒"
}
```

**偏差检测规则**：
| 脚本使用率 | 健康状态 | 说明 |
|-----------|---------|------|
| < 20% | 🔴 严重偷懒 | 只用了不到1/5的脚本，必须警告 |
| 20-40% | 🟡 可能偷懒 | 只用了不到一半的脚本，建议检查 |
| ≥ 40% | 🟢 正常 | 使用率合理 |

---

## 三、完整工作流集成

### 3.1 标准使用流程

```
开始分析
  ↓
第1步：数据采集
  → 运行脚本 → track记录（type=script）
  → 步骤完成 → track记录（type=step）
  ↓
第2步：指标计算
  → 读取文档 → track记录（type=doc）
  → 运行脚本 → track记录（type=script）
  → 步骤完成 → track记录（type=step）
  ↓
第3步：决策分析
  → ...
  ↓
提交输出前
  → verify验证必需步骤是否全部完成
  → report查看工具使用率
  → 不通过 → 继续执行
  → 通过 → 交付
```

### 3.2 在编排脚本中集成

在orchestrator.py的每个阶段结束后，自动调用runtime_guard：

```python
# 每个阶段完成后
def stage_completed(stage_name):
    subprocess.run([
        "python3", "scripts/runtime_guard.py", "track",
        "--step", stage_name,
        "--action", f"{stage_name}阶段完成",
        "--type", "step"
    ])

# 最终交付前
def final_delivery():
    required_steps = ["init", "execute", "validate", "review"]
    result = subprocess.run([
        "python3", "scripts/runtime_guard.py", "verify",
        "--required-steps", ",".join(required_steps)
    ])
    if result.returncode != 0:
        raise Exception("必需步骤未完成，不能交付")
```

---

## 四、五大新功能（v2.0扩展）

基于最新业界研究（Ralph Loop/Attention Decay/Quantitative Thresholds），v2.0新增5个高级功能：

### 4.1 loop（Stop Hook循环验证）

**原理**：不满足完成标准就强制继续，直到满足标准或达到最大迭代次数。这是Ralph Loop模式的核心。

```bash
python3 runtime_guard.py loop --required-steps "step1,step2,step3" --max-iterations 10
```

**适用场景**：防止LLM过早放弃，必须做完所有步骤才算完成。

---

### 4.2 budget（执行步骤预算）

**原理**：给agent设定明确的安全边界，防止失控。

```bash
python3 runtime_guard.py budget --max-steps 50
```

**输出示例**：
```json
{
  "current_steps": 25,
  "max_steps": 50,
  "budget_used_pct": 50.0,
  "remaining_steps": 25,
  "over_budget": false
}
```

**适用场景**：防止无限循环，控制token支出。

---

### 4.3 duplicate（重复动作检测）

**原理**：检测是否连续重复相同动作，防止agent卡住。

```bash
python3 runtime_guard.py duplicate
```

**输出示例**：
```
🔴 重复动作警告：最近3次都是「data_fetch」
   你可能卡住了，尝试换个方法或寻求帮助
```

**适用场景**：防止agent陷入死循环，连续做同一件事。

---

### 4.4 focus（注意力衰减检测）

**原理**：长对话中LLM的注意力会逐渐衰减，跑偏做无用功。

```bash
python3 runtime_guard.py focus
```

**输出示例**：
```
🔴 注意力衰减警告：已执行很多动作，但关键步骤完成很少
   总动作数: 25
   完成步骤数: 2
   建议：重新读取计划文件（plan.md），确认方向是否正确
```

**适用场景**：长对话中防止跑偏，定期检查是否还在任务范围内。

---

### 4.5 quantitative（定量阈值检查）

**原理**：设置硬性最低标准，避免"差不多就行"的捷径。

```bash
python3 runtime_guard.py quantitative --min-scripts 5 --min-docs 3 --min-steps 10
```

**输出示例**：
```json
{
  "scripts_used": 2,
  "min_scripts_required": 5,
  "docs_read": 1,
  "min_docs_required": 3,
  "steps_completed": 3,
  "min_steps_required": 10,
  "issues": [
    "❌ 脚本使用不足：仅2个，最低要求5个",
    "❌ 文档阅读不足：仅1个，最低要求3个",
    "❌ 步骤完成不足：仅3步，最低要求10步"
  ],
  "passed": false
}
```

**适用场景**：防止LLM"差不多就行"，确保真的用足了技能的能力。

---

## 五、为什么这不是"增加复杂度"

**常见质疑**：又加一个脚本，不是更复杂了吗？

**回答**：是的，但它解决的是"LLM偷懒"这个根本问题。之前的所有方案（触发路由/渐进式披露/Gotchas）都是在"告诉LLM应该怎么做"，而runtime_guard是在"监控LLM实际怎么做"。

| 方案 | 层级 | 效果 |
|------|------|------|
| 触发路由 | Prompt层 | 告诉LLM"你应该选对模式" |
| 渐进式披露 | 架构层 | 告诉LLM"你应该按需读文档" |
| Gotchas | 内容层 | 告诉LLM"你应该避免这些坑" |
| **Runtime Guard** | **运行时层** | **监控LLM"你实际做了什么"** |

**这才是最后一道防线**——不管LLM怎么偷懒，它做没做都有据可查，不完成就不能交付。

---

## 版本

- v1.0.0：初始版本
- 基于：SKILL SENTRY/Runtime Assurance/Completion Verification业界最佳实践
