# app/services/document_service.py

from sqlalchemy.orm import Session
from neo4j import Driver
from fastapi import HTTPException
from fastapi import UploadFile
from app.crud import crud_sqlite
from app.schemas.resource import BatchResourceCreate, BatchResourceResponse
from app.models.sqlite_models import SourceDocument
from fastapi import BackgroundTasks
from app.schemas.resource import ResourceCreate
from app.worker.tasks import run_batch_knowledge_extraction
from typing import List

async def create_upload_document(db: Session, file: UploadFile) -> SourceDocument:
    """
    处理文件上传，并创建文档记录的业务逻辑。
    
    :param db: 数据库会话
    :param file: FastAPI的UploadFile对象
    :return: 创建的SourceDocument对象
    """
    # 异步读取文件内容
    content_bytes = await file.read()
    content_str = content_bytes.decode("utf-8")
    
    # 准备Pydantic模型 - 使用ResourceCreate统一概念
    from app.models.sqlite_models import ResourceTypeEnum as ModelResourceTypeEnum
    resource_in = ResourceCreate(
        filename=file.filename, 
        content=content_str,
        parent_id="",  # 单个上传时可以为空
        graph_id="",   # 单个上传时可以为空
        type="论文"  # 默认为论文类型
    )
    
    # 调用CRUD层函数，将文档信息写入数据库
    document = crud_sqlite.create_source_document(
        db=db, 
        filename=resource_in.filename,
        content=resource_in.content,
        resource_type=ModelResourceTypeEnum.paper
    )
    
    # !!! 核心异步处理触发点 !!!
    # 在这里，我们将把文档ID发送给后台任务队列（Celery或ARQ）
    # background_tasks.add_task(process_document_task, document.id)
    print(f"文档 {document.id} 已保存，准备交由后台任务处理...") # 暂时用打印代替
    
    return document


def create_batch_resources(
    driver: Driver,
    db: Session,
    batch_request: BatchResourceCreate,
    background_tasks: BackgroundTasks
) -> BatchResourceResponse:
    """
    批量创建资源的完整业务流程：
    1. 验证父节点存在且合法
    2. 在SQLite中批量存储资源原文
    3. 收集成功和失败的结果
    4. 触发批量后台知识抽取任务（Neo4j资源节点将在此任务中创建）
    """
    # 父节点验证将在知识抽取任务中进行
    
    created_resources = []
    failed_resources = []
    document_ids = []  # 用于批量知识抽取
    
    # 批量处理每个资源
    for resource_item in batch_request.resources:
        try:
            # 创建完整的ResourceCreate对象
            resource = ResourceCreate(
                filename=resource_item.filename,
                parent_id=batch_request.parent_id,
                graph_id=batch_request.graph_id,
                type=resource_item.type,
                content=resource_item.content
            )
            
            # 在SQLite中存储资源原文
            source_document = crud_sqlite.create_source_document(
                db=db, 
                filename=resource.filename,
                content=resource.content,
                resource_type=resource.type
            )
            
            # 添加到成功列表 - 直接使用source_document对象
            created_resources.append(source_document)
            
            document_ids.append(source_document.id)
            
        except Exception as e:
             # 添加到失败列表
             failed_resources.append({
                 "filename": resource_item.filename,
                 "error": str(e)
             })
    
    # 如果有成功创建的资源，触发批量知识抽取任务
    if document_ids:
        background_tasks.add_task(
            run_batch_knowledge_extraction, 
            document_ids=document_ids, 
            graph_id=batch_request.graph_id,
            parent_id=batch_request.parent_id
        )
    
    return BatchResourceResponse(
        success_count=len(created_resources),
        failed_count=len(failed_resources),
        total_count=len(batch_request.resources),
        created_resources=created_resources,
        failed_resources=failed_resources
    )
