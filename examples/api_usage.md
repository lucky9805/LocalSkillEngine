# API 使用示例

本文档展示了 Skill Service HTTP API 的各种使用方法。

## 启动服务

```bash
# 使用 CLI 启动
skill-service serve

# 或使用 uvicorn 直接启动
uvicorn skill_service.api.server:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问以下地址：
- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## API 端点

### 1. 健康检查

检查服务健康状态。

**请求**:
```http
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### 2. 列出所有 Skills

获取所有可用的 skills 列表。

**请求**:
```http
GET /api/v1/skills
```

**cURL 示例**:
```bash
curl -X GET http://localhost:8000/api/v1/skills
```

**Python 示例**:
```python
import requests

response = requests.get('http://localhost:8000/api/v1/skills')
data = response.json()

print(f"总数: {data['total']}")
for skill in data['skills']:
    print(f"- {skill['name']}: {skill['description']}")
```

**响应**:
```json
{
  "skills": [
    {
      "name": "greeting",
      "version": "1.0.0",
      "category": "utility",
      "description": "打招呼技能 - 向指定的目标问好",
      "author": "Skill Service Team",
      "enabled": true,
      "status": "enabled"
    }
  ],
  "total": 1
}
```

### 3. 获取 Skill 详情

获取指定 skill 的详细信息。

**请求**:
```http
GET /api/v1/skills/{skill_name}
```

**cURL 示例**:
```bash
curl -X GET http://localhost:8000/api/v1/skills/greeting
```

**Python 示例**:
```python
import requests

skill_name = 'greeting'
response = requests.get(f'http://localhost:8000/api/v1/skills/{skill_name}')

if response.status_code == 200:
    skill_info = response.json()
    print(f"名称: {skill_info['name']}")
    print(f"版本: {skill_info['version']}")
    print(f"描述: {skill_info['description']}")
```

**响应**:
```json
{
  "name": "greeting",
  "version": "1.0.0",
  "author": "Skill Service Team",
  "category": "utility",
  "description": "打招呼技能 - 向指定的目标问好",
  "instructions": "这是 greeting skill 的执行指令...",
  "tools": [],
  "scripts": {},
  "enabled": true,
  "path": "/path/to/skills/greeting",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "status": "enabled"
}
```

### 4. 运行 Skill

执行指定的 skill 并返回结果。

**请求**:
```http
POST /api/v1/skills/{skill_name}/run
Content-Type: application/json

{
  "parameters": {},
  "timeout": null,
  "model": null
}
```

**参数说明**:
- `parameters`: Skill 执行参数（可选，默认为空对象）
- `timeout`: 执行超时时间，单位秒（可选，默认无超时）
- `model`: 指定使用的模型（可选，默认使用系统默认模型）

**cURL 示例**:
```bash
# 基本执行
curl -X POST http://localhost:8000/api/v1/skills/greeting/run \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"name": "World"}}'

# 带超时
curl -X POST http://localhost:8000/api/v1/skills/greeting/run \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"name": "Alice"}, "timeout": 30}'

# 指定模型执行（使用特定模型运行 skill）
curl -X POST http://localhost:8000/api/v1/skills/greeting/run \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"name": "Alice"}, "model": "gpt-4"}'
```

**Python 示例**:
```python
import requests
import json

skill_name = 'greeting'
url = f'http://localhost:8000/api/v1/skills/{skill_name}/run'

# 准备参数
payload = {
    "parameters": {
        "name": "Alice",
        "count": 3
    },
    "timeout": 30,  # 30 秒超时
    "model": "gpt-4"  # 指定使用 gpt-4 模型（可选）
}

# 发送请求
response = requests.post(url, json=payload)

# 处理响应
if response.status_code == 200:
    result = response.json()

    if result['success']:
        print(f"✅ 执行成功!")
        print(f"结果: {result['result']}")
        print(f"耗时: {result['execution_time']:.3f} 秒")

        # 显示日志
        if result['logs']:
            print("\n执行日志:")
            for log in result['logs']:
                print(f"  • {log}")
    else:
        print(f"❌ 执行失败: {result['error']}")
else:
    print(f"请求失败: {response.status_code}")
    print(response.text)
```

**JavaScript/Node.js 示例**:
```javascript
const axios = require('axios');

async function runSkill(skillName, parameters, timeout) {
    try {
        const response = await axios.post(
            `http://localhost:8000/api/v1/skills/${skillName}/run`,
            {
                parameters: parameters,
                timeout: timeout
            }
        );

        if (response.data.success) {
            console.log('✅ 执行成功!');
            console.log('结果:', response.data.result);
            console.log(`耗时: ${response.data.execution_time.toFixed(3)} 秒`);

            if (response.data.logs) {
                console.log('\n执行日志:');
                response.data.logs.forEach(log => {
                    console.log(`  • ${log}`);
                });
            }
        } else {
            console.log('❌ 执行失败:', response.data.error);
        }
    } catch (error) {
        console.error('请求失败:', error.response?.data || error.message);
    }
}

// 使用示例
runSkill('greeting', { name: 'Alice' }, 30);
```

**响应**:
```json
{
  "success": true,
  "skill_name": "greeting",
  "result": "Hello, Alice!",
  "execution_time": 0.001,
  "logs": [
    "开始执行 skill: greeting",
    "使用函数执行，参数: {'name': 'Alice'}",
    "执行完成，耗时: 0.001 秒"
  ],
  "error": null,
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

**错误响应示例**:
```json
{
  "detail": "Skill 'nonexistent' 不存在"
}
```

### 5. 重新加载 Skills

重新加载所有 skills（热更新）。

**请求**:
```http
POST /api/v1/skills/reload
```

**cURL 示例**:
```bash
curl -X POST http://localhost:8000/api/v1/skills/reload
```

**Python 示例**:
```python
import requests

response = requests.post('http://localhost:8000/api/v1/skills/reload')

if response.status_code == 200:
    result = response.json()
    print(f"✅ {result['message']}")
```

**响应**:
```json
{
  "success": true,
  "message": "Skills 已重新加载"
}
```

### 6. 智能对话 (Chat)

通过自然语言描述自动选择并执行 skill。

**请求**:
```http
POST /api/v1/chat
Content-Type: application/json

{
  "user_input": "计算 123 加 456",
  "model": "gpt-4"
}
```

**参数说明**:
- `user_input`: 用户输入的自然语言描述（必需）
- `model`: 指定使用的模型（可选，默认使用系统默认模型）

**cURL 示例**:
```bash
# 基本调用
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "计算 123 加 456"}'

# 指定模型
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "写一首关于春天的诗", "model": "claude-3-opus-20240229"}'
```

**Python 示例**:
```python
import requests

url = 'http://localhost:8000/api/v1/chat'

# 准备参数
payload = {
    "user_input": "计算 123 加 456",
    "model": "gpt-4"  # 指定使用 gpt-4 模型（可选）
}

# 发送请求
response = requests.post(url, json=payload)

# 处理响应
if response.status_code == 200:
    result = response.json()
    
    if result['success']:
        print(f"✅ 执行成功!")
        print(f"选择的 skill: {result['selection']['skill_name']}")
        print(f"置信度: {result['selection']['confidence']}")
        print(f"结果: {result['execution']['result']}")
    else:
        print(f"❌ 执行失败: {result['error']}")
else:
    print(f"请求失败: {response.status_code}")
    print(response.text)
```

**响应**:
```json
{
  "success": true,
  "user_input": "计算 123 加 456",
  "selection": {
    "skill_name": "calculator",
    "confidence": 0.95,
    "reasoning": "用户需要进行数学计算",
    "parameters": {
      "expression": "123 + 456"
    },
    "direct_response": null
  },
  "execution": {
    "success": true,
    "result": 579,
    "error": null,
    "execution_time": 0.123,
    "logs": ["开始执行 skill: calculator", "执行完成"]
  },
  "error": null,
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

## 高级用法

### 1. 批量执行 Skills

```python
import requests

skills_to_run = [
    {'name': 'greeting', 'params': {'name': 'Alice'}},
    {'name': 'greeting', 'params': {'name': 'Bob'}},
]

results = []
for skill_info in skills_to_run:
    response = requests.post(
        f"http://localhost:8000/api/v1/skills/{skill_info['name']}/run",
        json={'parameters': skill_info['params']}
    )
    results.append(response.json())

# 处理结果
for i, result in enumerate(results):
    print(f"{i+1}. {result['skill_name']}: {result['result']}")
```

### 2. 异步执行（Python）

```python
import asyncio
import aiohttp

async def run_skill(session, skill_name, parameters=None, timeout=None):
    """异步执行 skill"""
    url = f"http://localhost:8000/api/v1/skills/{skill_name}/run"
    payload = {
        'parameters': parameters or {},
        'timeout': timeout
    }

    async with session.post(url, json=payload) as response:
        return await response.json()

async def main():
    """主函数"""
    async with aiohttp.ClientSession() as session:
        # 并发执行多个 skills
        tasks = [
            run_skill(session, 'greeting', {'name': 'Alice'}),
            run_skill(session, 'greeting', {'name': 'Bob'}),
            run_skill(session, 'greeting', {'name': 'Charlie'}),
        ]

        results = await asyncio.gather(*tasks)

        for result in results:
            print(f"✅ {result['result']}")

# 运行
asyncio.run(main())
```

### 3. 错误处理和重试

```python
import requests
import time

def run_skill_with_retry(skill_name, parameters, max_retries=3, delay=1):
    """带重试的 skill 执行"""
    url = f"http://localhost:8000/api/v1/skills/{skill_name}/run"

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json={'parameters': parameters})

            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    return result['result']
                else:
                    raise Exception(result['error'])
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            print(f"尝试 {attempt + 1}/{max_retries} 失败: {e}")

            if attempt < max_retries - 1:
                time.sleep(delay)
                continue
            else:
                raise

# 使用
result = run_skill_with_retry('greeting', {'name': 'Alice'})
print(result)
```

### 4. 流式响应（大型结果）

如果 skill 返回大量数据，可以考虑使用流式响应：

```python
import requests

skill_name = 'large-data-skill'
url = f"http://localhost:8000/api/v1/skills/{skill_name}/run"

response = requests.post(
    url,
    json={'parameters': {}},
    stream=True
)

if response.status_code == 200:
    for chunk in response.iter_content(chunk_size=1024):
        process_chunk(chunk)  # 处理数据块
```

### 5. 集成到 Web 应用

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/api/greet', methods=['POST'])
def greet():
    """Web 应用端点"""
    data = request.json
    name = data.get('name', 'World')

    # 调用 skill service
    response = requests.post(
        'http://localhost:8000/api/v1/skills/greeting/run',
        json={'parameters': {'name': name}}
    )

    if response.status_code == 200:
        skill_result = response.json()
        return jsonify({
            'greeting': skill_result['result'],
            'execution_time': skill_result['execution_time']
        })
    else:
        return jsonify({'error': 'Skill 执行失败'}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

## 安全性

### API Key + Secret 双因子认证

在生产环境中，强烈建议启用 API Key + Secret 双因子认证：

```bash
# .env 文件
ENABLE_AUTH=true
API_KEY=your-api-key-change-this
API_SECRET=your-api-secret-change-this
```

**重要**：请务必将默认凭证修改为强密钥（至少 32 位随机字符串）！

#### 调用受保护接口

鉴权启用后，调用敏感接口（如 `/run`, `/chat`, `/reload` 等）需要提供凭证：

**方式 1: 请求头（推荐）**

```python
headers = {
    'X-API-Key': 'your-api-key',
    'X-API-Secret': 'your-api-secret'
}

response = requests.post(
    'http://localhost:8000/api/v1/skills/greeting/run',
    headers=headers,
    json={'parameters': {'name': 'World'}}
)
```

**方式 2: Query 参数**

```bash
curl -X POST "http://localhost:8000/api/v1/skills/greeting/run?api_key=your-api-key&api_secret=your-api-secret" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"name": "World"}}'
```

#### 受保护的端点

以下端点需要鉴权（当 `ENABLE_AUTH=true` 时）：
- `POST /api/v1/skills/{name}/run` - 执行 skill
- `POST /api/v1/chat` - 自然语言对话
- `POST /api/v1/skills/reload` - 重新加载 skills
- `POST /api/v1/import/directory` - 导入本地 skill
- `POST /api/v1/import/git` - 从 Git 导入 skill
- `POST /api/v1/install` - 安装 skill
- `POST /api/v1/install/text` - 从文本安装 skill
- `DELETE /api/v1/skills/{name}` - 删除 skill

以下端点**不需要**鉴权：
- `GET /health` - 健康检查
- `GET /api/v1/skills` - 列出 skills
- `GET /api/v1/skills/{name}` - 获取 skill 详情

#### 测试环境跳过鉴权

在开发和测试环境中，可以禁用鉴权：

```bash
# .env 文件
ENABLE_AUTH=false
```

此时所有接口都可以直接调用，方便测试。

### HTTPS

生产环境应该使用 HTTPS：

```bash
uvicorn skill_service.api.server:app \
    --host 0.0.0.0 \
    --port 443 \
    --ssl-keyfile /path/to/key.pem \
    --ssl-certfile /path/to/cert.pem
```

## 性能优化

### 连接池

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 创建 session
session = requests.Session()

# 配置重试策略
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)

# 配置连接池
adapter = HTTPAdapter(
    max_retries=retry,
    pool_connections=10,
    pool_maxsize=10
)

session.mount('http://', adapter)
session.mount('https://', adapter)

# 使用 session
response = session.post('http://localhost:8000/api/v1/skills/greeting/run', json={})
```

### 缓存

```python
import requests
from functools import lru_cache

@lru_cache(maxsize=128)
def get_skill_list():
    """缓存的 skill 列表"""
    response = requests.get('http://localhost:8000/api/v1/skills')
    return response.json()

# 第一次请求会调用 API
skills1 = get_skill_list()

# 后续请求从缓存读取
skills2 = get_skill_list()
```

## 测试

### 使用 pytest 测试

```python
import pytest
import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    """测试健康检查"""
    response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

def test_list_skills():
    """测试列出 skills"""
    response = requests.get(f"{BASE_URL}/skills")
    assert response.status_code == 200
    assert 'skills' in response.json()

def test_run_skill():
    """测试运行 skill"""
    response = requests.post(
        f"{BASE_URL}/skills/greeting/run",
        json={'parameters': {'name': 'Test'}}
    )
    assert response.status_code == 200
    result = response.json()
    assert result['success'] is True
    assert 'Hello, Test!' in result['result']
```

运行测试：
```bash
pytest tests/test_api.py -v
```

## 故障排除

### 问题 1: 连接超时

```python
import requests
from requests.exceptions import Timeout

try:
    response = requests.get(
        'http://localhost:8000/api/v1/skills',
        timeout=10  # 10 秒超时
    )
except Timeout:
    print("请求超时")
```

### 问题 2: JSON 解析错误

```python
import json

response = requests.post('http://localhost:8000/api/v1/skills/greeting/run', json={})

try:
    data = response.json()
except json.JSONDecodeError:
    print(f"响应不是有效的 JSON: {response.text}")
```

### 问题 3: 查看详细错误

```python
response = requests.post('http://localhost:8000/api/v1/skills/nonexistent/run', json={})

if response.status_code != 200:
    print(f"错误代码: {response.status_code}")
    print(f"错误详情: {response.text}")
```

## 更多资源

- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI 规范**: http://localhost:8000/openapi.json
