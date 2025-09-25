# app/api/v1/endpoints/system_config.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.crud.crud_system_config import crud_system_config
from app.schemas.system_config import (
    ChunkStrategyConfigRequest, 
    ChunkStrategyConfigResponse,
    SystemConfigResponse
)
from app.core.chunker import ChunkStrategy

router = APIRouter()

@router.get("/chunk-strategy", response_model=ChunkStrategyConfigResponse)
def get_chunk_strategy(
    db: Session = Depends(deps.get_db)
):
    """
    获取当前分块策略配置
    """
    try:
        current_strategy = crud_system_config.get_chunk_strategy(db)
        
        # 可用策略描述
        available_strategies = {
            "full_document": "全部文档作为一个块",
            "paragraph": "按段落分块（默认）",
            "sentence": "按句子分块"
        }
        
        return ChunkStrategyConfigResponse(
            strategy=current_strategy,
            description=available_strategies.get(current_strategy, "未知策略"),
            available_strategies=available_strategies
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分块策略失败: {str(e)}")

@router.put("/chunk-strategy", response_model=ChunkStrategyConfigResponse)
def update_chunk_strategy(
    *,
    db: Session = Depends(deps.get_db),
    config_in: ChunkStrategyConfigRequest
):
    """
    更新分块策略配置
    """
    try:
        # 验证策略是否有效
        valid_strategies = [strategy.value for strategy in ChunkStrategy]
        if config_in.strategy not in valid_strategies:
            raise HTTPException(
                status_code=400, 
                detail=f"无效的分块策略。可用策略: {', '.join(valid_strategies)}"
            )
        
        # 更新配置
        crud_system_config.set_chunk_strategy(db, config_in.strategy)
        
        # 返回更新后的配置
        available_strategies = {
            "full_document": "全部文档作为一个块",
            "paragraph": "按段落分块（默认）",
            "sentence": "按句子分块"
        }
        
        return ChunkStrategyConfigResponse(
            strategy=config_in.strategy,
            description=available_strategies.get(config_in.strategy, "未知策略"),
            available_strategies=available_strategies
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新分块策略失败: {str(e)}")

@router.get("/chunk-strategy/options")
def get_chunk_strategy_options():
    """
    获取所有可用的分块策略选项
    """
    return {
        "strategies": [
            {
                "value": "full_document",
                "label": "全文档",
                "description": "将整个文档作为一个块处理"
            },
            {
                "value": "paragraph", 
                "label": "段落",
                "description": "按段落分割文档（默认策略）"
            },
            {
                "value": "sentence",
                "label": "句子",
                "description": "按句子分割文档"
            }
        ]
    }