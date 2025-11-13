# app/core/middleware.py

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    记录所有HTTP请求和响应的中间件
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始时间
        start_time = time.time()

        # 获取请求信息
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        # 记录请求开始
        logger.info(
            f"请求开始: {method} {url}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "client_ip": client_host,
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )

        # 处理请求
        try:
            response = await call_next(request)

            # 计算处理时间
            duration = (time.time() - start_time) * 1000  # 转换为毫秒

            # 记录响应
            logger.info(
                f"请求完成: {method} {url} - 状态码: {response.status_code} - 耗时: {duration:.2f}ms",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "duration": duration,
                }
            )

            # 添加请求ID到响应头
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # 计算处理时间
            duration = (time.time() - start_time) * 1000

            # 记录错误
            logger.error(
                f"请求失败: {method} {url} - 错误: {str(e)} - 耗时: {duration:.2f}ms",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": method,
                    "url": url,
                    "duration": duration,
                    "error": str(e),
                }
            )

            # 重新抛出异常，让FastAPI的异常处理器处理
            raise


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    专门记录错误的中间件
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)

            # 如果是错误状态码，记录详细信息
            if response.status_code >= 400:
                request_id = getattr(request.state, "request_id", "unknown")
                logger.warning(
                    f"HTTP错误响应: {request.method} {request.url.path} - 状态码: {response.status_code}",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "url": str(request.url),
                        "status_code": response.status_code,
                    }
                )

            return response

        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.exception(
                f"未捕获的异常: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                }
            )
            raise
