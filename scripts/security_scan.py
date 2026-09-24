#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本: v1.0.0 | 许可证: MIT | 最低Python: 3.8+

skill-creator-pro 安全扫描脚本（security_scan.py）

自动检测技能中的安全风险：
  1. 提示注入（Prompt Injection）- "ignore previous instructions"等
  2. 危险代码（Dangerous Code）- eval/exec/os.system/rm -rf等
  3. 数据泄露（Data Exfiltration）- 硬编码凭据/外部webhook等
  4. 隐藏指令（Hidden Instructions）- 不可见Unicode/注释隐写等
  5. 其他风险（Other Risks）- 无错误处理/危险文件操作等

用法：
  python3 security_scan.py <skill_path>
  python3 security_scan.py <skill_path> --json   # JSON格式输出
  python3 security_scan.py <skill_path> --fail-on high  # 高风险时exit 1
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List


# ============================================================
# 数据结构
# ============================================================

@dataclass
class SecurityFinding:
    """安全发现"""
    category: str          # 类别：injection/dangerous_code/data_leak/hidden_instruction/other
    severity: str          # 严重度：high/medium/low/info
    file: str              # 文件路径（相对技能根目录）
    line: int              # 行号
    snippet: str           # 代码片段（截断）
    message: str           # 描述
    suggestion: str        # 修复建议


@dataclass
class SecurityReport:
    """安全报告"""
    skill_path: str
    total_files_scanned: int = 0
    findings: List[SecurityFinding] = field(default_factory=list)
    scan_time: str = ""

    @property
    def high_count(self):
        return sum(1 for f in self.findings if f.severity == "high")

    @property
    def medium_count(self):
        return sum(1 for f in self.findings if f.severity == "medium")

    @property
    def low_count(self):
        return sum(1 for f in self.findings if f.severity == "low")

    @property
    def info_count(self):
        return sum(1 for f in self.findings if f.severity == "info")

    @property
    def security_score(self):
        """安全评分（0-100，越高越安全）"""
        score = 100
        score -= self.high_count * 20
        score -= self.medium_count * 10
        score -= self.low_count * 3
        return max(0, score)

    @property
    def grade(self):
        """安全等级"""
        s = self.security_score
        if s >= 90:
            return "A（安全）"
        elif s >= 75:
            return "B（基本安全）"
        elif s >= 60:
            return "C（有风险）"
        elif s >= 40:
            return "D（高风险）"
        else:
            return "F（危险）"


# ============================================================
# 扫描规则
# ============================================================

# 提示注入模式（高风险）
INJECTION_PATTERNS = [
    (r"(?i)ignore\s+(all\s+)?(previous|prior|above|foregoing)\s+(instructions?|prompts?|contexts?)",
     "指令覆盖：要求忽略之前的指令", "删除此类指令，技能不应要求模型忽略系统指令"),
    (r"(?i)forget\s+(everything|all|previous|above)",
     "指令覆盖：要求忘记之前的内容", "删除此类指令"),
    (r"(?i)(you\s+are\s+now|your\s+new\s+role\s+is|now\s+act\s+as)",
     "角色覆盖：试图改变模型角色", "技能不应在运行时改变模型角色"),
    (r"(?i)(system\s+prompt\s+override|admin\s+mode\s+activated|developer\s+mode\s+(enabled|on))",
     "权限提升：声称进入管理员/开发者模式", "删除此类指令"),
    (r"(?i)(act\s+as\s+if\s+you\s+have\s+no\s+restrictions|without\s+(any\s+)?restrictions|unrestricted\s+mode)",
     "安全绕过：要求无限制运行", "删除此类指令"),
    (r"(?i)\[(SYSTEM|ADMIN|ROOT|SUPERUSER)\]",
     "假角色标签：使用系统级角色标签", "删除此类标签"),
    (r"(?i)(bypass\s+(safety|security|content\s+filter)|disable\s+(safety|security|filter))",
     "安全绕过：要求禁用安全检查", "删除此类指令"),
    (r"(?i)(jailbreak|DAN\s+(mode|prompt)|do\s+anything\s+now)",
     "越狱模式：使用已知越狱技术", "删除此类内容"),
    (r"(?i)(reveal|show|extract|dump|leak)\s+(your\s+)?(system\s+)?(prompt|instructions?|rules?)",
     "提示泄露：要求显示系统提示", "删除此类指令"),
    (r"(?i)(from\s+now\s+on|starting\s+now)\s+you\s+(will|are|should)",
     "行为覆盖：试图从现在起改变行为", "审查是否为合理的技能指令，避免覆盖系统行为"),
]

# 危险代码模式（高风险）
DANGEROUS_CODE_PATTERNS = [
    (r"\beval\s*\(", "动态执行：eval()可执行任意代码", "避免使用eval，使用ast.literal_eval或显式解析"),
    (r"\bexec\s*\(", "动态执行：exec()可执行任意代码", "避免使用exec，使用显式函数调用"),
    (r"\bos\.system\s*\(", "命令执行：os.system()直接执行shell命令", "使用subprocess.run([...], shell=False)替代"),
    (r"shell\s*=\s*True", "命令注入：subprocess使用shell=True", "使用shell=False并传参数列表"),
    (r"rm\s+-rf\s+(/|~|\$HOME|\*|/\*)", "危险删除：递归删除根目录/家目录", "避免使用rm -rf，使用shutil.rmtree并验证路径"),
    (r"dd\s+if=", "磁盘写入：dd命令可覆盖磁盘", "避免使用dd命令"),
    (r"chmod\s+(-R\s+)?777", "权限过宽：chmod 777给予所有用户完全权限", "使用最小权限原则，如755或644"),
    (r":\(\)\{\s*:\|:&\s*\};:", "Fork炸弹：经典fork bomb", "删除此类代码"),
    (r"\bpickle\.loads?\s*\(", "反序列化漏洞：pickle可执行任意代码", "使用json或其他安全格式替代pickle"),
    (r"__import__\s*\(", "动态导入：__import__可导入任意模块", "使用显式import语句"),
    (r"\bos\.popen\s*\(", "命令执行：os.popen()执行shell命令", "使用subprocess.run替代"),
    (r"(?i)(curl|wget)\s+.*\|\s*(bash|sh|zsh)", "远程执行：下载并直接执行脚本", "先下载审查再执行，不要管道直接执行"),
]

# 数据泄露模式（中风险）
DATA_LEAK_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "硬编码OpenAI API Key", "使用环境变量或配置文件，不要硬编码"),
    (r"AKIA[0-9A-Z]{16}", "硬编码AWS Access Key", "使用环境变量或IAM角色"),
    (r"ghp_[a-zA-Z0-9]{36}", "硬编码GitHub Personal Access Token", "使用环境变量或GitHub Apps"),
    (r"xox[baprs]-[a-zA-Z0-9-]{10,}", "硬编码Slack Token", "使用环境变量"),
    (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{6,}['\"]", "硬编码密码", "使用环境变量或密钥管理服务"),
    (r"(?i)(api[_-]?key|secret|token|private[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
     "硬编码密钥/令牌", "使用环境变量，不要在代码中硬编码"),
    (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "硬编码私钥", "使用密钥管理服务，不要硬编码私钥"),
    (r"(?i)(webhook|requestbin|ngrok|beeceptor|pipedream)", "外部数据接收服务：可能用于数据外泄",
     "确认webhook用途，避免将敏感数据发送到不可信服务"),
    (r"(?i)(send|post|upload|transmit).*(to\s+)?(external|third[-\s]?party|remote)\s+(url|server|endpoint)",
     "数据外发：将数据发送到外部服务", "确认数据外发的必要性和安全性"),
]

# 隐藏指令模式（中风险）
HIDDEN_INSTRUCTION_PATTERNS = [
    (r"[\u200b\u200c\u200d\u2060\ufeff]", "不可见Unicode字符（零宽空格/零宽非连接符等）",
     "删除不可见字符，可能用于隐藏指令"),
    (r"<!--[\s\S]*?(ignore|override|bypass|jailbreak|system\s+prompt)[\s\S]*?-->",
     "HTML注释中隐藏指令", "审查注释内容，删除隐藏的恶意指令"),
    (r"(?i)#\s*(TODO|FIXME|HACK|XXX).*?(ignore|override|bypass|disable).*?(instruction|safety|filter|check)",
     "代码注释中隐藏安全绕过指令", "审查注释内容，删除隐藏的恶意指令"),
    (r"!\[[^\]]*\]\([^)]+\)", "Markdown图片链接（可能包含隐藏信息）",
     "确认图片链接用途，避免通过图片传递隐藏指令"),
    (r"<span\s+style=[^>]*color:\s*(white|#fff|#ffffff|transparent)[^>]*>",
     "白色/透明文字（可能隐藏指令）", "删除隐藏文字，使用正常可见文本"),
]

# 其他风险模式（低风险/信息）
OTHER_RISK_PATTERNS = [
    (r"(?i)(write|overwrite|replace|delete|remove|truncate).*?(user|home|system|config|important)",
     "危险文件操作：可能覆盖用户重要文件", "验证文件路径，避免操作用户重要文件"),
    (r"(?i)(requests\.(get|post|put|delete)|urllib|http\.client|aiohttp)",
     "网络请求：技能包含网络访问", "确认网络请求的必要性和目标地址安全性"),
    (r"(?i)(open|write|creat).*?['\"](w|wb|w\+)[\"']", "文件写入：技能会写入文件",
     "确认文件写入路径，避免覆盖重要文件"),
]


# ============================================================
# 扫描器
# ============================================================

class SecurityScanner:
    """安全扫描器"""

    # 需要扫描的文件扩展名
    SCAN_EXTENSIONS = {'.py', '.md', '.sh', '.bash', '.zsh', '.js', '.ts', '.json', '.yaml', '.yml', '.txt'}

    # 跳过的目录
    SKIP_DIRS = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'dist', 'build', 'tests'}

    def __init__(self, skill_path: str):
        self.skill_path = os.path.abspath(skill_path)
        self.report = SecurityReport(skill_path=skill_path)

    def scan(self) -> SecurityReport:
        """执行完整扫描"""
        import datetime
        self.report.scan_time = datetime.datetime.now().isoformat()

        if not os.path.isdir(self.skill_path):
            self.report.findings.append(SecurityFinding(
                category="other", severity="high",
                file="", line=0, snippet="",
                message=f"技能目录不存在: {self.skill_path}",
                suggestion="确认技能目录路径正确"
            ))
            return self.report

        # 遍历所有文件
        for root, dirs, files in os.walk(self.skill_path):
            # 跳过不需要扫描的目录
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in self.SCAN_EXTENSIONS:
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, self.skill_path)
                self._scan_file(filepath, rel_path)
                self.report.total_files_scanned += 1

        return self.report

    def _scan_file(self, filepath: str, rel_path: str):
        """扫描单个文件"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                lines = content.splitlines(keepends=True)
        except Exception as e:
            self.report.findings.append(SecurityFinding(
                category="other", severity="info",
                file=rel_path, line=0, snippet="",
                message=f"无法读取文件: {e}",
                suggestion="检查文件编码和权限"
            ))
            return

        # 自跳过：如果是安全扫描工具本身（包含模式定义），跳过避免误报
        if "INJECTION_PATTERNS =" in content or "DANGEROUS_CODE_PATTERNS =" in content:
            return

        # 对每类模式进行扫描
        # references目录下的文档是安全检查清单/方法论，包含危险代码示例是正常的
        # 只扫描提示注入和隐藏指令（这些在文档中也可能是真实的恶意内容）
        is_reference_doc = rel_path.startswith("references" + os.sep) and rel_path.endswith(".md")

        self._scan_patterns(lines, rel_path, "injection", INJECTION_PATTERNS)
        self._scan_patterns(lines, rel_path, "hidden_instruction", HIDDEN_INSTRUCTION_PATTERNS)

        if not is_reference_doc:
            self._scan_patterns(lines, rel_path, "dangerous_code", DANGEROUS_CODE_PATTERNS)
            self._scan_patterns(lines, rel_path, "data_leak", DATA_LEAK_PATTERNS)
            self._scan_patterns(lines, rel_path, "other", OTHER_RISK_PATTERNS)

        # 检查Python脚本是否有基本的错误处理
        if filepath.endswith('.py') and len(lines) > 20:
            self._check_python_error_handling(lines, rel_path)

    def _scan_patterns(self, lines: list, rel_path: str, category: str, patterns: list):
        """扫描一组正则模式"""
        for line_num, line in enumerate(lines, 1):
            for pattern, message, suggestion in patterns:
                if re.search(pattern, line):
                    snippet = line.strip()[:120]
                    # 确定严重度
                    if category == "injection":
                        severity = "high"
                    elif category == "dangerous_code":
                        severity = "high"
                    elif category == "data_leak":
                        severity = "medium"
                    elif category == "hidden_instruction":
                        severity = "medium"
                    else:
                        severity = "low"

                    self.report.findings.append(SecurityFinding(
                        category=category,
                        severity=severity,
                        file=rel_path,
                        line=line_num,
                        snippet=snippet,
                        message=message,
                        suggestion=suggestion
                    ))

    def _check_python_error_handling(self, lines: list, rel_path: str):
        """检查Python脚本是否有基本的错误处理"""
        has_try = any('try:' in line or 'try ' in line for line in lines)
        has_main = any('if __name__' in line for line in lines)
        has_subprocess = any('subprocess' in line for line in lines)
        has_file_write = any(re.search(r"open\(.*['\"](w|wb|w\+)", line) for line in lines)

        if has_main and not has_try and (has_subprocess or has_file_write):
            self.report.findings.append(SecurityFinding(
                category="other", severity="low",
                file=rel_path, line=0, snippet="",
                message="脚本包含危险操作但没有try-except错误处理",
                suggestion="添加try-except错误处理，避免异常时崩溃或产生不可预期行为"
            ))


# ============================================================
# 输出格式化
# ============================================================

CATEGORY_NAMES = {
    "injection": "🔴 提示注入",
    "dangerous_code": "🔴 危险代码",
    "data_leak": "🟡 数据泄露",
    "hidden_instruction": "🟡 隐藏指令",
    "other": "🔵 其他风险",
}

SEVERITY_ICONS = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🔵",
    "info": "⚪",
}


def print_report(report: SecurityReport):
    """打印人类可读的安全报告"""
    print(f"\n{'='*70}")
    print(f"🛡️  技能安全扫描报告")
    print(f"{'='*70}")
    print(f"  技能路径: {report.skill_path}")
    print(f"  扫描文件: {report.total_files_scanned}个")
    print(f"  扫描时间: {report.scan_time}")
    print(f"{'='*70}")

    # 安全评分
    print(f"\n📊 安全评分: {report.security_score}/100  等级: {report.grade}")
    print(f"  🔴 高风险: {report.high_count}  🟡 中风险: {report.medium_count}  🔵 低风险: {report.low_count}  ⚪ 信息: {report.info_count}")

    if not report.findings:
        print(f"\n✅ 未发现安全风险！技能符合安全规范。")
        print(f"{'='*70}\n")
        return

    # 按类别分组输出
    for category in ["injection", "dangerous_code", "data_leak", "hidden_instruction", "other"]:
        category_findings = [f for f in report.findings if f.category == category]
        if not category_findings:
            continue

        print(f"\n{CATEGORY_NAMES[category]} ({len(category_findings)}项):")
        print(f"  {'-'*66}")
        for i, f in enumerate(category_findings, 1):
            print(f"  {SEVERITY_ICONS[f.severity]} [{f.severity.upper()}] #{i}")
            print(f"     文件: {f.file}:{f.line}")
            print(f"     问题: {f.message}")
            if f.snippet:
                print(f"     代码: {f.snippet}")
            print(f"     建议: {f.suggestion}")
            print()

    print(f"{'='*70}")
    print(f"💡 修复建议:")
    print(f"  1. 高风险问题必须修复后才能发布")
    print(f"  2. 中风险问题建议修复，发布前最好修复")
    print(f"  3. 低风险问题可选修复，有时间再修")
    print(f"  4. 修复后重新运行安全扫描验证")
    print(f"{'='*70}\n")


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 安全扫描脚本（检测提示注入/危险代码/数据泄露/隐藏指令）"
    )
    parser.add_argument("skill_path", help="技能目录路径")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    parser.add_argument("--fail-on", choices=["high", "medium", "low"], default=None,
                        help="发现指定级别及以上风险时exit 1（用于CI/CD门禁）")
    args = parser.parse_args()

    scanner = SecurityScanner(args.skill_path)
    report = scanner.scan()

    if args.json:
        output = {
            "skill_path": report.skill_path,
            "total_files_scanned": report.total_files_scanned,
            "security_score": report.security_score,
            "grade": report.grade,
            "high_count": report.high_count,
            "medium_count": report.medium_count,
            "low_count": report.low_count,
            "info_count": report.info_count,
            "findings": [asdict(f) for f in report.findings],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_report(report)

    # 门禁判断
    if args.fail_on:
        threshold = {"high": 1, "medium": 2, "low": 3}
        severity_order = {"high": 3, "medium": 2, "low": 1, "info": 0}
        threshold_value = severity_order.get(args.fail_on, 0)
        has_blocking = any(severity_order.get(f.severity, 0) >= threshold_value for f in report.findings)
        if has_blocking:
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
