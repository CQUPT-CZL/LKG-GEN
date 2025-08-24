# app/api/v1/endpoints/relations.py

from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from typing import List
from app.api import deps
from app.schemas import relation as relation_schemas
from app.crud import crud_relation

router = APIRouter()

@router.get("/", response_model=List[relation_schemas.Relation])
def get_relations(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    graph_id: str,
    skip: int = 0,
    limit: int = 100
):
    """
    获取指定图谱的关系列表
    """
    try:
        relations = crud_relation.get_relations_by_graph(driver=driver, graph_id=graph_id, skip=skip, limit=limit)
        return [
            relation_schemas.Relation(
                id=relation["id"],
                relation_type=relation["relation_type"],
                source_entity_id=relation["source_entity_id"],
                target_entity_id=relation["target_entity_id"],
                description=relation.get("description", ""),
                graph_id=relation.get("graph_id", graph_id),
                confidence=relation.get("confidence", 1.0)
            )
            for relation in relations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关系列表失败: {e}")

@router.post("/", response_model=relation_schemas.Relation)
def create_relation(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    relation: relation_schemas.RelationCreate
):
    """
    创建新关系
    """
    try:
        created_relation = crud_relation.create_relation(driver=driver, relation=relation)
        return relation_schemas.Relation(
            id=created_relation["id"],
            relation_type=created_relation["relation_type"],
            source_entity_id=created_relation["source_entity_id"],
            target_entity_id=created_relation["target_entity_id"],
            description=created_relation.get("description", ""),
            graph_id=created_relation.get("graph_id"),
            confidence=created_relation.get("confidence", 1.0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建关系失败: {e}")

@router.get("/{relation_id}", response_model=relation_schemas.Relation)
def get_relation(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    relation_id: str
):
    """
    获取单个关系详情
    """
    try:
        relation = crud_relation.get_relation_by_id(driver=driver, relation_id=relation_id)
        if not relation:
            raise HTTPException(status_code=404, detail="关系不存在")
        
        return relation_schemas.Relation(
            id=relation["id"],
            relation_type=relation["relation_type"],
            source_entity_id=relation["source_entity_id"],
            target_entity_id=relation["target_entity_id"],
            description=relation.get("description", ""),
            graph_id=relation.get("graph_id"),
            confidence=relation.get("confidence", 1.0)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关系失败: {e}")

@router.put("/{relation_id}", response_model=relation_schemas.Relation)
def update_relation(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    relation_id: str,
    relation: relation_schemas.RelationUpdate
):
    """
    更新关系信息
    """
    try:
        updated_relation = crud_relation.update_relation(driver=driver, relation_id=relation_id, relation=relation)
        if not updated_relation:
            raise HTTPException(status_code=404, detail="关系不存在")
        
        return relation_schemas.Relation(
            id=updated_relation["id"],
            relation_type=updated_relation["relation_type"],
            source_entity_id=updated_relation["source_entity_id"],
            target_entity_id=updated_relation["target_entity_id"],
            description=updated_relation.get("description", ""),
            graph_id=updated_relation.get("graph_id"),
            confidence=updated_relation.get("confidence", 1.0)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新关系失败: {e}")

@router.delete("/{relation_id}")
def delete_relation(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    relation_id: str
):
    """
    删除关系
    """
    try:
        success = crud_relation.delete_relation(driver=driver, relation_id=relation_id)
        if not success:
            raise HTTPException(status_code=404, detail="关系不存在")
        
        return {"message": "关系删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除关系失败: {e}")

@router.get("/entity/{entity_id}", response_model=List[relation_schemas.Relation])
def get_entity_relations(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    entity_id: str,
    skip: int = 0,
    limit: int = 100
):
    """
    获取指定实体的所有关系
    """
    try:
        relations = crud_relation.get_relations_by_entity(driver=driver, entity_id=entity_id, skip=skip, limit=limit)
        return [
            relation_schemas.Relation(
                id=relation["id"],
                relation_type=relation["relation_type"],
                source_entity_id=relation["source_entity_id"],
                target_entity_id=relation["target_entity_id"],
                description=relation.get("description", ""),
                graph_id=relation.get("graph_id"),
                confidence=relation.get("confidence", 1.0)
            )
            for relation in relations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体关系失败: {e}")