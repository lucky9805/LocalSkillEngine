"""
主入口模块
"""
from skill_service.cli import main, cli

if __name__ == "__main__":
    main()

# 导出 cli 供 setup.py 使用
__all__ = ['main', 'cli']
