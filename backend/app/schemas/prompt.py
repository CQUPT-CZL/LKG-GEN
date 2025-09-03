# app/schemas/prompt.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.sqlite_models import PromptTypeEnum


# --- Prompt Base Schemas ---
class PromptBase(BaseModel):
    name: str = Field(..., description="Prompt名称")
    prompt_type: PromptTypeEnum = Field(..., description="Prompt类型")
    content: str = Field(..., description="Prompt内容")
    description: Optional[str] = Field(None, description="Prompt描述")
    version: str = Field(default="1.0", description="版本号")


class PromptCreate(PromptBase):
    """创建Prompt的请求模型"""
    is_default: bool = Field(default=False, description="是否设为默认prompt")
    is_active: bool = Field(default=True, description="是否激活")


class PromptUpdate(BaseModel):
    """更新Prompt的请求模型"""
    name: Optional[str] = Field(None, description="Prompt名称")
    content: Optional[str] = Field(None, description="Prompt内容")
    description: Optional[str] = Field(None, description="Prompt描述")
    version: Optional[str] = Field(None, description="版本号")
    is_default: Optional[bool] = Field(None, description="是否设为默认prompt")
    is_active: Optional[bool] = Field(None, description="是否激活")


class PromptResponse(PromptBase):
    """Prompt响应模型"""
    id: int
    is_default: bool = Field(..., description="是否为默认prompt")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptListResponse(BaseModel):
    """Prompt列表响应模型"""
    prompts: List[PromptResponse]
    total: int
    page: int
    page_size: int


class SetDefaultPromptRequest(BaseModel):
    """设置默认Prompt的请求模型"""
    prompt_id: int = Field(..., description="要设为默认的Prompt ID")
    prompt_type: PromptTypeEnum = Field(..., description="Prompt类型")


class PromptTypeResponse(BaseModel):
    """Prompt类型响应模型"""
    type: str
    display_name: str
    description: str


class PromptTypesListResponse(BaseModel):
    """Prompt类型列表响应模型"""
    types: List[PromptTypeResponse]