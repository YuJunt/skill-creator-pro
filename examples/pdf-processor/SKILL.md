---
name: pdf-processor
description: >
  PDF文件处理工具，支持PDF合并、拆分、旋转、提取文本、提取图片、添加水印、加密解密。
  当用户需要处理PDF文件（合并/拆分/旋转/提取文本/提取图片/加水印/加密）时使用。
  触发词："PDF合并""PDF拆分""旋转PDF""提取PDF文本""PDF加水印""PDF加密""pdf处理"。
  不适用于：PDF内容创作（应使用文档工具）、PDF表单填写（需专门工具）。
---

# PDF 处理工具（PDF Processor）

> **设计哲学**: Capability型（工具包装型）——将复杂的PDF操作封装为确定性脚本，AI只负责选择工具和传递参数。

> **预加载**: 触发后先确认用户的PDF操作类型，再读取对应的references文档和运行脚本。

---

## 🔀 触发路由

```
🔀 路由: {操作类型}｜文件: {文件名}｜原因: {一句话}
```

| 操作类型 | 触发词 | 脚本 | 输出 |
|---------|--------|------|------|
| 合并PDF | "合并PDF""把多个PDF合成一个" | `scripts/merge_pdf.py` | 合并后的PDF |
| 拆分PDF | "拆分PDF""把PDF分成多个" | `scripts/split_pdf.py` | 拆分后的PDFs |
| 旋转PDF | "旋转PDF""PDF页面旋转" | `scripts/rotate_pdf.py` | 旋转后的PDF |
| 提取文本 | "提取PDF文本""PDF转文字" | `scripts/extract_text.py` | 文本文件 |
| 提取图片 | "提取PDF图片""PDF中的图片" | `scripts/extract_images.py` | 图片文件 |
| 添加水印 | "PDF加水印""PDF水印" | `scripts/add_watermark.py` | 带水印的PDF |
| 加密解密 | "PDF加密""PDF解密""PDF密码" | `scripts/encrypt_pdf.py` | 加密/解密后的PDF |

---

## 工作流程

### 第1步：确认操作类型和文件
- 确认用户要执行的PDF操作
- 确认输入文件路径（必须是.pdf文件）
- 确认输出路径（默认与输入文件同目录）

### 第2步：运行对应脚本
```bash
# 合并PDF
python3 scripts/merge_pdf.py input1.pdf input2.pdf -o output.pdf

# 拆分PDF（按页数范围）
python3 scripts/split_pdf.py input.pdf --pages 1-5,6-10

# 旋转PDF（90/180/270度）
python3 scripts/rotate_pdf.py input.pdf --angle 90 -o output.pdf

# 提取文本
python3 scripts/extract_text.py input.pdf -o output.txt

# 提取图片
python3 scripts/extract_images.py input.pdf -o output_dir/

# 添加水印
python3 scripts/add_watermark.py input.pdf --text "机密" -o output.pdf

# 加密/解密
python3 scripts/encrypt_pdf.py input.pdf --password 123456 -o output.pdf
python3 scripts/encrypt_pdf.py input.pdf --decrypt --password 123456 -o output.pdf
```

### 第3步：验证输出
- 确认输出文件存在且非空
- 简单验证输出内容（页数/文本/图片数量）

---

## Gotchas（常见坑）

1. **大文件处理慢**：超过100MB的PDF处理可能需要30秒以上，提前告知用户
2. **扫描版PDF无法提取文本**：扫描版PDF是图片，需要OCR才能提取文本，本工具不支持OCR
3. **加密PDF需要密码**：处理加密PDF前必须先解密，否则所有操作都会失败
4. **合并时页数顺序**：按命令行参数顺序合并，确认用户提供的顺序正确
5. **拆分页码从1开始**：页码从1开始，不是0，`--pages 1-5`表示第1到第5页
6. **水印文字编码**：中文水印需要确保系统有中文字体，否则可能显示为方框
7. **输出文件覆盖**：如果输出文件已存在，默认覆盖，确认用户是否需要备份

---

## 渐进式披露

| 场景 | 文档 |
|------|------|
| 需要了解PyPDF2 API细节 | `references/pypdf2-api.md` |
| 需要处理异常情况 | `references/error-handling.md` |
| 需要批量处理 | `references/batch-processing.md` |

---

## 输出格式

处理完成后输出：
```
✅ 处理完成
操作: {操作类型}
输入: {输入文件}（{页数}页，{大小}）
输出: {输出文件}（{页数}页，{大小}）
耗时: {耗时}秒
```

---

## 版本

- v1.0.0：初始版本，支持7种PDF操作
