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


def version_affected(version, affected_ranges):
    """简化版版本匹配（实际应使用语义化版本库）"""
    if version == "*" or not version:
        return True  # 未指定版本，默认可能受影响
    # 简化：只检查 < 范围
    for range_str in affected_ranges:
        if range_str.startswith("<"):
            try:
                limit = range_str[1:].strip()
                # 简单的版本比较（只比较数字部分）
                def parse_ver(v):
                    return [int(x) for x in re.findall(r"\d+", v)[:3]]
                current = parse_ver(version)
                target = parse_ver(limit)
                # 补齐长度
                max_len = max(len(current), len(target))
                current.extend([0] * (max_len - len(current)))
                target.extend([0] * (max_len - len(target)))
                if current < target:
                    return True
            except Exception:
                pass
    return False


def check_vulnerabilities(deps):
    """检查已知漏洞"""
    findings = []
    for dep in deps:
        name = dep["name"]
        if name in KNOWN_VULNERABILITIES:
            vuln = KNOWN_VULNERABILITIES[name]
            if version_affected(dep["version"], vuln["affected_versions"]):
                findings.append({
                    "package": name,
                    "version": dep["version"],
                    "severity": vuln["severity"],
                    "cve": vuln["cve"],
                    "description": vuln["description"],
                    "source": dep["source"],
                    "recommendation": f"升级 {name} 到最新安全版本"
                })
    return findings


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


def main():
    parser = argparse.ArgumentParser(
        description="skill-creator-pro 供应链安全扫描（依赖漏洞检测+SBOM生成）"
    )
    parser.add_argument("skill_path", help="技能目录路径")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    parser.add_argument("--generate-sbom", action="store_true", help="生成SBOM文件（sbom.json）")
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
    vuln_findings = check_vulnerabilities(deps)
    if vuln_findings:
        print(f"  ⚠️  发现 {len(vuln_findings)} 个已知漏洞")
        for v in vuln_findings:
            icon = "🔴" if v["severity"] == "high" else "🟡"
            print(f"    {icon} {v['package']} {v['version']}: {v['cve']} - {v['description']}")
            print(f"       建议: {v['recommendation']}")
    else:
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
    all_findings = vuln_findings + license_findings
    if args.generate_sbom:
        print("\n--- 步骤4: 生成SBOM ---")
        sbom = generate_sbom(args.skill_path, deps, vuln_findings)
        sbom_path = os.path.join(args.skill_path, "sbom.json")
        with open(sbom_path, "w", encoding="utf-8") as f:
            json.dump(sbom, f, ensure_ascii=False, indent=2)
        print(f"  ✅ SBOM已生成: {sbom_path}")
        print(f"     格式: CycloneDX 1.4, 组件数: {len(sbom['components'])}, 漏洞数: {len(sbom['vulnerabilities'])}")

    # 汇总
    print("\n" + "=" * 60)
    print("📊 扫描结果汇总")
    print("=" * 60)
    high = sum(1 for f in vuln_findings if f.get("severity") == "high")
    medium = sum(1 for f in vuln_findings if f.get("severity") == "medium") + sum(1 for f in license_findings if f.get("severity") == "medium")
    print(f"  依赖总数: {len(deps)}")
    print(f"  🔴 高危漏洞: {high}")
    print(f"  🟡 中危问题: {medium}")
    print(f"  状态: {'❌ 存在高危漏洞，必须修复' if high > 0 else '✅ 通过（无高危漏洞）'}")

    if args.json:
        print("\n" + json.dumps({
            "skill_path": args.skill_path,
            "dependencies": deps,
            "vulnerabilities": vuln_findings,
            "license_findings": license_findings,
            "summary": {"total_deps": len(deps), "high": high, "medium": medium, "passed": high == 0}
        }, ensure_ascii=False, indent=2))

    sys.exit(1 if high > 0 else 0)


if __name__ == "__main__":
    main()
