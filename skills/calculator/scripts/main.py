"""
Calculator Skill - 简单的计算器技能
"""


def execute(parameters):
    """
    执行数学运算

    Args:
        parameters: 包含 operation, a, b 的字典

    Returns:
        运算结果字符串
    """
    operation = parameters.get("operation", "add")
    a = parameters.get("a", 0)
    b = parameters.get("b", 0)

    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "错误: 除数不能为零"
    }

    if operation not in operations:
        return f"错误: 不支持的运算 '{operation}'"

    result = operations[operation](a, b)

    operation_names = {
        "add": "加",
        "subtract": "减",
        "multiply": "乘",
        "divide": "除"
    }

    return f"{a} {operation_names.get(operation, operation)} {b} = {result}"


if __name__ == "__main__":
    # 测试执行
    print(execute({"operation": "add", "a": 5, "b": 3}))
    print(execute({"operation": "multiply", "a": 4, "b": 7}))
    print(execute({"operation": "divide", "a": 10, "b": 2}))
