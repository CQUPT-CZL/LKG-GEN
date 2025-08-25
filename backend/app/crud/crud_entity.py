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


def merge_entities(driver: Driver, source_entity_id: str, target_entity_id: str, 
                  merged_name: Optional[str] = None, merged_description: Optional[str] = None) -> Dict[str, Any]:
    """
    合并两个实体：将源实体合并到目标实体
    1. 合并chunk_ids和document_ids
    2. 更新所有指向源实体的关系，改为指向目标实体
    3. 合并频次
    4. 删除源实体
    5. 更新目标实体信息
    """
    with driver.session() as session:
        # 开始事务
        with session.begin_transaction() as tx:
            # 1. 获取源实体和目标实体信息
            get_entities_query = """
            MATCH (source:Entity {id: $source_id}), (target:Entity {id: $target_id})
            RETURN source, target
            """
            entities_result = tx.run(get_entities_query, source_id=source_entity_id, target_id=target_entity_id)
            entities_record = entities_result.single()
            
            if not entities_record:
                raise ValueError("源实体或目标实体不存在")
            
            source_entity = dict(entities_record["source"])
            target_entity = dict(entities_record["target"])
            
            # 2. 合并chunk_ids和document_ids
            source_chunk_ids = source_entity.get("chunk_ids", []) or []
            target_chunk_ids = target_entity.get("chunk_ids", []) or []
            merged_chunk_ids = list(set(source_chunk_ids + target_chunk_ids))
            
            source_doc_ids = source_entity.get("document_ids", []) or []
            target_doc_ids = target_entity.get("document_ids", []) or []
            merged_doc_ids = list(set(source_doc_ids + target_doc_ids))
            
            # 3. 合并频次
            source_frequency = source_entity.get("frequency", 1)
            target_frequency = target_entity.get("frequency", 1)
            merged_frequency = source_frequency + target_frequency
            
            # 4. 合并描述
            if not merged_description:
                source_desc = source_entity.get("description", "")
                target_desc = target_entity.get("description", "")
                if source_desc and target_desc:
                    merged_description = f"{target_desc}"
                else:
                    merged_description = source_desc or target_desc
            
            # 5. 使用合并后的名称
            if not merged_name:
                merged_name = target_entity.get("name")
            
            # 6. 更新所有指向源实体的关系
            update_relations_query = """
            MATCH (source:Entity {id: $source_id})-[r:RELATION]-(other:Entity)
            WHERE other.id <> $target_id
            WITH r, other, type(r) as rel_type, properties(r) as rel_props
            DELETE r
            WITH other, rel_type, rel_props
            MATCH (target:Entity {id: $target_id})
            CREATE (target)-[new_r:RELATION]->(other)
            SET new_r = rel_props
            """
            tx.run(update_relations_query, source_id=source_entity_id, target_id=target_entity_id)
            
            # 7. 更新反向关系
            update_reverse_relations_query = """
            MATCH (other:Entity)-[r:RELATION]->(source:Entity {id: $source_id})
            WHERE other.id <> $target_id
            WITH r, other, type(r) as rel_type, properties(r) as rel_props
            DELETE r
            WITH other, rel_type, rel_props
            MATCH (target:Entity {id: $target_id})
            CREATE (other)-[new_r:RELATION]->(target)
            SET new_r = rel_props
            """
            tx.run(update_reverse_relations_query, source_id=source_entity_id, target_id=target_entity_id)
            
            # 8. 更新文档-实体关系
            update_doc_relations_query = """
            MATCH (doc:Document)-[r:HAS_ENTITY]->(source:Entity {id: $source_id})
            WITH doc, r, properties(r) as rel_props
            DELETE r
            WITH doc, rel_props
            MATCH (target:Entity {id: $target_id})
            MERGE (doc)-[new_r:HAS_ENTITY]->(target)
            SET new_r = rel_props
            """
            tx.run(update_doc_relations_query, source_id=source_entity_id, target_id=target_entity_id)
            
            # 9. 删除源实体
            delete_source_query = """
            MATCH (source:Entity {id: $source_id})
            DELETE source
            """
            tx.run(delete_source_query, source_id=source_entity_id)
            
            # 10. 更新目标实体
            update_target_query = """
            MATCH (target:Entity {id: $target_id})
            SET target.name = $name,
                target.description = $description,
                target.frequency = $frequency,
                target.chunk_ids = $chunk_ids,
                target.document_ids = $document_ids,
                target.updated_at = datetime()
            RETURN target
            """
            result = tx.run(update_target_query, 
                          target_id=target_entity_id,
                          name=merged_name,
                          description=merged_description,
                          frequency=merged_frequency,
                          chunk_ids=merged_chunk_ids,
                          document_ids=merged_doc_ids)
            
            updated_entity = result.single()
            if updated_entity:
                return dict(updated_entity["target"])
            else:
                raise ValueError("更新目标实体失败")

def get_entity_subgraph(driver: Driver, entity_id: str, hops: int = 1) -> Dict[str, Any]:
    """
    获取指定实体的x跳子图
    
    Args:
        driver: Neo4j驱动
        entity_id: 实体ID
        hops: 跳数，最大为3
    
    Returns:
        包含节点和关系的子图数据
    """
    if hops != 1:
        raise ValueError("目前只支持1跳查询")
    
    with driver.session() as session:
        # 只支持1跳查询
        query = """
        MATCH (center:Entity {id: $entity_id})
        OPTIONAL MATCH (center)-[r]-(connected:Entity)
        WITH center, collect(DISTINCT connected) as connected_entities, collect(DISTINCT r) as relations
        RETURN {
            center_entity: {
                id: center.id,
                name: center.name,
                entity_type: center.entity_type,
                description: center.description,
                frequency: center.frequency
            },
            entities: [entity in connected_entities | {
                id: entity.id,
                name: entity.name,
                entity_type: entity.entity_type,
                description: entity.description,
                frequency: entity.frequency
            }],
            relationships: [rel in relations | {
                id: id(rel),
                type: COALESCE(rel.relation_type, type(rel)),
                source_id: startNode(rel).id,
                target_id: endNode(rel).id,
                properties: properties(rel)
            }]
        } as subgraph
        """
        
        result = session.run(query, entity_id=entity_id)
        record = result.single()
        
        if record:
            subgraph_data = record["subgraph"]
            
            # 处理中心实体的 Neo4j DateTime 类型转换
            center_entity = subgraph_data.get("center_entity", {})
            processed_center = {}
            for key, value in center_entity.items():
                if hasattr(value, 'iso_format'):  # Neo4j DateTime
                    processed_center[key] = value.iso_format()
                elif isinstance(value, list):
                    processed_center[key] = [item.iso_format() if hasattr(item, 'iso_format') else item for item in value]
                else:
                    processed_center[key] = value
            subgraph_data["center_entity"] = processed_center
            
            # 处理实体列表的 Neo4j DateTime 类型转换
            processed_entities = []
            for entity in subgraph_data.get("entities", []):
                processed_entity = {}
                for key, value in entity.items():
                    if hasattr(value, 'iso_format'):  # Neo4j DateTime
                        processed_entity[key] = value.iso_format()
                    elif isinstance(value, list):
                        processed_entity[key] = [item.iso_format() if hasattr(item, 'iso_format') else item for item in value]
                    else:
                        processed_entity[key] = value
                processed_entities.append(processed_entity)
            subgraph_data["entities"] = processed_entities
            
            # 处理关系列表的 Neo4j DateTime 类型转换并去重
            unique_relationships = []
            seen_rels = set()
            for rel in subgraph_data.get("relationships", []):
                # 处理关系属性中的 Neo4j DateTime 类型
                processed_rel = {}
                for key, value in rel.items():
                    if key == "properties" and isinstance(value, dict):
                        # 处理 properties 字典中的 Neo4j DateTime
                        processed_properties = {}
                        for prop_key, prop_value in value.items():
                            if hasattr(prop_value, 'iso_format'):
                                processed_properties[prop_key] = prop_value.iso_format()
                            elif isinstance(prop_value, list):
                                processed_properties[prop_key] = [item.iso_format() if hasattr(item, 'iso_format') else item for item in prop_value]
                            else:
                                processed_properties[prop_key] = prop_value
                        processed_rel[key] = processed_properties
                    elif hasattr(value, 'iso_format'):
                        processed_rel[key] = value.iso_format()
                    elif isinstance(value, list):
                        processed_rel[key] = [item.iso_format() if hasattr(item, 'iso_format') else item for item in value]
                    else:
                        processed_rel[key] = value
                
                # 去重逻辑
                rel_key = (processed_rel["source_id"], processed_rel["target_id"], processed_rel["type"])
                if rel_key not in seen_rels:
                    seen_rels.add(rel_key)
                    unique_relationships.append(processed_rel)
            
            subgraph_data["relationships"] = unique_relationships
            return subgraph_data
        else:
            raise ValueError(f"未找到ID为 {entity_id} 的实体")