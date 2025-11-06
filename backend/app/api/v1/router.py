# app/api/v1/router.py

from fastapi import APIRouter
from app.api.v1.endpoints import documents, graphs, categories, entities, relations, config, prompts, ai_config, system_config, chat

# 创建v1版本的主路由
api_router = APIRouter()

# 包含各个功能模块的路由
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

api_router.include_router(
    graphs.router,
    prefix="/graphs",
    tags=["graphs"]
)

api_router.include_router(
    categories.router,
    prefix="/categories",
    tags=["categories"]
)

api_router.include_router(
    entities.router,
    prefix="/entities",
    tags=["entities"]
)

api_router.include_router(
    relations.router,
    prefix="/relations",
    tags=["relations"]
)

api_router.include_router(
    config.router,
    prefix="/config",
    tags=["config"]
)

api_router.include_router(
    prompts.router,
    prefix="/prompts",
    tags=["prompts"]
)

api_router.include_router(
    ai_config.router,
    prefix="/ai-configs",
    tags=["ai-configs"]
)

api_router.include_router(
    system_config.router,
    prefix="/system-config",
    tags=["system-config"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)