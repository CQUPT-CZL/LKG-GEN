# app/schemas/graph.py (新建这个文件)

from pydantic import BaseModel
from typing import Optional

# --- KnowledgeGraph Schemas ---
class GraphBase(BaseModel):
    description: Optional[str] = None
    name: str
    
class GraphCreate(GraphBase):
    pass

class Graph(GraphBase):
    id: str  # 在Neo4j中我们用UUID作为唯一标识符
    entity_count: Optional[int] = 0  # 实体数量
    relation_count: Optional[int] = 0  # 关系数量
    
    class Config:
        from_attributes = True

# --- Entity and Relationship Schemas for Subgraph ---
class Entity(BaseModel):
    id: str
    name: str
    entity_type: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[dict] = None
    
    class Config:
        from_attributes = True

class Relationship(BaseModel):
    id: str
    type: str
    start_node_id: str
    end_node_id: str
    properties: Optional[dict] = None
    
    class Config:
        from_attributes = True

class Subgraph(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]
    
    class Config:
        from_attributes = True

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    parent_id: str # 创建分类时，必须指定其父节点（图谱或另一个分类）的ID

class Category(CategoryBase):
    id: str
    parent_id: str
    graph_id: str

    class Config:
        from_attributes = True