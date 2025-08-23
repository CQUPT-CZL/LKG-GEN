# app/api/v1/endpoints/entities.py

from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from typing import List
from app.api import deps
from app.schemas import entity as entity_schemas
from app.crud import crud_entity

router = APIRouter()

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
                created_at=entity.get("created_at"),
                updated_at=entity.get("updated_at"),
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
            created_at=created_entity.get("created_at"),
            updated_at=created_entity.get("updated_at"),
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
            created_at=entity.get("created_at"),
            updated_at=entity.get("updated_at"),
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
            created_at=updated_entity.get("created_at"),
            updated_at=updated_entity.get("updated_at"),
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