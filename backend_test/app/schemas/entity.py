# app/schemas/entity.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Entity Schemas ---
class EntityBase(BaseModel):
    name: str
    entity_type: str
    description: Optional[str] = None
    graph_id: str
    chunk_ids: Optional[List[str]] = []  # 记录实体来源的分块ID列表

class EntityCreate(EntityBase):
    document_id: Optional[int] = None  # 关联的文档ID

class Entity(EntityBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 文档-实体关系Schema
class DocumentEntityRelationBase(BaseModel):
    document_id: str  # 改为字符串类型以支持Neo4j UUID
    entity_id: str
    relation_type: str = "HAS_ENTITY"  # 默认关系类型

class DocumentEntityRelationCreate(DocumentEntityRelationBase):
    pass

class DocumentEntityRelation(DocumentEntityRelationBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Relation Schemas ---
class RelationBase(BaseModel):
    relation_type: str
    description: Optional[str] = None
    confidence: Optional[float] = 1.0

class RelationCreate(RelationBase):
    source_entity_id: str
    target_entity_id: str
    graph_id: str  # 关系必须属于某个图谱

class Relation(RelationBase):
    id: str
    source_entity_id: str
    target_entity_id: str
    graph_id: str
    
    class Config:
        from_attributes = True