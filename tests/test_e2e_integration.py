#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-creator-pro 端到端集成测试套件

覆盖完整的技能生命周期流程：创建→优化→评审→测试→校验。
确保各脚本之间协作正常，流程完整可跑通。

运行方式：
  cd skill-creator-pro
  python3 -m pytest tests/test_e2e_integration.py -v
"""
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

# 技能根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(SKILL_ROOT, "scripts")


def run_script(script_name, *args, cwd=None):
    """运行脚本并返回CompletedProcess"""
    cmd = [sys.executable, os.path.join(SCRIPTS_DIR, script_name)] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or SKILL_ROOT)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_skill_dir():
    """创建临时技能目录，测试后自动清理"""
    tmpdir = tempfile.mkdtemp(prefix="e2e_test_")
    skill_dir = os.path.join(tmpdir, "test-skill")
    yield skill_dir, tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def created_skill(temp_skill_dir):
    """创建一个测试技能，供后续测试使用"""
    skill_dir, tmpdir = temp_skill_dir
    result = run_script("init_skill_pro.py", "test-skill", "--path", tmpdir, "--philosophy", "mixed")
    assert result.returncode == 0, f"创建技能失败: {result.stderr}"
    assert os.path.isdir(skill_dir)
    assert os.path.isfile(os.path.join(skill_dir, "SKILL.md"))
    return skill_dir


# ============================================================
# 端到端流程测试
# ============================================================

class TestE2ECreateSkill:
    """测试1：创建技能（init_skill_pro.py）"""

    def test_create_mixed_philosophy(self, temp_skill_dir):
        """测试创建mixed哲学技能"""
        skill_dir, tmpdir = temp_skill_dir
        result = run_script("init_skill_pro.py", "test-skill", "--path", tmpdir, "--philosophy", "mixed")
        assert result.returncode == 0
        assert os.path.isfile(os.path.join(skill_dir, "SKILL.md"))
        assert os.path.isdir(os.path.join(skill_dir, "scripts"))
        assert os.path.isdir(os.path.join(skill_dir, "references"))

    def test_create_capability_philosophy(self, temp_skill_dir):
        """测试创建capability哲学技能"""
        skill_dir, tmpdir = temp_skill_dir
        result = run_script("init_skill_pro.py", "test-skill", "--path", tmpdir, "--philosophy", "capability")
        assert result.returncode == 0
        assert os.path.isfile(os.path.join(skill_dir, "SKILL.md"))

    def test_create_process_philosophy(self, temp_skill_dir):
        """测试创建process哲学技能"""
        skill_dir, tmpdir = temp_skill_dir
        result = run_script("init_skill_pro.py", "test-skill", "--path", tmpdir, "--philosophy", "process")
        assert result.returncode == 0
        assert os.path.isfile(os.path.join(skill_dir, "SKILL.md"))

    def test_created_skill_description_has_trigger_words(self, created_skill):
        """测试创建的技能description包含触发词（三要素标准）"""
        with open(os.path.join(created_skill, "SKILL.md"), "r", encoding="utf-8") as f:
            content = f.read()
        assert "触发词" in content
        assert "不适用于" in content

    def test_created_skill_no_domain_residue(self, created_skill):
        """测试创建的技能没有特定领域残留"""
        result = run_script("output_validator.py", created_skill, "--mode", "create")
        assert result.returncode == 0, f"输出校验失败: {result.stdout}"


class TestE2EValidateSkill:
    """测试2：规范校验（validate_skill.py）"""

    def test_validate_created_skill(self, created_skill):
        """测试校验新创建的技能"""
        result = run_script("validate_skill.py", created_skill)
        assert result.returncode == 0, f"规范校验失败: {result.stdout}"
        assert "校验通过" in result.stdout

    def test_validate_nonexistent_path(self):
        """测试校验不存在的路径（应返回非0）"""
        result = run_script("validate_skill.py", "/tmp/nonexistent-path-12345")
        assert result.returncode != 0
        assert "不存在" in result.stderr


class TestE2ESecurityScan:
    """测试3：安全扫描（security_scan.py）"""

    def test_scan_created_skill(self, created_skill):
        """测试扫描新创建的技能"""
        result = run_script("security_scan.py", created_skill)
        assert result.returncode == 0
        assert "安全评分" in result.stdout

    def test_scan_nonexistent_path(self):
        """测试扫描不存在的路径（应返回非0）"""
        result = run_script("security_scan.py", "/tmp/nonexistent-path-12345")
        assert result.returncode != 0
        assert "不存在" in result.stderr

    def test_scan_skill_creator_pro_itself(self):
        """测试扫描skill-creator-pro自身（应100分A级）"""
        result = run_script("security_scan.py", SKILL_ROOT)
        assert result.returncode == 0
        assert "100/100" in result.stdout
        assert "A" in result.stdout


class TestE2EOrchestrator:
    """测试4：编排脚本（create_skill.py）各模式"""

    def test_optimize_mode_outputs_routing(self, created_skill):
        """测试optimize模式输出路由行（P3硬校验）"""
        result = run_script("create_skill.py", "optimize", created_skill)
        assert result.returncode == 0, f"optimize失败: {result.stdout}\n{result.stderr}"
        assert "🔀 路由: 优化技能" in result.stdout

    def test_optimize_mode_runs_output_validator(self, created_skill):
        """测试optimize模式调用output_validator（流程完整性）"""
        result = run_script("create_skill.py", "optimize", created_skill)
        assert result.returncode == 0
        assert "输出格式校验" in result.stdout

    def test_review_mode_outputs_routing(self, created_skill):
        """测试review模式输出路由行"""
        result = run_script("create_skill.py", "review", created_skill)
        assert result.returncode == 0, f"review失败: {result.stdout}\n{result.stderr}"
        assert "🔀 路由: 深度评审" in result.stdout

    def test_review_mode_runs_output_validator(self, created_skill):
        """测试review模式调用output_validator"""
        result = run_script("create_skill.py", "review", created_skill)
        assert result.returncode == 0
        assert "输出格式校验" in result.stdout

    def test_test_mode_outputs_routing(self, created_skill):
        """测试test模式输出路由行"""
        result = run_script("create_skill.py", "test", created_skill)
        assert result.returncode == 0, f"test失败: {result.stdout}\n{result.stderr}"
        assert "🔀 路由: 端到端测试" in result.stdout

    def test_create_mode_outputs_routing(self, temp_skill_dir):
        """测试create模式输出路由行"""
        skill_dir, tmpdir = temp_skill_dir
        result = run_script("create_skill.py", "create", "e2e-create-test", "--path", tmpdir, "--philosophy", "mixed")
        assert result.returncode == 0, f"create失败: {result.stdout}\n{result.stderr}"
        assert "🔀 路由: 新建技能" in result.stdout

    def test_invalid_mode_fails(self):
        """测试无效模式报错"""
        result = run_script("create_skill.py", "invalid_mode", "/tmp")
        assert result.returncode != 0

    def test_missing_mode_fails(self):
        """测试缺少模式参数报错（required=True硬门禁）"""
        result = run_script("create_skill.py")
        assert result.returncode != 0
        assert "required" in result.stderr


class TestE2EFullLifecycle:
    """测试5：完整生命周期（创建→优化→评审→测试）"""

    def test_full_lifecycle(self, temp_skill_dir):
        """测试完整技能生命周期流程"""
        skill_dir, tmpdir = temp_skill_dir

        # 步骤1：创建技能
        result = run_script("init_skill_pro.py", "lifecycle-test", "--path", tmpdir, "--philosophy", "mixed")
        assert result.returncode == 0, f"创建失败: {result.stderr}"
        skill_path = os.path.join(tmpdir, "lifecycle-test")
        assert os.path.isdir(skill_path)

        # 步骤2：规范校验
        result = run_script("validate_skill.py", skill_path)
        assert result.returncode == 0, f"规范校验失败: {result.stdout}"

        # 步骤3：安全扫描
        result = run_script("security_scan.py", skill_path)
        assert result.returncode == 0, f"安全扫描失败: {result.stdout}"

        # 步骤4：优化（编排脚本）
        result = run_script("create_skill.py", "optimize", skill_path)
        assert result.returncode == 0, f"优化失败: {result.stdout}"
        assert "🔀 路由: 优化技能" in result.stdout
        assert "输出格式校验" in result.stdout

        # 步骤5：评审（编排脚本）
        result = run_script("create_skill.py", "review", skill_path)
        assert result.returncode == 0, f"评审失败: {result.stdout}"
        assert "🔀 路由: 深度评审" in result.stdout

        # 步骤6：测试（编排脚本）
        result = run_script("create_skill.py", "test", skill_path)
        assert result.returncode == 0, f"测试失败: {result.stdout}"
        assert "🔀 路由: 端到端测试" in result.stdout

        # 步骤7：输出校验
        result = run_script("output_validator.py", skill_path, "--mode", "test")
        assert result.returncode == 0, f"输出校验失败: {result.stdout}"


class TestE2ERoutingP3:
    """测试6：P3路由行硬校验（所有模式都必须输出路由行）"""

    @pytest.mark.parametrize("mode,expected_routing", [
        ("optimize", "🔀 路由: 优化技能"),
        ("review", "🔀 路由: 深度评审"),
        ("test", "🔀 路由: 端到端测试"),
    ])
    def test_all_modes_output_routing(self, created_skill, mode, expected_routing):
        """测试所有模式都输出正确的路由行"""
        result = run_script("create_skill.py", mode, created_skill)
        assert result.returncode == 0
        assert expected_routing in result.stdout
        # 路由行应该在输出的前5行
        first_lines = result.stdout.split("\n")[:5]
        assert any(expected_routing in line for line in first_lines), \
            f"路由行不在前5行: {first_lines}"


class TestE2EErrorHandling:
    """测试7：错误处理（所有脚本对异常输入都应友好报错）"""

    def test_validate_nonexistent(self):
        """validate_skill.py不存在路径"""
        result = run_script("validate_skill.py", "/tmp/nonexistent-12345")
        assert result.returncode != 0
        assert "不存在" in result.stderr

    def test_security_nonexistent(self):
        """security_scan.py不存在路径"""
        result = run_script("security_scan.py", "/tmp/nonexistent-12345")
        assert result.returncode != 0
        assert "不存在" in result.stderr

    def test_output_validator_nonexistent(self):
        """output_validator.py不存在路径"""
        result = run_script("output_validator.py", "/tmp/nonexistent-12345")
        assert result.returncode != 0

    def test_orchestrator_nonexistent_skill(self):
        """create_skill.py优化不存在的技能"""
        result = run_script("create_skill.py", "optimize", "/tmp/nonexistent-12345")
        assert result.returncode != 0
        assert "不存在" in result.stderr
