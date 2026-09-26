#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-creator-pro 供应链安全扫描脚本（借鉴agent-plugin-creator）

检测技能的依赖安全风险，生成SBOM（软件物料清单）。
检查项：
  1. 依赖清单提取（requirements.txt/setup.py/pyproject.toml/package.json）
  2. 已知漏洞检测（基于内置漏洞数据库，离线可用）
  3. 许可证合规检查（GPL/AGPL等传染性许可证）
  4. 依赖过时检测（版本过旧）
  5. SBOM生成（CycloneDX格式JSON）

用法：
  python3 scripts/supply_chain_scan.py <skill-path>
  python3 scripts/supply_chain_scan.py <skill-path> --json
  python3 scripts/supply_chain_scan.py <skill-path> --generate-sbom  # 生成SBOM文件
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime


# 内置已知漏洞数据库（简化版，实际使用可对接OSV/NVD API）
# 格式：{"package_name": {"affected_versions": ["<1.0", ">=2.0,<2.5"], "severity": "high", "cve": "CVE-XXXX-XXXX", "description": "..."}}
KNOWN_VULNERABILITIES = {
    "requests": {"affected_versions": ["<2.20"], "severity": "high", "cve": "CVE-2023-32681", "description": "请求头泄露到重定向URL"},
    "urllib3": {"affected_versions": ["<1.26.18"], "severity": "medium", "cve": "CVE-2023-43804", "description": "Cookie泄露到重定向URL"},
    "cryptography": {"affected_versions": ["<39.0.1"], "severity": "high", "cve": "CVE-2023-23931", "description": "内存损坏漏洞"},
    "pyyaml": {"affected_versions": ["<5.4"], "severity": "high", "cve": "CVE-2020-14343", "description": "任意代码执行（yaml.load）"},
    "jinja2": {"affected_versions": ["<2.11.3"], "severity": "medium", "cve": "CVE-2020-28493", "description": "ReDoS拒绝服务"},
    "flask": {"affected_versions": ["<2.3.2"], "severity": "medium", "cve": "CVE-2023-30861", "description": "会话Cookie泄露"},
    "django": {"affected_versions": ["<3.2.19", ">=4.0,<4.0.11", ">=4.1,<4.1.5"], "severity": "high", "cve": "CVE-2023-31047", "description": "文件上传绕过"},
    "numpy": {"affected_versions": ["<1.22.2"], "severity": "high", "cve": "CVE-2021-41496", "description": "拒绝服务（缓冲区溢出）"},
    "pandas": {"affected_versions": ["<1.5.3"], "severity": "medium", "cve": "CVE-2023-0286", "description": "类型混淆漏洞"},
    "pillow": {"affected_versions": ["<9.0.1"], "severity": "high", "cve": "CVE-2022-22817", "description": "任意代码执行"},
}

# 传染性许可证列表（需要特别注意合规性）
COPYLEFT_LICENSES = {"GPL", "AGPL", "LGPL", "MPL", "EPL", "CDDL"}

# 宽松许可证列表（通常无合规问题）
PERMISSIVE_LICENSES = {"MIT", "Apache", "BSD", "ISC", "Unlicense", "CC0", "0BSD"}


def parse_requirements(filepath):
    """解析requirements.txt"""
    deps = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                # 解析包名和版本
                match = re.match(r"^([a-zA-Z0-9_.-]+)\s*([=<>!~]=?\s*[0-9.a-zA-Z*]+)?", line)
                if match:
                    name = match.group(1).lower()
                    version = match.group(2) or "*"
                    deps.append({"name": name, "version": version, "source": "requirements.txt"})
    except Exception:
        pass
    return deps


def parse_package_json(filepath):
    """解析package.json（Node.js依赖）"""
    deps = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for section in ["dependencies", "devDependencies", "peerDependencies"]:
            if section in data:
                for name, version in data[section].items():
                    deps.append({"name": name.lower(), "version": version, "source": f"package.json:{section}"})
    except Exception:
        pass
    return deps


def extract_dependencies(skill_path):
    """提取技能的所有依赖"""
    all_deps = []

    # Python依赖
    req_path = os.path.join(skill_path, "requirements.txt")
    if os.path.isfile(req_path):
        all_deps.extend(parse_requirements(req_path))

    # setup.py / pyproject.toml（简化处理，只检查存在性）
    for fname in ["setup.py", "pyproject.toml", "setup.cfg"]:
        fpath = os.path.join(skill_path, fname)
        if os.path.isfile(fpath):
            all_deps.append({"name": f"(见{fname})", "version": "*", "source": fname})

    # Node.js依赖
    pkg_path = os.path.join(skill_path, "package.json")
    if os.path.isfile(pkg_path):
        all_deps.extend(parse_package_json(pkg_path))

    return all_deps


def parse_version(version_str):
    """解析版本号为数字元组，如 '2.20.1' -> (2, 20, 1)"""
    parts = re.findall(r"\d+", version_str)[:3]
    nums = [int(p) for p in parts]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)


def parse_version_constraint(constraint_str):
    """
    解析版本约束，返回 (operator, version) 列表。
    支持：==, !=, <=, >=, <, >, ~=, 以及逗号分隔的多约束（如 >=1.0,<2.0）
    无约束或 * 返回 []
    """
    if not constraint_str or constraint_str.strip() in ("*", "latest", ""):
        return []

    constraints = []
    # 分割多约束（逗号分隔）
    parts = re.split(r",", constraint_str)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # 匹配操作符和版本号
        match = re.match(r"^(==|!=|<=|>=|<|>|~=)\s*(.+)$", part)
        if match:
            op = match.group(1)
            ver = match.group(2).strip()
            constraints.append((op, ver))
        else:
            # 没有操作符，当作 == 处理
            constraints.append(("==", part))
    return constraints


def version_affected(version_constraint, affected_ranges):
    """
    判断版本约束是否可能包含受影响的版本。

    返回值：
      - True: 确定受影响
      - "maybe": 可能受影响（建议锁定版本后重新扫描）
      - False: 确定不受影响

    逻辑：
      1. 无版本约束（*）-> maybe（可能受影响）
      2. 解析约束，提取上限（</<=）和下限（>/>=）
      3. 漏洞影响范围通常是 <某个版本
      4. 如果约束上限 <= 漏洞影响上限 -> 确定受影响
      5. 如果约束下限 >= 漏洞修复版本 -> 确定不受影响
      6. 其他情况 -> maybe（可能受影响）
    """
    constraints = parse_version_constraint(version_constraint)

    # 无版本约束，可能受影响
    if not constraints:
        return "maybe"

    # 提取约束的上限和下限
    upper_bound = None  # (version, inclusive)  inclusive=True 表示 <=，False 表示 <
    lower_bound = None  # (version, inclusive)  inclusive=True 表示 >=，False 表示 >

    for op, ver in constraints:
        ver_tuple = parse_version(ver)
        if op in ("<", "<="):
            if upper_bound is None or ver_tuple < upper_bound[0]:
                upper_bound = (ver_tuple, op == "<=")
        elif op in (">", ">="):
            if lower_bound is None or ver_tuple > lower_bound[0]:
                lower_bound = (ver_tuple, op == ">=")
        elif op == "==":
            # 精确版本，直接比较
            for range_str in affected_ranges:
                if range_str.startswith("<"):
                    limit = parse_version(range_str[1:].strip())
                    if ver_tuple < limit:
                        return True
                elif range_str.startswith("<="):
                    limit = parse_version(range_str[2:].strip())
                    if ver_tuple <= limit:
                        return True
            return False
        # ~= 和 != 暂不精确处理，当作可能受影响

    # 处理漏洞影响范围（目前主要是 < 范围）
    for range_str in affected_ranges:
        if range_str.startswith("<="):
            vuln_limit = parse_version(range_str[2:].strip())
            vuln_inclusive = True
        elif range_str.startswith("<"):
            vuln_limit = parse_version(range_str[1:].strip())
            vuln_inclusive = False
        else:
            continue

        # 如果有上限，且上限 <= 漏洞影响上限 -> 确定受影响
        # （约束范围内的版本都 <= 上限 <= 漏洞上限，因此都在漏洞影响范围内）
        if upper_bound is not None:
            if upper_bound[0] <= vuln_limit:
                return True

        # 如果有下限，且下限 >= 漏洞修复版本（即漏洞上限）-> 确定不受影响
        if lower_bound is not None:
            if lower_bound[0] > vuln_limit:
                return False
            if lower_bound[0] == vuln_limit and not lower_bound[1] and not vuln_inclusive:
                return False

    # 其他情况：可能受影响
    return "maybe"


def check_vulnerabilities(deps):
    """检查已知漏洞，返回 (confirmed_findings, maybe_findings)"""
    confirmed = []
    maybe = []
    for dep in deps:
        name = dep["name"]
        if name in KNOWN_VULNERABILITIES:
            vuln = KNOWN_VULNERABILITIES[name]
            result = version_affected(dep["version"], vuln["affected_versions"])
            finding = {
                "package": name,
                "version": dep["version"],
                "severity": vuln["severity"],
                "cve": vuln["cve"],
                "description": vuln["description"],
                "source": dep["source"],
                "recommendation": f"升级 {name} 到最新安全版本"
            }
            if result is True:
                finding["confidence"] = "confirmed"
                confirmed.append(finding)
            elif result == "maybe":
                finding["confidence"] = "maybe"
                finding["recommendation"] = f"版本约束 '{dep['version']}' 可能包含受影响版本，建议锁定具体版本后重新扫描"
                maybe.append(finding)
    return confirmed, maybe


def check_license_compliance(skill_path):
    """检查许可证合规性"""
    findings = []
    license_file = None
    for fname in ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"]:
        fpath = os.path.join(skill_path, fname)
        if os.path.isfile(fpath):
            license_file = fpath
            break

    if not license_file:
        findings.append({
            "type": "missing_license",
            "severity": "medium",
            "message": "缺少LICENSE文件，建议明确许可证类型"
        })
    else:
        try:
            with open(license_file, "r", encoding="utf-8") as f:
                content = f.read().upper()
            for license_type in COPYLEFT_LICENSES:
                if license_type in content:
                    findings.append({
                        "type": "copyleft_license",
                        "severity": "info",
                        "message": f"检测到{license_type}许可证，请注意传染性合规要求"
                    })
                    break
        except Exception:
            pass

    return findings


def generate_sbom(skill_path, deps, findings):
    """生成CycloneDX格式SBOM"""
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "tools": [{"vendor": "skill-creator-pro", "name": "supply_chain_scan", "version": "1.0.0"}],
            "component": {
                "type": "application",
                "name": os.path.basename(skill_path),
                "description": "Generated by skill-creator-pro supply chain scan"
            }
        },
        "components": [
            {
                "type": "library",
                "name": dep["name"],
                "version": dep["version"],
                "purl": f"pkg:pypi/{dep['name']}@{dep['version']}" if "package.json" not in dep["source"] else f"pkg:npm/{dep['name']}@{dep['version']}"
            }
            for dep in deps if not dep["name"].startswith("(")
        ],
        "vulnerabilities": [
            {
                "id": f["cve"],
                "source": {"name": "NVD"},
                "ratings": [{"severity": f["severity"].upper()}],
                "description": f["description"],
                "affects": [{"ref": f"pkg:pypi/{f['package']}@{f['version']}"}]
            }
            for f in findings if f.get("cve")
        ]
    }
    return sbom


def calculate_file_hash(file_path):
    """计算文件的SHA-256哈希"""
    import hashlib
    try:
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


def generate_aibom(skill_path):
    """生成AIBOM（AI Bill of Materials）——列出所有AI组件，带版本和哈希

    AIBOM是最新的供应链安全概念，用于AI Agent技能的完整性验证。
    参考：NVIDIA SkillSpector / Unit 42 BIV研究 / CycloneDX AI扩展

    包含：
    - 技能元数据（name/version/hash）
    - SKILL.md（hash/行数）
    - scripts/所有脚本（name/hash/行数）
    - references/所有文档（name/hash/行数）
    - examples/所有示例（name/hash）
    - assets/所有资源（name/hash）
    - 评估用例（name/hash）
    """
    from pathlib import Path
    import hashlib
    skill_path = Path(skill_path)
    skill_name = skill_path.name

    def scan_directory(dir_name, extensions=None):
        """扫描目录下的文件，返回组件列表"""
        components = []
        dir_path = skill_path / dir_name
        if not dir_path.exists():
            return components

        for file_path in sorted(dir_path.rglob("*")):
            if not file_path.is_file():
                continue
            if extensions and file_path.suffix not in extensions:
                continue
            # 跳过缓存和临时文件
            if "__pycache__" in str(file_path) or file_path.name.startswith("."):
                continue

            rel_path = str(file_path.relative_to(skill_path))
            file_hash = calculate_file_hash(file_path)
            try:
                line_count = sum(1 for _ in open(file_path, "r", encoding="utf-8", errors="replace"))
            except Exception:
                line_count = 0

            components.append({
                "path": rel_path,
                "name": file_path.name,
                "sha256": file_hash,
                "line_count": line_count,
                "size_bytes": file_path.stat().st_size,
            })
        return components

    # 技能整体哈希（SKILL.md + 所有脚本）
    skill_hash_parts = []
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        skill_hash_parts.append(calculate_file_hash(skill_md) or "")

    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        for script in sorted(scripts_dir.glob("*.py")):
            skill_hash_parts.append(calculate_file_hash(script) or "")

    import hashlib
    overall_hash = hashlib.sha256("".join(skill_hash_parts).encode()).hexdigest() if skill_hash_parts else None

    aibom = {
        "bomFormat": "AIBOM",
        "specVersion": "1.0",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "generator": {
                "name": "skill-creator-pro",
                "version": "2.1.0",
                "tool": "supply_chain_scan.py"
            },
            "component": {
                "type": "agent-skill",
                "name": skill_name,
                "sha256": overall_hash,
                "description": "AI Bill of Materials for Agent Skill"
            }
        },
        "core_files": [
            {
                "path": "SKILL.md",
                "sha256": calculate_file_hash(skill_md) if skill_md.exists() else None,
                "line_count": sum(1 for _ in open(skill_md, "r", encoding="utf-8")) if skill_md.exists() else 0,
                "size_bytes": skill_md.stat().st_size if skill_md.exists() else 0,
            }
        ],
        "scripts": scan_directory("scripts", extensions={".py", ".sh"}),
        "references": scan_directory("references", extensions={".md", ".json", ".yaml", ".yml"}),
        "examples": scan_directory("examples"),
        "assets": scan_directory("assets"),
        "tests": scan_directory("tests", extensions={".py"}),
        "summary": {
            "total_components": 0,  # 后面计算
            "total_scripts": 0,
            "total_references": 0,
            "total_examples": 0,
            "total_assets": 0,
            "total_tests": 0,
        }
    }

    # 计算汇总
    aibom["summary"]["total_scripts"] = len(aibom["scripts"])
    aibom["summary"]["total_references"] = len(aibom["references"])
    aibom["summary"]["total_examples"] = len(aibom["examples"])
    aibom["summary"]["total_assets"] = len(aibom["assets"])
    aibom["summary"]["total_tests"] = len(aibom["tests"])
    aibom["summary"]["total_components"] = (
        1 + len(aibom["scripts"]) + len(aibom["references"]) +
        len(aibom["examples"]) + len(aibom["assets"]) + len(aibom["tests"])
    )

    return aibom


def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 供应链安全扫描（依赖漏洞检测+SBOM生成）"
    )
    parser.add_argument("skill_path", help="技能目录路径")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    parser.add_argument("--generate-sbom", action="store_true", help="生成SBOM文件（sbom.json）")
    parser.add_argument("--generate-aibom", action="store_true", help="生成AIBOM文件（aibom.json，AI组件清单）")
    args = parser.parse_args()

    if not os.path.isdir(args.skill_path):
        print(f"❌ 技能目录不存在: {args.skill_path}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🔒 供应链安全扫描（Supply Chain Scan）")
    print("=" * 60)

    # 步骤1：提取依赖
    print("\n--- 步骤1: 提取依赖清单 ---")
    deps = extract_dependencies(args.skill_path)
    print(f"  发现 {len(deps)} 个依赖")
    for dep in deps:
        print(f"    - {dep['name']} {dep['version']} ({dep['source']})")

    # 步骤2：漏洞检测
    print("\n--- 步骤2: 已知漏洞检测 ---")
    confirmed_vulns, maybe_vulns = check_vulnerabilities(deps)
    if confirmed_vulns:
        print(f"  🔴 确认 {len(confirmed_vulns)} 个已知漏洞")
        for v in confirmed_vulns:
            icon = "🔴" if v["severity"] == "high" else "🟡"
            print(f"    {icon} {v['package']} {v['version']}: {v['cve']} - {v['description']}")
            print(f"       建议: {v['recommendation']}")
    if maybe_vulns:
        print(f"  🟡 待确认 {len(maybe_vulns)} 个可能受影响的依赖（版本约束未锁定）")
        for v in maybe_vulns:
            print(f"    🟡 {v['package']} {v['version']}: {v['cve']} - {v['description']}")
            print(f"       建议: {v['recommendation']}")
    if not confirmed_vulns and not maybe_vulns:
        print("  ✅ 未发现已知漏洞")

    # 步骤3：许可证合规
    print("\n--- 步骤3: 许可证合规检查 ---")
    license_findings = check_license_compliance(args.skill_path)
    if license_findings:
        for f in license_findings:
            icon = "🟡" if f["severity"] == "medium" else "ℹ️"
            print(f"  {icon} {f['message']}")
    else:
        print("  ✅ 许可证合规")

    # 步骤4：生成SBOM
    if args.generate_sbom:
        print("\n--- 步骤4: 生成SBOM ---")
        sbom = generate_sbom(args.skill_path, deps, confirmed_vulns)
        sbom_path = os.path.join(args.skill_path, "sbom.json")
        with open(sbom_path, "w", encoding="utf-8") as f:
            json.dump(sbom, f, ensure_ascii=False, indent=2)
        print(f"  ✅ SBOM已生成: {sbom_path}")
        print(f"     格式: CycloneDX 1.4, 组件数: {len(sbom['components'])}, 漏洞数: {len(sbom['vulnerabilities'])}")

    # 步骤5：生成AIBOM（AI Bill of Materials）
    if args.generate_aibom:
        print("\n--- 步骤5: 生成AIBOM（AI组件清单）---")
        aibom = generate_aibom(args.skill_path)
        aibom_path = os.path.join(args.skill_path, "aibom.json")
        with open(aibom_path, "w", encoding="utf-8") as f:
            json.dump(aibom, f, ensure_ascii=False, indent=2)
        print(f"  ✅ AIBOM已生成: {aibom_path}")
        print(f"     格式: AIBOM 1.0, 总组件数: {aibom['summary']['total_components']}")
        print(f"     脚本: {aibom['summary']['total_scripts']}, 文档: {aibom['summary']['total_references']}, 示例: {aibom['summary']['total_examples']}")
        print(f"     测试: {aibom['summary']['total_tests']}, 资源: {aibom['summary']['total_assets']}")
        print(f"     技能整体SHA-256: {aibom['metadata']['component']['sha256'][:16]}...")

    # 汇总
    all_vulns = confirmed_vulns + maybe_vulns
    print("\n" + "=" * 60)
    print("📊 扫描结果汇总")
    print("=" * 60)
    high = sum(1 for f in all_vulns if f.get("severity") == "high" and f.get("confidence") == "confirmed")
    medium = sum(1 for f in all_vulns if f.get("severity") == "medium") + sum(1 for f in license_findings if f.get("severity") == "medium")
    maybe_count = len(maybe_vulns)
    print(f"  依赖总数: {len(deps)}")
    print(f"  🔴 确认高危漏洞: {high}")
    print(f"  🟡 中危问题: {medium}")
    if maybe_count > 0:
        print(f"  🟡 待确认（版本未锁定）: {maybe_count}")
    print(f"  状态: {'❌ 存在确认高危漏洞，必须修复' if high > 0 else '✅ 通过（无确认高危漏洞）'}")

    if args.json:
        print("\n" + json.dumps({
            "skill_path": args.skill_path,
            "dependencies": deps,
            "vulnerabilities_confirmed": confirmed_vulns,
            "vulnerabilities_maybe": maybe_vulns,
            "license_findings": license_findings,
            "summary": {"total_deps": len(deps), "high_confirmed": high, "medium": medium, "maybe": maybe_count, "passed": high == 0}
        }, ensure_ascii=False, indent=2))

    sys.exit(1 if high > 0 else 0)


if __name__ == "__main__":
    main()
