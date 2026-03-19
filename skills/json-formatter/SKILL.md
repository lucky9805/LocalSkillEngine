---
name: json-formatter
description: JSON 格式化工具 - 美化和压缩 JSON 数据
license: MIT
compatibility: skill-service >=0.1.0
allowed-tools: python
metadata:
  version: 1.0.0
  author: Skill Service Team
  category: utility
---

## 简介

一个 JSON 格式化工具，可以美化或压缩 JSON 数据，支持多种输出格式。

## 执行逻辑

接收 JSON 字符串或字典，根据指定的模式进行格式化：
- pretty: 美化格式（缩进 2 空格）
- compact: 压缩格式（去除所有空格）
- sort: 排序键值对

## 参数

- data (必需): JSON 字符串或字典对象
- mode (可选): 格式化模式，默认为 "pretty"
  - pretty: 美化格式
  - compact: 压缩格式
  - sort: 排序键值对
- indent (可选): 缩进空格数，默认为 2

## 脚本

### main.py
```python
import json

def execute(parameters):
    """
    格式化 JSON 数据

    Args:
        parameters: 包含 data, mode, indent 的字典

    Returns:
        格式化后的 JSON 字符串
    """
    data = parameters.get("data", {})
    mode = parameters.get("mode", "pretty")
    indent = parameters.get("indent", 2)

    # 如果是字符串，尝试解析为 JSON
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return {"error": "无效的 JSON 字符串"}

    # 根据模式格式化
    if mode == "compact":
        # 压缩格式
        result = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    elif mode == "sort":
        # 排序键值对
        result = json.dumps(data, sort_keys=True, indent=indent, ensure_ascii=False)
    else:
        # 默认美化格式
        result = json.dumps(data, indent=indent, ensure_ascii=False)

    return result
```

## 使用示例

```bash
# 命令行调用
skill-service run json-formatter \
  --json-params '{"data":{"name":"Alice","age":25,"city":"Beijing"},"mode":"pretty"}'

# API 调用
POST /api/v1/skills/json-formatter/run
{
  "parameters": {
    "data": {"name": "Alice", "age": 25, "city": "Beijing"},
    "mode": "sort"
  }
}
```
