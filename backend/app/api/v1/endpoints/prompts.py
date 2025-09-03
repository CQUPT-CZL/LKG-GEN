# app/api/v1/endpoints/prompts.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api import deps
from app.schemas import prompt as prompt_schemas
from app.crud import crud_prompt
from app.models.sqlite_models import PromptTypeEnum

router = APIRouter()


@router.post("/", response_model=prompt_schemas.PromptResponse)
def create_prompt(
    *,
    db: Session = Depends(deps.get_db),
    prompt: prompt_schemas.PromptCreate
):
    """
    创建新的Prompt
    """
    try:
        db_prompt = crud_prompt.create_prompt(db=db, prompt=prompt)
        return db_prompt
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建Prompt失败: {e}")


@router.get("/", response_model=prompt_schemas.PromptListResponse)
def get_prompts(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    prompt_type: Optional[PromptTypeEnum] = Query(None, description="过滤的Prompt类型"),
    is_active: Optional[bool] = Query(None, description="过滤是否激活")
):
    """
    获取Prompt列表
    """
    try:
        prompts = crud_prompt.get_prompts(
            db=db, 
            skip=skip, 
            limit=limit, 
            prompt_type=prompt_type, 
            is_active=is_active
        )
        total = crud_prompt.get_prompts_count(
            db=db, 
            prompt_type=prompt_type, 
            is_active=is_active
        )
        
        return prompt_schemas.PromptListResponse(
            prompts=prompts,
            total=total,
            page=skip // limit + 1,
            page_size=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Prompt列表失败: {e}")


@router.get("/{prompt_id}", response_model=prompt_schemas.PromptResponse)
def get_prompt(
    *,
    db: Session = Depends(deps.get_db),
    prompt_id: int
):
    """
    根据ID获取Prompt详情
    """
    prompt = crud_prompt.get_prompt(db=db, prompt_id=prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt不存在")
    return prompt


@router.put("/{prompt_id}", response_model=prompt_schemas.PromptResponse)
def update_prompt(
    *,
    db: Session = Depends(deps.get_db),
    prompt_id: int,
    prompt_update: prompt_schemas.PromptUpdate
):
    """
    更新Prompt
    """
    try:
        updated_prompt = crud_prompt.update_prompt(
            db=db, 
            prompt_id=prompt_id, 
            prompt_update=prompt_update
        )
        if not updated_prompt:
            raise HTTPException(status_code=404, detail="Prompt不存在")
        return updated_prompt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新Prompt失败: {e}")


@router.delete("/{prompt_id}")
def delete_prompt(
    *,
    db: Session = Depends(deps.get_db),
    prompt_id: int
):
    """
    删除Prompt
    """
    try:
        success = crud_prompt.delete_prompt(db=db, prompt_id=prompt_id)
        if not success:
            raise HTTPException(status_code=404, detail="Prompt不存在")
        return {"message": "Prompt删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除Prompt失败: {e}")


@router.get("/default/{prompt_type}", response_model=prompt_schemas.PromptResponse)
def get_default_prompt(
    *,
    db: Session = Depends(deps.get_db),
    prompt_type: PromptTypeEnum
):
    """
    获取指定类型的默认Prompt
    """
    prompt = crud_prompt.get_default_prompt(db=db, prompt_type=prompt_type)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"未找到类型为 {prompt_type.value} 的默认Prompt")
    return prompt


@router.post("/set-default", response_model=prompt_schemas.PromptResponse)
def set_default_prompt(
    *,
    db: Session = Depends(deps.get_db),
    request: prompt_schemas.SetDefaultPromptRequest
):
    """
    设置默认Prompt
    """
    try:
        prompt = crud_prompt.set_default_prompt(
            db=db, 
            prompt_id=request.prompt_id, 
            prompt_type=request.prompt_type
        )
        if not prompt:
            raise HTTPException(
                status_code=404, 
                detail="Prompt不存在或类型不匹配"
            )
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置默认Prompt失败: {e}")


@router.get("/types/list", response_model=prompt_schemas.PromptTypesListResponse)
def get_prompt_types():
    """
    获取所有Prompt类型
    """
    try:
        types = crud_prompt.get_prompt_types()
        return prompt_schemas.PromptTypesListResponse(types=types)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Prompt类型失败: {e}")


@router.get("/by-type/{prompt_type}", response_model=List[prompt_schemas.PromptResponse])
def get_prompts_by_type(
    *,
    db: Session = Depends(deps.get_db),
    prompt_type: PromptTypeEnum,
    is_active: Optional[bool] = Query(True, description="是否只返回激活的Prompt")
):
    """
    根据类型获取Prompt列表
    """
    try:
        prompts = crud_prompt.get_prompts(
            db=db, 
            prompt_type=prompt_type, 
            is_active=is_active,
            limit=1000  # 获取所有该类型的prompt
        )
        return prompts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Prompt列表失败: {e}")