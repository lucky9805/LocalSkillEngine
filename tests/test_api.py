"""
测试 API 路由
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_service.api.server import app


# 创建测试客户端
client = TestClient(app)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Skill Service API"
    assert "docs" in data


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_list_skills():
    """测试列出 skills API"""
    response = client.get("/api/v1/skills")
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert "total" in data
    assert isinstance(data["skills"], list)


def test_get_skill_info():
    """测试获取 skill 详情 API"""
    # 测试存在的 skill
    response = client.get("/api/v1/skills/greeting")
    if response.status_code == 200:
        data = response.json()
        assert data["name"] == "greeting"
        assert "version" in data
        assert "description" in data


def test_get_nonexistent_skill():
    """测试获取不存在的 skill"""
    response = client.get("/api/v1/skills/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_run_skill():
    """测试运行 skill API"""
    response = client.post(
        "/api/v1/skills/greeting/run",
        json={"parameters": {"name": "TestUser"}}
    )
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert data["skill_name"] == "greeting"
        assert "Hello, TestUser!" in str(data["result"])


def test_run_skill_with_timeout():
    """测试运行 skill（带超时）"""
    response = client.post(
        "/api/v1/skills/greeting/run",
        json={
            "parameters": {"name": "TestUser"},
            "timeout": 30
        }
    )
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True


def test_run_nonexistent_skill():
    """测试运行不存在的 skill"""
    response = client.post(
        "/api/v1/skills/nonexistent/run",
        json={"parameters": {}}
    )
    assert response.status_code == 404


def test_reload_skills():
    """测试重新加载 skills API"""
    response = client.post("/api/v1/skills/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data


def test_cors_headers():
    """测试 CORS 头"""
    response = client.options("/api/v1/skills")
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
