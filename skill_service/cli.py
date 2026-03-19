"""
命令行接口 (CLI) 模块
"""
import asyncio
import json
import click
import os
import signal
import sys
import uvicorn
from pathlib import Path
from typing import Optional, List

from skill_service.runner import SkillRunner
from skill_service.models import SkillExecutionRequest
from skill_service.config import get_settings
from skill_service.utils.logger import get_logger
from skill_service.nl_generator import create_skill_from_text
from skill_service.scanner import SkillScanner
from skill_service.llm.config import configure_llm, get_llm_config_manager


# 延迟初始化的全局实例
_runner = None
_scanner = None
logger = get_logger(__name__)


def get_runner():
    """延迟初始化 SkillRunner"""
    global _runner
    if _runner is None:
        _runner = SkillRunner()
    return _runner


def get_scanner():
    """延迟初始化 SkillScanner"""
    global _scanner
    if _scanner is None:
        _scanner = SkillScanner()
    return _scanner


@click.group()
@click.version_option(version="0.1.0")
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
def cli(verbose):
    """Skill Service - 本地 Skill 运行服务"""
    if verbose:
        logger.handlers[0].setLevel(10)  # DEBUG level


@cli.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'catalog']), default='table',
              help='输出格式 (table: 表格, json: JSON, catalog: 目录视图)')
@click.option('--category', '-c', type=str, default=None,
              help='按分类过滤')
@click.option('--search', '-s', type=str, default=None,
              help='搜索关键词')
def list(format, category, search):
    """列出所有可用的 skills (Skill Catalog)"""
    skills = get_runner().list_skills()
    
    # 应用过滤
    if category:
        skills = [s for s in skills if s.category and category.lower() in s.category.lower()]
    
    if search:
        search_lower = search.lower()
        skills = [s for s in skills if 
                  search_lower in s.name.lower() or 
                  search_lower in (s.description or '').lower() or
                  search_lower in (s.category or '').lower()]

    if format == 'json':
        # Agent Skills 标准 JSON 格式
        catalog = {
            "version": "1.0",
            "total": len(skills),
            "skills": [
                {
                    "name": s.name,
                    "description": s.description,
                    "license": s.license,
                    "compatibility": s.compatibility,
                    "allowed_tools": s.allowed_tools,
                    "metadata": s.metadata
                }
                for s in skills
            ]
        }
        click.echo(json.dumps(catalog, indent=2, ensure_ascii=False))
    
    elif format == 'catalog':
        # Tier 1: Catalog 视图 (简洁列表)
        if not skills:
            click.echo("📭 没有找到可用的 skills")
            return

        click.echo("\n📦 Skill Catalog")
        click.echo("=" * 80)
        
        # 按分类分组
        by_category = {}
        for skill in skills:
            cat = skill.category or "uncategorized"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(skill)
        
        for cat, cat_skills in sorted(by_category.items()):
            click.echo(f"\n📁 {cat}")
            click.echo("-" * 40)
            for skill in cat_skills:
                status_icon = "✓" if skill.enabled else "✗"
                desc = skill.description or ""
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                click.echo(f"  {status_icon} {skill.name:<20} {desc}")
        
        click.echo(f"\n共 {len(skills)} 个 skills")
    
    else:  # table
        if not skills:
            click.echo("没有找到可用的 skills")
            return

        click.echo("\n📦 可用的 Skills:")
        click.echo("=" * 80)

        for i, skill in enumerate(skills, 1):
            status_icon = "✅" if skill.enabled else "❌"
            click.echo(f"\n{i:2}. {skill.name}")
            click.echo(f"    版本: {skill.version}")
            click.echo(f"    分类: {skill.category}")
            click.echo(f"    作者: {skill.author}")
            click.echo(f"    描述: {skill.description}")
            click.echo(f"    状态: {status_icon} {skill.status.value}")
            
            # Agent Skills 标准字段
            if skill.license:
                click.echo(f"    许可证: {skill.license}")
            if skill.allowed_tools:
                click.echo(f"    允许工具: {skill.allowed_tools}")

        click.echo("\n" + "=" * 80)
        click.echo(f"共 {len(skills)} 个 skills")


@cli.command()
@click.argument('name')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'tier']), default='text',
              help='输出格式 (text: 文本, json: JSON, tier: 渐进式披露视图)')
def info(name, format):
    """查看 skill 的详细信息 (Tier 2: Instructions)"""
    skill_info = get_runner().get_skill_info(name)

    if not skill_info:
        click.echo(f"❌ 未找到 skill: {name}")
        sys.exit(1)

    if format == 'json':
        click.echo(json.dumps(skill_info, indent=2, ensure_ascii=False))
    
    elif format == 'tier':
        # 渐进式披露视图
        click.echo("\n📋 Skill 详情 (渐进式披露)")
        click.echo("=" * 80)
        
        # Tier 1: Catalog
        click.echo("\n📌 Tier 1 - 目录信息")
        click.echo("-" * 40)
        click.echo(f"名称: {skill_info['name']}")
        click.echo(f"描述: {skill_info['description']}")
        if skill_info.get('license'):
            click.echo(f"许可证: {skill_info['license']}")
        if skill_info.get('compatibility'):
            click.echo(f"兼容性: {skill_info['compatibility']}")
        if skill_info.get('allowed_tools'):
            click.echo(f"允许工具: {skill_info['allowed_tools']}")
        
        # Tier 2: Instructions
        click.echo("\n📖 Tier 2 - 执行指令")
        click.echo("-" * 40)
        instructions = skill_info.get('instructions', '')
        if instructions:
            if len(instructions) > 800:
                click.echo(instructions[:800] + "\n... (内容过长，使用 --format text 查看完整内容)")
            else:
                click.echo(instructions)
        
        # Tier 3: Resources
        resources_exist = (skill_info.get('scripts') or 
                          skill_info.get('references') or 
                          skill_info.get('assets'))
        
        if resources_exist:
            click.echo("\n📦 Tier 3 - 资源文件")
            click.echo("-" * 40)
            
            if skill_info.get('scripts'):
                click.echo("脚本:")
                for script_name, script_path in skill_info['scripts'].items():
                    click.echo(f"  📜 {script_name}: {script_path}")
            
            if skill_info.get('references'):
                click.echo("参考文档:")
                for ref_name, ref_path in skill_info['references'].items():
                    click.echo(f"  📚 {ref_name}: {ref_path}")
            
            if skill_info.get('assets'):
                click.echo("资源文件:")
                for asset_name, asset_path in skill_info['assets'].items():
                    click.echo(f"  🎨 {asset_name}: {asset_path}")
        
        click.echo("\n" + "=" * 80)
    
    else:  # text
        click.echo("\n📋 Skill 详情:")
        click.echo("=" * 80)
        click.echo(f"名称:      {skill_info['name']}")
        click.echo(f"版本:      {skill_info['version']}")
        click.echo(f"作者:      {skill_info['author']}")
        click.echo(f"分类:      {skill_info['category']}")
        click.echo(f"描述:      {skill_info['description']}")
        click.echo(f"状态:      {skill_info['status']}")
        click.echo(f"路径:      {skill_info['path']}")
        
        # Agent Skills 标准字段
        if skill_info.get('license'):
            click.echo(f"许可证:    {skill_info['license']}")
        if skill_info.get('compatibility'):
            click.echo(f"兼容性:    {skill_info['compatibility']}")
        if skill_info.get('allowed_tools'):
            click.echo(f"允许工具:  {skill_info['allowed_tools']}")

        if skill_info['tools']:
            click.echo(f"\n工具依赖:")
            for tool in skill_info['tools']:
                click.echo(f"  - {tool}")

        if skill_info['scripts']:
            click.echo(f"\n脚本文件:")
            for script_name, script_path in skill_info['scripts'].items():
                click.echo(f"  - {script_name}: {script_path}")

        if skill_info.get('references'):
            click.echo(f"\n参考文档:")
            for ref_name, ref_path in skill_info['references'].items():
                click.echo(f"  - {ref_name}: {ref_path}")

        if skill_info.get('assets'):
            click.echo(f"\n资源文件:")
            for asset_name, asset_path in skill_info['assets'].items():
                click.echo(f"  - {asset_name}: {asset_path}")

        click.echo(f"\n执行指令:")
        click.echo("-" * 80)
        instructions = skill_info['instructions']
        if len(instructions) > 500:
            click.echo(instructions[:500] + "\n... (内容过长，已截断)")
        else:
            click.echo(instructions)

        click.echo("\n" + "=" * 80)


@cli.command(name='run')
@click.argument('name')
@click.option('--param', '-p', multiple=True,
              help='参数，格式: key=value')
@click.option('--json-params', '-j', type=str,
              help='JSON 格式的参数')
@click.option('--timeout', '-t', type=int, default=None,
              help='执行超时时间（秒）')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text',
              help='输出格式')
def run(name, param, json_params, timeout, format):
    """运行指定的 skill"""
    # 解析参数
    parameters = {}

    if json_params:
        try:
            parameters = json.loads(json_params)
        except json.JSONDecodeError:
            click.echo(f"❌ JSON 参数格式错误: {json_params}")
            sys.exit(1)
    else:
        for p in param:
            if '=' in p:
                key, value = p.split('=', 1)
                # 尝试转换为正确的类型
                try:
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
                parameters[key] = value

    # 创建执行请求
    request = SkillExecutionRequest(
        skill_name=name,
        parameters=parameters,
        timeout=timeout
    )

    # 执行 skill
    click.echo(f"\n🚀 执行 skill: {name}")
    click.echo("=" * 80)

    if parameters:
        click.echo(f"参数: {json.dumps(parameters, ensure_ascii=False)}")
    else:
        click.echo("参数: 无")

    click.echo("")

    try:
        result = get_runner().execute_sync(request)

        if result.success:
            click.echo("✅ 执行成功!")
            
            # 显示执行时间
            click.echo(f"\n⏱️  执行时间: {result.execution_time:.3f} 秒")

            # 显示日志
            if result.logs:
                click.echo(f"\n📝 执行日志:")
                for log in result.logs:
                    click.echo(f"  • {log}")

            # 显示结果
            click.echo(f"\n📊 执行结果:")
            click.echo("-" * 80)

            if format == 'json':
                click.echo(json.dumps(result.result, indent=2, ensure_ascii=False))
            else:
                # 智能格式化输出
                if isinstance(result.result, dict):
                    # 如果有 output 字段，优先显示
                    if 'output' in result.result:
                        click.echo(result.result['output'])
                        # 显示其他数据
                        other_data = {k: v for k, v in result.result.items() if k != 'output'}
                        if other_data:
                            click.echo("\n" + "-" * 80)
                            click.echo("附加数据:")
                            click.echo(json.dumps(other_data, indent=2, ensure_ascii=False))
                    else:
                        click.echo(json.dumps(result.result, indent=2, ensure_ascii=False))
                elif isinstance(result.result, (str, int, float, bool)):
                    click.echo(result.result)
                elif isinstance(result.result, list):
                    click.echo(json.dumps(result.result, indent=2, ensure_ascii=False))
                else:
                    click.echo(str(result.result))

        else:
            click.echo("❌ 执行失败!")

            # 显示错误信息
            if result.error:
                click.echo(f"\n错误: {result.error}")

            # 显示日志
            if result.logs:
                click.echo(f"\n📝 执行日志:")
                for log in result.logs:
                    click.echo(f"  • {log}")

            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ 执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    click.echo("\n" + "=" * 80)


# execute 作为 run 的别名
@cli.command(name='execute', hidden=True)
@click.argument('name')
@click.option('--parameters', '-p', type=str,
              help='JSON 格式的参数')
@click.option('--timeout', '-t', type=int, default=None,
              help='执行超时时间（秒）')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text',
              help='输出格式')
def execute(name, parameters, timeout, format):
    """执行指定的 skill (run 的别名)"""
    # 解析 JSON 参数
    json_params = parameters
    
    # 调用 run 命令的实现
    import click
    from skill_service.models import SkillExecutionRequest
    
    # 解析参数
    params = {}
    if json_params:
        try:
            params = json.loads(json_params)
        except json.JSONDecodeError as e:
            click.echo(f"❌ JSON 参数格式错误: {e}")
            sys.exit(1)
    
    # 创建执行请求
    request = SkillExecutionRequest(
        skill_name=name,
        parameters=params,
        timeout=timeout
    )
    
    # 执行 skill
    click.echo(f"\n🚀 执行 skill: {name}")
    click.echo("=" * 80)
    
    if params:
        click.echo(f"参数: {json.dumps(params, ensure_ascii=False)}")
    else:
        click.echo("参数: 无")
    
    click.echo("")
    
    try:
        result = get_runner().execute_sync(request)
        
        if result.success:
            click.echo("✅ 执行成功!")
            click.echo(f"\n⏱️  执行时间: {result.execution_time:.3f} 秒")
            
            if result.logs:
                click.echo(f"\n📝 执行日志:")
                for log in result.logs:
                    click.echo(f"  • {log}")
            
            click.echo(f"\n📊 执行结果:")
            click.echo("-" * 80)
            
            if format == 'json':
                click.echo(json.dumps(result.result, indent=2, ensure_ascii=False))
            else:
                if isinstance(result.result, (str, int, float, bool)):
                    click.echo(result.result)
                elif isinstance(result.result, (dict, list)):
                    click.echo(json.dumps(result.result, indent=2, ensure_ascii=False))
                else:
                    click.echo(str(result.result))
        else:
            click.echo("❌ 执行失败!")
            if result.error:
                click.echo(f"\n错误: {result.error}")
            if result.logs:
                click.echo(f"\n📝 执行日志:")
                for log in result.logs:
                    click.echo(f"  • {log}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 执行异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    click.echo("\n" + "=" * 80)


def get_pid_file():
    """获取 PID 文件路径"""
    pid_dir = Path.home() / ".skill-service"
    pid_dir.mkdir(parents=True, exist_ok=True)
    return pid_dir / "server.pid"


@cli.group(invoke_without_command=True)
@click.option('--host', '-h', type=str, default=None, help='主机地址')
@click.option('--port', '-p', type=int, default=None, help='端口号')
@click.option('--reload', is_flag=True, help='自动重载')
@click.pass_context
def serve(ctx, host, port, reload):
    """启动或管理 API 服务"""
    if ctx.invoked_subcommand is None:
        # 没有子命令，执行启动逻辑
        settings = get_settings()

        server_host = host or settings.server_host
        server_port = port or settings.server_port

        # 检查端口是否被占用
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((server_host, server_port))
        except OSError:
            click.echo(f"\n❌ 端口 {server_port} 已被占用")
            click.echo(f"   请检查是否有其他服务正在使用该端口：")
            click.echo(f"   lsof -i :{server_port}")
            click.echo(f"   或先停止已有服务：")
            click.echo(f"   skill-service serve stop")
            sys.exit(1)
        finally:
            sock.close()

        # 检查是否已有服务在运行
        pid_file = get_pid_file()
        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                os.kill(old_pid, 0)
                click.echo(f"\n⚠️  已有一个服务在运行 (PID: {old_pid})")
                click.echo("   如需重启，请先停止：skill-service serve stop")
                sys.exit(1)
            except (ValueError, ProcessLookupError):
                pid_file.unlink()

        # 写入 PID 文件
        pid_file.write_text(str(os.getpid()))

        click.echo("\n🌐 启动 Skill Service API...")
        click.echo("=" * 80)
        click.echo(f"地址: http://{server_host}:{server_port}")
        click.echo(f"文档: http://{server_host}:{server_port}/docs")
        click.echo(f"ReDoc: http://{server_host}:{server_port}/redoc")
        click.echo(f"PID 文件: {pid_file}")
        click.echo(f"停止服务: skill-service serve stop")
        click.echo("=" * 80)
        click.echo("")

        try:
            uvicorn.run(
                "skill_service.api.server:app",
                host=server_host,
                port=server_port,
                reload=reload,
                log_level=settings.log_level.lower()
            )
        except KeyboardInterrupt:
            click.echo("\n\n👋 服务已停止")
        except Exception as e:
            click.echo(f"\n❌ 启动失败: {e}")
            sys.exit(1)
        finally:
            # 退出时清理 PID 文件
            if pid_file.exists():
                pid_file.unlink()


@serve.command(name='stop')
@click.option('--port', '-p', type=int, default=None, help='指定要停止的服务端口（当 PID 文件不存在时使用）')
def serve_stop(port):
    """停止正在运行的 API 服务"""
    import subprocess

    pid_file = get_pid_file()
    pid = None

    # 方式一：通过 PID 文件查找
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
        except (ValueError, OSError):
            pid_file.unlink()
            pid = None

    if pid is not None:
        # 验证进程是否还活着
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            click.echo("⚠️  PID 文件存在但进程已不存在，清理 PID 文件")
            pid_file.unlink()
            pid = None
        except PermissionError:
            click.echo(f"❌ 没有权限停止进程 (PID: {pid})")
            return

    # 方式二：通过端口查找
    if pid is None:
        target_port = port or 8000
        try:
            result = subprocess.run(
                ['lsof', '-ti', f':{target_port}', '-sTCP:LISTEN'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                pid = int(pids[0])
                click.echo(f"📋 通过端口 {target_port} 找到进程 (PID: {pid})")
            else:
                click.echo(f"❌ 未找到运行中的服务（端口 {target_port} 未被占用）")
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            click.echo(f"❌ 无法通过端口查找进程（PID 文件也不存在）")
            click.echo("   请手动查找并停止: ps aux | grep skill-service")
            return

    # 发送 SIGTERM 信号
    try:
        os.kill(pid, signal.SIGTERM)
        click.echo(f"🛑 已发送停止信号给进程 (PID: {pid})")
        click.echo("等待服务关闭...")
    except OSError as e:
        click.echo(f"❌ 停止失败: {e}")
        return

    # 等待进程退出（最多 5 秒）
    import time
    for _ in range(10):
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            # 清理 PID 文件
            if pid_file.exists():
                pid_file.unlink()
            click.echo("✅ 服务已停止")
            return

    # 进程未响应，尝试 SIGKILL
    click.echo("⚠️  服务未响应，强制终止...")
    try:
        os.kill(pid, signal.SIGKILL)
        click.echo("✅ 服务已强制停止")
    except OSError as e:
        click.echo(f"❌ 强制停止失败: {e}")


@cli.command()
@click.argument('description')
@click.option('--name', '-n', type=str, default=None, help='skill 名称')
def create(description, name):
    """使用自然语言创建 skill"""
    click.echo("\n🤖 正在根据描述生成 skill...")
    click.echo("=" * 80)
    click.echo(f"描述: {description}")
    click.echo("=" * 80)

    try:
        result = create_skill_from_text(description, name)

        if result["success"]:
            click.echo("\n✅ Skill 创建成功!")
            click.echo(f"名称: {result['skill_name']}")
            click.echo(f"路径: {result['path']}")
            click.echo(f"\n类型: {result['intent']['type']}")
            click.echo(f"操作: {result['intent']['operation']}")

            # 重新加载 skills
            get_runner().reload_skills()

            click.echo("\n📝 使用示例:")
            click.echo(f"  skill-service run {result['skill_name']} --param ...")
            click.echo("\n💡 提示: 你可以编辑生成的代码来完善功能")
            click.echo(f"  vim {result['path']}/scripts/main.py")

        else:
            click.echo(f"\n❌ 创建失败: {result.get('error', '未知错误')}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"\n❌ 创建异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def reload():
    """重新加载所有 skills"""
    click.echo("\n🔄 重新加载 skills...")
    get_runner().reload_skills()
    click.echo("✅ 重新加载完成")


@cli.command()
@click.argument('query')
@click.option('--field', '-f', type=click.Choice(['name', 'description', 'category', 'all']), 
              default='all', help='搜索字段')
@click.option('--format', type=click.Choice(['table', 'json']), default='table',
              help='输出格式')
def search(query, field, format):
    """搜索 skills"""
    skills = get_runner().list_skills()
    query_lower = query.lower()
    
    # 执行搜索
    results = []
    for skill in skills:
        match = False
        if field in ['name', 'all'] and query_lower in skill.name.lower():
            match = True
        if field in ['description', 'all'] and skill.description and query_lower in skill.description.lower():
            match = True
        if field in ['category', 'all'] and skill.category and query_lower in skill.category.lower():
            match = True
        
        if match:
            results.append(skill)
    
    if format == 'json':
        click.echo(json.dumps([{
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "license": s.license,
            "compatibility": s.compatibility
        } for s in results], indent=2, ensure_ascii=False))
    else:
        if not results:
            click.echo(f"🔍 未找到匹配 '{query}' 的 skills")
            return
        
        click.echo(f"\n🔍 搜索结果: '{query}'")
        click.echo("=" * 80)
        
        for i, skill in enumerate(results, 1):
            status_icon = "✅" if skill.enabled else "❌"
            click.echo(f"\n{i:2}. {skill.name}")
            click.echo(f"    描述: {skill.description or 'N/A'}")
            click.echo(f"    分类: {skill.category or 'N/A'}")
            click.echo(f"    状态: {status_icon}")
        
        click.echo(f"\n共找到 {len(results)} 个匹配结果")


@cli.command()
@click.argument('path', required=False, default=None)
@click.option('--strict', '-s', is_flag=True, help='严格模式 (验证 Agent Skills 标准)')
@click.option('--format', type=click.Choice(['table', 'json']), default='table',
              help='输出格式')
def validate(path, strict, format):
    """验证 skill 或 skill 目录的合法性"""
    from skill_service.utils.validator import validate_skill_directory, validate_frontmatter
    
    # 如果没有指定路径，验证所有已加载的 skills
    if path is None:
        skills = get_runner().list_skills()
        results = []
        for skill in skills:
            # 从 skill 对象获取路径
            skill_info = get_runner().get_skill_info(skill.name)
            if skill_info and skill_info.get('path'):
                skill_path = Path(skill_info['path']).parent
                is_valid, errors = validate_skill_directory(skill_path, strict=strict)
                results.append({
                    "name": skill.name,
                    "path": str(skill_path),
                    "valid": is_valid,
                    "errors": errors
                })
    else:
        # 验证指定路径
        target_path = Path(path)
        if not target_path.exists():
            click.echo(f"❌ 路径不存在: {path}")
            sys.exit(1)
        
        is_valid, errors = validate_skill_directory(target_path, strict=strict)
        results = [{
            "name": target_path.name,
            "path": str(target_path),
            "valid": is_valid,
            "errors": errors
        }]
    
    # 输出结果
    if format == 'json':
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        click.echo("\n🔍 Skill 验证结果")
        click.echo("=" * 80)
        
        valid_count = 0
        for result in results:
            status_icon = "✅" if result['valid'] else "❌"
            click.echo(f"\n{status_icon} {result['name']}")
            click.echo(f"   路径: {result['path']}")
            
            if result['valid']:
                valid_count += 1
                click.echo(f"   状态: 通过验证")
            else:
                click.echo(f"   状态: 验证失败")
                click.echo(f"   错误:")
                for error in result['errors']:
                    click.echo(f"      • {error}")
        
        click.echo("\n" + "=" * 80)
        total = len(results)
        click.echo(f"总计: {total} 个 | 通过: {valid_count} 个 | 失败: {total - valid_count} 个")


@cli.command()
def version():
    """显示版本信息"""
    click.echo("\nSkill Service")
    click.echo("=" * 40)
    click.echo(f"版本: {sys.modules.get('skill_service').__version__}")
    click.echo(f"作者: {sys.modules.get('skill_service').__author__}")
    click.echo(f"Python: {sys.version.split()[0]}")
    click.echo("=" * 40)


# LLM 相关命令
@cli.group()
def llm():
    """LLM 配置和管理"""
    pass


@llm.command()
@click.option('--provider', '-p', type=click.Choice(['openai', 'anthropic', 'local', 'azure']), 
              help='LLM 提供商')
@click.option('--model', '-m', type=str, help='模型名称')
@click.option('--api-key', '-k', type=str, help='API Key')
@click.option('--base-url', '-u', type=str, help='Base URL (用于本地模型或 Azure)')
@click.option('--temperature', '-t', type=float, default=0.7, help='Temperature')
@click.option('--max-tokens', type=int, default=2000, help='最大 Token 数')
def config(provider, model, api_key, base_url, temperature, max_tokens):
    """配置 LLM"""
    try:
        configure_llm(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        click.echo("✅ LLM 配置已更新")
        
        # 显示当前配置（隐藏 API key）
        manager = get_llm_config_manager()
        config = manager.get_config()
        
        click.echo("\n当前配置:")
        click.echo(f"  提供商: {config.provider}")
        click.echo(f"  模型: {config.model}")
        if config.api_key:
            click.echo(f"  API Key: {'*' * 10}")
        if config.base_url:
            click.echo(f"  Base URL: {config.base_url}")
        click.echo(f"  Temperature: {config.temperature}")
        click.echo(f"  Max Tokens: {config.max_tokens}")
        
    except Exception as e:
        click.echo(f"❌ 配置失败: {e}")
        sys.exit(1)


@llm.command()
def status():
    """查看 LLM 配置状态"""
    from skill_service.llm.multi_model_config import get_multi_model_manager
    
    # 优先显示多模型配置
    multi_manager = get_multi_model_manager()
    current_profile = multi_manager.get_current_profile()
    
    if current_profile:
        click.echo("\n🤖 LLM 配置状态 (多模型模式)")
        click.echo("=" * 50)
        click.echo(f"当前模型: {current_profile.name}")
        if current_profile.description:
            click.echo(f"描述: {current_profile.description}")
        click.echo(f"提供商: {current_profile.provider}")
        click.echo(f"模型: {current_profile.model}")
        click.echo(f"API Key: {'✅ 已设置' if current_profile.api_key else '❌ 未设置'}")
        if current_profile.base_url:
            click.echo(f"Base URL: {current_profile.base_url}")
        click.echo(f"Temperature: {current_profile.temperature}")
        click.echo(f"Max Tokens: {current_profile.max_tokens}")
        click.echo("=" * 50)
        
        # 显示其他可用模型
        all_profiles = multi_manager.list_profiles()
        if len(all_profiles) > 1:
            click.echo("\n📋 其他可用模型:")
            for profile in all_profiles:
                if profile.name != current_profile.name:
                    marker = "✓" if profile.api_key else "✗"
                    click.echo(f"  [{marker}] {profile.name}: {profile.description or profile.model}")
            click.echo("\n使用 `skill-service llm use <模型名>` 切换模型")
    else:
        # 回退到单模型配置
        manager = get_llm_config_manager()
        config = manager.get_config()
        
        click.echo("\n🤖 LLM 配置状态")
        click.echo("=" * 40)
        click.echo(f"提供商: {config.provider}")
        click.echo(f"模型: {config.model}")
        click.echo(f"API Key: {'✅ 已设置' if config.api_key else '❌ 未设置'}")
        if config.base_url:
            click.echo(f"Base URL: {config.base_url}")
        click.echo(f"Temperature: {config.temperature}")
        click.echo(f"Max Tokens: {config.max_tokens}")
        click.echo("=" * 40)


@llm.command(name="list")
def list_models():
    """列出所有配置的模型"""
    from skill_service.llm.multi_model_config import get_multi_model_manager
    
    manager = get_multi_model_manager()
    profiles = manager.list_profiles()
    current = manager.get_current_name()
    
    if not profiles:
        click.echo("❌ 没有配置任何模型")
        click.echo("\n使用 `skill-service llm add` 添加模型配置")
        return
    
    click.echo("\n📋 已配置的模型列表")
    click.echo("=" * 70)
    click.echo(f"{'名称':<15} {'提供商':<12} {'模型':<25} {'状态':<10}")
    click.echo("-" * 70)
    
    for profile in profiles:
        is_current = profile.name == current
        has_key = bool(profile.api_key)
        
        status = []
        if is_current:
            status.append("★当前")
        if has_key:
            status.append("✓")
        else:
            status.append("✗")
        
        click.echo(f"{profile.name:<15} {profile.provider:<12} {profile.model:<25} {'/'.join(status):<10}")
    
    click.echo("=" * 70)
    click.echo("\n图例: ★当前 = 当前使用的模型, ✓ = API Key 已设置, ✗ = API Key 未设置")


@llm.command(name="use")
@click.argument("name")
def use_model(name):
    """切换到指定模型"""
    from skill_service.llm.multi_model_config import get_multi_model_manager
    
    manager = get_multi_model_manager()
    
    if manager.set_current(name):
        manager.save_to_file()
        click.echo(f"✅ 已切换到模型: {name}")
        
        # 显示新模型的信息
        profile = manager.get_current_profile()
        if profile:
            click.echo(f"   提供商: {profile.provider}")
            click.echo(f"   模型: {profile.model}")
    else:
        click.echo(f"❌ 模型 '{name}' 不存在")
        click.echo("\n使用 `skill-service llm list` 查看可用模型")


@llm.command(name="add")
@click.option("--name", "-n", required=True, help="模型配置名称")
@click.option("--provider", "-p", required=True, type=click.Choice(["openai", "anthropic", "azure", "local", "custom"]), help="提供商类型")
@click.option("--model", "-m", required=True, help="模型名称或 Endpoint ID")
@click.option("--api-key", "-k", help="API Key (或使用 --env-var 指定环境变量名)")
@click.option("--env-var", "-e", help="从环境变量读取 API Key (如: OPENAI_API_KEY)")
@click.option("--base-url", "-u", help="Base URL (可选)")
@click.option("--temperature", "-t", type=float, default=0.7, help="Temperature (默认 0.7)")
@click.option("--max-tokens", type=int, default=2000, help="Max Tokens (默认 2000)")
@click.option("--description", "-d", help="模型描述")
def add_model(name, provider, model, api_key, env_var, base_url, temperature, max_tokens, description):
    """添加新的模型配置"""
    from skill_service.llm.multi_model_config import get_multi_model_manager, ModelProfile
    
    # 处理 API key
    if env_var:
        # 从环境变量读取
        api_key = f"${{{env_var}}}"
    elif api_key:
        # 直接使用传入的 API key
        pass
    else:
        # 尝试根据 provider 推断环境变量名
        provider_env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY",
            "local": "LOCAL_LLM_KEY",
            "custom": f"{name.upper().replace('-', '_')}_API_KEY"
        }
        env_var_name = provider_env_map.get(provider, f"{name.upper().replace('-', '_')}_API_KEY")
        api_key = f"${{{env_var_name}}}"
    
    profile = ModelProfile(
        name=name,
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        description=description
    )
    
    manager = get_multi_model_manager()
    manager.add_profile(name, profile, set_current=True)
    manager.save_to_file()
    
    click.echo(f"✅ 已添加模型配置: {name}")
    click.echo(f"   提供商: {provider}")
    click.echo(f"   模型: {model}")
    if description:
        click.echo(f"   描述: {description}")
    click.echo(f"   API Key: 从环境变量 {api_key} 读取")


@llm.command(name="remove")
@click.argument("name")
@click.confirmation_option(prompt="确定要删除这个模型配置吗?")
def remove_model(name):
    """删除模型配置"""
    from skill_service.llm.multi_model_config import get_multi_model_manager
    
    manager = get_multi_model_manager()
    
    if manager.remove_profile(name):
        manager.save_to_file()
        click.echo(f"✅ 已删除模型配置: {name}")
    else:
        click.echo(f"❌ 模型 '{name}' 不存在")


@cli.command()
@click.argument('description')
@click.option('--name', '-n', type=str, default=None, help='skill 名称')
@click.option('--use-llm', '-l', is_flag=True, help='使用 LLM 生成（更智能）')
def create(description, name, use_llm):
    """使用自然语言创建 skill"""
    if use_llm:
        # 使用 LLM 生成
        click.echo("\n🤖 使用 LLM 生成 skill...")
        click.echo("=" * 80)
        click.echo(f"描述: {description}")
        click.echo("=" * 80)
        
        try:
            from skill_service.llm.generator import LLMSkillGenerator
            from skill_service.llm.config import create_llm_from_config
            
            llm = create_llm_from_config()
            generator = LLMSkillGenerator(llm)
            
            result = asyncio.run(generator.generate(description, name))
            
            if result["success"]:
                click.echo("\n✅ Skill 创建成功!")
                click.echo(f"名称: {result['skill_name']}")
                click.echo(f"路径: {result['path']}")
                
                # 重新加载 skills
                get_runner().reload_skills()
                
                click.echo("\n📝 使用示例:")
                click.echo(f"  skill-service run {result['skill_name']}")
            else:
                click.echo(f"\n❌ 创建失败: {result.get('error', '未知错误')}")
                sys.exit(1)
                
        except Exception as e:
            click.echo(f"\n❌ 创建异常: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # 使用原有方式
        click.echo("\n🤖 正在根据描述生成 skill...")
        click.echo("=" * 80)
        click.echo(f"描述: {description}")
        click.echo("=" * 80)

        try:
            result = create_skill_from_text(description, name)

            if result["success"]:
                click.echo("\n✅ Skill 创建成功!")
                click.echo(f"名称: {result['skill_name']}")
                click.echo(f"路径: {result['path']}")
                click.echo(f"\n类型: {result['intent']['type']}")
                click.echo(f"操作: {result['intent']['operation']}")

                # 重新加载 skills
                get_runner().reload_skills()

                click.echo("\n📝 使用示例:")
                click.echo(f"  skill-service run {result['skill_name']} --param ...")
                click.echo("\n💡 提示: 你可以编辑生成的代码来完善功能")
                click.echo(f"  vim {result['path']}/scripts/main.py")

            else:
                click.echo(f"\n❌ 创建失败: {result.get('error', '未知错误')}")
                sys.exit(1)

        except Exception as e:
            click.echo(f"\n❌ 创建异常: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


@cli.command()
@click.argument('user_input')
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text',
              help='输出格式 (text: 文本, json: JSON)')
def chat(user_input, verbose, format):
    """智能对话 - 自动选择并执行 skill"""
    
    # 内部函数：统一输出
    def output_result(data: dict):
        if format == 'json':
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # text 格式
            click.echo(f"\n👤 用户: {data['user_input']}")
            click.echo("=" * 80)
            
            if verbose and data.get('debug'):
                click.echo(f"\n🔧 调试信息:")
                for key, value in data['debug'].items():
                    click.echo(f"  {key}: {value}")
            
            if data.get('selection'):
                sel = data['selection']
                if verbose:
                    click.echo(f"\n🤖 选择分析:")
                    click.echo(f"  Skill: {sel.get('skill_name', 'None')}")
                    click.echo(f"  置信度: {sel.get('confidence', 0):.2f}")
                    click.echo(f"  理由: {sel.get('reasoning', '')}")
                    click.echo(f"  参数: {sel.get('parameters', {})}")
                
                if sel.get('skill_name'):
                    click.echo(f"\n🚀 执行 skill: {sel['skill_name']}")
                    
                if data.get('execution'):
                    exec_result = data['execution']
                    if exec_result.get('success'):
                        click.echo("\n✅ 执行成功!")
                        result_data = exec_result.get('result')
                        
                        # 优先显示 output 字段（如果存在）
                        if isinstance(result_data, dict) and 'output' in result_data:
                            click.echo(f"\n📝 输出内容:")
                            click.echo("-" * 80)
                            click.echo(result_data['output'])
                            click.echo("-" * 80)
                            
                            # 显示额外数据
                            if verbose and 'data' in result_data:
                                click.echo(f"\n📊 详细数据:")
                                click.echo(json.dumps(result_data['data'], indent=2, ensure_ascii=False))
                        else:
                            click.echo(f"\n📊 结果:")
                            try:
                                click.echo(json.dumps(result_data, indent=2, ensure_ascii=False))
                            except (TypeError, ValueError):
                                click.echo(str(result_data))
                    else:
                        click.echo(f"\n❌ 执行失败: {exec_result.get('error', '未知错误')}")
                else:
                    click.echo(f"\n🤖 回复: {sel.get('direct_response', '我不太明白你的需求，请尝试更具体的描述。')}")
            
            if data.get('error'):
                click.echo(f"\n❌ 对话失败: {data['error']}")
    
    try:
        from skill_service.llm.selector import SkillSelector
        from skill_service.llm.multi_model_config import get_multi_model_manager
        
        # 创建 LLM 和 Selector (使用多模型配置)
        manager = get_multi_model_manager()
        profile = manager.get_current_profile()
        
        debug_info = {}
        if verbose:
            debug_info = {
                "current_model": profile.name,
                "provider": profile.provider,
                "model": profile.model
            }
        
        llm = manager.create_llm_provider()
        selector = SkillSelector(llm)
        
        # 获取可用 skills
        available_skills = get_runner().list_skills()
        
        if not available_skills:
            output_result({
                "user_input": user_input,
                "success": False,
                "error": "没有可用的 skills",
                "debug": debug_info if verbose else None
            })
            return
        
        # 选择 skill
        import asyncio
        selection = asyncio.run(selector.select_skill(user_input, available_skills))
        
        selection_data = {
            "skill_name": selection.skill_name,
            "confidence": selection.confidence,
            "reasoning": selection.reasoning,
            "parameters": selection.parameters,
            "direct_response": selection.direct_response
        }
        
        result_data = {
            "user_input": user_input,
            "success": True,
            "selection": selection_data,
            "debug": debug_info if verbose else None
        }
        
        if selection.skill_name:
            # 执行 skill
            request = SkillExecutionRequest(
                skill_name=selection.skill_name,
                parameters=selection.parameters
            )
            
            result = get_runner().execute_sync(request)
            
            result_data["execution"] = {
                "success": result.success,
                "result": result.result if result.success else None,
                "error": result.error if not result.success else None,
                "execution_time": result.execution_time,
                "logs": result.logs
            }
            
            if not result.success:
                result_data["success"] = False
        
        output_result(result_data)
            
    except Exception as e:
        import traceback
        error_data = {
            "user_input": user_input,
            "success": False,
            "error": str(e),
            "debug": {"traceback": traceback.format_exc()} if verbose else None
        }
        output_result(error_data)


@cli.group()
def import_cmd():
    """导入外部 skills"""
    pass


@import_cmd.command(name='from')
@click.argument('source')
@click.option('--name', '-n', type=str, help='目标 skill 名称（默认自动检测）')
@click.option('--subdir', '-s', type=str, help='子目录路径（用于 Git/ZIP）')
@click.option('--overwrite', '-o', is_flag=True, help='覆盖已存在的 skill')
@click.option('--target-dir', '-t', type=Path, help='目标目录（默认 ./skills）')
def import_from(source, name, subdir, overwrite, target_dir):
    """从外部源导入 skill
    
    SOURCE 可以是:
    - 本地目录路径: /path/to/skill
    - Git 仓库地址: https://github.com/user/repo.git
    - ZIP 文件路径: /path/to/skill.zip
    
    示例:
        skill-service import from ./my-skill
        skill-service import from https://github.com/user/skill-repo.git
        skill-service import from ./skills.zip --subdir skills/calculator
    """
    from skill_service.migrator import migrate_skill
    
    click.echo(f"📦 导入 skill from: {source}")
    click.echo("=" * 80)
    
    result = migrate_skill(
        source=source,
        name=name,
        target_dir=target_dir,
        overwrite=overwrite,
        subdir=subdir
    )
    
    if result.success:
        click.echo(f"\n✅ {result.message}")
        click.echo(f"   名称: {result.skill_name}")
        click.echo(f"   路径: {result.target_path}")
        
        if result.warnings:
            click.echo(f"\n⚠️  警告:")
            for warning in result.warnings:
                click.echo(f"   - {warning}")
        
        # 重新加载 skills
        click.echo("\n🔄 重新加载 skills...")
        get_runner().reload_skills()
        click.echo("✅ 完成")
        
        click.echo(f"\n📝 使用示例:")
        click.echo(f"   skill-service run {result.skill_name} --param ...")
        click.echo(f"   skill-service chat '使用 {result.skill_name} ...'")
        
    else:
        click.echo(f"\n❌ {result.message}")
        
        if result.errors:
            click.echo(f"\n错误详情:")
            for error in result.errors:
                click.echo(f"   - {error}")
        
        sys.exit(1)


@import_cmd.command(name='list-source')
@click.argument('source_dir', type=Path)
def import_list_source(source_dir):
    """列出目录中可导入的 skills
    
    示例:
        skill-service import list-source ./external-skills
    """
    from skill_service.migrator import SkillMigrator
    
    click.echo(f"🔍 扫描目录: {source_dir}")
    click.echo("=" * 80)
    
    migrator = SkillMigrator()
    skills = migrator.list_importable_skills(source_dir)
    
    if not skills:
        click.echo("\n⚠️  没有找到可导入的 skills")
        return
    
    click.echo(f"\n找到 {len(skills)} 个可导入的 skill:\n")
    
    for i, skill in enumerate(skills, 1):
        click.echo(f"{i}. {skill['name']}")
        click.echo(f"   路径: {skill['path']}")
        if skill['metadata'].get('description'):
            click.echo(f"   描述: {skill['metadata']['description']}")
        click.echo()
    
    click.echo("=" * 80)
    click.echo("\n导入命令示例:")
    for skill in skills[:3]:  # 只显示前3个示例
        click.echo(f"   skill-service import from {skill['path']} --name {skill['name']}")


def main():
    """主入口函数"""
    cli()
