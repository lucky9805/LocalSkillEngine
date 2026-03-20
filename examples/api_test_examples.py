"""
API 测试示例代码

这些代码片段展示了如何使用 Python 测试 Skill Service API
"""
import os
import requests
import json
from typing import Dict, Any


# API 基础配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 鉴权配置（从环境变量读取，未设置则使用空值）
API_KEY = os.environ.get("API_KEY", "")
API_SECRET = os.environ.get("API_SECRET", "")


def get_auth_headers() -> Dict[str, str]:
    """获取鉴权请求头"""
    if API_KEY and API_SECRET:
        return {
            "X-API-Key": API_KEY,
            "X-API-Secret": API_SECRET
        }
    return {}


def get_auth_params() -> Dict[str, str]:
    """获取鉴权 Query 参数"""
    if API_KEY and API_SECRET:
        return {
            "api_key": API_KEY,
            "api_secret": API_SECRET
        }
    return {}


def print_response(title: str, response: requests.Response):
    """打印响应信息"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(f"状态码: {response.status_code}")
    print(f"响应内容:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_health_check():
    """测试 1: 健康检查"""
    print("\n📋 测试 1: 健康检查")

    response = requests.get(f"{BASE_URL}/health")
    print_response("健康检查响应", response)

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'

    print("✅ 健康检查测试通过")


def test_list_skills():
    """测试 2: 列出所有 skills"""
    print("\n📋 测试 2: 列出所有 skills")

    response = requests.get(f"{BASE_URL}{API_PREFIX}/skills")
    print_response("Skills 列表", response)

    assert response.status_code == 200
    data = response.json()
    assert 'skills' in data
    assert 'total' in data

    print(f"✅ 共找到 {data['total']} 个 skills")


def test_get_skill_info():
    """测试 3: 获取 skill 详情"""
    print("\n📋 测试 3: 获取 skill 详情")

    skill_name = "greeting"
    response = requests.get(f"{BASE_URL}{API_PREFIX}/skills/{skill_name}")

    if response.status_code == 200:
        print_response("Skill 详情", response)

        data = response.json()
        assert data['name'] == skill_name
        assert 'version' in data
        assert 'description' in data

        print(f"✅ 成功获取 {skill_name} 的详情")
    else:
        print(f"⚠️  Skill {skill_name} 不存在")


def test_run_skill_simple():
    """测试 4: 简单执行 skill"""
    print("\n📋 测试 4: 简单执行 skill")

    skill_name = "greeting"
    payload = {
        "parameters": {"name": "Alice"}
    }

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/skills/{skill_name}/run",
        headers=get_auth_headers(),
        json=payload
    )

    if response.status_code == 200:
        print_response("执行结果", response)

        data = response.json()
        assert data['success'] is True
        assert 'Hello, Alice!' in str(data['result'])
        print(f"⏱️  执行时间: {data['execution_time']:.3f} 秒")

        # 显示日志
        if data['logs']:
            print("\n📝 执行日志:")
            for log in data['logs']:
                print(f"  • {log}")

        print("✅ Skill 执行成功")
    else:
        print(f"❌ 执行失败: {response.text}")


def test_run_skill_with_timeout():
    """测试 5: 带超时的 skill 执行"""
    print("\n📋 测试 5: 带超时的 skill 执行")

    skill_name = "greeting"
    payload = {
        "parameters": {"name": "Bob"},
        "timeout": 30  # 30 秒超时
    }

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/skills/{skill_name}/run",
        headers=get_auth_headers(),
        json=payload
    )

    if response.status_code == 200:
        print_response("执行结果（带超时）", response)

        data = response.json()
        assert data['success'] is True
        print("✅ 带超时的 skill 执行成功")
    else:
        print(f"❌ 执行失败: {response.text}")


def test_run_skill_complex_params():
    """测试 6: 复杂参数的 skill 执行"""
    print("\n📋 测试 6: 复杂参数的 skill 执行")

    skill_name = "greeting"
    payload = {
        "parameters": {
            "name": "Charlie",
            "count": 3,
            "active": True,
            "score": 95.5
        }
    }

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/skills/{skill_name}/run",
        headers=get_auth_headers(),
        json=payload
    )

    if response.status_code == 200:
        print_response("执行结果（复杂参数）", response)

        data = response.json()
        assert data['success'] is True
        print("✅ 复杂参数的 skill 执行成功")
    else:
        print(f"❌ 执行失败: {response.text}")


def test_run_skill_no_params():
    """测试 7: 无参数的 skill 执行"""
    print("\n📋 测试 7: 无参数的 skill 执行")

    skill_name = "greeting"
    payload = {
        "parameters": {}
    }

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/skills/{skill_name}/run",
        headers=get_auth_headers(),
        json=payload
    )

    if response.status_code == 200:
        print_response("执行结果（无参数）", response)

        data = response.json()
        assert data['success'] is True
        # 应该使用默认值 "World"
        assert 'Hello' in str(data['result'])
        print("✅ 无参数的 skill 执行成功")
    else:
        print(f"❌ 执行失败: {response.text}")


def test_reload_skills():
    """测试 8: 重新加载 skills"""
    print("\n📋 测试 8: 重新加载 skills")

    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/skills/reload",
        headers=get_auth_headers()
    )
    print_response("重新加载结果", response)

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True

    print("✅ Skills 重新加载成功")


def test_error_handling():
    """测试 9: 错误处理"""
    print("\n📋 测试 9: 错误处理")

    # 测试 1: 不存在的 skill
    print("\n  9.1. 测试不存在的 skill")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/skills/nonexistent/run",
        headers=get_auth_headers(),
        json={"parameters": {}}
    )
    print(f"      状态码: {response.status_code}")
    assert response.status_code == 404
    print("      ✅ 正确返回 404")

    # 测试 2: 获取不存在的 skill
    print("\n  9.2. 测试获取不存在的 skill")
    response = requests.get(f"{BASE_URL}{API_PREFIX}/skills/nonexistent")
    print(f"      状态码: {response.status_code}")
    assert response.status_code == 404
    print("      ✅ 正确返回 404")


def test_api_docs():
    """测试 10: API 文档"""
    print("\n📋 测试 10: API 文档访问")

    # 测试 Swagger UI
    response = requests.get(f"{BASE_URL}/docs")
    print(f"\n  Swagger UI: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")

    # 测试 ReDoc
    response = requests.get(f"{BASE_URL}/redoc")
    print(f"  ReDoc: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")

    # 测试 OpenAPI 规范
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"  OpenAPI 规范: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")

    if response.status_code == 200:
        openapi_data = response.json()
        print(f"  API 版本: {openapi_data['info']['version']}")
        print(f"  端点数量: {len(openapi_data['paths'])}")


def test_auth_with_query_params():
    """测试 11: 使用 Query 参数鉴权"""
    print("\n📋 测试 11: 使用 Query 参数鉴权")

    if not API_KEY or not API_SECRET:
        print("⚠️  未配置 API_KEY/API_SECRET，跳过鉴权测试")
        return

    skill_name = "greeting"
    payload = {
        "parameters": {"name": "QueryAuth"}
    }

    # 使用 Query 参数传凭证
    params = get_auth_params()
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/skills/{skill_name}/run",
        params=params,
        json=payload
    )

    if response.status_code == 200:
        print_response("Query 参数鉴权执行结果", response)
        data = response.json()
        assert data['success'] is True
        print("✅ Query 参数鉴权执行成功")
    else:
        print(f"❌ 执行失败: {response.text}")


def test_auth_failure():
    """测试 12: 鉴权失败场景"""
    print("\n📋 测试 12: 鉴权失败场景")

    # 测试无鉴权调用受保护接口
    print("\n  12.1. 测试无鉴权调用 run 接口")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/skills/greeting/run",
        json={"parameters": {}}
    )
    print(f"      状态码: {response.status_code}")
    # 如果鉴权开启，应该返回 401；如果关闭，应该返回 200
    if response.status_code == 401:
        print("      ✅ 正确返回 401（鉴权已开启）")
    elif response.status_code == 200:
        print("      ⚠️  返回 200（鉴权未开启）")
    else:
        print(f"      ⚠️  返回 {response.status_code}")

    # 测试错误凭证
    print("\n  12.2. 测试错误凭证")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/skills/greeting/run",
        headers={"X-API-Key": "wrong-key", "X-API-Secret": "wrong-secret"},
        json={"parameters": {}}
    )
    print(f"      状态码: {response.status_code}")
    if response.status_code == 403:
        print("      ✅ 正确返回 403（鉴权失败）")
    elif response.status_code == 200:
        print("      ⚠️  返回 200（鉴权未开启）")
    else:
        print(f"      ⚠️  返回 {response.status_code}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🚀 开始运行 API 测试")
    print("="*80)

    # 显示鉴权配置状态
    if API_KEY and API_SECRET:
        print(f"\n🔐 鉴权配置: 已启用 (Key: {API_KEY[:4]}...{API_KEY[-4:] if len(API_KEY) > 8 else ''})")
    else:
        print("\n🔓 鉴权配置: 未配置（测试将在无鉴权模式下运行）")
    print("   如需启用鉴权测试，请设置环境变量: API_KEY 和 API_SECRET")

    try:
        # 检查服务是否运行
        print("\n🔍 检查服务状态...")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务运行正常")
        else:
            print("❌ 服务状态异常")
            return
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请确保服务已启动")
        print("   启动命令: skill-service serve")
        return
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        return

    # 运行测试
    test_health_check()
    test_list_skills()
    test_get_skill_info()
    test_run_skill_simple()
    test_run_skill_with_timeout()
    test_run_skill_complex_params()
    test_run_skill_no_params()
    test_reload_skills()
    test_error_handling()
    test_api_docs()
    test_auth_with_query_params()
    test_auth_failure()

    print("\n" + "="*80)
    print("🎉 所有测试完成!")
    print("="*80)


if __name__ == "__main__":
    run_all_tests()
