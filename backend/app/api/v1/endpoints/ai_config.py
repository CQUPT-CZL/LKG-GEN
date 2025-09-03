# app/api/v1/endpoints/ai_config.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.crud import crud_ai_config
from app.schemas import ai_config as ai_config_schemas
from app.models.sqlite_models import AIProviderEnum

router = APIRouter()


@router.post("/", response_model=ai_config_schemas.AIConfigResponse)
def create_ai_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: ai_config_schemas.AIConfigCreate
):
    """
    创建新的AI配置
    """
    try:
        ai_config = crud_ai_config.create_ai_config(db=db, config=config_in)
        return ai_config
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建AI配置失败: {str(e)}")


@router.get("/list", response_model=ai_config_schemas.AIConfigListResponse)
def get_ai_configs(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    provider: Optional[AIProviderEnum] = Query(None, description="AI提供商过滤"),
    is_active: Optional[bool] = Query(None, description="是否激活过滤")
):
    """
    获取AI配置列表
    """
    skip = (page - 1) * page_size
    
    configs = crud_ai_config.get_ai_configs(
        db=db, 
        skip=skip, 
        limit=page_size,
        provider=provider,
        is_active=is_active
    )
    
    total = crud_ai_config.get_ai_configs_count(
        db=db,
        provider=provider,
        is_active=is_active
    )
    
    return ai_config_schemas.AIConfigListResponse(
        configs=configs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{config_id}", response_model=ai_config_schemas.AIConfigResponse)
def get_ai_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int
):
    """
    根据ID获取AI配置详情
    """
    ai_config = crud_ai_config.get_ai_config(db=db, config_id=config_id)
    if not ai_config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    return ai_config


@router.put("/{config_id}", response_model=ai_config_schemas.AIConfigResponse)
def update_ai_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    config_in: ai_config_schemas.AIConfigUpdate
):
    """
    更新AI配置
    """
    ai_config = crud_ai_config.update_ai_config(
        db=db, 
        config_id=config_id, 
        config_update=config_in
    )
    if not ai_config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    return ai_config


@router.delete("/{config_id}")
def delete_ai_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int
):
    """
    删除AI配置
    """
    # 检查是否为默认配置
    ai_config = crud_ai_config.get_ai_config(db=db, config_id=config_id)
    if not ai_config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    if ai_config.is_default:
        raise HTTPException(status_code=400, detail="不能删除默认配置")
    
    success = crud_ai_config.delete_ai_config(db=db, config_id=config_id)
    if not success:
        raise HTTPException(status_code=400, detail="删除AI配置失败")
    
    return {"message": "AI配置删除成功"}


@router.get("/default/get", response_model=ai_config_schemas.AIConfigResponse)
def get_default_ai_config(
    db: Session = Depends(deps.get_db)
):
    """
    获取默认AI配置
    """
    ai_config = crud_ai_config.get_default_ai_config(db=db)
    if not ai_config:
        raise HTTPException(status_code=404, detail="未找到默认AI配置")
    return ai_config


@router.post("/default/set", response_model=ai_config_schemas.AIConfigResponse)
def set_default_ai_config(
    *,
    db: Session = Depends(deps.get_db),
    request: ai_config_schemas.SetDefaultAIConfigRequest
):
    """
    设置默认AI配置
    """
    ai_config = crud_ai_config.set_default_ai_config(
        db=db, 
        config_id=request.config_id
    )
    if not ai_config:
        raise HTTPException(
            status_code=404, 
            detail="AI配置不存在或未激活"
        )
    return ai_config


@router.get("/providers/list", response_model=ai_config_schemas.AIProvidersListResponse)
def get_ai_providers():
    """
    获取所有支持的AI提供商
    """
    providers = crud_ai_config.get_ai_providers()
    return ai_config_schemas.AIProvidersListResponse(providers=providers)


@router.post("/{config_id}/activate")
def activate_ai_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int
):
    """
    激活AI配置
    """
    ai_config = crud_ai_config.update_ai_config(
        db=db,
        config_id=config_id,
        config_update=ai_config_schemas.AIConfigUpdate(is_active=True)
    )
    if not ai_config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    return {"message": "AI配置已激活"}


@router.post("/{config_id}/deactivate")
def deactivate_ai_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int
):
    """
    停用AI配置
    """
    # 检查是否为默认配置
    ai_config = crud_ai_config.get_ai_config(db=db, config_id=config_id)
    if not ai_config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    if ai_config.is_default:
        raise HTTPException(status_code=400, detail="不能停用默认配置")
    
    ai_config = crud_ai_config.update_ai_config(
        db=db,
        config_id=config_id,
        config_update=ai_config_schemas.AIConfigUpdate(is_active=False)
    )
    
    return {"message": "AI配置已停用"}