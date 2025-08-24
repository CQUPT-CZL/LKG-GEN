# app/crud/crud_graph.py

from neo4j import Driver
from app.schemas.graph import GraphCreate, CategoryCreate
from app.schemas.resource import ResourceCreate # 导入新schema
from app.schemas.entity import EntityCreate, RelationCreate, DocumentEntityRelationCreate
import uuid

def create_knowledge_graph(driver: Driver, graph: GraphCreate) -> dict:
    """在Neo4j中创建一个新的KnowledgeGraph节点"""
    graph_id = str(uuid.uuid4())
    query = """
    CREATE (g:KnowledgeGraph {
        id: $id,
        name: $name,
        description: $description,
        graph_id: $id  // 顶级节点的graph_id就是它自己的id
    })
    RETURN g
    """
    with driver.session() as session:
        result = session.run(query, id=graph_id, name=graph.name, description=graph.description)
        return result.single()[0]

def get_document_subgraph(driver: Driver, document_id: int) -> dict:
    """
    获取某个文档下面的所有实体和关系
    返回该文档相关的所有实体和它们之间的关系
    """
    query = """
    // 步骤1: 找到指定的文档节点
    MATCH (doc:Document {source_document_id: $document_id})
    
    // 步骤2: 获取该文档关联的所有实体
    MATCH (doc)-[:HAS_ENTITY]->(entity:Entity)
    
    // 步骤3: 将找到的所有不重复的实体收集起来
    WITH COLLECT(DISTINCT entity) AS subgraph_entities
    
    // 步骤4: 在收集到的实体集合内部，寻找它们之间的关系
    UNWIND subgraph_entities AS e1
    MATCH (e1)-[r:RELATION]-(e2) WHERE e2 IN subgraph_entities
    
    // 步骤5: 返回构成子图谱的节点和关系
    RETURN COLLECT(DISTINCT e1) AS entities, COLLECT(DISTINCT {relation: r, start_node: startNode(r), end_node: endNode(r)}) AS relationships
    """
    
    with driver.session() as session:
        result = session.run(query, document_id=document_id)
        record = result.single()
        
        if not record:
            return {"entities": [], "relationships": []}
        
        # 处理实体数据
        entities = []
        for entity in record["entities"]:
            # 处理实体属性，转换Neo4j特殊类型
            properties = dict(entity)
            processed_properties = {}
            for key, value in properties.items():
                if hasattr(value, 'iso_format'):  # Neo4j DateTime类型
                    processed_properties[key] = value.iso_format()
                elif isinstance(value, list):
                    processed_properties[key] = [str(item) for item in value]
                else:
                    processed_properties[key] = value
            
            entities.append({
                "id": processed_properties.get("id", ""),
                "name": processed_properties.get("name", ""),
                "type": processed_properties.get("type"),
                "properties": processed_properties
            })
        
        # 处理关系数据
        relationships = []
        for rel_data in record["relationships"]:
            relation = rel_data["relation"]
            start_node = rel_data["start_node"]
            end_node = rel_data["end_node"]
            
            # 处理关系属性
            rel_properties = dict(relation)
            processed_rel_properties = {}
            for key, value in rel_properties.items():
                if hasattr(value, 'iso_format'):  # Neo4j DateTime类型
                    processed_rel_properties[key] = value.iso_format()
                elif isinstance(value, list):
                    processed_rel_properties[key] = [str(item) for item in value]
                else:
                    processed_rel_properties[key] = value
            
            relationships.append({
                "id": processed_rel_properties.get("id", str(relation.id)),
                "type": processed_rel_properties.get("relation_type") or processed_rel_properties.get("type", "") or relation.type or "",
                "description": processed_rel_properties.get("description", ""),
                "start_node_id": start_node.get("id", ""),
                "end_node_id": end_node.get("id", ""),
                "properties": processed_rel_properties
            })
        
        return {
            "entities": entities,
            "relationships": relationships
        }

def get_category_subgraph(driver: Driver, category_id: str) -> dict:
    """
    获取某一分类下面的子图谱
    返回该分类下所有实体和它们之间的关系
    """
    query = """
    // 步骤1: 找到起始分类节点，并遍历其下的所有层级，找到所有提及的实体
    MATCH (start_category:Category {id: $category_id})
    // 使用实际存在的关系类型进行可变长度的路径遍历
    MATCH (start_category)-[:HAS_CHILD|CONTAINS_RESOURCE*]->(doc:Document)
    MATCH (doc)-[:HAS_ENTITY]->(entity:Entity)
    
    // 步骤2: 将找到的所有不重复的实体收集起来
    WITH COLLECT(DISTINCT entity) AS subgraph_entities
    
    // 步骤3: 在收集到的实体集合内部，寻找它们之间的关系
    UNWIND subgraph_entities AS e1
    MATCH (e1)-[r:RELATION]-(e2) WHERE e2 IN subgraph_entities
    
    // 步骤4: 返回构成子图谱的节点和关系
    RETURN COLLECT(DISTINCT e1) AS entities, COLLECT(DISTINCT {relation: r, start_node: startNode(r), end_node: endNode(r)}) AS relationships
    """
    
    with driver.session() as session:
        result = session.run(query, category_id=category_id)
        record = result.single()
        
        if not record:
            return {"entities": [], "relationships": []}
            
        # 处理实体数据
        entities = []
        for entity_node in record["entities"]:
            # 打印实体节点的属性
            # print(f"Entity Node: {entity_node}")

            # 转换Neo4j特殊类型为Python标准类型
            properties = {}
            for key, value in entity_node.items():
                if hasattr(value, 'iso_format'):  # Neo4j DateTime  
                    properties[key] = value.iso_format()
                elif isinstance(value, list):
                    properties[key] = [str(item) if hasattr(item, 'iso_format') else item for item in value]
                else:
                    properties[key] = value
            
            entities.append({
                "id": entity_node["id"],
                "name": entity_node["name"],
                "type": entity_node.get("entity_type"),
                "properties": properties
            })
        
        # 处理关系数据
        relationships = []
        for rel_data in record["relationships"]:
            rel = rel_data["relation"]
            start_node = rel_data["start_node"]
            end_node = rel_data["end_node"]
            
            # 转换关系属性中的Neo4j特殊类型
            rel_properties = {}
            for key, value in rel.items():
                if hasattr(value, 'iso_format'):  # Neo4j DateTime
                    rel_properties[key] = value.iso_format()
                elif isinstance(value, list):
                    rel_properties[key] = [str(item) if hasattr(item, 'iso_format') else item for item in value]
                else:
                    rel_properties[key] = value
            
            relationships.append({
                "id": str(rel.id),
                "type": rel_properties.get("relation_type") or rel_properties.get("type", "") or rel.type or "",
                "description": rel_properties.get("description", ""),
                "start_node_id": start_node["id"],
                "end_node_id": end_node["id"],
                "properties": rel_properties
            })
        
        return {
            "entities": entities,
            "relationships": relationships
        }


# === 实体相关操作 ===
def create_entity(driver: Driver, entity: EntityCreate) -> dict:
    """在Neo4j中创建实体节点"""
    entity_id = str(uuid.uuid4())
    query = """
    CREATE (e:Entity {
        id: $id,
        name: $name,
        entity_type: $entity_type,
        description: $description,
        graph_id: $graph_id,
        chunk_ids: $chunk_ids,
        frequency: $frequency,
        created_at: datetime(),
        document_ids: $document_ids
    })
    RETURN e
    """
    with driver.session() as session:
        result = session.run(
            query,
            id=entity_id,
            name=entity.name,
            entity_type=entity.entity_type,
            description=entity.description,
            graph_id=entity.graph_id,
            frequency=entity.frequency,
            chunk_ids=entity.chunk_ids or [],
            document_ids=entity.document_ids or []
        )   
        return result.single()[0]


def get_entities_by_graph(driver: Driver, graph_id: str) -> list:
    """获取指定图谱的所有实体"""
    query = """
    MATCH (e:Entity {graph_id: $graph_id})
    RETURN e
    ORDER BY e.name
    """
    with driver.session() as session:
        result = session.run(query, graph_id=graph_id)
        return [dict(record[0]) for record in result]


def get_entity_by_id(driver: Driver, entity_id: str) -> dict | None:
    """根据ID获取实体"""
    query = """
    MATCH (e:Entity {id: $id})
    RETURN e
    """
    with driver.session() as session:
        result = session.run(query, id=entity_id)
        record = result.single()
        return dict(record[0]) if record else None


def update_entity(driver: Driver, entity_id: str, new_chunk_ids: list = None, new_document_ids: list = None, frequency: int = None) -> dict | None:
    """更新现有实体的chunk_ids和document_ids"""
    params = {"id": entity_id}
    
    if new_chunk_ids is not None:
        params["new_chunk_ids"] = new_chunk_ids
    
    if new_document_ids is not None:
        params["new_document_ids"] = new_document_ids
    
    if frequency is not None:
        params["frequency_increment"] = frequency
    
    # 使用纯Cypher语法进行合并和去重
    query = """
    MATCH (e:Entity {id: $id})
    WITH e,
         CASE WHEN $new_chunk_ids IS NOT NULL 
              THEN [x IN (e.chunk_ids + $new_chunk_ids) WHERE x IS NOT NULL | x] 
              ELSE e.chunk_ids END AS merged_chunk_ids,
         CASE WHEN $new_document_ids IS NOT NULL 
              THEN [x IN (e.document_ids + $new_document_ids) WHERE x IS NOT NULL | x] 
              ELSE e.document_ids END AS merged_document_ids,
         CASE WHEN $frequency_increment IS NOT NULL 
              THEN e.frequency + $frequency_increment 
              ELSE e.frequency END AS new_frequency
    
    // 去重处理
    WITH e, 
         [x IN merged_chunk_ids | x] AS unique_chunk_ids,
         [x IN merged_document_ids | x] AS unique_document_ids,
         new_frequency
    
    // 手动去重
    WITH e,
         REDUCE(acc = [], x IN unique_chunk_ids | 
           CASE WHEN x IN acc THEN acc ELSE acc + [x] END) AS final_chunk_ids,
         REDUCE(acc = [], x IN unique_document_ids | 
           CASE WHEN x IN acc THEN acc ELSE acc + [x] END) AS final_document_ids,
         new_frequency
    
    SET e.chunk_ids = final_chunk_ids,
        e.document_ids = final_document_ids,
        e.frequency = new_frequency,
        e.updated_at = datetime()
    RETURN e
    """
    
    with driver.session() as session:
        result = session.run(query, **params)
        record = result.single()
        return dict(record[0]) if record else None


def delete_entity(driver: Driver, entity_id: str) -> bool:
    """删除实体及其相关关系"""
    query = """
    MATCH (e:Entity {id: $id})
    DETACH DELETE e
    RETURN count(e) as deleted_count
    """
    with driver.session() as session:
        result = session.run(query, id=entity_id)
        record = result.single()
        return record["deleted_count"] > 0 if record else False


def cleanup_entities_for_document(driver: Driver, document_id: int) -> dict:
    """清理文档删除时的相关实体：从实体的document_ids中移除该文档ID，如果实体只关联该文档则删除整个实体"""
    with driver.session() as session:
        # 首先找到所有包含该document_id的实体
        find_entities_query = """
        MATCH (e:Entity)
        WHERE $document_id IN e.document_ids
        RETURN e.id as entity_id, e.name as entity_name, e.document_ids as document_ids
        """
        
        entities_result = session.run(find_entities_query, document_id=document_id)
        entities_to_update = []
        entities_to_delete = []
        
        for record in entities_result:
            entity_id = record["entity_id"]
            entity_name = record["entity_name"]
            document_ids = record["document_ids"]
            
            # 如果实体只关联这一个文档，标记为删除
            if len(document_ids) == 1 and document_ids[0] == document_id:
                entities_to_delete.append({"id": entity_id, "name": entity_name})
            else:
                # 否则从document_ids中移除该文档ID
                entities_to_update.append({"id": entity_id, "name": entity_name})
        
        # 删除只关联该文档的实体
        deleted_entities = []
        for entity in entities_to_delete:
            delete_query = """
            MATCH (e:Entity {id: $entity_id})
            DETACH DELETE e
            RETURN count(e) as deleted_count
            """
            delete_result = session.run(delete_query, entity_id=entity["id"])
            if delete_result.single()["deleted_count"] > 0:
                deleted_entities.append(entity["name"])
        
        # 更新其他实体的document_ids
        updated_entities = []
        for entity in entities_to_update:
            update_query = """
            MATCH (e:Entity {id: $entity_id})
            SET e.document_ids = [x IN e.document_ids WHERE x <> $document_id]
            RETURN e.name as entity_name
            """
            update_result = session.run(update_query, entity_id=entity["id"], document_id=document_id)
            record = update_result.single()
            if record:
                updated_entities.append(record["entity_name"])
        
        return {
            "deleted_entities": deleted_entities,
            "updated_entities": updated_entities,
            "deleted_count": len(deleted_entities),
            "updated_count": len(updated_entities)
        }


def delete_document_node(driver: Driver, document_id: int) -> bool:
    """删除Neo4j中的文档节点及其关系"""
    query = """
    MATCH (d:Document {source_document_id: $document_id})
    DETACH DELETE d
    RETURN count(d) as deleted_count
    """
    with driver.session() as session:
        result = session.run(query, document_id=document_id)
        record = result.single()
        return record["deleted_count"] > 0 if record else False


# === 关系相关操作 ===
def create_relation(driver: Driver, relation: RelationCreate) -> dict:
    """在Neo4j中创建关系，如果相同类型的关系已存在则不重复创建"""
    with driver.session() as session:
        # 首先检查是否已存在相同类型的关系
        check_query = """
        MATCH (source:Entity {id: $source_id})-[r:RELATION {relation_type: $relation_type}]->(target:Entity {id: $target_id})
        RETURN r, source.name as source_name, target.name as target_name
        """
        
        existing_result = session.run(
            check_query,
            source_id=relation.source_entity_id,
            target_id=relation.target_entity_id,
            relation_type=relation.relation_type
        )
        
        existing_record = existing_result.single()
        if existing_record:
            # 如果关系已存在，返回现有关系
            relation_data = dict(existing_record[0])
            relation_data["source_name"] = existing_record["source_name"]
            relation_data["target_name"] = existing_record["target_name"]
            print(f"  ⚠️ 关系已存在，跳过创建: {existing_record['source_name']} -[{relation.relation_type}]-> {existing_record['target_name']}")
            return relation_data
        
        # 如果关系不存在，创建新关系
        relation_id = str(uuid.uuid4())
        create_query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})
        CREATE (source)-[r:RELATION {
            id: $id,
            relation_type: $relation_type,
            description: $description,
            confidence: $confidence,
            graph_id: $graph_id,
            created_at: datetime()
        }]->(target)
        RETURN r, source.name as source_name, target.name as target_name
        """
        
        result = session.run(
            create_query,
            id=relation_id,
            source_id=relation.source_entity_id,
            target_id=relation.target_entity_id,
            relation_type=relation.relation_type,
            description=relation.description,
            confidence=relation.confidence,
            graph_id=relation.graph_id
        )
        
        record = result.single()
        if record:
            relation_data = dict(record[0])
            relation_data["source_name"] = record["source_name"]
            relation_data["target_name"] = record["target_name"]
            return relation_data
        return None


def get_relations_by_graph(driver: Driver, graph_id: str) -> list:
    """获取指定图谱的所有关系"""
    query = """
    MATCH (source:Entity)-[r:RELATION {graph_id: $graph_id}]->(target:Entity)
    RETURN r, source.name as source_name, target.name as target_name
    ORDER BY r.relation_type
    """
    with driver.session() as session:
        result = session.run(query, graph_id=graph_id)
        relations = []
        for record in result:
            relation_data = dict(record[0])
            relation_data["source_name"] = record["source_name"]
            relation_data["target_name"] = record["target_name"]
            relations.append(relation_data)
        return relations


def get_relation_by_id(driver: Driver, relation_id: str) -> dict | None:
    """根据ID获取关系"""
    query = """
    MATCH (source:Entity)-[r:RELATION {id: $id}]->(target:Entity)
    RETURN r, source.name as source_name, target.name as target_name
    """
    with driver.session() as session:
        result = session.run(query, id=relation_id)
        record = result.single()
        if record:
            relation_data = dict(record[0])
            relation_data["source_name"] = record["source_name"]
            relation_data["target_name"] = record["target_name"]
            return relation_data
        return None


def delete_relation(driver: Driver, relation_id: str) -> bool:
    """删除关系"""
    query = """
    MATCH ()-[r:RELATION {id: $id}]-()
    DELETE r
    RETURN count(r) as deleted_count
    """
    with driver.session() as session:
        result = session.run(query, id=relation_id)
        record = result.single()
        return record["deleted_count"] > 0 if record else False

# --- 文档-实体关系 CRUD 操作 ---
def create_document_entity_relation(driver: Driver, relation: DocumentEntityRelationCreate) -> dict:
    """创建文档-实体关系"""
    with driver.session() as session:
        # 首先确保Document节点存在
        session.run(
            """
            MERGE (d:Document {id: $document_id})
            """,
            document_id=str(relation.document_id)
        )
        
        # 然后创建关系
        result = session.run(
            """
            MATCH (d:Document {id: $document_id}), (e:Entity {id: $entity_id})
            CREATE (d)-[r:HAS_ENTITY {
                id: randomUUID(),
                relation_type: $relation_type,
                created_at: datetime()
            }]->(e)
            RETURN r
            """,
            document_id=relation.document_id,  # 直接使用字符串，不需要转换
            entity_id=relation.entity_id,
            relation_type=relation.relation_type
        )
        record = result.single()
        return dict(record["r"]) if record else None

def get_entities_by_document(driver: Driver, document_id: str) -> list:
    """获取文档关联的所有实体"""
    with driver.session() as session:
        result = session.run(
            """
            MATCH (d:Document {id: $document_id})-[:HAS_ENTITY]->(e:Entity)
            RETURN e
            ORDER BY e.name
            """,
            document_id=document_id  # 直接使用字符串参数
        )
        return [dict(record["e"]) for record in result]

def get_documents_by_entity(driver: Driver, entity_id: str) -> list:
    """获取实体关联的所有文档"""
    with driver.session() as session:
        result = session.run(
            """
            MATCH (d:Document)-[:HAS_ENTITY]->(e:Entity {id: $entity_id})
            RETURN d
            ORDER BY d.created_at DESC
            """,
            entity_id=entity_id
        )
        return [dict(record["d"]) for record in result]

def create_category(driver: Driver, category: CategoryCreate, graph_id: str) -> dict:
    """在指定的父节点下创建一个新的Category节点"""
    category_id = str(uuid.uuid4())
    query = """
    // 1. 首先找到父节点 (可以是KnowledgeGraph或另一个Category)
    MATCH (parent) WHERE parent.id = $parent_id
    // 2. 创建新的Category节点，并创建与父节点的层级关系
    CREATE (parent)-[:HAS_CHILD]->(child:Category {
        id: $id,
        name: $name,
        parent_id: $parent_id,
        graph_id: $graph_id
    })
    RETURN child
    """
    with driver.session() as session:
        result = session.run(
            query,
            id=category_id,
            name=category.name,
            parent_id=category.parent_id,
            graph_id=graph_id
        )
        return result.single()[0]

def get_node_by_id(driver: Driver, node_id: str) -> dict | None:
    """根据ID查找任何一个节点"""
    query = "MATCH (n {id: $id}) RETURN n"
    with driver.session() as session:
        result = session.run(query, id=node_id)
        record = result.single()
        return dict(record[0]) if record else None


def get_knowledge_graphs(driver: Driver, skip: int = 0, limit: int = 100) -> list:
    """获取所有知识图谱列表，包含实体和关系统计"""
    query = """
    MATCH (g:KnowledgeGraph)
    OPTIONAL MATCH (e:Entity {graph_id: g.id})
    OPTIONAL MATCH ()-[r:RELATION {graph_id: g.id}]-()
    WITH g, count(DISTINCT e) as entity_count, count(DISTINCT r) as relation_count
    RETURN g, entity_count, relation_count
    ORDER BY g.name
    SKIP $skip
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, skip=skip, limit=limit)
        graphs = []
        for record in result:
            graph_data = dict(record[0])
            graph_data["entity_count"] = record["entity_count"]
            graph_data["relation_count"] = record["relation_count"]
            graphs.append(graph_data)
        return graphs

# === 新增：按图谱获取分类列表 ===

def get_categories_by_graph(driver: Driver, graph_id: str) -> list:
    """获取指定图谱下的所有分类（任意层级）"""
    query = """
    MATCH (g:KnowledgeGraph {id: $graph_id})-[:HAS_CHILD*]->(c:Category)
    RETURN DISTINCT c
    ORDER BY c.name
    """
    with driver.session() as session:
        result = session.run(query, graph_id=graph_id)
        return [dict(record[0]) for record in result]

# === 新增：获取整张图谱的子图谱（实体+边） ===

def get_graph_subgraph(driver: Driver, graph_id: str) -> dict:
    """获取某个图谱下的全部实体集合及其内部的关系列表"""
    query = """
    // 收集该图谱的所有实体
    MATCH (e:Entity {graph_id: $graph_id})
    WITH COLLECT(DISTINCT e) AS subgraph_entities
    // 在实体集合内部查找关系
    UNWIND subgraph_entities AS e1
    MATCH (e1)-[r:RELATION {graph_id: $graph_id}]-(e2)
    WHERE e2 IN subgraph_entities
    RETURN COLLECT(DISTINCT e1) AS entities,
           COLLECT(DISTINCT {relation: r, start_node: startNode(r), end_node: endNode(r)}) AS relationships
    """
    with driver.session() as session:
        result = session.run(query, graph_id=graph_id)
        record = result.single()
        if not record:
            return {"entities": [], "relationships": []}
        # 处理实体
        entity_list = []
        for e in record["entities"]:
            props = dict(e)
            processed = {}
            for k, v in props.items():
                if hasattr(v, 'iso_format'):
                    processed[k] = v.iso_format()
                elif isinstance(v, list):
                    processed[k] = [str(item) for item in v]
                else:
                    processed[k] = v
            entity_list.append({
                "id": processed.get("id", ""),
                "name": processed.get("name", ""),
                # 兼容 entity_type 与 type 两种字段
                "type": processed.get("entity_type") or processed.get("type"),
                "properties": processed
            })
        # 处理关系
        rel_list = []
        for rel_data in record["relationships"]:
            r = rel_data["relation"]
            start_node = rel_data["start_node"]
            end_node = rel_data["end_node"]
            r_props = dict(r)
            processed_r = {}
            for k, v in r_props.items():
                if hasattr(v, 'iso_format'):
                    processed_r[k] = v.iso_format()
                elif isinstance(v, list):
                    processed_r[k] = [str(item) for item in v]
                else:
                    processed_r[k] = v
            rel_list.append({
                "id": processed_r.get("id", str(getattr(r, 'id', ''))),
                # 标准化字段以兼容前端 - 优先使用属性中的relation_type
                "relation_type": processed_r.get("relation_type") or processed_r.get("type", "") or getattr(r, 'type', None) or "",
                "description": processed_r.get("description", ""),
                "source_entity_id": start_node.get("id", ""),
                "target_entity_id": end_node.get("id", ""),
                "properties": processed_r
            })
        return {"entities": entity_list, "relationships": rel_list}


def delete_knowledge_graph(driver: Driver, graph_id: str) -> bool:
    """删除知识图谱及其所有相关节点和关系"""
    query = """
    // 首先找到图谱节点
    MATCH (g:KnowledgeGraph {id: $graph_id})
    // 找到所有属于这个图谱的节点（包括分类、实体等）
    OPTIONAL MATCH (g)-[:HAS_CHILD*]->(child)
    // 删除所有相关节点和关系
    DETACH DELETE g, child
    RETURN count(g) as deleted_count
    """
    with driver.session() as session:
        result = session.run(query, graph_id=graph_id)
        record = result.single()
        return record["deleted_count"] > 0 if record else False



def create_resource_node(driver: Driver, resource: ResourceCreate, sqlite_doc_id: int) -> dict:
    """在Neo4j中创建资源节点 (Document) 并连接到其父节点"""
    resource_id = str(uuid.uuid4())
    query = """
    MATCH (parent) WHERE parent.id = $parent_id
    CREATE (parent)-[:CONTAINS_RESOURCE]->(res:Document {
        id: $id,
        filename: $filename,
        type: $type,
        graph_id: $graph_id,
        parent_id: $parent_id,
        source_document_id: $sqlite_doc_id  // 关联SQLite的ID
    })
    RETURN res
    """
    with driver.session() as session:
        result = session.run(
            query,
            id=resource_id,
            filename=resource.filename,
            type=resource.type,
            graph_id=resource.graph_id,
            parent_id=resource.parent_id,
            sqlite_doc_id=sqlite_doc_id
        )
        return result.single()[0]


def get_document_ids_by_graph(driver: Driver, graph_id: str) -> list[int]:
    """获取图谱下所有资源(Document)对应的SQLite文档ID列表"""
    query = """
    MATCH (g:KnowledgeGraph {id: $graph_id})
    OPTIONAL MATCH (g)-[:HAS_CHILD*0..]->(parent)-[:CONTAINS_RESOURCE]->(d:Document)
    WITH collect(DISTINCT d.source_document_id) AS ids
    RETURN [id IN ids WHERE id IS NOT NULL] AS doc_ids
    """
    with driver.session() as session:
        result = session.run(query, graph_id=graph_id)
        record = result.single()
        if not record:
            return []
        doc_ids = record.get("doc_ids") or []
        # 转为int类型，过滤None
        return [int(i) for i in doc_ids if i is not None]


def get_document_ids_by_category(driver: Driver, category_id: str) -> list[int]:
    """获取分类（包含其子分类）下所有资源(Document)对应的SQLite文档ID列表"""
    query = """
    MATCH (c:Category {id: $category_id})
    OPTIONAL MATCH (c)-[:HAS_CHILD*0..]->(parent)-[:CONTAINS_RESOURCE]->(d:Document)
    WITH collect(DISTINCT d.source_document_id) AS ids
    RETURN [id IN ids WHERE id IS NOT NULL] AS doc_ids
    """
    with driver.session() as session:
        result = session.run(query, category_id=category_id)
        record = result.single()
        if not record:
            return []
        doc_ids = record.get("doc_ids") or []
        return [int(i) for i in doc_ids if i is not None]