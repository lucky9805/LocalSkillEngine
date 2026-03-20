"""
FastAPI 服务器模块
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from skill_service.config import get_settings
from skill_service.api.routes import router
from skill_service.utils.logger import get_logger

# 获取配置
settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    Args:
        app: FastAPI 应用实例
    """
    # 启动时
    logger.info("=" * 80)
    logger.info("Skill Service API 启动中...")
    logger.info("=" * 80)
    logger.info(f"版本: {settings.api_prefix}")
    logger.info(f"调试模式: {settings.debug}")
    logger.info(f"Skills 目录: {settings.skills_directory}")

    # 鉴权状态提示
    if settings.enable_auth:
        if settings.is_using_default_credentials:
            logger.warning("⚠️  [安全警告] 鉴权已启用，但 API_KEY / API_SECRET 仍为默认值！")
            logger.warning("⚠️  请立即在 .env 中修改 API_KEY 和 API_SECRET，否则所有受保护接口将拒绝访问！")
        else:
            logger.info("🔒 API 鉴权已启用（X-API-Key + X-API-Secret 双因子）")
    else:
        logger.warning("⚠️  [安全提示] API 鉴权未启用（ENABLE_AUTH=false）")
        logger.warning("⚠️  生产环境请在 .env 中设置 ENABLE_AUTH=true 并配置 API_KEY / API_SECRET")

    logger.info("=" * 80)

    yield

    # 关闭时
    logger.info("Skill Service API 正在关闭...")


# 创建 FastAPI 应用
app = FastAPI(
    title="Skill Service API",
    description="本地 Skill 运行服务 API - 支持通过 HTTP 接口运行和管理 skills",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(
    router,
    prefix=settings.api_prefix,
    tags=["skills"]
)


def custom_openapi():
    """
    自定义 OpenAPI schema，添加双因子鉴权的安全方案
    
    在 Swagger UI 中显示两个输入框：API Key 和 API Secret
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 添加安全方案 - 使用清晰的名称，与显示的名称一致
    openapi_schema["components"]["securitySchemes"] = {
        "X-API-Key": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key 凭证"
        },
        "X-API-Secret": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Secret",
            "description": "API Secret 凭证"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求验证异常处理

    Args:
        request: 请求对象
        exc: 验证异常

    Returns:
        JSON 错误响应
    """
    logger.error(f"请求验证失败: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "请求参数验证失败",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        JSON 错误响应
    """
    logger.error(f"未处理的异常: {type(exc).__name__}: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "服务器内部错误",
            "error": str(exc) if settings.debug else None
        }
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    请求日志中间件

    Args:
        request: 请求对象
        call_next: 下一个中间件或路由处理器

    Returns:
        响应对象
    """
    # 记录请求
    logger.info(f"请求: {request.method} {request.url.path}")

    # 处理请求
    response = await call_next(request)

    # 记录响应状态
    logger.info(f"响应: {response.status_code}")

    return response


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Skill Service API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }
