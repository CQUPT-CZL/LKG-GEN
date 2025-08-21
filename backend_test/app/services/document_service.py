# app/services/document_service.py

from sqlalchemy.orm import Session
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