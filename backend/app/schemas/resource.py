# app/schemas/resource.py

from pydantic import BaseModel
from datetime import datetime
from typing import List
import enum
from typing import Optional

from app.models.sqlite_models import DocumentStatusEnum

# --- 新增 Resource Schemas ---

class ResourceCreate(BaseModel):
    filename: str
    parent_id: str  # 父节点ID (必须是 KnowledgeGraph 或 Category 的 ID)
    graph_id: str   # 资源所属的顶级图谱ID
    type: str # 资源类型字符串
    content: str    # 资源的原文内容

# SQLite数据库中的资源响应模型
class SourceResource(BaseModel):
    id: int
    filename: str
    status: DocumentStatusEnum
    uploaded_at: datetime
    resource_type: str  # 资源类型的字符串值
    content: Optional[str] = None  # 文档内容

    class Config:
        from_attributes = True

# Neo4j图数据库中的资源节点模型
class Resource(BaseModel):
    id: str         # Neo4j中节点的UUID
    filename: str
    type: str
    parent_id: str
    graph_id: str
    source_document_id: int # 关联到SQLite中的ID

    class Config:
        from_attributes = True

# --- 批量资源创建 Schemas ---

class ResourceItem(BaseModel):
    filename: str
    content: str    # 资源的原文内容
    type: str # 资源类型字符串

class BatchResourceCreate(BaseModel):
    parent_id: str  # 父节点ID (必须是 KnowledgeGraph 或 Category 的 ID)
    graph_id: str   # 资源所属的顶级图谱ID
    resources: List[ResourceItem]  # 批量资源列表

class BatchResourceResponse(BaseModel):
    success_count: int
    failed_count: int
    total_count: int
    created_resources: List[SourceResource]  # SQLite中创建的资源
    failed_resources: List[dict]  # 包含失败原因的资源信息