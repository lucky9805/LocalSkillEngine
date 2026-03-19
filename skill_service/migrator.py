"""
Skill 迁移工具 - 支持从外部导入 skills

支持多种迁移方式:
1. 从本地目录复制
2. 从 Git 仓库克隆
3. 从 ZIP 文件解压
"""
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

import yaml

from skill_service.utils.logger import get_logger
from skill_service.utils.validator import validate_skill_directory

logger = get_logger(__name__)


@dataclass
class MigrationResult:
    """迁移结果"""
    success: bool
    skill_name: Optional[str] = None
    target_path: Optional[Path] = None
    message: str = ""
    warnings: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


class SkillMigrator:
    """Skill 迁移器"""
    
    def __init__(self, target_dir: Optional[Path] = None):
        """
        初始化迁移器
        
        Args:
            target_dir: 目标 skills 目录，默认为 ./skills
        """
        self.target_dir = target_dir or Path("./skills").resolve()
        self.target_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Skill 迁移目标目录: {self.target_dir}")
    
    def migrate_from_directory(
        self, 
        source_dir: Path, 
        skill_name: Optional[str] = None,
        overwrite: bool = False
    ) -> MigrationResult:
        """
        从本地目录迁移 skill
        
        Args:
            source_dir: 源 skill 目录
            skill_name: 目标 skill 名称（默认使用源目录名）
            overwrite: 是否覆盖已存在的 skill
            
        Returns:
            MigrationResult 迁移结果
        """
        source_dir = Path(source_dir).resolve()
        
        if not source_dir.exists():
            return MigrationResult(
                success=False,
                message=f"源目录不存在: {source_dir}"
            )
        
        if not source_dir.is_dir():
            return MigrationResult(
                success=False,
                message=f"源路径不是目录: {source_dir}"
            )
        
        # 确定 skill 名称
        target_name = skill_name or source_dir.name
        target_path = self.target_dir / target_name
        
        # 检查是否已存在
        if target_path.exists() and not overwrite:
            return MigrationResult(
                success=False,
                skill_name=target_name,
                target_path=target_path,
                message=f"Skill '{target_name}' 已存在，使用 --overwrite 覆盖"
            )
        
        try:
            # 验证源目录是否是有效的 skill
            is_valid, errors = validate_skill_directory(source_dir)
            if not is_valid:
                return MigrationResult(
                    success=False,
                    skill_name=target_name,
                    message=f"源目录不是有效的 skill: {', '.join(errors)}"
                )
            
            # 复制目录
            if target_path.exists():
                shutil.rmtree(target_path)
            
            shutil.copytree(source_dir, target_path)
            
            # 验证复制后的 skill
            is_valid, errors = validate_skill_directory(target_path)
            
            result = MigrationResult(
                success=is_valid,
                skill_name=target_name,
                target_path=target_path,
                message=f"Skill '{target_name}' 迁移成功" if is_valid else f"迁移后验证失败",
                errors=errors if not is_valid else []
            )
            
            return result
            
        except Exception as e:
            logger.error(f"迁移失败: {e}")
            return MigrationResult(
                success=False,
                skill_name=target_name,
                message=f"迁移失败: {str(e)}"
            )
    
    def migrate_from_git(
        self, 
        git_url: str, 
        skill_name: Optional[str] = None,
        subdir: Optional[str] = None,
        overwrite: bool = False
    ) -> MigrationResult:
        """
        从 Git 仓库迁移 skill
        
        Args:
            git_url: Git 仓库地址
            skill_name: 目标 skill 名称
            subdir: skill 在仓库中的子目录（如果 skill 不在仓库根目录）
            overwrite: 是否覆盖已存在的 skill
            
        Returns:
            MigrationResult 迁移结果
        """
        # 检查 git 是否可用
        if not shutil.which("git"):
            return MigrationResult(
                success=False,
                message="Git 未安装，请先安装 Git"
            )
        
        # 从 URL 提取默认 skill 名称
        if not skill_name:
            parsed = urlparse(git_url)
            path = parsed.path
            # 移除 .git 后缀
            skill_name = Path(path).stem
        
        target_path = self.target_dir / skill_name
        
        # 检查是否已存在
        if target_path.exists() and not overwrite:
            return MigrationResult(
                success=False,
                skill_name=skill_name,
                target_path=target_path,
                message=f"Skill '{skill_name}' 已存在，使用 --overwrite 覆盖"
            )
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            clone_dir = temp_path / "repo"
            
            try:
                # 克隆仓库
                logger.info(f"克隆仓库: {git_url}")
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", git_url, str(clone_dir)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # 确定 skill 源目录
                if subdir:
                    source_dir = clone_dir / subdir
                else:
                    # 尝试在仓库中查找 skill 目录
                    source_dir = self._find_skill_in_directory(clone_dir)
                    if not source_dir:
                        source_dir = clone_dir
                
                if not source_dir.exists():
                    return MigrationResult(
                        success=False,
                        skill_name=skill_name,
                        message=f"找不到 skill 目录: {subdir or '仓库根目录'}"
                    )
                
                # 迁移到目标目录
                return self.migrate_from_directory(source_dir, skill_name, overwrite)
                
            except subprocess.CalledProcessError as e:
                return MigrationResult(
                    success=False,
                    skill_name=skill_name,
                    message=f"Git 克隆失败: {e.stderr}"
                )
            except Exception as e:
                return MigrationResult(
                    success=False,
                    skill_name=skill_name,
                    message=f"迁移失败: {str(e)}"
                )
    
    def migrate_from_zip(
        self, 
        zip_path: Path, 
        skill_name: Optional[str] = None,
        subdir: Optional[str] = None,
        overwrite: bool = False
    ) -> MigrationResult:
        """
        从 ZIP 文件迁移 skill
        
        Args:
            zip_path: ZIP 文件路径
            skill_name: 目标 skill 名称
            subdir: skill 在 ZIP 中的子目录
            overwrite: 是否覆盖已存在的 skill
            
        Returns:
            MigrationResult 迁移结果
        """
        zip_path = Path(zip_path).resolve()
        
        if not zip_path.exists():
            return MigrationResult(
                success=False,
                message=f"ZIP 文件不存在: {zip_path}"
            )
        
        # 确定 skill 名称
        if not skill_name:
            skill_name = zip_path.stem
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_dir = temp_path / "extracted"
            
            try:
                # 解压 ZIP
                logger.info(f"解压 ZIP: {zip_path}")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # 确定 skill 源目录
                if subdir:
                    source_dir = extract_dir / subdir
                else:
                    # 尝试在解压目录中查找 skill
                    source_dir = self._find_skill_in_directory(extract_dir)
                    if not source_dir:
                        # 如果解压后只有一个目录，进入该目录
                        items = [d for d in extract_dir.iterdir() if d.is_dir()]
                        if len(items) == 1:
                            source_dir = items[0]
                        else:
                            source_dir = extract_dir
                
                if not source_dir.exists():
                    return MigrationResult(
                        success=False,
                        skill_name=skill_name,
                        message=f"找不到 skill 目录: {subdir or 'ZIP 根目录'}"
                    )
                
                # 迁移到目标目录
                return self.migrate_from_directory(source_dir, skill_name, overwrite)
                
            except zipfile.BadZipFile:
                return MigrationResult(
                    success=False,
                    skill_name=skill_name,
                    message=f"无效的 ZIP 文件: {zip_path}"
                )
            except Exception as e:
                return MigrationResult(
                    success=False,
                    skill_name=skill_name,
                    message=f"迁移失败: {str(e)}"
                )
    
    def _find_skill_in_directory(self, directory: Path) -> Optional[Path]:
        """
        在目录中查找 skill 目录
        
        Args:
            directory: 搜索目录
            
        Returns:
            skill 目录路径，未找到返回 None
        """
        # 直接检查当前目录
        skill_md = directory / "SKILL.md"
        if skill_md.exists():
            return directory
        
        # 搜索子目录
        for item in directory.iterdir():
            if item.is_dir():
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    return item
        
        return None
    
    def list_importable_skills(self, source_dir: Path) -> List[Dict]:
        """
        列出目录中可导入的 skills
        
        Args:
            source_dir: 源目录
            
        Returns:
            可导入的 skill 列表
        """
        source_dir = Path(source_dir)
        importable = []
        
        if not source_dir.exists():
            return importable
        
        # 检查当前目录
        is_valid, errors = validate_skill_directory(source_dir)
        if is_valid:
            skill_md = source_dir / "SKILL.md"
            if skill_md.exists():
                name, metadata = self._parse_skill_md(skill_md)
                importable.append({
                    "name": name or source_dir.name,
                    "path": str(source_dir),
                    "type": "skill",
                    "metadata": metadata
                })
        
        # 检查子目录
        for item in source_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                is_valid, errors = validate_skill_directory(item)
                if is_valid:
                    skill_md = item / "SKILL.md"
                    if skill_md.exists():
                        name, metadata = self._parse_skill_md(skill_md)
                        importable.append({
                            "name": name or item.name,
                            "path": str(item),
                            "type": "skill",
                            "metadata": metadata
                        })
        
        return importable
    
    def _parse_skill_md(self, skill_md_path: Path) -> Tuple[Optional[str], Dict]:
        """
        解析 SKILL.md 文件获取元数据
        
        Args:
            skill_md_path: SKILL.md 路径
            
        Returns:
            (skill 名称, 元数据字典)
        """
        try:
            content = skill_md_path.read_text(encoding='utf-8')
            
            # 提取 frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if frontmatter:
                        return frontmatter.get('name'), frontmatter
            
            return None, {}
        except Exception as e:
            logger.warning(f"解析 SKILL.md 失败: {e}")
            return None, {}


def migrate_skill(
    source: str,
    name: Optional[str] = None,
    target_dir: Optional[Path] = None,
    overwrite: bool = False,
    subdir: Optional[str] = None
) -> MigrationResult:
    """
    便捷函数：迁移 skill
    
    自动识别源类型（本地目录、Git URL、ZIP 文件）并执行迁移
    
    Args:
        source: 源路径（本地路径、Git URL、或 ZIP 路径）
        name: 目标 skill 名称
        target_dir: 目标目录
        overwrite: 是否覆盖
        subdir: 子目录（用于 Git/ZIP）
        
    Returns:
        MigrationResult 迁移结果
    """
    migrator = SkillMigrator(target_dir)
    
    # 判断源类型
    source_path = Path(source)
    
    # Git URL
    if source.startswith(('http://', 'https://', 'git@', 'git://')) or source.endswith('.git'):
        return migrator.migrate_from_git(source, name, subdir, overwrite)
    
    # ZIP 文件
    if source.endswith('.zip') or (source_path.exists() and source_path.suffix == '.zip'):
        return migrator.migrate_from_zip(source_path, name, subdir, overwrite)
    
    # 本地目录
    return migrator.migrate_from_directory(source_path, name, overwrite)
