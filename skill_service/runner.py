"""
Skill 执行器模块
"""
import asyncio
import sys
import traceback
from io import StringIO
from pathlib import Path
from typing import Optional, Any, List
import time

from skill_service.models import Skill, SkillExecutionRequest, SkillExecutionResult, SkillStatus
from skill_service.loader import SkillLoader
from skill_service.utils.logger import get_logger


class SkillRunner:
    """Skill 执行器 - 负责执行 skill 并返回结果"""

    def __init__(self):
        """初始化 skill 执行器"""
        self.logger = get_logger(__name__)
        self.loader = SkillLoader()

    async def execute(
        self,
        request: SkillExecutionRequest
    ) -> SkillExecutionResult:
        """
        异步执行 skill

        Args:
            request: 执行请求

        Returns:
            执行结果
        """
        skill_name = request.skill_name
        parameters = request.parameters
        timeout = request.timeout

        logs: List[str] = []
        logs.append(f"开始执行 skill: {skill_name}")

        try:
            # 准备执行
            skill, execute_func, error_msg = self.loader.prepare_execution(
                skill_name, request
            )

            if error_msg:
                logs.append(f"错误: {error_msg}")
                return SkillExecutionResult(
                    success=False,
                    skill_name=skill_name,
                    result=None,
                    execution_time=0,
                    logs=logs,
                    error=error_msg
                )

            # 记录开始时间
            start_time = time.time()

            # 执行 skill
            if execute_func:
                # 有脚本函数
                result = await self._execute_function(
                    execute_func, parameters, timeout, logs, skill
                )
            else:
                # 没有脚本函数，尝试使用 instructions
                result = await self._execute_instructions(
                    skill, parameters, timeout, logs
                )

            # 计算执行时间
            execution_time = time.time() - start_time
            logs.append(f"执行完成，耗时: {execution_time:.3f} 秒")

            return SkillExecutionResult(
                success=True,
                skill_name=skill_name,
                result=result,
                execution_time=execution_time,
                logs=logs
            )

        except TimeoutError as e:
            execution_time = time.time() - time.time()
            logs.append(f"执行超时: {e}")
            return SkillExecutionResult(
                success=False,
                skill_name=skill_name,
                result=None,
                execution_time=execution_time,
                logs=logs,
                error=str(e)
            )

        except Exception as e:
            execution_time = 0
            error_msg = f"执行失败: {str(e)}"
            logs.append(error_msg)
            logs.append(traceback.format_exc())

            self.logger.error(f"Skill 执行异常 {skill_name}: {e}")

            return SkillExecutionResult(
                success=False,
                skill_name=skill_name,
                result=None,
                execution_time=execution_time,
                logs=logs,
                error=error_msg
            )

    async def _execute_function(
        self,
        execute_func: Any,
        parameters: dict,
        timeout: Optional[int],
        logs: List[str],
        skill: Skill = None
    ) -> Any:
        """
        执行脚本函数

        Args:
            execute_func: 执行函数
            parameters: 参数
            timeout: 超时时间
            logs: 日志列表
            skill: Skill 对象（用于提供 references 和 assets 路径）

        Returns:
            执行结果
        """
        logs.append(f"使用函数执行，参数: {parameters}")

        # 如果提供了 skill，添加 references 和 assets 路径到参数
        if skill:
            parameters = parameters.copy()
            parameters['_skill_context'] = {
                'references': skill.references,
                'assets': skill.assets,
                'skill_path': skill.path
            }
            logs.append(f"已加载 references: {len(skill.references)} 个")
            logs.append(f"已加载 assets: {len(skill.assets)} 个")

        if timeout:
            # 带超时执行
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(execute_func, parameters),
                    timeout=timeout
                )
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(f"执行超时（{timeout}秒）")
        else:
            # 不带超时执行
            if asyncio.iscoroutinefunction(execute_func):
                result = await execute_func(parameters)
            else:
                result = await asyncio.to_thread(execute_func, parameters)
            return result

    async def _execute_instructions(
        self,
        skill: Skill,
        parameters: dict,
        timeout: Optional[int],
        logs: List[str]
    ) -> Any:
        """
        执行 instructions（模拟执行）

        Args:
            skill: Skill 对象
            parameters: 参数
            timeout: 超时时间
            logs: 日志列表

        Returns:
            执行结果
        """
        logs.append(f"使用 instructions 执行")
        logs.append(f"Instructions: {skill.instructions[:100]}...")

        # 这里可以根据 instructions 内容解析和执行
        # 简单实现：返回 skill 的描述和参数
        result = {
            "skill": skill.name,
            "description": skill.description,
            "parameters": parameters,
            "message": "Skill instructions executed (placeholder)"
        }

        # 模拟执行时间
        await asyncio.sleep(0.1)

        return result

    def execute_sync(
        self,
        request: SkillExecutionRequest
    ) -> SkillExecutionResult:
        """
        同步执行 skill

        Args:
            request: 执行请求

        Returns:
            执行结果
        """
        return asyncio.run(self.execute(request))

    def list_skills(self) -> List:
        """
        列出所有 skills

        Returns:
            Skill 信息列表
        """
        return self.loader.list_skills()

    def get_skill_info(self, skill_name: str) -> Optional[dict]:
        """
        获取 skill 信息

        Args:
            skill_name: Skill 名称

        Returns:
            Skill 信息字典
        """
        skill = self.loader.get_skill(skill_name)
        if not skill:
            return None

        return {
            "name": skill.name,
            "version": skill.version,
            "author": skill.author,
            "category": skill.category,
            "description": skill.description,
            "instructions": skill.instructions,
            "tools": skill.tools,
            "scripts": skill.scripts,
            "references": skill.references,
            "assets": skill.assets,
            "enabled": skill.enabled,
            "status": skill.status.value,
            "path": skill.path,
            "created_at": skill.created_at,
            "updated_at": skill.updated_at
        }

    def reload_skills(self) -> None:
        """重新加载所有 skills"""
        self.loader.reload_skills()
