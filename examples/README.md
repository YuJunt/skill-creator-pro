# 示例技能库

本目录包含3个完整的技能示例，覆盖三种设计哲学，供学习和参考。

## 示例列表

| 示例 | 设计哲学 | 特点 |
|------|---------|------|
| [pdf-processor](./pdf-processor/) | Capability型（工具包装型） | 7种PDF操作，全部脚本化 |
| [code-reviewer](./code-reviewer/) | Process型（方法论型） | 5维度30+项Checklist，6步审查流程 |
| [data-analyzer](./data-analyzer/) | Mixed型（混合型） | 脚本做指标计算，AI做归因分析 |

## 设计哲学对比

### Capability型
- **适用**：操作类任务（PDF处理/图片处理）
- **特点**：大部分逻辑脚本化，AI只负责选工具传参
- **优点**：确定性高
- **缺点**：灵活性低

### Process型
- **适用**：分析类任务（代码审查/需求分析）
- **特点**：固定流程和Checklist，AI按步骤执行
- **优点**：流程规范，不遗漏
- **缺点**：可能僵化

### Mixed型
- **适用**：复杂任务（数据分析/决策支持）
- **特点**：脚本做确定性计算，AI做分析判断
- **优点**：兼顾确定性和灵活性
- **缺点**：复杂度高

## 如何使用

```bash
# 1. 学习参考：阅读每个示例的SKILL.md
# 2. 作为模板：复制并修改
cp -r examples/pdf-processor /path/to/workspace/.user_skills/my-skill
# 3. 验证规范
python3 scripts/validate_skill.py examples/pdf-processor
```

## 版本

- v1.0.0：初始版本，包含3个示例
