---
name: your-skill-name
version: 1.0.0
author: Your Name
category: utility
description: 简短描述你的 skill 功能
---

## 简介

详细描述你的 skill 的功能和用途。说明它解决了什么问题，有什么特点。

## 执行逻辑

描述 skill 的执行流程和步骤。可以包含：
1. 输入参数说明
2. 处理逻辑描述
3. 输出结果说明

## 参数

列出所有参数及其说明：

- param1 (必需): 参数1的说明
- param2 (可选): 参数2的说明，默认值为xxx
- param3 (可选): 参数3的说明，可选值为 [a, b, c]

## 使用示例

### 命令行调用

```bash
skill-service run your-skill-name \
  --param param1="value1" \
  --param param2="value2"
```

### API 调用

```bash
POST /api/v1/skills/your-skill-name/run
{
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

## 注意事项

- 注意事项1
- 注意事项2
- 特殊情况说明

## 依赖

列出 skill 的依赖项（如果有的话）：
- 需要的 Python 包
- 需要的系统工具
- 需要的 API 密钥或配置

## 脚本

### main.py
```python
def execute(parameters):
    """
    执行 skill 的主函数

    Args:
        parameters: 包含所有参数的字典

    Returns:
        执行结果，可以是任何类型（字符串、字典、列表等）
    """
    # 1. 提取参数
    param1 = parameters.get("param1", "default_value")
    param2 = parameters.get("param2", "default_value")

    # 2. 执行你的逻辑
    result = f"处理结果: {param1} + {param2}"

    # 3. 返回结果
    return result


if __name__ == "__main__":
    # 测试代码
    test_params = {
        "param1": "test1",
        "param2": "test2"
    }
    result = execute(test_params)
    print(result)
```

## 最佳实践

1. **参数验证**: 在函数开始时验证所有必需参数
2. **错误处理**: 使用 try-except 捕获可能的异常
3. **日志记录**: 添加适当的日志信息便于调试
4. **文档注释**: 添加详细的 docstring 说明函数用途
5. **类型提示**: 使用类型注解提高代码可读性

## 示例代码结构

```python
"""
Skill 名称和简短描述
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def execute(parameters: Dict[str, Any]) -> Any:
    """
    执行 skill

    Args:
        parameters: 参数字典

    Returns:
        执行结果
    """
    try:
        # 1. 参数验证
        if not parameters:
            return {"error": "缺少必要参数"}

        # 2. 提取参数
        param1 = parameters.get("param1")
        if not param1:
            return {"error": "缺少 param1 参数"}

        # 3. 执行逻辑
        result = process_data(param1)

        # 4. 返回结果
        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        logger.error(f"执行失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def process_data(data: Any) -> Any:
    """
    处理数据的辅助函数

    Args:
        data: 输入数据

    Returns:
        处理后的数据
    """
    # 你的处理逻辑
    return data


if __name__ == "__main__":
    # 测试代码
    test_result = execute({"param1": "test"})
    print(test_result)
```
