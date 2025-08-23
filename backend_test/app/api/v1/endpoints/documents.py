# app/api/v1/endpoints/documents.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from typing import List
from neo4j import Driver
from app.api import deps
from app.services import document_service
from app.schemas import resource as resource_schemas
from app.schemas import graph as graph_schemas
from app.crud import crud_sqlite, crud_graph

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
    driver: Driver = Depends(deps.get_neo4j_driver),
    document_id: int
):
    """
    删除文档及其相关的实体和关系
    """
    try:
        # 1. 检查文档是否存在
        document = crud_sqlite.get_source_document(db=db, document_id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 2. 清理Neo4j中的相关实体
        cleanup_result = crud_graph.cleanup_entities_for_document(driver, document_id)
        print(f"🧹 实体清理完成: 删除了 {cleanup_result['deleted_count']} 个实体，更新了 {cleanup_result['updated_count']} 个实体")
        
        # 3. 删除Neo4j中的文档节点
        document_deleted = crud_graph.delete_document_node(driver, document_id)
        if document_deleted:
            print(f"🗑️ Neo4j文档节点删除成功: document_id={document_id}")
        else:
            print(f"⚠️ Neo4j文档节点未找到或删除失败: document_id={document_id}")
        
        # 4. 删除SQLite中的文档记录
        sqlite_deleted = crud_sqlite.delete_source_document(db=db, document_id=document_id)
        if not sqlite_deleted:
            raise HTTPException(status_code=500, detail="SQLite文档删除失败")
        
        return {
            "message": "文档删除成功",
            "details": {
                "deleted_entities": cleanup_result['deleted_entities'],
                "updated_entities": cleanup_result['updated_entities'],
                "neo4j_document_deleted": document_deleted,
                "sqlite_document_deleted": sqlite_deleted
            }
        }
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
        raise HTTPException(status_code=500, detail=f"批量创建资源失败: {e}")


@router.get("/{document_id}/subgraph", response_model=graph_schemas.Subgraph)
def get_document_subgraph(
    *,
    db: Session = Depends(deps.get_db),
    driver: Driver = Depends(deps.get_neo4j_driver),
    document_id: int
):
    """
    获取指定文档下的子图谱
    返回该文档相关的所有实体和它们之间的关系
    """
    try:
        # 首先检查文档是否存在
        document = crud_sqlite.get_source_document(db=db, document_id=document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取文档的子图谱数据
        subgraph_data = crud_graph.get_document_subgraph(driver=driver, document_id=document_id)
        
        # 转换为Pydantic模型
        entities = [graph_schemas.Entity(**entity) for entity in subgraph_data["entities"]]
        relationships = [graph_schemas.Relationship(**rel) for rel in subgraph_data["relationships"]]
        
        return graph_schemas.Subgraph(
            entities=entities,
            relationships=relationships
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档子图谱失败: {e}")
