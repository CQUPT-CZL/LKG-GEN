# app/api/v1/endpoints/documents.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from typing import List
from neo4j import Driver
from app.api import deps
from app.services import document_service
from app.schemas import document as document_schemas
from app.crud import crud_sqlite

router = APIRouter()

@router.post("/upload", response_model=document_schemas.Document)
async def upload_document(
    *,
    db: Session = Depends(deps.get_db), # 通过依赖注入获取DB会话
    file: UploadFile = File(...)      # 要求必须上传一个文件
):
    """
    上传一个文档 (.md, .txt等) 进行处理。
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="没有文件名")
        
    try:
        document = await document_service.create_upload_document(db=db, file=file)
        return document
    except Exception as e:
        # 在真实应用中，这里应该有更详细的错误处理
        raise HTTPException(status_code=500, detail=f"文件处理失败: {e}")


@router.get("/", response_model=List[document_schemas.Document])
def get_documents(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    获取文档列表
    """
    try:
        documents = crud_sqlite.get_source_documents(db=db, skip=skip, limit=limit)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {e}")


@router.get("/{document_id}", response_model=document_schemas.Document)
def get_document(
    *,
    db: Session = Depends(deps.get_db),
    document_id: int
):
    """
    获取单个文档详情
    """
    try:
        document = crud_sqlite.get_source_document(db=db, document_id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档失败: {e}")


@router.delete("/{document_id}")
def delete_document(
    *,
    db: Session = Depends(deps.get_db),
    document_id: int
):
    """
    删除文档
    """
    try:
        document = crud_sqlite.get_source_document(db=db, document_id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        crud_sqlite.delete_source_document(db=db, document_id=document_id)
        return {"message": "文档删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {e}")



@router.post("/resources", response_model=document_schemas.Resource)
def create_resource(
    *,
    db: Session = Depends(deps.get_db),
    driver: Driver = Depends(deps.get_neo4j_driver),
    resource_in: document_schemas.ResourceCreate,
    background_tasks: BackgroundTasks
):
    """
    创建一个新的资源（论文、书籍、网页等）。
    
    这个接口会处理所有必要的数据库操作，并触发后台知识抽取。
    """
    try:
        resource_node = document_service.create_new_resource(
            driver=driver,
            db=db,
            resource=resource_in,
            background_tasks=background_tasks
        )
        return resource_node
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建资源失败: {e}")
