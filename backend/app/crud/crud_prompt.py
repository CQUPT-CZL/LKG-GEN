# app/crud/crud_prompt.py

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.sqlite_models import Prompt, PromptTypeEnum
from app.schemas.prompt import PromptCreate, PromptUpdate


def create_prompt(db: Session, prompt: PromptCreate) -> Prompt:
    """
    创建新的Prompt
    
    :param db: SQLAlchemy 数据库会话
    :param prompt: Prompt创建数据
    :return: 创建的Prompt实例
    """
    # 如果设置为默认，先取消同类型的其他默认prompt
    if prompt.is_default:
        _unset_default_prompts(db, prompt.prompt_type)
    
    db_prompt = Prompt(
        name=prompt.name,
        prompt_type=prompt.prompt_type,
        content=prompt.content,
        description=prompt.description,
        is_default=1 if prompt.is_default else 0,
        is_active=1 if prompt.is_active else 0,
        version=prompt.version
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def get_prompt(db: Session, prompt_id: int) -> Optional[Prompt]:
    """
    根据ID获取Prompt
    
    :param db: SQLAlchemy 数据库会话
    :param prompt_id: Prompt ID
    :return: Prompt实例或None
    """
    return db.query(Prompt).filter(Prompt.id == prompt_id).first()


def get_prompts(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    prompt_type: Optional[PromptTypeEnum] = None,
    is_active: Optional[bool] = None
) -> List[Prompt]:
    """
    获取Prompt列表
    
    :param db: SQLAlchemy 数据库会话
    :param skip: 跳过的记录数
    :param limit: 返回的最大记录数
    :param prompt_type: 过滤的Prompt类型
    :param is_active: 过滤是否激活
    :return: Prompt列表
    """
    query = db.query(Prompt)
    
    if prompt_type is not None:
        query = query.filter(Prompt.prompt_type == prompt_type)
    
    if is_active is not None:
        query = query.filter(Prompt.is_active == (1 if is_active else 0))
    
    return query.offset(skip).limit(limit).all()


def get_prompts_count(
    db: Session,
    prompt_type: Optional[PromptTypeEnum] = None,
    is_active: Optional[bool] = None
) -> int:
    """
    获取Prompt总数
    
    :param db: SQLAlchemy 数据库会话
    :param prompt_type: 过滤的Prompt类型
    :param is_active: 过滤是否激活
    :return: Prompt总数
    """
    query = db.query(Prompt)
    
    if prompt_type is not None:
        query = query.filter(Prompt.prompt_type == prompt_type)
    
    if is_active is not None:
        query = query.filter(Prompt.is_active == (1 if is_active else 0))
    
    return query.count()


def get_default_prompt(db: Session, prompt_type: PromptTypeEnum) -> Optional[Prompt]:
    """
    获取指定类型的默认Prompt
    
    :param db: SQLAlchemy 数据库会话
    :param prompt_type: Prompt类型
    :return: 默认Prompt实例或None
    """
    return db.query(Prompt).filter(
        Prompt.prompt_type == prompt_type,
        Prompt.is_default == 1,
        Prompt.is_active == 1
    ).first()


def update_prompt(db: Session, prompt_id: int, prompt_update: PromptUpdate) -> Optional[Prompt]:
    """
    更新Prompt
    
    :param db: SQLAlchemy 数据库会话
    :param prompt_id: Prompt ID
    :param prompt_update: 更新数据
    :return: 更新后的Prompt实例或None
    """
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not db_prompt:
        return None
    
    # 如果要设置为默认，先取消同类型的其他默认prompt
    if prompt_update.is_default is True:
        _unset_default_prompts(db, db_prompt.prompt_type)
    
    # 更新字段
    update_data = prompt_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ['is_default', 'is_active']:
            # 转换布尔值为整数
            setattr(db_prompt, field, 1 if value else 0)
        else:
            setattr(db_prompt, field, value)
    
    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def delete_prompt(db: Session, prompt_id: int) -> bool:
    """
    删除Prompt
    
    :param db: SQLAlchemy 数据库会话
    :param prompt_id: Prompt ID
    :return: 是否删除成功
    """
    db_prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not db_prompt:
        return False
    
    db.delete(db_prompt)
    db.commit()
    return True


def set_default_prompt(db: Session, prompt_id: int, prompt_type: PromptTypeEnum) -> Optional[Prompt]:
    """
    设置默认Prompt
    
    :param db: SQLAlchemy 数据库会话
    :param prompt_id: 要设为默认的Prompt ID
    :param prompt_type: Prompt类型
    :return: 设置后的Prompt实例或None
    """
    # 检查prompt是否存在且类型匹配
    db_prompt = db.query(Prompt).filter(
        Prompt.id == prompt_id,
        Prompt.prompt_type == prompt_type
    ).first()
    
    if not db_prompt:
        return None
    
    # 取消同类型的其他默认prompt
    _unset_default_prompts(db, prompt_type)
    
    # 设置当前prompt为默认
    db_prompt.is_default = 1
    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def _unset_default_prompts(db: Session, prompt_type: PromptTypeEnum) -> None:
    """
    取消指定类型的所有默认Prompt设置
    
    :param db: SQLAlchemy 数据库会话
    :param prompt_type: Prompt类型
    """
    db.query(Prompt).filter(
        Prompt.prompt_type == prompt_type,
        Prompt.is_default == 1
    ).update({Prompt.is_default: 0})
    db.commit()


def get_prompt_types() -> List[dict]:
    """
    获取所有Prompt类型及其描述
    
    :return: Prompt类型列表
    """
    return [
        {
            "type": PromptTypeEnum.ner.value,
            "display_name": "命名实体识别",
            "description": "用于从文本中提取实体的prompt模板"
        },
        {
            "type": PromptTypeEnum.re.value,
            "display_name": "关系抽取",
            "description": "用于从文本中提取实体关系的prompt模板"
        },
        {
            "type": PromptTypeEnum.entity_validation.value,
            "display_name": "实体验证",
            "description": "用于验证提取实体准确性的prompt模板"
        },
        {
            "type": PromptTypeEnum.custom.value,
            "display_name": "自定义",
            "description": "用户自定义的prompt模板"
        }
    ]