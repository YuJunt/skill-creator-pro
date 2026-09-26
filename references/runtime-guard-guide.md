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

## 四、为什么这不是"增加复杂度"

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
