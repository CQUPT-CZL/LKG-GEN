# app/crud/crud_entity.py

from neo4j import Driver
from typing import List, Optional, Dict, Any
from app.schemas.entity import EntityCreate, EntityUpdate
import uuid
from datetime import datetime

def get_entities_by_graph(driver: Driver, graph_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    获取指定图谱的实体列表
    """
    with driver.session() as session:
        query = """
        MATCH (e:Entity {graph_id: $graph_id})
        RETURN e.id as id, e.name as name, e.entity_type as entity_type, 
               e.description as description, e.graph_id as graph_id,
               e.frequency as frequency, e.created_at as created_at,
               e.updated_at as updated_at, e.chunk_ids as chunk_ids
        ORDER BY e.created_at DESC
        SKIP $skip LIMIT $limit
        """
        result = session.run(query, graph_id=graph_id, skip=skip, limit=limit)
        return [dict(record) for record in result]

def create_entity(driver: Driver, entity: EntityCreate) -> Dict[str, Any]:
    """
    创建新实体
    """
    with driver.session() as session:
        entity_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        query = """
        CREATE (e:Entity {
            id: $id,
            name: $name,
            entity_type: $entity_type,
            description: $description,
            graph_id: $graph_id,
            frequency: $frequency,
            chunk_ids: $chunk_ids,
            created_at: $created_at,
            updated_at: $updated_at
        })
        RETURN e.id as id, e.name as name, e.entity_type as entity_type,
               e.description as description, e.graph_id as graph_id,
               e.frequency as frequency, e.created_at as created_at,
               e.updated_at as updated_at, e.chunk_ids as chunk_ids
        """
        
        result = session.run(
            query,
            id=entity_id,
            name=entity.name,
            entity_type=entity.entity_type,
            description=entity.description,
            graph_id=entity.graph_id,
            frequency=entity.frequency,
            chunk_ids=entity.chunk_ids or [],
            created_at=now,
            updated_at=now
        )
        
        record = result.single()
        return dict(record) if record else None

def get_entity_by_id(driver: Driver, entity_id: str) -> Optional[Dict[str, Any]]:
    """
    根据ID获取实体
    """
    with driver.session() as session:
        query = """
        MATCH (e:Entity {id: $entity_id})
        RETURN e.id as id, e.name as name, e.entity_type as entity_type,
               e.description as description, e.graph_id as graph_id,
               e.frequency as frequency, e.created_at as created_at,
               e.updated_at as updated_at, e.chunk_ids as chunk_ids
        """
        result = session.run(query, entity_id=entity_id)
        record = result.single()
        return dict(record) if record else None

def update_entity(driver: Driver, entity_id: str, entity: EntityUpdate) -> Optional[Dict[str, Any]]:
    """
    更新实体信息
    """
    with driver.session() as session:
        # 构建更新字段
        update_fields = []
        params = {"entity_id": entity_id, "updated_at": datetime.utcnow().isoformat()}
        
        if entity.name is not None:
            update_fields.append("e.name = $name")
            params["name"] = entity.name
            
        if entity.entity_type is not None:
            update_fields.append("e.entity_type = $entity_type")
            params["entity_type"] = entity.entity_type
            
        if entity.description is not None:
            update_fields.append("e.description = $description")
            params["description"] = entity.description
            
        if entity.frequency is not None:
            update_fields.append("e.frequency = $frequency")
            params["frequency"] = entity.frequency
            
        if entity.chunk_ids is not None:
            update_fields.append("e.chunk_ids = $chunk_ids")
            params["chunk_ids"] = entity.chunk_ids
        
        if not update_fields:
            return get_entity_by_id(driver, entity_id)
        
        update_fields.append("e.updated_at = $updated_at")
        
        query = f"""
        MATCH (e:Entity {{id: $entity_id}})
        SET {', '.join(update_fields)}
        RETURN e.id as id, e.name as name, e.entity_type as entity_type,
               e.description as description, e.graph_id as graph_id,
               e.frequency as frequency, e.created_at as created_at,
               e.updated_at as updated_at, e.chunk_ids as chunk_ids
        """
        
        result = session.run(query, **params)
        record = result.single()
        return dict(record) if record else None

def delete_entity(driver: Driver, entity_id: str) -> bool:
    """
    删除实体及其相关关系
    """
    with driver.session() as session:
        # 先删除相关关系
        delete_relations_query = """
        MATCH (e:Entity {id: $entity_id})-[r]->()
        DELETE r
        """
        session.run(delete_relations_query, entity_id=entity_id)
        
        delete_relations_query2 = """
        MATCH ()-[r]->(e:Entity {id: $entity_id})
        DELETE r
        """
        session.run(delete_relations_query2, entity_id=entity_id)
        
        # 删除实体
        delete_entity_query = """
        MATCH (e:Entity {id: $entity_id})
        DELETE e
        RETURN count(e) as deleted_count
        """
        result = session.run(delete_entity_query, entity_id=entity_id)
        record = result.single()
        return record["deleted_count"] > 0 if record else False

def search_entities(driver: Driver, graph_id: str, query: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    搜索实体
    """
    with driver.session() as session:
        search_query = """
        MATCH (e:Entity {graph_id: $graph_id})
        WHERE toLower(e.name) CONTAINS toLower($query) 
           OR toLower(e.description) CONTAINS toLower($query)
        RETURN e.id as id, e.name as name, e.entity_type as entity_type,
               e.description as description, e.graph_id as graph_id,
               e.frequency as frequency, e.created_at as created_at,
               e.updated_at as updated_at, e.chunk_ids as chunk_ids
        ORDER BY e.frequency DESC, e.created_at DESC
        SKIP $skip LIMIT $limit
        """
        result = session.run(search_query, graph_id=graph_id, query=query, skip=skip, limit=limit)
        return [dict(record) for record in result]