"""
API 路由模块
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from skill_service.api.schemas import (
    SkillListResponse,
    SkillDetail,
    SkillExecutionRequest,
    SkillExecutionResult,
    SkillInfo,
    SkillInstallRequest,
    HealthResponse,
    ErrorResponse,
    ChatRequest,
    ChatResponse,
    SkillSelection,
    ChatExecutionResult,
    ImportFromDirectoryRequest,
    ImportFromGitRequest,
    ImportResponse,
    InstallRequest,
    InstallFromTextRequest,
    UninstallResponse,
)
from skill_service.runner import SkillRunner
from skill_service.models import SkillExecutionRequest as ModelExecutionRequest
from skill_service.utils.logger import get_logger
from skill_service.api.auth import verify_api_credentials

# 创建 router
router = APIRouter()

# 创建 runner 实例
runner = SkillRunner()
logger = get_logger(__name__)


@router.get(
    "/skills",
    response_model=SkillListResponse,
    summary="列出所有 Skills",
    description="获取所有可用的 skills 列表"
)
async def list_skills() -> SkillListResponse:
    """
    列出所有可用的 skills

    Returns:
        Skill 列表响应
    """
    try:
        skills_info = runner.list_skills()
        
        # 将 dataclass 转换为 Pydantic 模型
        skills_list = [
            SkillInfo(
                name=skill.name,
                version=skill.version,
                category=skill.category,
                description=skill.description,
                author=skill.author,
                enabled=skill.enabled,
                status=skill.status.value if hasattr(skill.status, 'value') else skill.status
            )
            for skill in skills_info
        ]

        return SkillListResponse(
            skills=skills_list,
            total=len(skills_list)
        )
    except Exception as e:
        logger.error(f"列出 skills 失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出 skills 失败: {str(e)}"
        )


@router.get(
    "/skills/{skill_name}",
    response_model=SkillDetail,
    summary="获取 Skill 详情",
    description="获取指定 skill 的详细信息"
)
async def get_skill(skill_name: str) -> SkillDetail:
    """
    获取 skill 的详细信息

    Args:
        skill_name: Skill 名称

    Returns:
        Skill 详细信息

    Raises:
        HTTPException: Skill 不存在时返回 404
    """
    try:
        skill_info = runner.get_skill_info(skill_name)

        if not skill_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill '{skill_name}' 不存在"
            )

        return SkillDetail(**skill_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 skill 详情失败 {skill_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 skill 详情失败: {str(e)}"
        )


@router.post(
    "/skills/{skill_name}/run",
    response_model=SkillExecutionResult,
    summary="运行 Skill",
    description="执行指定的 skill 并返回结果（需要鉴权）",
    openapi_extra={
        "security": [{"X-API-Key": [], "X-API-Secret": []}]
    }
)
async def run_skill(
    skill_name: str,
    request: SkillExecutionRequest,
    _auth: None = Depends(verify_api_credentials),
) -> SkillExecutionResult:
    """
    运行指定的 skill

    Args:
        skill_name: Skill 名称
        request: 执行请求，包含参数和超时设置

    Returns:
        执行结果

    Raises:
        HTTPException: Skill 不存在或执行失败时返回错误
    """
    try:
        # 创建模型请求对象
        model_request = ModelExecutionRequest(
            skill_name=skill_name,
            parameters=request.parameters,
            timeout=request.timeout,
            model=request.model
        )

        # 执行 skill
        result = await runner.execute(model_request)

        # 如果执行失败，返回 400 错误
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Skill 执行失败"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行 skill 失败 {skill_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行 skill 失败: {str(e)}"
        )


@router.post(
    "/skills/reload",
    response_model=dict,
    summary="重新加载 Skills",
    description="重新加载所有 skills（热更新）（需要鉴权）",
    openapi_extra={
        "security": [{"X-API-Key": [], "X-API-Secret": []}]
    }
)
async def reload_skills(
    _auth: None = Depends(verify_api_credentials),
) -> dict:
    """
    重新加载所有 skills

    Returns:
        重载结果
    """
    try:
        runner.reload_skills()

        return {
            "success": True,
            "message": "Skills 已重新加载"
        }
    except Exception as e:
        logger.error(f"重新加载 skills 失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新加载 skills 失败: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查服务健康状态"
)
async def health_check() -> HealthResponse:
    """
    健康检查端点

    Returns:
        健康状态信息
    """
    try:
        from skill_service import __version__

        return HealthResponse(
            status="healthy",
            version=__version__
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            version="unknown"
        )


@router.get(
    "/",
    summary="API 根路径",
    description="API 根路径，返回欢迎信息"
)
async def root() -> dict:
    """
    API 根路径

    Returns:
        欢迎信息
    """
    return {
        "message": "Skill Service API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="智能对话",
    description="通过自然语言描述自动选择并执行 skill（需要鉴权）",
    openapi_extra={
        "security": [{"X-API-Key": [], "X-API-Secret": []}]
    }
)
async def chat(
    request: ChatRequest,
    _auth: None = Depends(verify_api_credentials),
) -> ChatResponse:
    """
    智能对话接口 - 自动选择并执行 skill

    Args:
        request: 对话请求，包含用户输入

    Returns:
        包含 skill 选择和执行结果的响应

    Raises:
        HTTPException: 处理失败时返回错误
    """
    import asyncio
    from datetime import datetime
    from skill_service.llm.selector import SkillSelector
    from skill_service.llm.multi_model_config import get_multi_model_manager
    from skill_service.models import SkillExecutionRequest as ModelExecutionRequest
    
    try:
        # 创建 LLM 和 Selector
        manager = get_multi_model_manager()
        llm = manager.create_llm_provider(model=request.model)
        selector = SkillSelector(llm)
        
        # 获取可用 skills
        available_skills = runner.list_skills()
        
        if not available_skills:
            return ChatResponse(
                success=False,
                user_input=request.user_input,
                selection=SkillSelection(
                    skill_name=None,
                    confidence=0.0,
                    reasoning="没有可用的 skills",
                    parameters={},
                    direct_response="没有可用的 skills"
                ),
                error="没有可用的 skills",
                timestamp=datetime.now()
            )
        
        # 选择 skill
        selection = await selector.select_skill(request.user_input, available_skills)
        
        selection_data = SkillSelection(
            skill_name=selection.skill_name,
            confidence=selection.confidence,
            reasoning=selection.reasoning,
            parameters=selection.parameters,
            direct_response=selection.direct_response
        )
        
        # 如果没有匹配到 skill，返回直接回复
        if not selection.skill_name:
            return ChatResponse(
                success=True,
                user_input=request.user_input,
                selection=selection_data,
                timestamp=datetime.now()
            )
        
        # 执行 skill
        model_request = ModelExecutionRequest(
            skill_name=selection.skill_name,
            parameters=selection.parameters,
            model=request.model
        )
        
        result = await runner.execute(model_request)
        
        execution_result = ChatExecutionResult(
            success=result.success,
            result=result.result if result.success else None,
            error=result.error if not result.success else None,
            execution_time=result.execution_time,
            logs=result.logs
        )
        
        return ChatResponse(
            success=result.success,
            user_input=request.user_input,
            selection=selection_data,
            execution=execution_result,
            error=result.error if not result.success else None,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"智能对话处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"智能对话处理失败: {str(e)}"
        )


@router.post(
    "/import/directory",
    response_model=ImportResponse,
    summary="从目录导入 Skill",
    description="从本地目录导入 skill（需要鉴权）",
    openapi_extra={
        "security": [{"X-API-Key": [], "X-API-Secret": []}]
    }
)
async def import_from_directory(
    request: ImportFromDirectoryRequest,
    _auth: None = Depends(verify_api_credentials),
) -> ImportResponse:
    """
    从本地目录导入 skill
    
    Args:
        request: 导入请求
        
    Returns:
        导入结果
    """
    from skill_service.migrator import SkillMigrator
    
    try:
        migrator = SkillMigrator()
        result = migrator.migrate_from_directory(
            source_dir=Path(request.source_dir),
            skill_name=request.skill_name,
            overwrite=request.overwrite
        )
        
        # 重新加载 skills
        if result.success:
            runner.reload_skills()
        
        return ImportResponse(
            success=result.success,
            skill_name=result.skill_name,
            target_path=str(result.target_path) if result.target_path else None,
            message=result.message,
            warnings=result.warnings,
            errors=result.errors
        )
        
    except Exception as e:
        logger.error(f"导入 skill 失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.post(
    "/import/git",
    response_model=ImportResponse,
    summary="从 Git 导入 Skill",
    description="从 Git 仓库克隆并导入 skill（需要鉴权）",
    openapi_extra={
        "security": [{"X-API-Key": [], "X-API-Secret": []}]
    }
)
async def import_from_git(
    request: ImportFromGitRequest,
    _auth: None = Depends(verify_api_credentials),
) -> ImportResponse:
    """
    从 Git 仓库导入 skill

    Args:
        request: 导入请求

    Returns:
        导入结果
    """
    from skill_service.migrator import SkillMigrator

    try:
        migrator = SkillMigrator()
        result = migrator.migrate_from_git(
            git_url=request.git_url,
            skill_name=request.skill_name,
            subdir=request.subdir,
            overwrite=request.overwrite
        )

        # 重新加载 skills
        if result.success:
            runner.reload_skills()

        return ImportResponse(
            success=result.success,
            skill_name=result.skill_name,
            target_path=str(result.target_path) if result.target_path else None,
            message=result.message,
            warnings=result.warnings,
            errors=result.errors
        )

    except Exception as e:
        logger.error(f"从 Git 导入 skill 失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.post(
    "/install",
    response_model=ImportResponse,
    summary="安装 Skill",
    description="统一安装接口：自动识别 Git URL / 本地路径 / ZIP 文件（需要鉴权）",
    openapi_extra={
        "security": [{"X-API-Key": [], "X-API-Secret": []}]
    }
)
async def install_skill(
    request: InstallRequest,
    _auth: None = Depends(verify_api_credentials),
) -> ImportResponse:
    """
    统一安装 skill 接口

    自动识别来源类型：
    - Git URL (http/https/git@)
    - 本地目录路径
    - ZIP 文件路径

    Args:
        request: 安装请求

    Returns:
        安装结果
    """
    from skill_service.migrator import migrate_skill

    try:
        result = migrate_skill(
            source=request.source,
            name=request.skill_name,
            overwrite=request.overwrite,
            subdir=request.subdir
        )

        if result.success:
            runner.reload_skills()

        return ImportResponse(
            success=result.success,
            skill_name=result.skill_name,
            target_path=str(result.target_path) if result.target_path else None,
            message=result.message,
            warnings=result.warnings,
            errors=result.errors
        )

    except Exception as e:
        logger.error(f"安装 skill 失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"安装失败: {str(e)}"
        )


@router.post(
    "/install/text",
    response_model=ImportResponse,
    summary="从文本安装 Skill",
    description="将 SKILL.md 文本内容直接安装为 skill（需要鉴权）",
    openapi_extra={
        "security": [{"X-API-Key": [], "X-API-Secret": []}]
    }
)
async def install_skill_from_text(
    request: InstallFromTextRequest,
    _auth: None = Depends(verify_api_credentials),
) -> ImportResponse:
    """
    从 SKILL.md 文本内容安装 skill

    适合分享安装提示词的场景：将别人提供的 SKILL.md 内容
    直接 POST 过来即可完成安装。

    Args:
        request: 包含 SKILL.md 内容的安装请求

    Returns:
        安装结果
    """
    import shutil
    import yaml
    import re
    from skill_service.config import get_settings
    from skill_service.utils.validator import validate_skill_directory

    try:
        content = request.content.strip()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="content 不能为空"
            )

        # 解析 skill 名称
        skill_name = request.skill_name
        if not skill_name:
            try:
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        fm = yaml.safe_load(parts[1])
                        if fm and fm.get('name'):
                            skill_name = fm['name']
            except Exception:
                pass

        if not skill_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法从 SKILL.md 中提取 skill 名称，请在请求中指定 skill_name"
            )

        settings = get_settings()
        skills_dir = Path(settings.skills_directory)
        target_path = skills_dir / skill_name

        if target_path.exists():
            if not request.overwrite:
                return ImportResponse(
                    success=False,
                    skill_name=skill_name,
                    target_path=str(target_path),
                    message=f"Skill '{skill_name}' 已存在，设置 overwrite=true 覆盖"
                )
            shutil.rmtree(target_path)

        # 创建目录结构
        target_path.mkdir(parents=True)
        scripts_dir = target_path / 'scripts'
        scripts_dir.mkdir()

        # 写入 SKILL.md
        (target_path / 'SKILL.md').write_text(content, encoding='utf-8')

        # 提取脚本代码块
        named_pattern = re.compile(
            r'###\s+(?:scripts/)?(\w+\.py)\s*\n```(?:python|py)?\s*\n(.*?)```',
            re.DOTALL
        )
        found_named = False
        for match in named_pattern.finditer(content):
            filename, code = match.group(1), match.group(2)
            (scripts_dir / filename).write_text(code, encoding='utf-8')
            found_named = True

        if not found_named:
            generic_pattern = re.compile(r'```(?:python|py)\s*\n(.*?)```', re.DOTALL)
            match = generic_pattern.search(content)
            if match and 'def execute' in match.group(1):
                (scripts_dir / 'main.py').write_text(match.group(1), encoding='utf-8')

        # 验证
        is_valid, errors = validate_skill_directory(target_path)
        if not is_valid:
            shutil.rmtree(target_path)
            return ImportResponse(
                success=False,
                skill_name=skill_name,
                message="Skill 内容验证失败",
                errors=errors
            )

        runner.reload_skills()

        warnings = []
        main_py = scripts_dir / 'main.py'
        if not main_py.exists() or main_py.stat().st_size == 0:
            warnings.append("SKILL.md 中未找到可执行脚本，请手动创建 scripts/main.py")

        return ImportResponse(
            success=True,
            skill_name=skill_name,
            target_path=str(target_path),
            message=f"Skill '{skill_name}' 安装成功",
            warnings=warnings
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从文本安装 skill 失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"安装失败: {str(e)}"
        )


@router.delete(
    "/skills/{skill_name}",
    response_model=UninstallResponse,
    summary="卸载 Skill",
    description="删除已安装的 skill（需要鉴权）",
    openapi_extra={
        "security": [{"X-API-Key": [], "X-API-Secret": []}]
    }
)
async def uninstall_skill(
    skill_name: str,
    _auth: None = Depends(verify_api_credentials),
) -> UninstallResponse:
    """
    卸载（删除）已安装的 skill

    Args:
        skill_name: 要卸载的 skill 名称

    Returns:
        卸载结果
    """
    import shutil
    from skill_service.config import get_settings

    try:
        settings = get_settings()
        skill_path = Path(settings.skills_directory) / skill_name

        if not skill_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill '{skill_name}' 不存在"
            )

        shutil.rmtree(skill_path)
        runner.reload_skills()

        return UninstallResponse(
            success=True,
            skill_name=skill_name,
            message=f"Skill '{skill_name}' 已卸载"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"卸载 skill 失败 {skill_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"卸载失败: {str(e)}"
        )
