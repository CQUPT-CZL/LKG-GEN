# app/crud/crud_sqlite.py

from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import sqlite_models
from app.schemas import resource as resource_schemas


def create_source_document(db: Session, filename: str, content: str, resource_type: str = None) -> sqlite_models.SourceDocument:
    """
    在数据库中创建一条新的源文档记录。
    
    :param db: SQLAlchemy 数据库会话
    :param filename: 文件名
    :param content: 文件内容
    :param resource_type: 资源类型枚举
    :return: 创建的SQLAlchemy模型实例
    """
    # 创建 SQLAlchemy model 实例
    db_document = sqlite_models.SourceDocument(
        filename=filename,
        content=content,
        resource_type=resource_type
    )
    db.add(db_document)  # 添加到会话
    db.commit()          # 提交事务到数据库
    db.refresh(db_document) # 刷新实例，以获取数据库生成的值（如ID）
    return db_document


def get_source_documents(db: Session, skip: int = 0, limit: int = 100) -> List[sqlite_models.SourceDocument]:
    """
    获取源文档列表
    
    :param db: SQLAlchemy 数据库会话
    :param skip: 跳过的记录数（用于分页）
    :param limit: 返回的最大记录数
    :return: 源文档列表
    """
    return db.query(sqlite_models.SourceDocument).offset(skip).limit(limit).all()


def get_source_document(db: Session, document_id: str) -> Optional[sqlite_models.SourceDocument]:
    """
    根据ID获取单个源文档
    
    :param db: SQLAlchemy 数据库会话
    :param document_id: 文档ID
    :return: 源文档对象或None
    """
    return db.query(sqlite_models.SourceDocument).filter(sqlite_models.SourceDocument.id == document_id).first()


def get_source_documents_by_ids(db: Session, document_ids: List[int]) -> List[sqlite_models.SourceDocument]:
    """
    根据一组ID批量获取源文档列表
    """
    if not document_ids:
        return []
    return db.query(sqlite_models.SourceDocument).filter(sqlite_models.SourceDocument.id.in_(document_ids)).all()


def delete_source_document(db: Session, document_id: int) -> bool:
    """
    删除源文档
    
    :param db: SQLAlchemy 数据库会话
    :param document_id: 文档ID
    :return: 是否删除成功
    """
    document = db.query(sqlite_models.SourceDocument).filter(sqlite_models.SourceDocument.id == document_id).first()
    if document:
        db.delete(document)
        db.commit()
        return True
    return False


def update_document_status(db: Session, document_id: int, status: sqlite_models.DocumentStatusEnum) -> Optional[sqlite_models.SourceDocument]:
    """
    更新文档状态
    
    :param db: SQLAlchemy 数据库会话
    :param document_id: 文档ID
    :param status: 新的状态
    :return: 更新后的文档对象或None
    """
    document = db.query(sqlite_models.SourceDocument).filter(sqlite_models.SourceDocument.id == document_id).first()
    if document:
        document.status = status
        db.commit()
        db.refresh(document)
        return document
    return None


def create_text_chunk(db: Session, document_id: int, chunk_text: str, chunk_index: int) -> sqlite_models.TextChunk:
    """
    在数据库中创建一条新的文本分块记录。
    
    :param db: SQLAlchemy 数据库会话
    :param document_id: 关联的文档ID
    :param chunk_text: 分块文本内容
    :param chunk_index: 分块在文档中的索引位置
    :return: 创建的SQLAlchemy模型实例
    """
    # 创建 SQLAlchemy model 实例
    db_chunk = sqlite_models.TextChunk(
        document_id=document_id,
        chunk_text=chunk_text,
        chunk_index=chunk_index
    )
    db.add(db_chunk)  # 添加到会话
    db.commit()       # 提交事务到数据库
    db.refresh(db_chunk) # 刷新实例，以获取数据库生成的值（如ID）
    return db_chunk


def get_text_chunks_by_document(db: Session, document_id: int) -> List[sqlite_models.TextChunk]:
    """
    根据文档ID获取所有相关的文本分块
    
    :param db: SQLAlchemy 数据库会话
    :param document_id: 文档ID
    :return: 文本分块列表
    """
    return db.query(sqlite_models.TextChunk).filter(sqlite_models.TextChunk.document_id == document_id).order_by(sqlite_models.TextChunk.chunk_index).all()
