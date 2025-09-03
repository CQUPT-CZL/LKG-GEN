# app/services/prompt_service.py

from typing import Optional
from sqlalchemy.orm import Session
from app.crud import crud_prompt
from app.models.sqlite_models import PromptTypeEnum
from app.db.sqlite_session import SessionLocal


def get_prompt_content(prompt_type: PromptTypeEnum, db: Session = None) -> Optional[str]:
    """
    从数据库获取指定类型的默认prompt内容
    
    Args:
        prompt_type: prompt类型
        db: 数据库会话，如果不提供则创建新会话
    
    Returns:
        prompt内容，如果未找到则返回None
    """
    # 如果没有提供数据库会话，创建新的会话
    if db is None:
        db = SessionLocal()
        try:
            return _get_prompt_content_internal(prompt_type, db)
        finally:
            db.close()
    else:
        return _get_prompt_content_internal(prompt_type, db)


def _get_prompt_content_internal(prompt_type: PromptTypeEnum, db: Session) -> Optional[str]:
    """
    内部函数：从数据库获取prompt内容
    
    Args:
        prompt_type: prompt类型
        db: 数据库会话
    
    Returns:
        prompt内容，如果未找到则返回None
    """
    try:
        # 获取默认的prompt
        prompt = crud_prompt.get_default_prompt(db=db, prompt_type=prompt_type)
        if prompt and prompt.is_active:
            return prompt.content
        
        # 如果没有默认的，获取该类型的第一个激活的prompt
        prompts = crud_prompt.get_prompts(
            db=db, 
            prompt_type=prompt_type, 
            is_active=True, 
            limit=1
        )
        if prompts:
            return prompts[0].content
        
        return None
    except Exception as e:
        print(f"❌ 从数据库获取prompt失败: {e}")
        return None


def get_ner_prompt_content(db: Session = None) -> Optional[str]:
    """
    获取NER prompt内容
    
    Args:
        db: 数据库会话
    
    Returns:
        NER prompt内容
    """
    return get_prompt_content(PromptTypeEnum.ner, db)


def get_re_prompt_content(db: Session = None) -> Optional[str]:
    """
    获取关系抽取prompt内容
    
    Args:
        db: 数据库会话
    
    Returns:
        关系抽取prompt内容
    """
    return get_prompt_content(PromptTypeEnum.re, db)


def get_entity_validation_prompt_content(db: Session = None) -> Optional[str]:
    """
    获取实体验证prompt内容
    
    Args:
        db: 数据库会话
    
    Returns:
        实体验证prompt内容
    """
    return get_prompt_content(PromptTypeEnum.entity_validation, db)


def get_custom_prompt_content(db: Session = None) -> Optional[str]:
    """
    获取自定义prompt内容
    
    Args:
        db: 数据库会话
    
    Returns:
        自定义prompt内容
    """
    return get_prompt_content(PromptTypeEnum.custom, db)