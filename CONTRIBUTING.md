# 贡献指南

感谢你对 skill-creator-pro 的关注！本指南帮助你高效地参与贡献。

## 开发环境搭建

### 前置要求
- Python 3.7+（dataclasses 要求）
- pytest（运行测试）
- bash（打包脚本）

### 安装步骤
```bash
# 1. Fork 并克隆仓库
git clone <your-fork-url>
cd skill-creator-pro

# 2. 安装测试依赖
pip install pytest

# 3. 验证环境
python3 -m pytest tests/ -v
```

## 项目结构

```
skill-creator-pro/
├── SKILL.md                    # 技能入口（<500行）
├── LICENSE                     # MIT
├── CHANGELOG.md                # 版本历史
├── CONTRIBUTING.md             # 本文件
├── scripts/                    # 9个脚本
│   ├── create_skill.py         # 编排脚本（5种模式）
│   ├── validate_skill.py       # 规范校验
│   ├── audit_skill.py          # 深度审计（36项）
│   ├── security_scan.py        # 安全扫描
│   ├── output_validator.py     # 输出校验硬门禁
│   ├── init_skill_pro.py       # 模板生成（3种哲学）
│   ├── upgrade_skill.py        # 迁移升级
│   ├── templates.py            # 模板库
│   └── package.sh              # 一键打包
├── references/                  # 24个参考文档
├── tests/                       # pytest测试套件
└── .github/workflows/ci.yml    # CI/CD配置
```

## 代码规范

### Python 代码
- 遵循 PEP 8
- 使用 4 空格缩进
- 函数和类必须有 docstring
- 所有脚本必须有 `if __name__ == "__main__":` 入口
- 错误处理：不静默失败，错误信息可定位
- 退出码规范：0=成功，1=校验失败，2=参数错误，3=运行时错误

### SKILL.md 规范
- 必须 < 500 行
- frontmatter 只包含 name 和 description
- description 必须包含三要素（What/When/Trigger）
- 渐进式披露：核心在 SKILL.md，细节在 references/
- 每个 reference 必须从 SKILL.md 引用，并说明什么时候读

### 提交信息
使用 Conventional Commits 格式：
```
feat: 新增功能
fix: 修复bug
docs: 文档更新
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

## 测试要求

### 运行测试
```bash
# 运行全部测试
python3 -m pytest tests/ -v

# 运行特定测试类
python3 -m pytest tests/test_skill_creator_pro.py::TestValidateSkill -v

# 运行带输出
python3 -m pytest tests/ -v -s
```

### 新增代码必须
1. 添加对应的单元测试
2. 确保所有现有测试通过
3. 运行规范校验：`python3 scripts/validate_skill.py .`
4. 运行安全扫描：`python3 scripts/security_scan.py .`

## 提交流程

### 1. 创建分支
```bash
git checkout -b feat/your-feature-name
```

### 2. 开发并测试
```bash
# 编写代码
# 运行测试
python3 -m pytest tests/ -v

# 运行校验
python3 scripts/validate_skill.py .
python3 scripts/security_scan.py .
```

### 3. 提交
```bash
git add .
git commit -m "feat: 描述你的改动"
```

### 4. 推送并创建 PR
```bash
git push origin feat/your-feature-name
```
然后在 GitHub 上创建 Pull Request。

## PR 检查清单

提交 PR 前，请确认：
- [ ] 所有测试通过（`pytest tests/ -v`）
- [ ] 规范校验通过（`validate_skill.py .`）
- [ ] 安全扫描无高风险（`security_scan.py .`）
- [ ] 新增代码有对应的单元测试
- [ ] SKILL.md < 500 行
- [ ] 没有硬编码的 `/home/user` 路径
- [ ] 提交信息符合 Conventional Commits 格式
- [ ] 更新了 CHANGELOG.md（如果是用户可见的改动）

## 常见问题

### Q: 如何添加新的检查项到 validate_skill.py？
A: 在 `check_skill_md()` 或 `check_scripts_integrity()` 中添加新的检查函数，返回 `{"level": "high/medium/low", "item": "...", "message": "..."}`。

### Q: 如何添加新的安全扫描模式？
A: 在 `security_scan.py` 的 `PATTERNS` 列表中添加新的正则表达式模式，格式为 `(regex, message, suggestion)`。

### Q: 如何添加新的设计哲学？
A: 在 `init_skill_pro.py` 的 `--philosophy` 参数 choices 中添加，并在 `templates.py` 中添加对应的模板。

### Q: 测试失败怎么办？
A: 
1. 查看失败的测试用例和错误信息
2. 检查是否是测试 fixture 的问题（临时技能不完整）
3. 如果是脚本 bug，修复后重新运行
4. 如果是测试用例问题，更新测试用例

## 版本发布

### 发布流程
1. 确认所有测试通过
2. 更新 CHANGELOG.md
3. 更新版本号（SKILL.md + 所有脚本头部）
4. 运行打包脚本：`bash scripts/package.sh`
5. 创建 GitHub Release，上传 zip 包

### 版本号规则
遵循 Semantic Versioning：
- 主版本号：不兼容的 API 改动
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

## 联系

有问题或建议？欢迎创建 Issue 或 PR。
