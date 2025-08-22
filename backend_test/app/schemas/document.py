# app/schemas/document.py

from pydantic import BaseModel
from datetime import datetime
from typing import List
import enum
from typing import Optional

from app.models.sqlite_models import DocumentStatusEnum

# --- Base Schema ---
# 包含所有模型共有的字段
class DocumentBase(BaseModel):
    filename: str

# --- Create Schema ---
# 在创建文档时，API需要接收的字段
class DocumentCreate(DocumentBase):
    content: str  # 上传时需要原始内容

# --- Response Schema ---
# 从API返回文档信息时使用的模型
# 这是为了保护数据，不会意外泄露不必要的字段
class Document(DocumentBase):
    id: int
    status: DocumentStatusEnum
    uploaded_at: datetime

    class Config:
        # 这个配置告诉Pydantic模型可以从ORM对象中读取数据
        # (例如，从SQLAlchemy的模型实例中)
        from_attributes = True



# 新增：定义一个资源类型的枚举
class ResourceTypeEnum(str, enum.Enum):
    paper = "论文"
    book = "书籍"
    webpage = "网页"
    report = "报告"

# --- 新增 Resource Schemas ---

class ResourceCreate(BaseModel):
    title: str
    parent_id: str  # 父节点ID (必须是 KnowledgeGraph 或 Category 的 ID)
    graph_id: str   # 资源所属的顶级图谱ID
    type: ResourceTypeEnum # 必须是枚举中定义的一种
    content: str    # 资源的原文内容

class Resource(BaseModel):
    id: str         # Neo4j中节点的UUID
    title: str
    type: str
    parent_id: str
    graph_id: str
    source_document_id: int # 关联到SQLite中的ID

    class Config:
        from_attributes = True