"""
API 路由模块
"""
from fastapi import APIRouter, HTTPException, status
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
    ImportResponse
)
from skill_service.runner import SkillRunner
from skill_service.models import SkillExecutionRequest as ModelExecutionRequest
from skill_service.utils.logger import get_logger

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

        return SkillListResponse(
            skills=skills_info,
            total=len(skills_info)
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
    description="执行指定的 skill 并返回结果"
)
async def run_skill(skill_name: str, request: SkillExecutionRequest) -> SkillExecutionResult:
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
            timeout=request.timeout
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
    description="重新加载所有 skills（热更新）"
)
async def reload_skills() -> dict:
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
    description="通过自然语言描述自动选择并执行 skill"
)
async def chat(request: ChatRequest) -> ChatResponse:
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
        llm = manager.create_llm_provider()
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
            parameters=selection.parameters
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
    description="从本地目录导入 skill"
)
async def import_from_directory(request: ImportFromDirectoryRequest) -> ImportResponse:
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
    description="从 Git 仓库克隆并导入 skill"
)
async def import_from_git(request: ImportFromGitRequest) -> ImportResponse:
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
