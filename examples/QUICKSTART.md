# 快速开始指南

本指南将帮助你在 5 分钟内开始使用 Skill Service。

## 📦 安装

### 1. 克隆或下载项目

```bash
git clone https://github.com/yourusername/skill-service.git
cd skill-service
```

### 2. 创建虚拟环境

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt

# 或使用开发模式安装
pip install -e .
```

### 4. 配置环境变量（可选）

```bash
# 复制示例配置文件
cp env.example .env

# 根据需要修改配置
# 默认配置即可运行
```

**生产环境重要配置**：

```bash
# 启用 API 鉴权（生产环境强烈建议开启）
ENABLE_AUTH=true
API_KEY=your-strong-api-key-here
API_SECRET=your-strong-api-secret-here
```

鉴权启用后，调用敏感接口（如运行 skill）需要在请求头中添加：
```
X-API-Key: your-api-key
X-API-Secret: your-api-secret
```

## 🚀 快速开始

### 方法 1: 使用命令行 (CLI)

#### 1. 列出可用的 skills

```bash
skill-service list
```

输出示例：
```
📦 可用的 Skills:
================================================================================

 1. greeting
    版本: 1.0.0
    分类: utility
    作者: Skill Service Team
    描述: 打招呼技能 - 向指定的目标问好
    状态: ✅ enabled

 2. calculator
    版本: 1.0.0
    分类: utility
    作者: Skill Service Team
    描述: 简单的计算器技能 - 支持基本数学运算
    状态: ✅ enabled

 3. json-formatter
    版本: 1.0.0
    分类: utility
    作者: Skill Service Team
    描述: JSON 格式化工具 - 美化和压缩 JSON 数据
    状态: ✅ enabled

================================================================================
共 3 个 skills
```

#### 2. 运行一个 skill

```bash
#打招呼
skill-service run greeting --param name="World"

# 计算
skill-service run calculator --param operation=add --param a=5 --param b=3

# 格式化 JSON
skill-service run json-formatter \
  --json-params '{"data":{"name":"Alice","age":25},"mode":"pretty"}'
```

### 方法 2: 使用 API 服务

#### 1. 启动 API 服务

```bash
skill-service serve
```

服务启动后，访问以下地址：
- **API 文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### 2. 使用 API

**使用 cURL**:
```bash
# 健康检查
curl http://localhost:8000/health

# 列出 skills
curl http://localhost:8000/api/v1/skills

# 运行 skill
curl -X POST http://localhost:8000/api/v1/skills/greeting/run \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"name": "World"}}'
```

**使用 Python**:
```python
import requests
import os

# 配置（如果启用了鉴权）
headers = {}
if os.environ.get("ENABLE_AUTH") == "true":
    headers = {
        "X-API-Key": os.environ.get("API_KEY"),
        "X-API-Secret": os.environ.get("API_SECRET")
    }

# 运行 skill
response = requests.post(
    'http://localhost:8000/api/v1/skills/greeting/run',
    headers=headers,
    json={'parameters': {'name': 'World'}}
)

result = response.json()
print(f"结果: {result['result']}")
```

## 📝 创建你自己的 Skill

### 步骤 1: 创建 skill 目录

```bash
mkdir skills/my-skill
mkdir skills/my-skill/scripts
```

### 步骤 2: 创建 SKILL.md

复制模板并修改：

```bash
cp examples/SKILL_TEMPLATE.md skills/my-skill/SKILL.md
# 编辑 skills/my-skill/SKILL.md
```

### 步骤 3: 创建执行脚本

```python
# skills/my-skill/scripts/main.py

def execute(parameters):
    """执行你的 skill 逻辑"""
    name = parameters.get("name", "World")
    return f"Hello, {name}! This is my custom skill."

if __name__ == "__main__":
    print(execute({"name": "Test"}))
```

### 步骤 4: 测试你的 skill

```bash
# 列出 skills（应该能看到你的 skill）
skill-service list

# 运行你的 skill
skill-service run my-skill --param name="Alice"
```

## 🎯 示例场景

### 场景 1: 数据处理

创建一个处理 CSV 文件的 skill：

```python
# skills/csv-processor/scripts/main.py
import pandas as pd

def execute(parameters):
    """处理 CSV 文件"""
    file_path = parameters.get("file_path")
    operation = parameters.get("operation", "info")

    df = pd.read_csv(file_path)

    if operation == "info":
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": df.columns.tolist()
        }
    elif operation == "summary":
        return df.describe().to_dict()
```

### 场景 2: API 集成

创建一个调用外部 API 的 skill：

```python
# skills/weather/scripts/main.py
import requests

def execute(parameters):
    """获取天气信息"""
    city = parameters.get("city", "Beijing")

    # 调用天气 API
    response = requests.get(f"https://api.weather.com/{city}")

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "无法获取天气信息"}
```

### 场景 3: 批量任务

创建一个批量处理任务的 skill：

```python
# skills/batch-processor/scripts/main.py
import asyncio

def execute(parameters):
    """批量处理任务"""
    tasks = parameters.get("tasks", [])

    results = []
    for task in tasks:
        # 处理每个任务
        result = process_single_task(task)
        results.append(result)

    return {
        "total": len(tasks),
        "success": len([r for r in results if r.get("success")]),
        "results": results
    }
```

## 🔧 高级用法

### 1. 在脚本中使用异步

```python
import asyncio

async def execute_async(parameters):
    """异步执行"""
    await asyncio.sleep(1)
    return "异步执行完成"

def execute(parameters):
    """同步包装器"""
    return asyncio.run(execute_async(parameters))
```

### 2. 添加配置文件

```python
import yaml

def execute(parameters):
    """使用配置文件"""
    # 读取配置
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # 使用配置
    return f"配置: {config}"
```

### 3. 错误处理

```python
def execute(parameters):
    """带错误处理的执行"""
    try:
        # 验证参数
        required = ["param1", "param2"]
        for param in required:
            if param not in parameters:
                return {"error": f"缺少必要参数: {param}"}

        # 执行逻辑
        result = do_something(parameters)

        return {"success": True, "result": result}

    except Exception as e:
        return {"error": str(e), "success": False}
```

## 📚 更多资源

- **完整文档**: 查看 `README.md`
- **CLI 使用**: 查看 `examples/cli_usage.md`
- **API 使用**: 查看 `examples/api_usage.md`
- **Skill 模板**: 查看 `examples/SKILL_TEMPLATE.md`
- **示例 Skills**: 查看 `skills/` 目录

## ❓ 常见问题

### Q: 如何安装新的 skill？

A: 只需将 skill 目录放入 `skills/` 文件夹，然后运行 `skill-service reload`。

### Q: 如何调试 skill？

A: 在 `scripts/main.py` 中添加 `print()` 语句，或在 API 响应中查看日志。

### Q: Skill 可以访问文件系统吗？

A: 可以，但要注意安全性。建议限制在特定目录内操作。

### Q: 如何共享 skill？

A: 可以将 skill 目录打包为 zip 文件，其他人解压到 `skills/` 目录即可使用。

## 🎉 下一步

现在你已经了解了基本用法，可以：

1. **创建自己的 skill**: 使用模板创建自定义技能
2. **探索示例 skills**: 查看 `skills/` 目录中的示例
3. **集成到项目**: 通过 CLI 或 API 集成到现有项目
4. **部署服务**: 将服务部署到服务器

祝你使用愉快！🚀
