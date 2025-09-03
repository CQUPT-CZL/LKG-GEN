# app/crud/crud_ai_config.py

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.sqlite_models import AIConfig, AIProviderEnum
from app.schemas import ai_config as ai_config_schemas


def create_ai_config(db: Session, config: ai_config_schemas.AIConfigCreate) -> AIConfig:
    """
    创建新的AI配置
    
    :param db: SQLAlchemy 数据库会话
    :param config: AI配置创建数据
    :return: 创建的AI配置实例
    """
    # 如果设置为默认配置，先取消其他默认配置
    if config.is_default:
        db.query(AIConfig).filter(AIConfig.is_default == 1).update({"is_default": 0})
    
    db_config = AIConfig(
        name=config.name,
        provider=config.provider,
        model_name=config.model_name,
        api_key=config.api_key,
        base_url=config.base_url,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        description=config.description,
        is_default=1 if config.is_default else 0,
        is_active=1 if config.is_active else 0
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def get_ai_configs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    provider: Optional[AIProviderEnum] = None,
    is_active: Optional[bool] = None
) -> List[AIConfig]:
    """
    获取AI配置列表
    
    :param db: SQLAlchemy 数据库会话
    :param skip: 跳过的记录数
    :param limit: 返回的最大记录数
    :param provider: 过滤的提供商类型
    :param is_active: 过滤是否激活
    :return: AI配置列表
    """
    query = db.query(AIConfig)
    
    if provider is not None:
        query = query.filter(AIConfig.provider == provider)
    
    if is_active is not None:
        query = query.filter(AIConfig.is_active == (1 if is_active else 0))
    
    return query.offset(skip).limit(limit).all()


def get_ai_configs_count(
    db: Session,
    provider: Optional[AIProviderEnum] = None,
    is_active: Optional[bool] = None
) -> int:
    """
    获取AI配置总数
    
    :param db: SQLAlchemy 数据库会话
    :param provider: 过滤的提供商类型
    :param is_active: 过滤是否激活
    :return: AI配置总数
    """
    query = db.query(AIConfig)
    
    if provider is not None:
        query = query.filter(AIConfig.provider == provider)
    
    if is_active is not None:
        query = query.filter(AIConfig.is_active == (1 if is_active else 0))
    
    return query.count()


def get_ai_config(db: Session, config_id: int) -> Optional[AIConfig]:
    """
    根据ID获取AI配置
    
    :param db: SQLAlchemy 数据库会话
    :param config_id: AI配置ID
    :return: AI配置实例或None
    """
    return db.query(AIConfig).filter(AIConfig.id == config_id).first()


def update_ai_config(
    db: Session, 
    config_id: int, 
    config_update: ai_config_schemas.AIConfigUpdate
) -> Optional[AIConfig]:
    """
    更新AI配置
    
    :param db: SQLAlchemy 数据库会话
    :param config_id: AI配置ID
    :param config_update: 更新数据
    :return: 更新后的AI配置实例或None
    """
    db_config = get_ai_config(db, config_id)
    if not db_config:
        return None
    
    # 如果设置为默认配置，先取消其他默认配置
    if config_update.is_default is True:
        db.query(AIConfig).filter(
            AIConfig.is_default == 1,
            AIConfig.id != config_id
        ).update({"is_default": 0})
    
    # 更新字段
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ["is_default", "is_active"]:
            # 布尔值转换为整数
            setattr(db_config, field, 1 if value else 0)
        else:
            setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config


def delete_ai_config(db: Session, config_id: int) -> bool:
    """
    删除AI配置
    
    :param db: SQLAlchemy 数据库会话
    :param config_id: AI配置ID
    :return: 是否删除成功
    """
    db_config = get_ai_config(db, config_id)
    if not db_config:
        return False
    
    db.delete(db_config)
    db.commit()
    return True


def get_default_ai_config(db: Session) -> Optional[AIConfig]:
    """
    获取默认AI配置
    
    :param db: SQLAlchemy 数据库会话
    :return: 默认AI配置实例或None
    """
    return db.query(AIConfig).filter(
        AIConfig.is_default == 1,
        AIConfig.is_active == 1
    ).first()


def set_default_ai_config(db: Session, config_id: int) -> Optional[AIConfig]:
    """
    设置默认AI配置
    
    :param db: SQLAlchemy 数据库会话
    :param config_id: 要设为默认的AI配置ID
    :return: 设置后的AI配置实例或None
    """
    # 检查配置是否存在且激活
    db_config = db.query(AIConfig).filter(
        AIConfig.id == config_id,
        AIConfig.is_active == 1
    ).first()
    
    if not db_config:
        return None
    
    # 取消所有其他默认配置
    db.query(AIConfig).filter(AIConfig.is_default == 1).update({"is_default": 0})
    
    # 设置新的默认配置
    db_config.is_default = 1
    db.commit()
    db.refresh(db_config)
    return db_config


def get_ai_providers() -> List[dict]:
    """
    获取所有AI提供商及其描述
    
    :return: AI提供商列表
    """
    return [
        {
            "provider": AIProviderEnum.openai.value,
            "display_name": "OpenAI",
            "description": "OpenAI GPT系列模型"
        },
        {
            "provider": AIProviderEnum.anthropic.value,
            "display_name": "Anthropic Claude",
            "description": "Anthropic Claude系列模型"
        },
        {
            "provider": AIProviderEnum.azure.value,
            "display_name": "Azure OpenAI",
            "description": "微软Azure OpenAI服务"
        },
        {
            "provider": AIProviderEnum.google.value,
            "display_name": "Google Gemini",
            "description": "Google Gemini系列模型"
        },
        {
            "provider": AIProviderEnum.ollama.value,
            "display_name": "Ollama",
            "description": "本地部署的开源模型"
        },
        {
            "provider": AIProviderEnum.custom.value,
            "display_name": "自定义",
            "description": "用户自定义的AI服务"
        }
    ]