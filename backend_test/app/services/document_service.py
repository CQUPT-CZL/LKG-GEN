# app/services/document_service.py

from sqlalchemy.orm import Session
from neo4j import Driver
from fastapi import HTTPException
from app.crud import crud_graph
from fastapi import UploadFile
from app.crud import crud_sqlite
from app.schemas.document import DocumentCreate
from app.models.sqlite_models import SourceDocument

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
    
    # 准备Pydantic模型
    doc_in = DocumentCreate(filename=file.filename, content=content_str)
    
    # 调用CRUD层函数，将文档信息写入数据库
    document = crud_sqlite.create_source_document(db=db, doc=doc_in)
    
    # !!! 核心异步处理触发点 !!!
    # 在这里，我们将把文档ID发送给后台任务队列（Celery或ARQ）
    # background_tasks.add_task(process_document_task, document.id)
    print(f"文档 {document.id} 已保存，准备交由后台任务处理...") # 暂时用打印代替
    
    return document



from fastapi import BackgroundTasks
from app.schemas.document import ResourceCreate

def create_new_resource(
    driver: Driver,
    db: Session,
    resource: ResourceCreate,
    background_tasks: BackgroundTasks
) -> dict:
    """
    创建新资源的完整业务流程：
    1. 验证父节点存在且合法
    2. 在SQLite中存储原文
    3. 在Neo4j中创建元数据节点
    4. 触发后台知识抽取任务
    """
    # 验证1：父节点必须存在
    parent_node = crud_graph.get_node_by_id(driver=driver, node_id=resource.parent_id)
    if not parent_node:
        raise HTTPException(status_code=404, detail=f"父节点 ID '{resource.parent_id}' 不存在")

    # 验证2：父节点必须属于当前操作的图谱
    if parent_node.get("graph_id") != resource.graph_id:
        raise HTTPException(status_code=400, detail="不能跨图谱创建资源")

    # 步骤1：在SQLite中存储资源原文
    source_document = crud_sqlite.create_source_document(
        db=db, title=resource.title, content=resource.content
    )

    # 步骤2：在Neo4j中创建资源的元数据节点，并关联SQLite的ID
    resource_node = crud_graph.create_resource_node(
        driver=driver, resource=resource, sqlite_doc_id=source_document.id
    )

    # 步骤3：触发后台知识抽取任务
    # background_tasks.add_task(run_knowledge_extraction, document_id=source_document.id)

    return resource_node
