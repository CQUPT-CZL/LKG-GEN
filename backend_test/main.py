# main.py

from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 包含v1版本的API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": f"欢迎来到 {settings.PROJECT_NAME}"}

# 在这里可以添加应用的启动和关闭事件，例如连接和断开Neo4j驱动
# @app.on_event("startup")
# def startup_event():
#     ...

# @app.on_event("shutdown")
# def shutdown_event():
#     ...