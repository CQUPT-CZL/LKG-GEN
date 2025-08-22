# app/api/v1/endpoints/categories.py

from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from typing import List
from app.api import deps
from app.schemas import graph as graph_schemas
from app.crud import crud_graph

router = APIRouter()

@router.post("/", response_model=graph_schemas.Category)
def create_category(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    category: graph_schemas.CategoryCreate
):
    """
    创建分类
    """
    try:
        # 验证父节点是否存在
        parent_node = crud_graph.get_node_by_id(driver=driver, node_id=category.parent_id)
        if not parent_node:
            raise HTTPException(status_code=404, detail="父节点不存在")
        
        # 获取图谱ID（如果父节点是图谱，则graph_id就是parent_id；如果是分类，则使用其graph_id）
        graph_id = parent_node.get("graph_id", category.parent_id)
        
        # 创建分类
        created_category = crud_graph.create_category(
            driver=driver, 
            category=category, 
            graph_id=graph_id
        )
        
        return graph_schemas.Category(
            id=created_category["id"],
            name=created_category["name"],
            parent_id=created_category["parent_id"],
            graph_id=created_category["graph_id"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分类失败: {e}")


@router.get("/{category_id}", response_model=graph_schemas.Category)
def get_category(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    category_id: str
):
    """
    获取单个分类详情
    """
    try:
        category = crud_graph.get_node_by_id(driver=driver, node_id=category_id)
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        
        return graph_schemas.Category(
            id=category["id"],
            name=category["name"],
            parent_id=category["parent_id"],
            graph_id=category["graph_id"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类失败: {e}")


@router.delete("/{category_id}")
def delete_category(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    category_id: str
):
    """
    删除分类
    """
    try:
        # 检查分类是否存在
        category = crud_graph.get_node_by_id(driver=driver, node_id=category_id)
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        
        # 这里可以添加删除分类的逻辑
        # 暂时返回成功消息
        return {"message": "分类删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除分类失败: {e}")


@router.get("/{category_id}/subgraph", response_model=graph_schemas.Subgraph)
def get_category_subgraph(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    category_id: str
):
    """
    获取某一分类下面的子图谱
    返回该分类下所有实体和它们之间的关系
    """
    try:
        # 检查分类是否存在
        category = crud_graph.get_node_by_id(driver=driver, node_id=category_id)
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        
        # 获取子图谱数据
        subgraph_data = crud_graph.get_category_subgraph(driver=driver, category_id=category_id)
        
        # 转换为响应模型
        entities = [
            graph_schemas.Entity(
                id=entity["id"],
                name=entity["name"],
                type=entity["type"],
                properties=entity["properties"]
            )
            for entity in subgraph_data["entities"]
        ]
        
        relationships = [
            graph_schemas.Relationship(
                id=rel["id"],
                type=rel["type"],
                start_node_id=rel["start_node_id"],
                end_node_id=rel["end_node_id"],
                properties=rel["properties"]
            )
            for rel in subgraph_data["relationships"]
        ]
        
        return graph_schemas.Subgraph(
            entities=entities,
            relationships=relationships
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类子图谱失败: {e}")