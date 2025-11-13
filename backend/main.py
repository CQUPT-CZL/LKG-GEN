# main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.logging_config import setup_logging, get_logger
from app.core.middleware import LoggingMiddleware, ErrorLoggingMiddleware
import logging

# 初始化日志系统
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    json_logs=settings.LOG_JSON_FORMAT,
    enable_file_logging=settings.LOG_FILE_ENABLED,
    enable_console_logging=settings.LOG_CONSOLE_ENABLED,
)

logger = get_logger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorLoggingMiddleware)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获所有未处理的异常并记录"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"全局异常捕获: {request.method} {request.url.path} - {str(exc)}",
        exc_info=True,
        extra={"request_id": request_id}
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "request_id": request_id
        }
    )

# 包含v1版本的API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    logger.info("访问根路径")
    return {"message": f"欢迎来到 {settings.PROJECT_NAME}"}

# 应用启动和关闭事件
@app.on_event("startup")
async def startup_event():
    logger.info(f"应用启动: {settings.PROJECT_NAME}")
    logger.info(f"API版本: {settings.API_V1_STR}")
    logger.info(f"日志级别: {settings.LOG_LEVEL}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"应用关闭: {settings.PROJECT_NAME}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)