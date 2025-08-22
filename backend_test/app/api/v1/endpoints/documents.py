# app/api/v1/endpoints/documents.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from typing import List
from neo4j import Driver
from app.api import deps
from app.services import document_service
from app.schemas import resource as resource_schemas
from app.crud import crud_sqlite

router = APIRouter()

@router.get("/", response_model=List[resource_schemas.SourceResource])
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


@router.get("/{document_id}", response_model=resource_schemas.SourceResource)
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



@router.post("/resources", response_model=resource_schemas.BatchResourceResponse)
def create_resources(
    *,
    db: Session = Depends(deps.get_db),
    driver: Driver = Depends(deps.get_neo4j_driver),
    batch_request: resource_schemas.BatchResourceCreate,
    background_tasks: BackgroundTasks
):
    """
    创建资源（论文、书籍、网页等）。
    
    支持批量创建多个资源，包括数据库操作和后台知识抽取。
    返回成功和失败的统计信息。
    """
    try:
        result = document_service.create_batch_resources(
            driver=driver,
            db=db,
            batch_request=batch_request,
            background_tasks=background_tasks
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建资源失败: {e}")
