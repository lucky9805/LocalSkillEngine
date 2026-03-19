"""
Skill 扫描器 - 支持多级目录扫描

符合 Agent Skills 规范，支持以下扫描路径：
- Project-level: <project>/.agents/skills/
- Project-level: <project>/.workbuddy/skills/ (客户端原生)
- User-level: ~/.agents/skills/
- User-level: ~/.workbuddy/skills/ (客户端原生)

冲突解决: project-level 覆盖 user-level
"""
import os
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field

from skill_service.utils.logger import get_logger


@dataclass
class ScanResult:
    """扫描结果"""
    skill_dirs: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SkillScanner:
    """
    Skill 扫描器
    
    扫描多个路径寻找 skill 目录，处理冲突和优先级。
    """
    
    # 默认扫描路径模板
    DEFAULT_PATHS = [
        # Project-level (高优先级)
        "{project}/.agents/skills",
        "{project}/.workbuddy/skills",
        
        # User-level (低优先级)
        "{home}/.agents/skills",
        "{home}/.workbuddy/skills",
    ]
    
    def __init__(
        self,
        project_dir: Optional[Path] = None,
        additional_paths: Optional[List[Path]] = None,
    ):
        """
        初始化扫描器
        
        Args:
            project_dir: 项目目录路径，默认为当前工作目录
            additional_paths: 额外的扫描路径
        """
        self.logger = get_logger(__name__)
        self.project_dir = project_dir or Path.cwd()
        self.home_dir = Path.home()
        self.additional_paths = additional_paths or []
        
    def get_scan_paths(self) -> List[Tuple[Path, int]]:
        """
        获取所有扫描路径及其优先级
        
        Returns:
            [(路径, 优先级)] 列表，优先级数字越小越高
        """
        paths = []
        
        # 展开模板路径
        for i, template in enumerate(self.DEFAULT_PATHS):
            path_str = template.format(
                project=str(self.project_dir),
                home=str(self.home_dir),
            )
            path = Path(path_str).resolve()
            # project-level 优先级 0-1, user-level 优先级 2-3
            paths.append((path, i))
        
        # 添加额外路径（最低优先级）
        for i, path in enumerate(self.additional_paths):
            paths.append((path.resolve(), 100 + i))
        
        return paths
    
    def scan(self) -> ScanResult:
        """
        扫描所有路径寻找 skill 目录
        
        Returns:
            ScanResult 包含找到的 skill 目录和任何错误/警告
        """
        result = ScanResult()
        found_skills: Dict[str, Path] = {}  # name -> path
        
        scan_paths = self.get_scan_paths()
        
        for path, priority in scan_paths:
            if not path.exists():
                self.logger.debug(f"扫描路径不存在，跳过: {path}")
                continue
            
            if not path.is_dir():
                result.warnings.append(f"扫描路径不是目录: {path}")
                continue
            
            self.logger.info(f"扫描路径: {path} (优先级: {priority})")
            
            # 扫描该路径下的子目录
            try:
                for item in path.iterdir():
                    if not item.is_dir():
                        continue
                    
                    # 跳过隐藏目录和特殊目录
                    if item.name.startswith('.') or item.name == '__pycache__':
                        continue
                    
                    # 检查是否包含 SKILL.md
                    has_skill_md = self._has_skill_md(item)
                    if not has_skill_md:
                        continue
                    
                    skill_name = item.name
                    
                    # 检查冲突
                    if skill_name in found_skills:
                        existing_path = found_skills[skill_name]
                        existing_priority = self._get_path_priority(existing_path, scan_paths)
                        
                        if priority < existing_priority:
                            # 当前路径优先级更高，覆盖
                            result.warnings.append(
                                f"Skill '{skill_name}' 冲突: {path} 覆盖 {existing_path}"
                            )
                            found_skills[skill_name] = item
                        else:
                            # 当前路径优先级更低，跳过
                            result.warnings.append(
                                f"Skill '{skill_name}' 冲突: 保留 {existing_path}，跳过 {path}"
                            )
                    else:
                        found_skills[skill_name] = item
                        
            except PermissionError as e:
                result.errors.append(f"权限错误扫描路径 {path}: {e}")
            except Exception as e:
                result.errors.append(f"扫描路径 {path} 时出错: {e}")
        
        result.skill_dirs = list(found_skills.values())
        
        self.logger.info(f"扫描完成: 找到 {len(result.skill_dirs)} 个 skills")
        for warning in result.warnings:
            self.logger.warning(warning)
        for error in result.errors:
            self.logger.error(error)
        
        return result
    
    def _has_skill_md(self, directory: Path) -> bool:
        """
        检查目录是否包含 SKILL.md（支持大小写）
        
        Args:
            directory: 目录路径
            
        Returns:
            是否包含 SKILL.md
        """
        for name in ("SKILL.md", "skill.md"):
            if (directory / name).exists():
                return True
        return False
    
    def _get_path_priority(self, skill_path: Path, scan_paths: List[Tuple[Path, int]]) -> int:
        """
        获取 skill 所在扫描路径的优先级
        
        Args:
            skill_path: skill 目录路径
            scan_paths: 扫描路径列表
            
        Returns:
            优先级数字
        """
        # 找到 skill 所在的扫描路径
        for scan_path, priority in scan_paths:
            if str(skill_path).startswith(str(scan_path)):
                return priority
        return 999  # 未知路径，最低优先级
    
    def find_skill(self, name: str) -> Optional[Path]:
        """
        查找指定名称的 skill 目录
        
        Args:
            name: skill 名称
            
        Returns:
            skill 目录路径，未找到返回 None
        """
        result = self.scan()
        
        for skill_dir in result.skill_dirs:
            if skill_dir.name == name:
                return skill_dir
        
        return None


def get_default_skills_directory() -> Path:
    """
    获取默认的 skills 目录
    
    按优先级尝试：
    1. 当前目录下的 ./skills
    2. 当前目录下的 ./.agents/skills
    3. 当前目录下的 ./.workbuddy/skills
    
    Returns:
        默认 skills 目录路径
    """
    cwd = Path.cwd()
    
    candidates = [
        cwd / "skills",
        cwd / ".agents" / "skills",
        cwd / ".workbuddy" / "skills",
    ]
    
    for path in candidates:
        if path.exists():
            return path
    
    # 默认返回 ./skills
    return cwd / "skills"


def scan_all_skills(
    project_dir: Optional[Path] = None,
    additional_paths: Optional[List[Path]] = None,
) -> List[Path]:
    """
    便捷函数：扫描所有 skills
    
    Args:
        project_dir: 项目目录
        additional_paths: 额外扫描路径
        
    Returns:
        skill 目录路径列表
    """
    scanner = SkillScanner(project_dir, additional_paths)
    result = scanner.scan()
    return result.skill_dirs
