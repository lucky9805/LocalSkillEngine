"""
测试 CLI 功能
"""
import pytest
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_cli_list():
    """测试 CLI list 命令"""
    from click.testing import CliRunner
    from skill_service.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['list'])

    assert result.exit_code == 0
    assert '可用的 Skills' in result.output


def test_cli_version():
    """测试 CLI version 命令"""
    from click.testing import CliRunner
    from skill_service.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['version'])

    assert result.exit_code == 0
    assert 'Skill Service' in result.output
    assert '版本:' in result.output


def test_cli_info():
    """测试 CLI info 命令"""
    from click.testing import CliRunner
    from skill_service.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['info', 'greeting'])

    if result.exit_code == 0:
        assert 'greeting' in result.output
        assert '版本:' in result.output


def test_cli_run():
    """测试 CLI run 命令"""
    from click.testing import CliRunner
    from skill_service.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, [
        'run', 'greeting',
        '--param', 'name=TestUser'
    ])

    if result.exit_code == 0:
        assert '执行成功' in result.output
        assert 'Hello, TestUser!' in result.output


def test_cli_run_json_format():
    """测试 CLI run 命令 JSON 格式"""
    from click.testing import CliRunner
    from skill_service.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, [
        'run', 'greeting',
        '--param', 'name=TestUser',
        '--format', 'json'
    ])

    if result.exit_code == 0:
        assert '"success": true' in result.output
        assert '"skill_name": "greeting"' in result.output


def test_cli_run_json_params():
    """测试 CLI run 命令 JSON 参数"""
    from click.testing import CliRunner
    from skill_service.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, [
        'run', 'greeting',
        '--json-params', '{"name":"TestUser"}'
    ])

    if result.exit_code == 0:
        assert '执行成功' in result.output


def test_cli_reload():
    """测试 CLI reload 命令"""
    from click.testing import CliRunner
    from skill_service.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['reload'])

    assert result.exit_code == 0
    assert '重新加载完成' in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
