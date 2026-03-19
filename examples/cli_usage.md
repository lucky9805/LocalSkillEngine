# CLI 使用示例

本文档展示了 Skill Service 命令行接口的各种使用方法。

## 安装

```bash
# 开发模式安装
pip install -e .

# 或直接使用 Python 运行
python -m skill_service.main
```

## 基本命令

### 1. 查看帮助

```bash
skill-service --help
```

### 2. 查看版本

```bash
skill-service version
```

输出示例：
```
Skill Service
========================================
版本: 0.1.0
作者: Your Name
Python: 3.10.0
========================================
```

### 3. 列出所有 Skills

```bash
# 表格格式（默认）
skill-service list

# JSON 格式
skill-service list --format json
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

================================================================================
共 1 个 skills
```

### 4. 查看 Skill 详情

```bash
# 文本格式（默认）
skill-service info greeting

# JSON 格式
skill-service info greeting --format json
```

输出示例：
```
📋 Skill 详情:
================================================================================
名称:      greeting
版本:      1.0.0
作者:      Skill Service Team
分类:      utility
描述:      打招呼技能 - 向指定的目标问好
状态:      enabled
路径:      /path/to/skills/greeting

执行指令:
--------------------------------------------------------------------------------
这是 greeting skill 的执行指令...
...
================================================================================
```

### 5. 运行 Skill

#### 5.1 使用单个参数

```bash
# 字符串参数
skill-service run greeting --param name="Alice"

# 输出: Hello, Alice!
```

#### 5.2 使用多个参数

```bash
skill-service run my-skill --param name="Alice" --param age=25 --param active=true
```

#### 5.3 使用 JSON 参数

```bash
skill-service run greeting --json-params '{"name":"Alice","count":3}'
```

#### 5.4 设置超时

```bash
# 30 秒超时
skill-service run long-task --timeout 30
```

#### 5.5 JSON 格式输出

```bash
skill-service run greeting --param name="Alice" --format json
```

输出示例：
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
  "timestamp": "2024-01-01T12:00:00"
}
```

### 6. 启动 API 服务

```bash
# 默认配置（localhost:8000）
skill-service serve

# 指定主机和端口
skill-service serve --host 0.0.0.0 --port 9000

# 自动重载（开发模式）
skill-service serve --reload
```

输出示例：
```
🌐 启动 Skill Service API...
================================================================================
地址: http://0.0.0.0:8000
文档: http://0.0.0.0:8000/docs
ReDoc: http://0.0.0.0:8000/redoc
================================================================================

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 7. 重新加载 Skills

```bash
skill-service reload
```

输出示例：
```
🔄 重新加载 skills...
INFO: 重新加载 skills...
INFO: 加载完成，共 1 个 skills
✅ 重新加载完成
```

## 常用场景

### 场景 1: 批量执行 Skills

```bash
#!/bin/bash
# 执行多个 skills

skill-service run greeting --param name="Alice"
skill-service run report --param date="2024-01-01"
skill-service run cleanup
```

### 场景 2: 条件执行

```bash
#!/bin/bash
# 根据结果决定下一步操作

result=$(skill-service run check-status --format json --json-params '{"target":"server"}')

if echo "$result" | grep -q '"success":true'; then
    echo "状态正常，继续执行..."
    skill-service run deploy
else
    echo "状态异常，停止执行"
    exit 1
fi
```

### 场景 3: 开发模式

```bash
# 启动服务并自动重载
skill-service serve --reload

# 在另一个终端测试
skill-service run greeting --param name="Dev"

# 修改 skill 代码后，服务会自动重载
```

### 场景 4: 脚本集成

```python
#!/usr/bin/env python3
import subprocess
import json

# 执行 skill 并获取 JSON 结果
result = subprocess.run(
    ['skill-service', 'run', 'greeting', '--format', 'json',
     '--json-params', json.dumps({'name': 'Python'})],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
if data['success']:
    print(f"结果: {data['result']}")
    print(f"执行时间: {data['execution_time']}")
```

## 参数说明

### 全局选项

- `-v, --verbose`: 详细输出模式

### list 命令选项

- `-f, --format`: 输出格式（table/json）

### info 命令选项

- `-f, --format`: 输出格式（text/json）

### run 命令选项

- `-p, --param`: 参数，格式：key=value（可多次使用）
- `-j, --json-params`: JSON 格式的参数
- `-t, --timeout`: 执行超时时间（秒）
- `-f, --format`: 输出格式（text/json）

### serve 命令选项

- `-h, --host`: 主机地址
- `-p, --port`: 端口号
- `--reload`: 自动重载（开发模式）

## 技巧

### 1. 使用 Tab 补全

如果安装了 bash-completion：
```bash
eval "$(_SKILL_SERVICE_COMPLETE=source skill-service)"
```

### 2. 管道输出

```bash
# 将结果保存到文件
skill-service run report --format json > report.json

# 处理输出
skill-service run list-items | grep "item"
```

### 3. 后台运行服务

```bash
# 启动服务并在后台运行
nohup skill-service serve > service.log 2>&1 &

# 查看日志
tail -f service.log

# 停止服务
pkill -f "skill-service serve"
```

### 4. 调试模式

```bash
# 启用详细日志
skill-service --verbose run greeting --param name="Debug"
```

## 故障排除

### 问题 1: 命令未找到

```bash
# 确保已正确安装
pip install -e .

# 或使用 Python 模块方式
python -m skill_service.main list
```

### 问题 2: Skill 未找到

```bash
# 检查 skill 是否存在
skill-service list

# 确保技能目录中有 SKILL.md 文件
ls -la skills/your-skill/
```

### 问题 3: 参数格式错误

```bash
# 使用 JSON 格式避免复杂参数问题
skill-service run my-skill --json-params '{"key":"value","number":123}'
```

## 更多帮助

```bash
skill-service --help
skill-service <command> --help
```
