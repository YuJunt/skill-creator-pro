# 示例：使用skill-creator-pro创建一个新技能

> 这是一个完整的使用示例，照着做就能创建一个专业级技能。

## 场景

我想创建一个"股票日报"技能，每天自动分析指定股票的行情、资金流、新闻公告，生成日报。

## Step 1: 初始化技能模板

```bash
cd /home/user/.doubao/agent_mode/workspace/.user_skills/skill-creator-pro

python3 scripts/init_skill_pro.py stock-daily \
  --path /home/user/.doubao/agent_mode/workspace/.user_skills \
  --title "股票日报" \
  --description "股票日报专业分析。自动采集行情/资金流/新闻公告，生成结构化日报，支持单股分析/多股对比/行业板块分析。" \
  --triggers "股票日报,个股分析,今天涨跌,资金面" \
  --not-for "基金/债券/期货/加密货币等非股票品种"
```

输出：
```
✅ 技能创建成功: /home/user/.doubao/agent_mode/workspace/.user_skills/stock-daily

📁 目录结构:
  stock-daily/
  ├── SKILL.md（主入口，触发路由+Gotchas+快速开始）
  ├── scripts/
  │   └── orchestrator.py（编排脚本模板）
  ├── references/
  │   ├── rules.md（规则模板）
  │   └── methods.md（方法论模板）
  └── examples/
      └── example-full-analysis.md（完整示例模板）
```

## Step 2: 规范校验

```bash
python3 scripts/validate_skill.py /home/user/.doubao/agent_mode/workspace/.user_skills/stock-daily
```

输出：
```
✅ 校验通过（无高优先级问题）
问题统计: 高=0  中=0  低=1
```

## Step 3: 深度审计（基线）

```bash
python3 scripts/audit_skill.py /home/user/.doubao/agent_mode/workspace/.user_skills/stock-daily
```

输出（基线，模板状态）：
```
📊 总体评分: 23/36 (64%)
🏆 等级: 不合格

规范层 8/8 ✅
架构层 5/6
内容层 4/5
工程层 2/5 🔴（需要实现脚本）
质量层 3/4
进化层 1/4
运维层 0/4
```

**解读**：规范层满分说明模板合格，其他层需要根据股票日报的具体业务来实现。

## Step 4: 实现业务逻辑

### 4.1 编辑SKILL.md

打开`stock-daily/SKILL.md`，修改：
- Gotchas：填写股票分析常见的坑（如"停牌股票无法获取行情""除权除息日价格异常"）
- 快速开始：修改脚本命令为股票日报的实际命令
- 输出格式：修改为股票日报的输出格式

### 4.2 实现scripts/orchestrator.py

打开`stock-daily/scripts/orchestrator.py`，实现：
- `cmd_start`：采集股票行情、资金流、新闻公告
- `cmd_continue`：校验分析完整性，写入云端
- `cmd_settle`：次日验证预测准确性，复盘

### 4.3 完善references/

- `rules.md`：填写股票分析规则（如交易时间、涨跌幅限制、停牌规则）
- `methods.md`：填写分析方法论（如技术面分析、资金面分析、消息面分析框架）

## Step 5: 再次审计（验证改进）

```bash
python3 scripts/audit_skill.py /home/user/.doubao/agent_mode/workspace/.user_skills/stock-daily
```

目标：总分≥28/36（良好），规范层和工程层必须满分。

## Step 6: 端到端实测

```bash
# 测试完整流程
cd /home/user/.doubao/agent_mode/workspace/.user_skills/stock-daily/scripts
python3 orchestrator.py start --mode full --stock 600519
# ... 做分析 ...
python3 orchestrator.py continue --budget 0 --result-json '{...}'
```

## 常用命令速查

```bash
# 校验规范
python3 validate_skill.py <skill-path>

# 深度审计
python3 audit_skill.py <skill-path>

# JSON输出（用于自动化）
python3 validate_skill.py <skill-path> --json
python3 audit_skill.py <skill-path> --json

# 创建新技能
python3 init_skill_pro.py <skill-name> --path <output-dir>
```

## 评分标准参考

| 等级 | 分数 | 说明 |
|------|------|------|
| 优秀 | ≥32/36 (89%) | 生产级技能，可直接上线 |
| 良好 | 28-31/36 (78-86%) | 核心能力完整，少量优化空间 |
| 合格 | 24-27/36 (67-75%) | 基本可用，有明显短板 |
| 不合格 | <24/36 (<67%) | 不建议使用，需大幅重构 |

**目标**：新建技能至少达到"良好"（28/36），规范层和工程层必须满分。
