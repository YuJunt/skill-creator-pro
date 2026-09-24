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
2. **可操作性**：每个退出码都有明确的修复方向
3. **兼容性**：0=成功，非0=失败，符合Unix惯例
4. **渐进式**：1=可修复的输入问题，3=需要人工干预的环境问题
5. **argparse优先**：参数错误由argparse自动处理（exit 2），不需要手动检查

---

## 版本

- v1.0：初始版本，定义4级退出码规范
