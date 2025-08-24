# app/schemas/relation.py

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# --- Relation Schemas ---
class RelationBase(BaseModel):
    relation_type: str  # 关系类型
    description: Optional[str] = None
    confidence: Optional[float] = 1.0

class RelationCreate(RelationBase):
    source_entity_id: str
    target_entity_id: str
    graph_id: str

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