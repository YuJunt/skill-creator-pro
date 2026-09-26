# 技能注册表格式（Registry）

> 基于deepwiki.com skills-first架构实践。核心结论：**技能多了需要注册表——程序化发现所有技能及其元数据，不用靠人脑记。**

---

## 一、什么时候需要注册表

| 技能数 | 是否需要注册表 |
|--------|-------------|
| < 5个 | 不需要，人脑能记住 |
| 5-15个 | 建议有，方便查找 |
| > 15个 | 必须有，否则找不到 |

---

## 二、注册表格式

```json
{
  "version": "1.0",
  "skills": [
    {
      "name": "my-skill",
      "path": "skills/my-skill/",
      "version": "1.2.0",
      "description": "简短描述（和SKILL.md frontmatter一致）",
      "trigger_words": ["触发词1", "触发词2"],
      "tags": ["分类1", "分类2"],
      "status": "active",
      "last_used": "2026-09-26",
      "created": "2026-09-01"
    }
  ]
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| name | ✅ | 技能名，与目录名一致 |
| path | ✅ | 相对路径 |
| version | ✅ | semver版本 |
| description | ✅ | 简短描述 |
| trigger_words | ✅ | 触发词列表 |
| tags | 可选 | 分类标签 |
| status | ✅ | active/archived/deprecated |
| last_used | 可选 | 最后使用日期 |
| created | 可选 | 创建日期 |

---

## 三、注册表的用途

1. **程序化发现**：脚本自动列出所有技能
2. **批量操作**：批量跑eval、批量安全扫描
3. **生命周期管理**：通过last_used判断归档/删除
4. **去重检查**：检查是否有两个技能功能重叠
5. **触发词冲突检测**：检查是否有两个技能触发词重叠

---

## 四、维护规则

- 新建技能时：自动注册
- 归档技能时：status改为archived
- 删除技能时：从注册表移除
- 版本升级时：更新version
- 每季度：检查last_used，更新生命周期状态

---

## 版本

- v1.0：初始版本
