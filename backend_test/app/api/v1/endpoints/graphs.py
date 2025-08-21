# app/api/v1/endpoints/graphs.py

from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from typing import List
from app.api import deps
from app.schemas import graph as graph_schemas
from app.crud import crud_graph

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
    获取图谱列表
    """
    try:
        graphs = crud_graph.get_knowledge_graphs(driver=driver, skip=skip, limit=limit)
        return [
            graph_schemas.Graph(
                id=graph["id"],
                name=graph["name"],
                description=graph.get("description")
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