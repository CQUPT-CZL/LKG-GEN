# app/models/sqlite_models.py

import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    func
)
from sqlalchemy.orm import relationship, declarative_base

# 创建一个所有模型类都会继承的基类
Base = declarative_base()


# 定义一个Python枚举类，用于文档状态
class DocumentStatusEnum(enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


# 定义一个Python枚举类，用于三元组审核状态
class TripleStatusEnum(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SourceDocument(Base):
    """
    源文档表模型
    存储上传的原始文件信息
    """
    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text, nullable=False)
    status = Column(Enum(DocumentStatusEnum), nullable=False, default=DocumentStatusEnum.pending)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # 定义与TextChunk的一对多关系
    # 当一个文档被删除时，所有关联的文本块也会被自动删除 (cascade)
    chunks = relationship("TextChunk", back_populates="document", cascade="all, delete-orphan")


class TextChunk(Base):
    """
    文本片段表模型
    存储被分割后的文本块，是知识溯源的最小单元
    """
    __tablename__ = "text_chunks"

    id = Column(Integer, primary_key=True, index=True)  # 这就是我们常说的 chunk_id
    document_id = Column(Integer, ForeignKey("source_documents.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # 用于保持文本块在原文中的顺序

    # 定义与SourceDocument的多对一关系
    document = relationship("SourceDocument", back_populates="chunks")


class PendingTriple(Base):
    """
    待审核三元组表模型
    存储由问答助手生成，等待管理员审核的知识
    """
    __tablename__ = "pending_triples"

    id = Column(Integer, primary_key=True, index=True)
    # 这里的graph_id暂时用Integer，对应Neo4j中KnowledgeGraph节点的唯一标识
    # 如果未来neo4j节点id用uuid，这里可以改为String
    graph_id = Column(Integer, nullable=False, index=True)
    subject = Column(Text, nullable=False)
    predicate = Column(Text, nullable=False)
    object = Column(Text, nullable=False)
    status = Column(Enum(TripleStatusEnum), nullable=False, default=TripleStatusEnum.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)