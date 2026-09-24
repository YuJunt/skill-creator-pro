# 预加载机制设计指南

> 基于多个技能（数据分析/内容生成/工具包装/决策支持等）多轮开发实战总结。预加载是渐进式披露的**前置环节**，决定了LLM在对话开头就知道什么、准备什么。
> 核心结论：**没有预加载的渐进式披露是不完整的——LLM不会主动加载extended/full层，必须在对话开头就告诉它本批需要什么。**

---

## 一、什么是预加载

### 1.1 定义

预加载（Preload）是指在技能触发后、正式执行任务前，**主动告诉LLM本批需要加载哪些资源、执行哪些步骤、注意哪些事项**的机制。

### 1.2 预加载 vs 渐进式披露

| 维度 | 渐进式披露 | 预加载 |
|------|-----------|--------|
| 时机 | 执行过程中按需加载 | 执行前一次性告知 |
| 主动性 | LLM主动判断需要什么 | 脚本/技能主动告诉LLM需要什么 |
| 内容 | 文档/脚本/资源 | mandatory_steps + must_read + 注意事项 |
| 问题 | LLM可能不主动加载扩展层 | 解决了"LLM不知道该加载什么"的问题 |

**关系**：预加载是渐进式披露的**触发器和导航器**。没有预加载，渐进式披露的extended/full层就是摆设。

### 1.3 为什么预加载至关重要

实战发现的核心问题：
```
问题：技能有多个功能模块，分core(基础)/extended(高级)/full(完整)三层
      但LLM永远只用core层的基础功能，extended/full层从未被加载

根因：渐进式披露只告诉LLM"有这些层"，但没告诉LLM"本批该用哪层"
      LLM倾向于用最少的token完成任务，不会主动加载更多

解决方案：create_skill.py start输出must_read，告诉LLM本批必须读哪些扩展功能文档
```

---

## 二、预加载的四层架构

### Layer 1: frontmatter description（始终加载）

**内容**：技能做什么 + 什么时候用 + 触发词

**时机**：技能未触发时就已在上下文中（~100词）

**设计要点**：
- description必须包含触发词，用引号标注
- 不要在description里写使用说明（body才加载）
- description是LLM判断是否触发的唯一信号

### Layer 2: SKILL.md body（触发后加载）

**内容**：触发路由 + Gotchas + 快速开始 + 渐进式披露索引

**时机**：技能触发后立即加载（<5000词）

**设计要点**：
- 开头必须有触发路由，任何输出前先声明模式
- Gotchas必须是具体的失败模式+修正方法
- 快速开始必须有可复制粘贴的命令
- 渐进式披露索引必须明确说明"什么时候读什么"

### Layer 3: start输出的预加载信息（执行前加载）

**内容**：mandatory_steps + must_read + candidate_outputs + 数据快照

**时机**：运行create_skill.py start后，脚本输出给LLM

**设计要点**：
- `mandatory_steps`：本批必须完成的分析步骤清单（LLM必须逐项完成）
- `must_read`：本批必须读的参考文档列表（LLM必须读）
- `candidate_outputs`：决策树生成的候选参数/候选配置/候选方案（LLM从候选中选）
- `latest_batch` + `latest_data`：最新数据快照（LLM必须引用，防止复用旧数据）

### Layer 4: references按需加载（执行中加载）

**内容**：规则文档/方法论文档/评估指南/示例

**时机**：LLM根据must_read和实际需要，主动读取

**设计要点**：
- 每个references文件必须从SKILL.md引用
- 文件引用一级深度，不嵌套
- 大文件（>100行）要有目录索引
- must_read里列出的文件，LLM必须读

---

## 三、预加载信息的输出格式

### 3.1 create_skill.py start的标准输出

```json
{
  "success": true,
  "stage": "analyzing",
  "mode": "full",
  "batch": "20260922-001",
  "latest_data": {"key": "value", "count": 42},

  "mandatory_steps": [
    "路由模式声明",
    "输入数据校验（格式/范围/异常值）",
    "数据特征分析（分布/趋势/相关性）",
    "模式判断（分类/回归/聚类概率）",
    "方法论选择（引用方法论文档具体章节）",
    "信号强度评估+置信区间",
    "矛盾信号分析",
    "冲突检测（多指标不一致时降权）",
    "决策（从候选中选择）",
    "输出方案设计（多层结构）",
    "风险提示+局限性说明"
  ],

  "must_read": [
    "references/methods.md（第五章决策树）",
    "references/rules.md（输出格式规范）"
  ],

  "decision_tree": {
    "recommendation": "JSON格式输出",
    "best_score": 75,
    "candidates": [
      ["JSON格式", 75],
      ["CSV格式", 72],
      ["Markdown格式", 65],
      ["PDF格式", 60]
    ],
    "candidate_params": {
      "encoding": ["utf-8", "gbk"],
      "note": "决策树推荐参数"
    }
  },

  "data_warning": null
}
```

### 3.2 mandatory_steps的设计原则

1. **必须可验证**：每个步骤都有明确的完成标准，LLM不能说"我做了"但实际没做
2. **必须具体**：不能写"分析数据"，要写"输入数据校验（格式/范围/异常值）"
3. **必须有序**：按执行顺序排列，LLM按顺序完成
4. **必须完整**：覆盖从路由声明到风险提示的全流程
5. **动态调整**：根据模式（full/quick）动态调整步骤数量

### 3.3 must_read的设计原则

1. **必须是本批真正需要的**：不要列所有文档，只列本批需要的
2. **必须指定章节**：不要只写"读方法论文档"，要写"读方法论文档第五章决策树"
3. **必须与mandatory_steps对应**：每个分析步骤都有对应的参考文档
4. **动态调整**：根据决策树推荐的输出格式，动态调整must_read

---

## 四、预加载的验证机制

### 4.1 continue阶段校验预加载是否被执行

```python
mandatory_checks = [
    ("路由模式", "路由模式" in report, "Step0: 缺路由模式，没先做触发路由"),
    ("摘要", "摘要" in report, "Step1: 缺摘要"),
    ("方法论", "方法论" in report, "Step2: 缺方法论引用"),
    ("推荐结果", "推荐结果" in report, "Step4: 缺推荐结果"),
    ("置信度", "置信度" in report, "Step4: 缺置信度"),
    ("决策依据", "决策依据" in report, "Step1: 缺决策依据"),
]
```

### 4.2 事后审计预加载利用率

```
审计指标：
  1. mandatory_steps完成率：LLM输出中覆盖了多少个mandatory_steps
  2. must_read读取率：LLM是否引用了must_read里的文档
  3. 候选利用率：推荐结果是否在决策树候选范围内
  4. 数据新鲜度：是否引用了最新批次号和最新实际结果
  5. 功能引用率：分析中引用了多少项功能（vs总功能数）
```

---

## 五、预加载的演进历史

### v1.0：无预加载（问题最多）
```
SKILL.md只写了"运行init_skill_pro.py创建技能"
LLM行为：只运行基础模板，不读references文档，不运行校验/审计
结果：19个references文档只读了2个，5个脚本只用了2个
```

### v2.0：SKILL.md里写"必须读所有文档"（无效）
```
SKILL.md写了"必须阅读所有references文档"
LLM行为：表面上说读了，但实际只引用SKILL.md里的内容
结果：文档存在但没被使用，浪费上下文
```

### v3.0：create_skill.py start输出mandatory_steps+must_read（有效）
```
start输出：
  mandatory_steps: 10个必须完成的分析步骤
  must_read: 本批必须读的文档
  candidate_outputs: 决策树生成的候选
LLM行为：按mandatory_steps逐项完成，读must_read里的文档，从候选中决策
结果：功能利用率从30%提升到80%+，输出格式推荐多样化
```

### v4.0：continue硬校验+事后审计（最有效）
```
continue校验：6项强制字段，缺就报错
事后审计：mandatory_steps完成率/must_read读取率/候选利用率
结果：偷懒空间从70%降到5%以下
```

---

## 六、检查清单：你的技能是否有完整的预加载

- [ ] frontmatter description是否包含触发词？
- [ ] SKILL.md开头是否有触发路由？
- [ ] create_skill.py start是否输出mandatory_steps？
- [ ] create_skill.py start是否输出must_read？
- [ ] create_skill.py start是否输出candidate_outputs？
- [ ] create_skill.py start是否输出latest_batch+latest_data？
- [ ] mandatory_steps是否可验证、具体、有序、完整？
- [ ] must_read是否指定了具体章节？
- [ ] continue阶段是否校验mandatory_steps的完成情况？
- [ ] 是否有事后审计预加载利用率的机制？

**0-4项**：预加载严重不足，LLM大概率只用core层
**5-7项**：预加载基本完整，但可能有遗漏
**8-11项**：预加载完整，LLM偷懒空间很小

---

## 版本

- v2.0：完全重写为通用版本，去掉所有特定领域案例
- 核心：四层架构（description→SKILL.md→start输出→references）+ mandatory_steps + must_read
