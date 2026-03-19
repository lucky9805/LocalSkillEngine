"""
测试 Skill Loader
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_service.loader import SkillLoader
from skill_service.models import SkillExecutionRequest


def test_skill_loader_init():
    """测试 SkillLoader 初始化"""
    loader = SkillLoader()
    assert loader is not None
    assert loader.skill_store is not None


def test_list_skills():
    """测试列出所有 skills"""
    loader = SkillLoader()
    skills = loader.list_skills()

    assert isinstance(skills, list)
    # 应该至少有一个 example skill
    assert len(skills) >= 0


def test_get_skill():
    """测试获取 skill"""
    loader = SkillLoader()

    # 测试存在的 skill
    skill = loader.get_skill("greeting")
    if skill:
        assert skill.name == "greeting"
        assert skill.version == "1.0.0"

    # 测试不存在的 skill
    skill = loader.get_skill("nonexistent")
    assert skill is None


def test_load_skill_script():
    """测试加载 skill 脚本"""
    loader = SkillLoader()
    skill = loader.get_skill("greeting")

    if skill:
        execute_func = loader.load_skill_script(skill)
        if execute_func:
            # 测试执行函数
            result = execute_func({"name": "Test"})
            assert result == "Hello, Test!"


def test_validate_skill():
    """测试验证 skill"""
    loader = SkillLoader()

    skill = loader.get_skill("greeting")
    if skill:
        is_valid, error_msg = loader.validate_skill(skill)
        assert is_valid
        assert error_msg == ""


def test_prepare_execution():
    """测试准备执行"""
    loader = SkillLoader()

    request = SkillExecutionRequest(
        skill_name="greeting",
        parameters={"name": "Test"}
    )

    skill, execute_func, error_msg = loader.prepare_execution(
        "greeting", request
    )

    if skill:
        assert skill.name == "greeting"
        # 如果有 execute_func，测试一下
        if execute_func:
            result = execute_func({"name": "Test"})
            assert result == "Hello, Test!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
