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


# 定义一个Python枚举类，用于Prompt类型
class PromptTypeEnum(enum.Enum):
    ner = "ner"  # 命名实体识别
    re = "re"    # 关系抽取
    entity_validation = "entity_validation"  # 实体验证
    custom = "custom"  # 自定义类型


# 定义一个Python枚举类，用于AI提供商类型
class AIProviderEnum(enum.Enum):
    openai = "openai"  # OpenAI
    anthropic = "anthropic"  # Anthropic Claude
    azure = "azure"  # Azure OpenAI
    google = "google"  # Google Gemini
    ollama = "ollama"  # Ollama本地模型
    custom = "custom"  # 自定义提供商


class SourceDocument(Base):
    """
    源文档表模型
    存储上传的原始文件信息
    """
    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text, nullable=False)
    resource_type = Column(String, nullable=False, default="论文")
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


class Prompt(Base):
    """
    Prompt模板表模型
    存储各种类型的prompt模板，支持版本管理和默认设置
    """
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # prompt名称
    prompt_type = Column(Enum(PromptTypeEnum), nullable=False, index=True)  # prompt类型
    content = Column(Text, nullable=False)  # prompt内容
    description = Column(Text, nullable=True)  # prompt描述
    is_default = Column(Integer, nullable=False, default=0)  # 是否为默认prompt (0=否, 1=是)
    is_active = Column(Integer, nullable=False, default=1)  # 是否激活 (0=否, 1=是)
    version = Column(String, nullable=False, default="1.0")  # 版本号
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 添加唯一约束：每种类型只能有一个默认prompt
    # 这个约束需要在数据库层面通过migration或手动创建


class AIConfig(Base):
    """
    AI配置表模型
    存储各种AI提供商的配置信息，支持多个配置和默认设置
    """
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # 配置名称
    provider = Column(Enum(AIProviderEnum), nullable=False, index=True)  # AI提供商
    model_name = Column(String, nullable=False)  # 模型名称
    api_key = Column(String, nullable=False)  # API密钥
    base_url = Column(String, nullable=True)  # API基础URL（可选）
    temperature = Column(String, nullable=False, default="0.7")  # 温度参数
    max_tokens = Column(String, nullable=False, default="4000")  # 最大token数
    description = Column(Text, nullable=True)  # 配置描述
    is_default = Column(Integer, nullable=False, default=0)  # 是否为默认配置 (0=否, 1=是)
    is_active = Column(Integer, nullable=False, default=1)  # 是否激活 (0=否, 1=是)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 添加唯一约束：只能有一个默认配置
    # 这个约束需要在数据库层面通过migration或手动创建