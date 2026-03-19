"""
Skill 加载器模块
"""
import importlib.util
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import time
from contextlib import contextmanager

from skill_service.models import Skill, SkillExecutionRequest, SkillExecutionResult
from skill_service.storage.skill_store import SkillStore
from skill_service.utils.logger import get_logger
from skill_service.utils.validator import validate_parameters


class SkillLoader:
    """Skill 加载器 - 负责加载和管理 skill"""

    def __init__(self):
        """初始化 skill 加载器"""
        self.logger = get_logger(__name__)
        self.skill_store = SkillStore()
        self.loaded_scripts: Dict[str, Any] = {}

    @contextmanager
    def execution_timeout(self, timeout: Optional[int] = None):
        """
        执行超时上下文管理器

        Args:
            timeout: 超时时间（秒）
        """
        if timeout is None:
            yield
            return

        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Skill 执行超时（{timeout}秒）")

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        获取 skill

        Args:
            name: Skill 名称

        Returns:
            Skill 对象，不存在返回 None
        """
        return self.skill_store.get_skill(name)

    def list_skills(self) -> list:
        """
        列出所有 skills

        Returns:
            Skill 信息列表
        """
        return self.skill_store.list_skills()

    def reload_skills(self) -> None:
        """重新加载所有 skills"""
        self.logger.info("重新加载 skills...")
        self.loaded_scripts.clear()
        self.skill_store.reload()

    def load_skill_script(self, skill: Skill) -> Any:
        """
        加载 skill 的主脚本

        Args:
            skill: Skill 对象

        Returns:
            加载的脚本模块或函数
        """
        # 检查是否已加载
        if skill.name in self.loaded_scripts:
            return self.loaded_scripts[skill.name]

        # 查找主脚本
        main_script_path = None
        for script_name, script_path in skill.scripts.items():
            if script_name in ['main.py', '__init__.py']:
                main_script_path = Path(script_path)
                break

        if not main_script_path:
            # 尝试使用 SKILL.md 中的脚本代码
            self.logger.warning(f"Skill {skill.name} 没有找到脚本文件")
            return None

        try:
            # 动态加载 Python 模块
            spec = importlib.util.spec_from_file_location(
                f"skill_{skill.name}",
                main_script_path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"skill_{skill.name}"] = module
            spec.loader.exec_module(module)

            # 查找 execute 函数
            if hasattr(module, 'execute'):
                self.loaded_scripts[skill.name] = module.execute
                self.logger.info(f"成功加载 skill 脚本: {skill.name}")
                return module.execute
            else:
                self.logger.warning(f"Skill {skill.name} 的脚本缺少 execute 函数")
                return None

        except Exception as e:
            self.logger.error(f"加载 skill 脚本失败 {skill.name}: {e}")
            return None

    def validate_skill(self, skill: Skill) -> tuple[bool, str]:
        """
        验证 skill 是否有效

        Args:
            skill: Skill 对象

        Returns:
            (是否有效, 错误信息)
        """
        # 检查 skill 是否启用
        if not skill.enabled:
            return False, "Skill 未启用"

        # 检查是否有脚本
        if not skill.scripts and not skill.instructions:
            return False, "Skill 缺少执行脚本或指令"

        return True, ""

    def prepare_execution(
        self,
        skill_name: str,
        request: SkillExecutionRequest
    ) -> tuple[Optional[Skill], Any, str]:
        """
        准备 skill 执行

        Args:
            skill_name: Skill 名称
            request: 执行请求

        Returns:
            (Skill 对象, 执行函数, 错误信息)
        """
        # 获取 skill
        skill = self.get_skill(skill_name)
        if not skill:
            return None, None, f"Skill '{skill_name}' 不存在"

        # 验证 skill
        is_valid, error_msg = self.validate_skill(skill)
        if not is_valid:
            return None, None, error_msg

        # 加载脚本
        execute_func = self.load_skill_script(skill)

        return skill, execute_func, ""
