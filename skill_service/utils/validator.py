"""
验证工具模块 - 符合 Agent Skills 规范

参考: https://github.com/agentskills/agentskills
"""
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


# 常量定义
MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500

# 允许的 frontmatter 字段
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "compatibility",
}


class ValidationError(Exception):
    """验证错误"""
    pass


class ParseError(Exception):
    """解析错误"""
    pass


def validate_skill_name(name: str, skill_dir: Optional[Path] = None) -> List[str]:
    """
    验证 skill 名称格式 - Agent Skills 标准
    
    规则:
    - 1-64 字符
    - 只能包含小写字母、数字和连字符
    - 不能以连字符开头或结尾
    - 不能包含连续连字符
    - 目录名必须与 skill name 匹配
    
    Args:
        name: skill 名称
        skill_dir: skill 目录路径（可选）
        
    Returns:
        错误列表，空列表表示验证通过
    """
    errors = []
    
    if not name or not isinstance(name, str) or not name.strip():
        errors.append("Field 'name' must be a non-empty string")
        return errors
    
    # Unicode 规范化
    name = unicodedata.normalize("NFKC", name.strip())
    
    # 长度检查
    if len(name) > MAX_SKILL_NAME_LENGTH:
        errors.append(
            f"Skill name '{name}' exceeds {MAX_SKILL_NAME_LENGTH} character limit "
            f"({len(name)} chars)"
        )
    
    # 小写检查
    if name != name.lower():
        errors.append(f"Skill name '{name}' must be lowercase")
    
    # 开头/结尾连字符检查
    if name.startswith("-") or name.endswith("-"):
        errors.append("Skill name cannot start or end with a hyphen")
    
    # 连续连字符检查
    if "--" in name:
        errors.append("Skill name cannot contain consecutive hyphens")
    
    # 字符集检查
    if not all(c.isalnum() or c == "-" for c in name):
        errors.append(
            f"Skill name '{name}' contains invalid characters. "
            "Only lowercase letters, digits, and hyphens are allowed."
        )
    
    # 目录名匹配检查
    if skill_dir:
        dir_name = unicodedata.normalize("NFKC", skill_dir.name)
        if dir_name != name:
            errors.append(
                f"Directory name '{skill_dir.name}' must match skill name '{name}'"
            )
    
    return errors


def validate_description(description: str) -> List[str]:
    """
    验证 description 格式
    
    规则:
    - 不能为空
    - 最多 1024 字符
    
    Args:
        description: 描述文本
        
    Returns:
        错误列表
    """
    errors = []
    
    if not description or not isinstance(description, str) or not description.strip():
        errors.append("Field 'description' must be a non-empty string")
        return errors
    
    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"Description exceeds {MAX_DESCRIPTION_LENGTH} character limit "
            f"({len(description)} chars)"
        )
    
    return errors


def validate_compatibility(compatibility: str) -> List[str]:
    """验证 compatibility 格式"""
    errors = []
    
    if not isinstance(compatibility, str):
        errors.append("Field 'compatibility' must be a string")
        return errors
    
    if len(compatibility) > MAX_COMPATIBILITY_LENGTH:
        errors.append(
            f"Compatibility exceeds {MAX_COMPATIBILITY_LENGTH} character limit "
            f"({len(compatibility)} chars)"
        )
    
    return errors


def validate_metadata_fields(metadata: Dict[str, Any]) -> List[str]:
    """验证 frontmatter 字段是否包含未定义的字段"""
    errors = []
    
    extra_fields = set(metadata.keys()) - ALLOWED_FIELDS
    if extra_fields:
        errors.append(
            f"Unexpected fields in frontmatter: {', '.join(sorted(extra_fields))}. "
            f"Only {sorted(ALLOWED_FIELDS)} are allowed."
        )
    
    return errors


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    解析 SKILL.md 的 YAML frontmatter
    
    Args:
        content: SKILL.md 文件内容
        
    Returns:
        (metadata 字典, markdown body)
        
    Raises:
        ParseError: 如果 frontmatter 格式不正确
    """
    if not content.startswith("---"):
        raise ParseError("SKILL.md must start with YAML frontmatter (---)")
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ParseError("SKILL.md frontmatter not properly closed with ---")
    
    frontmatter_str = parts[1]
    body = parts[2].strip()
    
    try:
        import yaml
        metadata = yaml.safe_load(frontmatter_str)
        if not isinstance(metadata, dict):
            raise ParseError("SKILL.md frontmatter must be a YAML mapping")
        
        # 处理 metadata 字段，确保值为字符串
        if "metadata" in metadata and isinstance(metadata["metadata"], dict):
            metadata["metadata"] = {str(k): str(v) for k, v in metadata["metadata"].items()}
        
        return metadata, body
    except ImportError:
        raise ParseError("PyYAML is required to parse frontmatter")
    except Exception as e:
        raise ParseError(f"Invalid YAML in frontmatter: {e}")


def validate_frontmatter(metadata: Dict[str, Any], skill_dir: Optional[Path] = None) -> List[str]:
    """
    验证完整的 frontmatter
    
    Args:
        metadata: 解析后的 frontmatter 字典
        skill_dir: skill 目录路径（可选）
        
    Returns:
        错误列表
    """
    errors = []
    
    # 检查必需字段
    if "name" not in metadata:
        errors.append("Missing required field in frontmatter: name")
    else:
        errors.extend(validate_skill_name(metadata["name"], skill_dir))
    
    if "description" not in metadata:
        errors.append("Missing required field in frontmatter: description")
    else:
        errors.extend(validate_description(metadata["description"]))
    
    # 检查可选字段
    if "compatibility" in metadata:
        errors.extend(validate_compatibility(metadata["compatibility"]))
    
    # 检查额外字段（警告）
    errors.extend(validate_metadata_fields(metadata))
    
    return errors


def validate_skill_directory(skill_dir: Path, strict: bool = False) -> Tuple[bool, List[str]]:
    """
    验证 skill 目录
    
    Args:
        skill_dir: skill 目录路径
        strict: 是否使用严格模式（验证 Agent Skills 标准）
        
    Returns:
        (是否通过, 错误列表)
    """
    skill_dir = Path(skill_dir)
    errors = []
    
    if not skill_dir.exists():
        return False, [f"Path does not exist: {skill_dir}"]
    
    if not skill_dir.is_dir():
        return False, [f"Not a directory: {skill_dir}"]
    
    # 查找 SKILL.md（支持大小写）
    skill_md = None
    for name in ("SKILL.md", "skill.md"):
        path = skill_dir / name
        if path.exists():
            skill_md = path
            break
    
    if skill_md is None:
        return False, ["Missing required file: SKILL.md"]
    
    try:
        content = skill_md.read_text(encoding='utf-8')
        metadata, _ = parse_frontmatter(content)
    except ParseError as e:
        return False, [str(e)]
    except Exception as e:
        return False, [f"Error reading SKILL.md: {e}"]
    
    # 验证 frontmatter
    fm_errors = validate_frontmatter(metadata, skill_dir)
    errors.extend(fm_errors)
    
    # 严格模式：检查目录结构
    if strict:
        # 检查 scripts 目录（如果存在）
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists() and not scripts_dir.is_dir():
            errors.append("'scripts' must be a directory")
        
        # 检查 references 目录（如果存在）
        refs_dir = skill_dir / "references"
        if refs_dir.exists() and not refs_dir.is_dir():
            errors.append("'references' must be a directory")
        
        # 检查 assets 目录（如果存在）
        assets_dir = skill_dir / "assets"
        if assets_dir.exists() and not assets_dir.is_dir():
            errors.append("'assets' must be a directory")
    
    return len(errors) == 0, errors


def read_skill_properties(skill_dir: Path) -> Dict[str, Any]:
    """
    读取 skill 属性（不验证，只解析）
    
    Args:
        skill_dir: skill 目录路径
        
    Returns:
        skill 属性字典
        
    Raises:
        ParseError: 如果解析失败
    """
    skill_dir = Path(skill_dir)
    
    skill_md = None
    for name in ("SKILL.md", "skill.md"):
        path = skill_dir / name
        if path.exists():
            skill_md = path
            break
    
    if skill_md is None:
        raise ParseError(f"SKILL.md not found in {skill_dir}")
    
    content = skill_md.read_text(encoding='utf-8')
    metadata, body = parse_frontmatter(content)
    
    # 构建属性字典
    props = {
        "name": metadata.get("name", ""),
        "description": metadata.get("description", ""),
        "instructions": body,
        "path": str(skill_md.absolute()),
        "skill_dir": str(skill_dir.absolute()),
    }
    
    # 可选字段
    if "license" in metadata:
        props["license"] = metadata["license"]
    if "compatibility" in metadata:
        props["compatibility"] = metadata["compatibility"]
    if "allowed-tools" in metadata:
        props["allowed_tools"] = metadata["allowed-tools"]
    if "metadata" in metadata:
        props["metadata"] = metadata["metadata"]
    
    return props


# 向后兼容：保留旧的验证函数签名
def validate_skill_md(content: str) -> Tuple[bool, str]:
    """
    验证 SKILL.md 内容（向后兼容）
    
    Returns:
        (是否有效, 错误信息)
    """
    try:
        metadata, _ = parse_frontmatter(content)
        errors = validate_frontmatter(metadata)
        if errors:
            return False, "; ".join(errors)
        return True, ""
    except ParseError as e:
        return False, str(e)


def validate_skill_path(path: str) -> bool:
    """
    验证 skill 路径是否有效（向后兼容）
    
    Args:
        path: Skill 路径

    Returns:
        是否有效
    """
    skill_path = Path(path)
    return skill_path.exists() and skill_path.is_dir()


def validate_parameters(parameters: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    验证参数是否符合 schema

    Args:
        parameters: 参数字典
        schema: 参数 schema

    Returns:
        (是否有效, 错误信息)
    """
    required = schema.get('required', [])

    for field in required:
        if field not in parameters:
            return False, f"缺少必要参数: {field}"

    return True, ""


def validate_parameters(parameters: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, str]:
    """
    验证参数是否符合 schema

    Args:
        parameters: 参数字典
        schema: 参数 schema

    Returns:
        (是否有效, 错误信息)
    """
    # 简单验证逻辑，可以根据需要扩展
    required = schema.get('required', [])

    for field in required:
        if field not in parameters:
            return False, f"缺少必要参数: {field}"

    return True, ""
