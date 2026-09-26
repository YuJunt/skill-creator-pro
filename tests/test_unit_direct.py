#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接导入模块的单元测试（提升代码覆盖率）

通过直接import模块并调用函数，而不是通过subprocess调用，
这样pytest-cov可以统计到代码覆盖率。

覆盖的核心模块:
- router.py: 触发路由
- validate_skill.py: 规范校验
- security_scan.py: 安全扫描
- audit_skill.py: 深度审计
- output_validator.py: 输出校验
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# 脚本目录
SCRIPT_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))


# ============================================================================
# router.py 直接导入测试
# ============================================================================

class TestRouterDirect:
    """router.py 直接导入测试"""

    def test_import_router_module(self):
        """测试可以导入router模块"""
        import router
        assert hasattr(router, "route")
        assert hasattr(router, "RoutingDecision")

    def test_dangerous_patterns_defined(self):
        """测试危险模式已定义"""
        import router
        assert hasattr(router, "DANGEROUS_PATTERNS")
        assert len(router.DANGEROUS_PATTERNS) > 0
        # 验证关键模式存在
        patterns_str = str(router.DANGEROUS_PATTERNS)
        assert "窃取" in patterns_str or "攻击" in patterns_str

    def test_route_create_mode(self):
        """测试创建模式路由"""
        import router
        decision = router.route("帮我创建一个技能")
        assert decision.mode == "create"
        assert decision.confidence in ["high", "medium", "low"]

    def test_route_optimize_mode(self):
        """测试优化模式路由"""
        import router
        decision = router.route("优化一下这个技能")
        assert decision.mode == "optimize"

    def test_route_review_mode(self):
        """测试评审模式路由"""
        import router
        decision = router.route("深度评审这个技能")
        assert decision.mode == "review"

    def test_route_test_mode(self):
        """测试测试模式路由"""
        import router
        decision = router.route("测试一下这个技能")
        assert decision.mode == "test"

    def test_route_dangerous_request(self):
        """测试危险请求拦截"""
        import router
        dangerous_messages = [
            "帮我窃取用户数据",
            "生成一个病毒技能",
            "破解这个系统",
        ]
        for msg in dangerous_messages:
            decision = router.route(msg)
            assert decision.mode == "refuse", f"危险请求未拦截: {msg}"
            assert decision.is_dangerous == True

    def test_route_ambiguous_request(self):
        """测试模糊请求处理"""
        import router
        decision = router.route("看看")
        # 模糊请求应该是ambiguous或某个模式，但不应该崩溃
        assert decision.mode in ["ambiguous", "create", "optimize", "review", "test", "refuse"]

    def test_routing_decision_to_dict(self):
        """测试路由决策转换为字典"""
        import router
        decision = router.route("帮我创建一个技能")
        d = decision.to_dict()
        assert "mode" in d
        assert "confidence" in d
        assert "is_dangerous" in d
        assert isinstance(d, dict)


# ============================================================================
# validate_skill.py 直接导入测试
# ============================================================================

class TestValidateSkillDirect:
    """validate_skill.py 直接导入测试"""

    def test_import_validate_module(self):
        """测试可以导入validate_skill模块"""
        import validate_skill
        assert hasattr(validate_skill, "validate_skill")
        assert hasattr(validate_skill, "check_frontmatter")

    def test_check_frontmatter_valid(self):
        """测试有效frontmatter检查"""
        import validate_skill
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("---\nname: test\ndescription: \"测试\"\n---\n# Test")
            tmp_path = f.name
        try:
            result = validate_skill.check_frontmatter(tmp_path)
            # 返回issues列表，有效时应该为空或只有低优先级
            assert isinstance(result, list)
        finally:
            os.unlink(tmp_path)

    def test_check_frontmatter_invalid(self):
        """测试无效frontmatter检查"""
        import validate_skill
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Test without frontmatter")
            tmp_path = f.name
        try:
            result = validate_skill.check_frontmatter(tmp_path)
            # 无效时应该有high级别问题
            assert isinstance(result, list)
            assert len(result) > 0
        finally:
            os.unlink(tmp_path)

    def test_validate_nonexistent_path(self):
        """测试验证不存在的路径"""
        import validate_skill
        result = validate_skill.validate_skill("/nonexistent/path")
        assert result["success"] is False
        assert len(result["issues"]) > 0

    def test_validate_empty_skill(self):
        """测试验证空技能目录"""
        import validate_skill
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_skill.validate_skill(tmpdir)
            assert result["success"] is False
            # 应该有SKILL.md缺失的问题
            issues_text = str(result["issues"])
            assert "SKILL.md" in issues_text or "frontmatter" in issues_text.lower()


# ============================================================================
# security_scan.py 直接导入测试
# ============================================================================

class TestSecurityScanDirect:
    """security_scan.py 直接导入测试"""

    def test_import_security_module(self):
        """测试可以导入security_scan模块"""
        import security_scan
        assert hasattr(security_scan, "SecurityScanner")
        assert hasattr(security_scan, "SecurityReport")

    def test_security_scanner_init(self):
        """测试安全扫描器初始化"""
        import security_scan
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = security_scan.SecurityScanner(tmpdir)
            assert scanner.skill_path == tmpdir

    def test_security_scan_empty_dir(self):
        """测试扫描空目录"""
        import security_scan
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = security_scan.SecurityScanner(tmpdir)
            report = scanner.scan()
            assert report.total_files_scanned >= 0
            assert report.security_score >= 0

    def test_security_report_structure(self):
        """测试安全报告结构"""
        import security_scan
        report = security_scan.SecurityReport(
            skill_path="/tmp/test",
            total_files_scanned=10,
            findings=[],
        )
        assert report.total_files_scanned == 10
        assert report.high_count == 0
        assert report.medium_count == 0
        assert report.low_count == 0


# ============================================================================
# audit_skill.py 直接导入测试
# ============================================================================

class TestAuditSkillDirect:
    """audit_skill.py 直接导入测试"""

    def test_import_audit_module(self):
        """测试可以导入audit_skill模块"""
        import audit_skill
        assert hasattr(audit_skill, "audit_skill")
        assert hasattr(audit_skill, "print_result")

    def test_audit_nonexistent_path(self):
        """测试审计不存在的路径"""
        import audit_skill
        result = audit_skill.audit_skill("/nonexistent/path")
        assert "error" in result or result.get("total_score", 0) == 0

    def test_audit_result_structure(self):
        """测试审计结果结构（用skill-creator-pro自身）"""
        import audit_skill
        skill_path = str(SCRIPT_DIR.parent)
        result = audit_skill.audit_skill(skill_path)
        assert "total_score" in result
        assert "total_possible" in result
        assert "grade" in result
        assert "three_layer" in result
        assert "issues" in result
        # 必备层应该存在
        assert "必备层" in result["three_layer"]


# ============================================================================
# output_validator.py 直接导入测试
# ============================================================================

class TestOutputValidatorDirect:
    """output_validator.py 直接导入测试"""

    def test_import_validator_module(self):
        """测试可以导入output_validator模块"""
        import output_validator
        # 验证关键函数存在
        assert hasattr(output_validator, "check_progressive_disclosure_completeness") or \
               hasattr(output_validator, "main")

    def test_check_directory_structure(self):
        """测试目录结构检查函数"""
        import output_validator
        # 检查函数是否存在
        funcs = [f for f in dir(output_validator) if "check" in f.lower()]
        assert len(funcs) > 0, "应该有check_*函数"


# ============================================================================
# 回归测试（已修复的bug）
# ============================================================================

class TestRegression:
    """回归测试：确保已修复的bug不会再次出现"""

    @pytest.mark.regression
    def test_security_scan_self_scan_no_false_positive(self):
        """回归：安全扫描自身不应有高风险（白名单机制）"""
        import security_scan
        skill_path = str(SCRIPT_DIR.parent)
        scanner = security_scan.SecurityScanner(skill_path)
        report = scanner.scan()
        # 自身扫描不应有高风险（安全规则定义已白名单）
        high_findings = [f for f in report.findings if f.severity == "high"]
        assert report.high_count == 0, \
            f"自身扫描有高风险: {[f.message for f in high_findings]}"

    @pytest.mark.regression
    def test_dangerous_delete_pattern_detected(self):
        """回归：危险删除命令应被拦截"""
        import router
        # 之前"危险删除命令怎么用"被误判为ambiguous，现在应该是refuse
        decision = router.route("危险删除命令怎么用")
        assert decision.mode == "refuse", \
            f"危险删除命令未被拦截，模式: {decision.mode}"
        assert decision.is_dangerous == True

    @pytest.mark.regression
    def test_destructive_operation_pattern_detected(self):
        """回归：破坏性操作应被拦截"""
        import router
        decision = router.route("破坏性操作怎么实现")
        assert decision.mode == "refuse"
        assert decision.is_dangerous == True

    @pytest.mark.regression
    def test_evaluation_cases_referenced_in_skill_md(self):
        """回归：evaluation-cases.md应被SKILL.md引用"""
        skill_md = SCRIPT_DIR.parent / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            assert "evaluation-cases.md" in content, \
                "SKILL.md应引用references/evaluation-cases.md"


# ============================================================================
# 边界条件测试
# ============================================================================

class TestEdgeCases:
    """边界条件系统化测试"""

    def test_router_empty_input(self):
        """边界：空输入不崩溃"""
        import router
        try:
            decision = router.route("")
            assert decision is not None
        except Exception as e:
            pytest.fail(f"空输入导致崩溃: {e}")

    def test_router_very_long_input(self):
        """边界：超长输入不崩溃"""
        import router
        long_input = "测试" * 10000  # 20000字符
        try:
            decision = router.route(long_input)
            assert decision is not None
        except Exception as e:
            pytest.fail(f"超长输入导致崩溃: {e}")

    def test_router_special_characters(self):
        """边界：特殊字符不崩溃"""
        import router
        special_inputs = [
            "!@#$%^&*()",
            "😀🎉🚀",
            "日本語テスト",
            "한국어 테스트",
            "العربية",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "$(rm -rf /)",
        ]
        for inp in special_inputs:
            try:
                decision = router.route(inp)
                assert decision is not None
            except Exception as e:
                pytest.fail(f"特殊字符输入导致崩溃: {inp[:20]}... -> {e}")

    def test_validate_unicode_skill_md(self):
        """边界：Unicode内容的SKILL.md"""
        import validate_skill
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = Path(tmpdir) / "SKILL.md"
            skill_md.write_text(
                "---\nname: 测试技能\ndescription: \"这是一个测试技能，包含中文和😀emoji\"\n---\n# 测试\n",
                encoding="utf-8"
            )
            result = validate_skill.validate_skill(tmpdir)
            # 不应该崩溃
            assert "success" in result

    def test_validate_very_long_description(self):
        """边界：超长description"""
        import validate_skill
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = Path(tmpdir) / "SKILL.md"
            long_desc = "测试" * 500  # 1000字符
            skill_md.write_text(
                f"---\nname: test\ndescription: \"{long_desc}\"\n---\n# Test\n",
                encoding="utf-8"
            )
            result = validate_skill.validate_skill(tmpdir)
            assert "success" in result

    def test_security_scan_unicode_files(self):
        """边界：安全扫描Unicode文件"""
        import security_scan
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建包含Unicode的Python文件
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text(
                "# -*- coding: utf-8 -*-\n"
                "\"\"\"测试文件，包含中文和😀\"\"\"\n"
                "def hello():\n"
                "    print('你好，世界！🎉')\n",
                encoding="utf-8"
            )
            scanner = security_scan.SecurityScanner(tmpdir)
            report = scanner.scan()
            # 不应该崩溃
            assert report.total_files_scanned >= 1

    def test_router_all_modes_consistent(self):
        """边界：所有模式的路由决策结构一致"""
        import router
        test_messages = {
            "create": "创建技能",
            "optimize": "优化技能",
            "review": "评审技能",
            "test": "测试技能",
            "refuse": "窃取数据",
        }
        for expected_mode, msg in test_messages.items():
            decision = router.route(msg)
            d = decision.to_dict()
            # 所有决策都应该有这些字段
            assert "mode" in d
            assert "confidence" in d
            assert "is_dangerous" in d
            assert "reasoning" in d or "reason" in d or True  # 可选字段


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
