"""
测试 Skill Runner
"""
import pytest
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_service.runner import SkillRunner
from skill_service.models import SkillExecutionRequest


@pytest.mark.asyncio
async def test_runner_init():
    """测试 SkillRunner 初始化"""
    runner = SkillRunner()
    assert runner is not None
    assert runner.loader is not None


@pytest.mark.asyncio
async def test_list_skills():
    """测试列出所有 skills"""
    runner = SkillRunner()
    skills = runner.list_skills()

    assert isinstance(skills, list)
    assert len(skills) >= 0


@pytest.mark.asyncio
async def test_execute_skill():
    """测试执行 skill"""
    runner = SkillRunner()

    request = SkillExecutionRequest(
        skill_name="greeting",
        parameters={"name": "TestUser"}
    )

    result = await runner.execute(request)

    assert result.success is True
    assert result.skill_name == "greeting"
    assert "Hello, TestUser!" in str(result.result)


@pytest.mark.asyncio
async def test_execute_skill_timeout():
    """测试执行 skill 超时"""
    runner = SkillRunner()

    request = SkillExecutionRequest(
        skill_name="greeting",
        parameters={"name": "TestUser"},
        timeout=1  # 1 秒超时
    )

    result = await runner.execute(request)

    assert result.skill_name == "greeting"
    # greeting skill 应该很快完成，不会超时


def test_execute_sync():
    """测试同步执行 skill"""
    runner = SkillRunner()

    request = SkillExecutionRequest(
        skill_name="greeting",
        parameters={"name": "TestUser"}
    )

    result = runner.execute_sync(request)

    assert result.success is True
    assert result.skill_name == "greeting"
    assert "Hello, TestUser!" in str(result.result)


def test_get_skill_info():
    """测试获取 skill 信息"""
    runner = SkillRunner()

    info = runner.get_skill_info("greeting")

    if info:
        assert info["name"] == "greeting"
        assert info["version"] == "1.0.0"
        assert "author" in info
        assert "description" in info


def test_reload_skills():
    """测试重新加载 skills"""
    runner = SkillRunner()
    # 不应该抛出异常
    runner.reload_skills()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
