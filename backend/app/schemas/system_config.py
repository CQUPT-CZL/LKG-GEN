# app/schemas/system_config.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class SystemConfigBase(BaseModel):
    config_key: str = Field(..., description="配置键名")
    config_value: str = Field(..., description="配置值（JSON格式）")
    description: Optional[str] = Field(None, description="配置描述")

class SystemConfigCreate(SystemConfigBase):
    """创建系统配置的请求模型"""
    pass

class SystemConfigUpdate(BaseModel):
    """更新系统配置的请求模型"""
    config_value: Optional[str] = Field(None, description="配置值（JSON格式）")
    description: Optional[str] = Field(None, description="配置描述")

class SystemConfigResponse(SystemConfigBase):
    """系统配置响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 分块策略配置模型
class ChunkStrategyConfig(BaseModel):
    """分块策略配置"""
    strategy: str = Field(..., description="分块策略: full_document, paragraph, sentence")
    description: str = Field(..., description="策略描述")

class ChunkStrategyConfigRequest(BaseModel):
    """分块策略配置请求"""
    strategy: str = Field(..., description="分块策略: full_document, paragraph, sentence")

class ChunkStrategyConfigResponse(BaseModel):
    """分块策略配置响应"""
    strategy: str
    description: str
    available_strategies: Dict[str, str]