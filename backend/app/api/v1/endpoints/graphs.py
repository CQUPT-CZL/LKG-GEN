# app/api/v1/endpoints/graphs.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from neo4j import Driver
from typing import List
from app.api import deps
from app.schemas import graph as graph_schemas
from app.schemas import resource as resource_schemas
from app.crud import crud_graph, crud_sqlite

router = APIRouter()

@router.post("/", response_model=graph_schemas.Graph)
def create_graph(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    graph: graph_schemas.GraphCreate
):
    """
    创建新的知识图谱
    """
    try:
        # 调用CRUD层创建图谱
        created_graph = crud_graph.create_knowledge_graph(driver=driver, graph=graph)
        
        # 转换Neo4j节点为Pydantic模型
        return graph_schemas.Graph(
            id=created_graph["id"],
            name=created_graph["name"],
            description=created_graph.get("description")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建图谱失败: {e}")


@router.get("/", response_model=List[graph_schemas.Graph])
def get_graphs(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    skip: int = 0,
    limit: int = 100
):
    """
    获取图谱列表，包含实体和关系统计
    """
    try:
        graphs = crud_graph.get_knowledge_graphs(driver=driver, skip=skip, limit=limit)
        return [
            graph_schemas.Graph(
                id=graph["id"],
                name=graph["name"],
                description=graph.get("description"),
                entity_count=graph.get("entity_count", 0),
                relation_count=graph.get("relation_count", 0)
            )
            for graph in graphs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图谱列表失败: {e}")


@router.get("/{graph_id}", response_model=graph_schemas.Graph)
def get_graph(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    graph_id: str
):
    """
    获取单个图谱详情
    """
    try:
        graph = crud_graph.get_node_by_id(driver=driver, node_id=graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="图谱不存在")
        
        return graph_schemas.Graph(
            id=graph["id"],
            name=graph["name"],
            description=graph.get("description")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图谱失败: {e}")


@router.get("/{graph_id}/categories", response_model=List[graph_schemas.Category])
def get_graph_categories(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    graph_id: str
):
    """
    获取指定图谱下的所有分类
    """
    try:
        # 检查图谱是否存在
        graph = crud_graph.get_node_by_id(driver=driver, node_id=graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="图谱不存在")
        categories = crud_graph.get_categories_by_graph(driver=driver, graph_id=graph_id)
        return [
            graph_schemas.Category(
                id=c["id"],
                name=c.get("name", ""),
                parent_id=c.get("parent_id", graph_id),
                graph_id=c.get("graph_id", graph_id)
            ) for c in categories
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图谱分类失败: {e}")


@router.get("/{graph_id}/subgraph", response_model=graph_schemas.Subgraph)
def get_graph_subgraph(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    graph_id: str
):
    """
    获取整个图谱（按graph_id）的子图谱（所有实体及其内部关系）
    """
    try:
        # 检查图谱是否存在
        graph = crud_graph.get_node_by_id(driver=driver, node_id=graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="图谱不存在")
        subgraph_data = crud_graph.get_graph_subgraph(driver=driver, graph_id=graph_id)
        entities = [graph_schemas.Entity(**entity) for entity in subgraph_data["entities"]]
        # 关系字段与Schema不同名，逐项映射
        relationships = [
            graph_schemas.Relationship(
                id=rel["id"],
                type=rel.get("relation_type") or rel.get("type", ""),
                start_node_id=rel.get("source_entity_id") or rel.get("start_node_id", ""),
                end_node_id=rel.get("target_entity_id") or rel.get("end_node_id", ""),
                properties=rel.get("properties")
            ) for rel in subgraph_data["relationships"]
        ]
        return graph_schemas.Subgraph(entities=entities, relationships=relationships)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图谱子图谱失败: {e}")


@router.get("/{graph_id}/documents", response_model=List[resource_schemas.SourceResource])
def get_graph_documents(
    *,
    db: Session = Depends(deps.get_db),
    driver: Driver = Depends(deps.get_neo4j),
    graph_id: str
):
    """
    获取指定图谱下的资源（文档）列表。
    基于Neo4j中Graph/Category到Document的CONTAINS_RESOURCE关系，
    收集source_document_id，再到SQLite中批量查询。
    """
    try:
        # 检查图谱是否存在
        graph = crud_graph.get_node_by_id(driver=driver, node_id=graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="图谱不存在")
        doc_ids = crud_graph.get_document_ids_by_graph(driver=driver, graph_id=graph_id)
        documents = crud_sqlite.get_source_documents_by_ids(db=db, document_ids=doc_ids)
        return documents
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图谱文档失败: {e}")


@router.delete("/{graph_id}")
def delete_graph(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    graph_id: str
):
    """
    删除图谱
    """
    try:
        # 检查图谱是否存在
        graph = crud_graph.get_node_by_id(driver=driver, node_id=graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="图谱不存在")
        
        # 删除图谱及其所有相关节点和关系
        crud_graph.delete_knowledge_graph(driver=driver, graph_id=graph_id)
        return {"message": "图谱删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除图谱失败: {e}")