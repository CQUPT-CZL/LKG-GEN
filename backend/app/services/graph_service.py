# app/services/graph_service.py

from neo4j import Driver
from app.crud import crud_graph
from app.schemas.graph import GraphCreate, CategoryCreate
from fastapi import HTTPException

def create_new_graph(driver: Driver, graph: GraphCreate) -> dict:
    """业务逻辑：创建一个新的图谱项目"""
    # 未来可以在这里添加逻辑，比如检查图谱名称是否已存在
    return crud_graph.create_knowledge_graph(driver=driver, graph=graph)

def create_new_category(driver: Driver, category: CategoryCreate, graph_id: str) -> dict:
    """业务逻辑：创建一个新的分类"""
    # 业务检查：确保父节点是真实存在的
    parent_node = crud_graph.get_node_by_id(driver=driver, node_id=category.parent_id)
    if not parent_node:
        raise HTTPException(status_code=404, detail="父节点不存在")
    
    # 业务检查：确保父节点属于当前操作的图谱
    if parent_node.get("graph_id") != graph_id:
        raise HTTPException(status_code=400, detail="不能跨图谱创建子分类")

    return crud_graph.create_category(driver=driver, category=category, graph_id=graph_id)