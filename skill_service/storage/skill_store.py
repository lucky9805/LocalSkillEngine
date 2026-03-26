"""
Skill 存储模块 - 符合 Agent Skills 规范
"""
from pathlib import Path
from typing import Dict, List, Optional, Any

from skill_service.config import get_settings
from skill_service.models import Skill, SkillInfo
from skill_service.utils.logger import get_logger
from skill_service.utils.validator import (
    validate_skill_directory,
    read_skill_properties,
    parse_frontmatter,
    validate_frontmatter,
    ParseError,
)


class SkillStore:
    """
    Skill 存储类 - 符合 Agent Skills 规范
    
    支持渐进式披露：
    - Tier 1: Catalog (name + description)
    - Tier 2: Instructions (SKILL.md body)
    - Tier 3: Resources (scripts, references, assets)
    """

    def __init__(self):
        """初始化 skill 存储"""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.skills: Dict[str, Skill] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        """加载所有 skills"""
        self.logger.info("开始加载 skills...")

        skills_dir = Path(self.settings.skills_directory)
        if not skills_dir.exists():
            skills_dir.mkdir(parents=True, exist_ok=True)
            self.logger.warning(f"创建 skills 目录: {skills_dir}")
            return

        loaded_count = 0
        error_count = 0

        for skill_path in skills_dir.iterdir():
            if skill_path.is_dir():
                # 跳过隐藏目录和特殊目录
                if skill_path.name.startswith('.') or skill_path.name == '__pycache__':
                    continue
                    
                skill = self._load_skill(skill_path)
                if skill:
                    loaded_count += 1
                else:
                    error_count += 1

        self.logger.info(f"加载完成: {loaded_count} 个成功, {error_count} 个失败, 共 {len(self.skills)} 个 skills")

    def _load_skill(self, skill_path: Path) -> Optional[Skill]:
        """
        加载单个 skill

        Args:
            skill_path: Skill 目录路径

        Returns:
            加载的 Skill 对象，失败返回 None
        """
        # 跳过有 .skip 标记的目录
        if (skill_path / '.skip').exists():
            return None
        
        # 检查 SKILL.md 是否存在（支持大小写）
        skill_md_path = None
        for name in ("SKILL.md", "skill.md"):
            path = skill_path / name
            if path.exists():
                skill_md_path = path
                break

        if not skill_md_path:
            # 如果目录为空，静默跳过；否则输出警告
            try:
                is_empty = not any(skill_path.iterdir())
            except Exception:
                is_empty = False
            if not is_empty:
                self.logger.warning(f"未找到 SKILL.md，已跳过: {skill_path.resolve()}")
            return None

        try:
            # 读取并解析属性
            props = read_skill_properties(skill_path)
            
            # 验证（警告但不阻止加载）
            is_valid, errors = validate_skill_directory(skill_path)
            if not is_valid:
                self.logger.warning(f"Skill '{props['name']}' 验证警告: {'; '.join(errors)}")

            # 创建 Skill 对象
            skill = Skill(
                name=props['name'],
                description=props['description'],
                license=props.get('license'),
                compatibility=props.get('compatibility'),
                allowed_tools=props.get('allowed_tools'),
                metadata=props.get('metadata', {}),
                instructions=props['instructions'],
                scripts=self._scan_scripts(skill_path),
                references=self._scan_references(skill_path),
                assets=self._scan_assets(skill_path),
                path=props['path'],
            )
            skill.skill_dir = props['skill_dir']

            self.skills[skill.name] = skill
            
            # 从 metadata 获取版本信息用于日志
            version = skill.metadata.get('version', '1.0.0')
            self.logger.info(f"成功加载 skill: {skill.name} v{version}")

            return skill

        except ParseError as e:
            self.logger.error(f"解析 SKILL.md 失败 {skill_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"加载 skill 失败 {skill_path}: {e}")
            return None

    def _scan_scripts(self, skill_path: Path) -> Dict[str, str]:
        """
        扫描 skill 目录下的脚本文件

        Args:
            skill_path: Skill 目录路径

        Returns:
            脚本文件名到路径的映射
        """
        scripts = {}
        scripts_dir = skill_path / "scripts"

        if scripts_dir.exists() and scripts_dir.is_dir():
            for script_file in scripts_dir.iterdir():
                if script_file.is_file():
                    scripts[script_file.name] = str(script_file)

        return scripts

    def _scan_references(self, skill_path: Path) -> Dict[str, str]:
        """
        扫描 skill 目录下的 references 文件

        Args:
            skill_path: Skill 目录路径

        Returns:
            参考文档文件名到路径的映射
        """
        references = {}
        references_dir = skill_path / "references"

        if references_dir.exists() and references_dir.is_dir():
            for ref_file in references_dir.iterdir():
                if ref_file.is_file():
                    references[ref_file.name] = str(ref_file)

        return references

    def _scan_assets(self, skill_path: Path) -> Dict[str, str]:
        """
        扫描 skill 目录下的 assets 文件

        Args:
            skill_path: Skill 目录路径

        Returns:
            资源文件名到路径的映射
        """
        assets = {}
        assets_dir = skill_path / "assets"

        if assets_dir.exists() and assets_dir.is_dir():
            for asset_file in assets_dir.rglob("*"):
                if asset_file.is_file():
                    # 使用相对路径作为 key
                    rel_path = asset_file.relative_to(assets_dir)
                    assets[str(rel_path)] = str(asset_file)

        return assets

    def list_skills(self) -> List[SkillInfo]:
        """
        列出所有 skills - Tier 1: Catalog
        
        只返回 name 和 description，用于模型判断何时使用 skill。
        这是渐进式披露的第一级，token 成本最低。

        Returns:
            Skill 信息列表
        """
        return [
            SkillInfo(
                name=skill.name,
                description=skill.description,
                location=skill.path,
                enabled=skill.enabled,
                status=skill.status
            )
            for skill in self.skills.values()
            if skill.enabled
        ]

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        获取 skill - Tier 2: Instructions
        
        返回完整的 Skill 对象，包含 instructions。
        这是渐进式披露的第二级，在 skill 被激活时加载。

        Args:
            name: Skill 名称

        Returns:
            Skill 对象，不存在返回 None
        """
        return self.skills.get(name)

    def get_skill_catalog(self) -> Dict[str, Any]:
        """
        获取 skill 目录 - 用于生成 prompt
        
        Returns:
            包含所有 skill 元数据的字典
        """
        return {
            name: {
                "name": skill.name,
                "description": skill.description,
                "location": skill.path,
            }
            for name, skill in self.skills.items()
            if skill.enabled
        }

    def has_skill(self, name: str) -> bool:
        """
        检查 skill 是否存在

        Args:
            name: Skill 名称

        Returns:
            是否存在
        """
        return name in self.skills

    def reload(self) -> None:
        """重新加载所有 skills"""
        self.logger.info("重新加载 skills...")
        self.skills.clear()
        self._load_skills()

    def validate_skill(self, name: str) -> tuple[bool, List[str]]:
        """
        验证指定 skill

        Args:
            name: Skill 名称

        Returns:
            (是否通过, 错误列表)
        """
        skill = self.get_skill(name)
        if not skill:
            return False, [f"Skill '{name}' not found"]
        
        return validate_skill_directory(Path(skill.skill_dir))