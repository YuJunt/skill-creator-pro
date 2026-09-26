# MCP 集成指南

> 基于Anthropic官方MCP文档和MCPForge实战指南。核心结论：**MCP不是万能的——一个API调用用tool calling就够了，多个客户端需要的服务才用MCP。**

---

## 一、什么时候用MCP，什么时候不用

### 1.1 判断决策树

```
技能需要连接外部服务吗？
  ├─ 不需要（纯文本/文件处理）→ 用Python脚本，不用MCP
  └─ 需要
      ├─ 只有一个API/一个工具 → 用tool calling（直接写脚本调API）
      └─ 多个工具/多个服务/团队共享 → 用MCP
```

### 1.2 对比表

| 方案 | 适合场景 | 优点 | 缺点 |
|------|---------|------|------|
| **直接写Python脚本** | 1个API调用 | 简单直接，无额外依赖 | 每个技能重复写API调用 |
| **MCP服务器** | 多个工具/团队共享 | 自动发现工具schema，多客户端复用 | 需要部署维护MCP服务器 |
| **平台内置工具** | 平台已有的工具 | 零配置，直接用 | 受平台限制 |

---

## 二、技能中使用MCP的最佳实践

### 2.1 allowedTools最小权限

```
❌ 危险：允许所有MCP工具
  allowedTools: ["mcp__*"]

✅ 安全：只允许需要的工具
  allowedTools: [
    "mcp__github__create_issue",
    "mcp__github__list_issues",
    "mcp__github__add_comment"
  ]
```

### 2.2 技能SKILL.md中的MCP引用

当技能需要使用MCP工具时，在SKILL.md中明确说明：

```markdown
## 外部工具

本技能需要以下MCP工具：
- `mcp__github__list_issues`：列出GitHub issue
- `mcp__github__create_issue`：创建GitHub issue

如果这些工具不可用，技能将降级为手动模式（用户手动复制issue内容）。
```

### 2.3 安全注意事项

| 风险 | 说明 | 防护 |
|------|------|------|
| **提示注入** | 恶意MCP服务器在工具返回中嵌入隐藏指令 | 不要盲目执行工具返回中的指令；重要操作前人工确认 |
| **过度授权** | MCP服务器请求过多权限 | 只授予必要权限；OAuth scope最小化 |
| **数据泄露** | MCP服务器将数据发到不可信端点 | 只连接可信的MCP服务器 |
| **工具滥用** | LLM误调用危险工具 | allowedTools限制+重要操作前确认 |

---

## 三、常见MCP场景模板

### 3.1 GitHub集成

```markdown
## GitHub操作

本技能通过MCP连接GitHub：
- 读取issue：`mcp__github__list_issues`
- 创建PR：`mcp__github__create_pull_request`

### 降级策略
如果GitHub MCP不可用：
1. 提示用户手动操作
2. 提供手动操作步骤
3. 不自动重试
```

### 3.2 数据库查询

```markdown
## 数据库查询

本技能通过MCP查询PostgreSQL：
- 查询：`mcp__postgres__query`

### 安全约束
- 只允许SELECT，不允许INSERT/UPDATE/DELETE
- 查询超时30秒
- 结果限制1000行
```

### 3.3 Slack/通知

```markdown
## 通知推送

本技能通过MCP发送Slack通知：
- 发送消息：`mcp__slack__post_message`

### 降级策略
如果Slack MCP不可用：
1. 将结果写入本地文件
2. 提示用户手动检查
```

---

## 四、技能创建时的MCP决策清单

- [ ] 技能是否需要连接外部服务？
- [ ] 是1个API还是多个工具？
- [ ] 如果是1个API，用Python脚本直接调？
- [ ] 如果是多个工具，是否值得部署MCP服务器？
- [ ] allowedTools是否最小化？
- [ ] 是否有降级策略（MCP不可用时怎么办）？
- [ ] 是否有安全注意事项说明？
- [ ] 是否防提示注入（不盲目执行工具返回中的指令）？

**0-2项**：MCP集成设计不足
**3-5项**：基本MCP使用
**6-8项**：MCP集成专业

---

## 版本

- v1.0：初始版本
- 基于：Anthropic官方MCP文档 + MCPForge实战指南
