# app/crud/crud_relation.py

from neo4j import Driver
from typing import List, Optional, Dict, Any
from app.schemas.relation import RelationCreate, RelationUpdate
import uuid
from datetime import datetime

def get_relations_by_graph(driver: Driver, graph_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    获取指定图谱的关系列表
    """
    with driver.session() as session:
        query = """
        MATCH (source:Entity)-[r:RELATION]->(target:Entity)
        WHERE r.graph_id = $graph_id
        RETURN r.id as id, r.relation_type as relation_type, r.description as description,
               r.graph_id as graph_id, r.confidence as confidence,
               source.id as source_entity_id,
               target.id as target_entity_id
        ORDER BY r.confidence DESC
        SKIP $skip LIMIT $limit
        """
        result = session.run(query, graph_id=graph_id, skip=skip, limit=limit)
        return [dict(record) for record in result]

def create_relation(driver: Driver, relation: RelationCreate) -> Dict[str, Any]:
    """
    创建新关系
    """
    with driver.session() as session:
        relation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # 首先检查源实体和目标实体是否存在
        check_entities_query = """
        MATCH (source:Entity {id: $source_id}), (target:Entity {id: $target_id})
        RETURN source.name as source_name, target.name as target_name
        """
        
        entities_result = session.run(
            check_entities_query,
            source_id=relation.source_entity_id,
            target_id=relation.target_entity_id
        )
        entities_record = entities_result.single()
        
        if not entities_record:
            raise ValueError("源实体或目标实体不存在")
        
        # 创建关系
        create_query = """
        MATCH (source:Entity {id: $source_id}), (target:Entity {id: $target_id})
        CREATE (source)-[r:RELATION {
            id: $id,
            relation_type: $relation_type,
            description: $description,
            graph_id: $graph_id,
            confidence: $confidence
        }]->(target)
        RETURN r.id as id, r.relation_type as relation_type, r.description as description,
               r.graph_id as graph_id, r.confidence as confidence,
               source.id as source_entity_id,
               target.id as target_entity_id
        """
        
        result = session.run(
            create_query,
            id=relation_id,
            relation_type=relation.relation_type,
            description=relation.description,
            graph_id=relation.graph_id,
            confidence=relation.confidence,
            source_id=relation.source_entity_id,
            target_id=relation.target_entity_id
        )
        
        record = result.single()
        return dict(record) if record else None

def get_relation_by_id(driver: Driver, relation_id: str) -> Optional[Dict[str, Any]]:
    """
    根据ID获取关系
    """
    with driver.session() as session:
        query = """
        MATCH (source:Entity)-[r:RELATION {id: $relation_id}]->(target:Entity)
        RETURN r.id as id, r.relation_type as relation_type, r.description as description,
               r.graph_id as graph_id, r.confidence as confidence,
               source.id as source_entity_id,
               target.id as target_entity_id
        """
        result = session.run(query, relation_id=relation_id)
        record = result.single()
        return dict(record) if record else None

def update_relation(driver: Driver, relation_id: str, relation: RelationUpdate) -> Optional[Dict[str, Any]]:
    """
    更新关系信息
    """
    with driver.session() as session:
        # 构建更新字段
        update_fields = []
        params = {"relation_id": relation_id, "updated_at": datetime.utcnow().isoformat()}
        
        if relation.relation_type is not None:
            update_fields.append("r.relation_type = $relation_type")
            params["relation_type"] = relation.relation_type
            
        if relation.description is not None:
            update_fields.append("r.description = $description")
            params["description"] = relation.description
            
        if relation.confidence is not None:
            update_fields.append("r.confidence = $confidence")
            params["confidence"] = relation.confidence
        
        if not update_fields:
            return get_relation_by_id(driver, relation_id)
        
        update_fields.append("r.updated_at = $updated_at")
        
        query = f"""
        MATCH (source:Entity)-[r:RELATION {{id: $relation_id}}]->(target:Entity)
        SET {', '.join(update_fields)}
        RETURN r.id as id, r.relation_type as relation_type, r.description as description,
               r.graph_id as graph_id, r.confidence as confidence,
               source.id as source_entity_id,
               target.id as target_entity_id
        """
        
        result = session.run(query, **params)
        record = result.single()
        return dict(record) if record else None

def delete_relation(driver: Driver, relation_id: str) -> bool:
    """
    删除关系
    """
    with driver.session() as session:
        query = """
        MATCH ()-[r:RELATION {id: $relation_id}]->()
        DELETE r
        RETURN count(r) as deleted_count
        """
        result = session.run(query, relation_id=relation_id)
        record = result.single()
        return record["deleted_count"] > 0 if record else False

def get_relations_by_entity(driver: Driver, entity_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    获取指定实体的所有关系（作为源实体或目标实体）
    """
    with driver.session() as session:
        query = """
        MATCH (source:Entity)-[r:RELATION]->(target:Entity)
        WHERE source.id = $entity_id OR target.id = $entity_id
        RETURN r.id as id, r.relation_type as relation_type, r.description as description,
               r.graph_id as graph_id, r.confidence as confidence,
               source.id as source_entity_id,
               target.id as target_entity_id
        ORDER BY r.confidence DESC
        SKIP $skip LIMIT $limit
        """
        result = session.run(query, entity_id=entity_id, skip=skip, limit=limit)
        return [dict(record) for record in result]

def search_relations(driver: Driver, graph_id: str, query: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    搜索关系
    """
    with driver.session() as session:
        search_query = """
        MATCH (source:Entity)-[r:RELATION]->(target:Entity)
        WHERE r.graph_id = $graph_id
          AND (toLower(r.type) CONTAINS toLower($query)
               OR toLower(r.description) CONTAINS toLower($query)
               OR toLower(source.name) CONTAINS toLower($query)
               OR toLower(target.name) CONTAINS toLower($query))
        RETURN r.id as id, r.type as type, r.description as description,
               r.graph_id as graph_id, r.frequency as frequency,
               r.created_at as created_at, r.updated_at as updated_at,
               r.properties as properties,
               source.id as source_entity_id, source.name as source_entity_name,
               target.id as target_entity_id, target.name as target_entity_name
        ORDER BY r.frequency DESC, r.created_at DESC
        SKIP $skip LIMIT $limit
        """
        result = session.run(search_query, graph_id=graph_id, query=query, skip=skip, limit=limit)
        return [dict(record) for record in result]