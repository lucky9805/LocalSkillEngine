"""
API 鉴权模块

支持 api_key / api_secret 双因子校验。
启用方式：在 .env 中设置 ENABLE_AUTH=true，并配置 API_KEY 和 API_SECRET。

调用方式（二选一）：
  1. 请求头（推荐）：
       X-API-Key: <your_api_key>
       X-API-Secret: <your_api_secret>

  2. Query 参数：
       ?api_key=<your_api_key>&api_secret=<your_api_secret>
"""
import hmac
import logging
from typing import Optional, Dict, Any

from fastapi import HTTPException, Depends, status, Request

from skill_service.config import get_settings

logger = logging.getLogger(__name__)


def _safe_compare(a: str, b: str) -> bool:
    """使用常数时间比较，防止时序攻击"""
    return hmac.compare_digest(a.encode(), b.encode())


async def extract_credentials(request: Request) -> Dict[str, Any]:
    """
    从请求中提取 API 凭证
    
    优先从 Header 提取，其次从 Query 参数提取
    
    Returns:
        Dict 包含 api_key 和 api_secret
    """
    # 从 Header 提取
    api_key = request.headers.get("X-API-Key")
    api_secret = request.headers.get("X-API-Secret")
    
    # 如果 Header 没有，从 Query 参数提取
    if not api_key:
        api_key = request.query_params.get("api_key")
    if not api_secret:
        api_secret = request.query_params.get("api_secret")
    
    return {
        "api_key": api_key,
        "api_secret": api_secret
    }


async def verify_api_credentials(
    credentials: Dict[str, Any] = Depends(extract_credentials),
) -> None:
    """
    FastAPI 依赖：校验 api_key + api_secret。

    - 若 enable_auth=False，直接放行（开发模式）。
    - Header 优先于 Query 参数。
    - api_key 和 api_secret **必须同时正确**，缺一不可。

    Raises:
        HTTPException 401: 未提供凭证
        HTTPException 403: 凭证错误
        HTTPException 500: 服务器未正确配置凭证（仍为默认值）
    """
    settings = get_settings()

    # 鉴权未开启时直接放行
    if not settings.enable_auth:
        return

    # 检查服务端是否仍使用默认凭证（危险配置）
    if settings.is_using_default_credentials:
        logger.error("API 鉴权已启用，但仍使用默认凭证，拒绝所有请求！请在 .env 中配置 API_KEY 和 API_SECRET。")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器鉴权配置错误：仍在使用默认凭证，请联系管理员",
        )

    # 从 credentials 中提取凭证
    api_key = credentials.get("api_key")
    api_secret = credentials.get("api_secret")

    # 未提供任何凭证 → 401
    if not api_key and not api_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少鉴权凭证：请在请求头中提供 X-API-Key 和 X-API-Secret",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 只提供了其中一个 → 401
    if not api_key or not api_secret:
        missing = "X-API-Key" if not api_key else "X-API-Secret"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"缺少鉴权凭证：{missing} 未提供",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # 校验 key 和 secret（常数时间比较）
    key_ok = _safe_compare(api_key, settings.api_key)
    secret_ok = _safe_compare(api_secret, settings.api_secret)

    if not key_ok or not secret_ok:
        # 不要透露是 key 还是 secret 错了，统一返回 403
        logger.warning(
            "API 鉴权失败：key_ok=%s, secret_ok=%s（IP/请求路径未记录以避免日志注入）",
            key_ok,
            secret_ok,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="鉴权失败：api_key 或 api_secret 不正确",
        )

    # 通过
    logger.debug("API 鉴权通过")
