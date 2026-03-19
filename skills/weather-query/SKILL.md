---
name: weather-query
description: 创建一个天气查询 skill，可以查询实时天气和未来7天预报
license: MIT
compatibility: Requires Python 3.9+
metadata:
  version: "1.0.0"
  author: Skill Service Team
  category: api
  keywords:
    - weather
    - auto-generated
    - 查询实时天气和未来7天预报
---

# Weather Query Skill

创建一个天气查询 skill，可以查询实时天气和未来7天预报

## 功能特性

- HTTP 请求
- 错误处理
- 数据解析

## 使用方法

### 通过 chat 命令

```bash
python -m skill_service chat "使用 weather-query 完成某项任务"
```

### 通过 run 命令

```bash
python -m skill_service run weather-query --param 查询实时天气和未来7天预报=value
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| 查询实时天气和未来7天预报 | string | 否 | 查询实时天气和未来7天预报参数 |

## 示例

### 输入

```json
{
  "查询实时天气和未来7天预报": "查询实时天气和未来7天预报的值"
}
```

### 输出

```json
{
  "success": true,
  "output": "结果"
}
```

## 注意事项

- 首次使用建议先查看生成的代码
- 根据实际需求调整参数和逻辑
- 建议添加适当的错误处理

## 依赖

- Python 3.9+
- import requests
- import json
- from typing import Dict, Any
