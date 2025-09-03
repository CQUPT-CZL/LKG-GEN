# app/schemas/ai_config.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.sqlite_models import AIProviderEnum


# --- AI配置 Base Schemas ---
class AIConfigBase(BaseModel):
    name: str = Field(..., description="配置名称")
    provider: AIProviderEnum = Field(..., description="AI提供商")
    model_name: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    temperature: str = Field(default="0.7", description="温度参数")
    max_tokens: str = Field(default="4000", description="最大token数")
    description: Optional[str] = Field(None, description="配置描述")


class AIConfigCreate(AIConfigBase):
    """创建AI配置的请求模型"""
    is_default: bool = Field(default=False, description="是否设为默认配置")
    is_active: bool = Field(default=True, description="是否激活")


class AIConfigUpdate(BaseModel):
    """更新AI配置的请求模型"""
    name: Optional[str] = Field(None, description="配置名称")
    model_name: Optional[str] = Field(None, description="模型名称")
    api_key: Optional[str] = Field(None, description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    temperature: Optional[str] = Field(None, description="温度参数")
    max_tokens: Optional[str] = Field(None, description="最大token数")
    description: Optional[str] = Field(None, description="配置描述")
    is_default: Optional[bool] = Field(None, description="是否设为默认配置")
    is_active: Optional[bool] = Field(None, description="是否激活")


class AIConfigResponse(AIConfigBase):
    """AI配置响应模型"""
    id: int
    is_default: bool = Field(..., description="是否为默认配置")
    is_active: bool = Field(..., description="是否激活")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIConfigListResponse(BaseModel):
    """AI配置列表响应模型"""
    configs: List[AIConfigResponse]
    total: int
    page: int
    page_size: int


class SetDefaultAIConfigRequest(BaseModel):
    """设置默认AI配置的请求模型"""
    config_id: int = Field(..., description="要设为默认的配置ID")


class AIProviderResponse(BaseModel):
    """AI提供商响应模型"""
    provider: str
    display_name: str
    description: str


class AIProvidersListResponse(BaseModel):
    """AI提供商列表响应模型"""
    providers: List[AIProviderResponse]