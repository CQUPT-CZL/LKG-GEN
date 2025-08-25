# app/api/v1/endpoints/entities.py

from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from neo4j.time import DateTime as Neo4jDateTime
from typing import List
from datetime import datetime
from app.api import deps
from app.schemas import entity as entity_schemas
from app.crud import crud_entity

router = APIRouter()

def convert_neo4j_datetime(value):
    """转换 Neo4j DateTime 对象为 Python datetime 对象"""
    if isinstance(value, Neo4jDateTime):
        return value.to_native()
    return value

@router.get("/", response_model=List[entity_schemas.Entity])
def get_entities(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    graph_id: str,
    skip: int = 0,
    limit: int = 100
):
    """
    获取指定图谱的实体列表
    """
    try:
        entities = crud_entity.get_entities_by_graph(driver=driver, graph_id=graph_id, skip=skip, limit=limit)
        return [
            entity_schemas.Entity(
                id=entity["id"],
                name=entity["name"],
                entity_type=entity.get("entity_type", ""),
                description=entity.get("description", ""),
                graph_id=entity.get("graph_id", graph_id),
                frequency=entity.get("frequency", 0),
                created_at=convert_neo4j_datetime(entity.get("created_at")),
                chunk_ids=entity.get("chunk_ids", [])
            )
            for entity in entities
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体列表失败: {e}")

@router.post("/", response_model=entity_schemas.Entity)
def create_entity(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    entity: entity_schemas.EntityCreate
):
    """
    创建新实体
    """
    try:
        created_entity = crud_entity.create_entity(driver=driver, entity=entity)
        return entity_schemas.Entity(
            id=created_entity["id"],
            name=created_entity["name"],
            entity_type=created_entity.get("entity_type", ""),
            description=created_entity.get("description", ""),
            graph_id=created_entity.get("graph_id"),
            frequency=created_entity.get("frequency", 0),
            created_at=convert_neo4j_datetime(created_entity.get("created_at")),
            updated_at=convert_neo4j_datetime(created_entity.get("updated_at")),
            chunk_ids=created_entity.get("chunk_ids", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建实体失败: {e}")

@router.get("/{entity_id}", response_model=entity_schemas.Entity)
def get_entity(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    entity_id: str
):
    """
    获取单个实体详情
    """
    try:
        entity = crud_entity.get_entity_by_id(driver=driver, entity_id=entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        return entity_schemas.Entity(
            id=entity["id"],
            name=entity["name"],
            entity_type=entity.get("entity_type", ""),
            description=entity.get("description", ""),
            graph_id=entity.get("graph_id"),
            frequency=entity.get("frequency", 0),
            created_at=convert_neo4j_datetime(entity.get("created_at")),
            updated_at=convert_neo4j_datetime(entity.get("updated_at")),
            chunk_ids=entity.get("chunk_ids", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体失败: {e}")

@router.put("/{entity_id}", response_model=entity_schemas.Entity)
def update_entity(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    entity_id: str,
    entity: entity_schemas.EntityUpdate
):
    """
    更新实体信息
    """
    try:
        updated_entity = crud_entity.update_entity(driver=driver, entity_id=entity_id, entity=entity)
        if not updated_entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        return entity_schemas.Entity(
            id=updated_entity["id"],
            name=updated_entity["name"],
            entity_type=updated_entity.get("entity_type", ""),
            description=updated_entity.get("description", ""),
            graph_id=updated_entity.get("graph_id"),
            frequency=updated_entity.get("frequency", 0),
            created_at=convert_neo4j_datetime(updated_entity.get("created_at")),
            updated_at=convert_neo4j_datetime(updated_entity.get("updated_at")),
            chunk_ids=updated_entity.get("chunk_ids", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新实体失败: {e}")

@router.delete("/{entity_id}")
def delete_entity(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    entity_id: str
):
    """
    删除实体
    """
    try:
        success = crud_entity.delete_entity(driver=driver, entity_id=entity_id)
        if not success:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        return {"message": "实体删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除实体失败: {e}")


@router.post("/merge", response_model=entity_schemas.EntityMergeResponse)
def merge_entities(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    merge_request: entity_schemas.EntityMergeRequest
):
    """
    合并两个实体
    将源实体合并到目标实体，包括：
    - 合并chunk_ids和document_ids
    - 转移所有关系到目标实体
    - 合并频次
    - 删除源实体
    """
    try:
        # 验证两个实体不能相同
        if merge_request.source_entity_id == merge_request.target_entity_id:
            raise HTTPException(status_code=400, detail="源实体和目标实体不能相同")
        
        # 执行合并操作
        merged_entity_data = crud_entity.merge_entities(
            driver=driver,
            source_entity_id=merge_request.source_entity_id,
            target_entity_id=merge_request.target_entity_id,
            merged_name=merge_request.merged_name,
            merged_description=merge_request.merged_description
        )
        
        # 构造返回的实体对象
        merged_entity = entity_schemas.Entity(
            id=merged_entity_data["id"],
            name=merged_entity_data["name"],
            entity_type=merged_entity_data.get("entity_type", ""),
            description=merged_entity_data.get("description", ""),
            graph_id=merged_entity_data.get("graph_id"),
            frequency=merged_entity_data.get("frequency", 0),
            created_at=convert_neo4j_datetime(merged_entity_data.get("created_at")),
            updated_at=convert_neo4j_datetime(merged_entity_data.get("updated_at")),
            chunk_ids=merged_entity_data.get("chunk_ids", [])
        )
        
        return entity_schemas.EntityMergeResponse(
            success=True,
            message=f"实体合并成功，源实体 {merge_request.source_entity_id} 已合并到目标实体 {merge_request.target_entity_id}",
            merged_entity=merged_entity
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实体合并失败: {e}")


@router.get("/{entity_id}/subgraph", response_model=entity_schemas.EntitySubgraphResponse)
def get_entity_subgraph(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    entity_id: str,
    hops: int = 1
):
    """
    获取指定实体的1跳子图
    
    Args:
        entity_id: 实体ID
        hops: 跳数，目前只支持1，默认为1
    
    Returns:
        包含中心实体、相关实体和关系的子图数据
    """
    try:
        # 验证跳数范围
        if hops != 1:
            raise HTTPException(status_code=400, detail="目前只支持1跳查询")
        
        # 获取子图数据
        subgraph_data = crud_entity.get_entity_subgraph(
            driver=driver,
            entity_id=entity_id,
            hops=hops
        )
        
        # 构造响应数据
        center_entity = entity_schemas.SubgraphEntity(**subgraph_data["center_entity"])
        
        entities = [
            entity_schemas.SubgraphEntity(**entity_data)
            for entity_data in subgraph_data.get("entities", [])
        ]
        
        relationships = [
            entity_schemas.SubgraphRelationship(**rel_data)
            for rel_data in subgraph_data.get("relationships", [])
        ]
        
        return entity_schemas.EntitySubgraphResponse(
            center_entity=center_entity,
            entities=entities,
            relationships=relationships,
            hops=hops,
            total_entities=len(entities),
            total_relationships=len(relationships)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体子图失败: {e}")