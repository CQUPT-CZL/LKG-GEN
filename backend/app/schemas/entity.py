# app/schemas/entity.py

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

# --- Entity Schemas ---
class EntityBase(BaseModel):
    name: str
    entity_type: str
    description: Optional[str] = None
    graph_id: str
    chunk_ids: Optional[List[str]] = []  # 记录实体来源的分块ID列表
    frequency: Optional[int] = 1  # 实体出现次数


class EntityCreate(EntityBase):
    document_ids: Optional[List[int]] = None  # 关联的文档ID

class EntityUpdate(BaseModel):
    name: Optional[str] = None
    entity_type: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[int] = None
    chunk_ids: Optional[List[str]] = None

class Entity(EntityBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# 实体合并Schema
class EntityMergeRequest(BaseModel):
    source_entity_id: str  # 源实体ID（将被合并到目标实体）
    target_entity_id: str  # 目标实体ID（保留的实体）
    merged_name: Optional[str] = None  # 合并后的名称，如果不提供则使用目标实体名称
    merged_description: Optional[str] = None  # 合并后的描述，如果不提供则合并两个描述

class EntityMergeResponse(BaseModel):
    success: bool
    message: str
    merged_entity: Optional[Entity] = None

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

class RelationUpdate(BaseModel):
    relation_type: Optional[str] = None
    description: Optional[str] = None
    confidence: Optional[float] = None

class Relation(RelationBase):
    id: str
    source_entity_id: str
    target_entity_id: str
    graph_id: str
    
    class Config:
        from_attributes = True

# 子图查询相关Schema
class SubgraphEntity(BaseModel):
    """子图中的实体信息"""
    id: str
    name: str
    entity_type: str
    description: Optional[str] = None
    frequency: Optional[int] = 0

class SubgraphRelationship(BaseModel):
    """子图中的关系信息"""
    id: int
    type: str
    source_id: str
    target_id: str
    properties: Optional[Dict] = {}

class EntitySubgraphResponse(BaseModel):
    """实体子图查询响应"""
    center_entity: SubgraphEntity
    entities: List[SubgraphEntity]
    relationships: List[SubgraphRelationship]
    hops: int
    total_entities: int
    total_relationships: int