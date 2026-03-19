"""
JSON Formatter Skill - JSON 格式化工具
"""
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


if __name__ == "__main__":
    # 测试执行
    test_data = {"name": "Alice", "age": 25, "city": "Beijing", "active": True}

    print("Pretty format:")
    print(execute({"data": test_data, "mode": "pretty"}))

    print("\nCompact format:")
    print(execute({"data": test_data, "mode": "compact"}))

    print("\nSorted format:")
    print(execute({"data": test_data, "mode": "sort"}))
