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
    CREATE (g:图谱 {
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
        frequency: 1,
        created_at: datetime()
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
            chunk_ids=entity.chunk_ids or []
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


# === 关系相关操作 ===
def create_relation(driver: Driver, relation: RelationCreate) -> dict:
    """在Neo4j中创建关系"""
    relation_id = str(uuid.uuid4())
    query = """
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
    with driver.session() as session:
        result = session.run(
            query,
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
    """获取所有知识图谱列表"""
    query = """
    MATCH (g:图谱)
    RETURN g
    ORDER BY g.name
    SKIP $skip
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, skip=skip, limit=limit)
        return [dict(record[0]) for record in result]


def delete_knowledge_graph(driver: Driver, graph_id: str) -> bool:
    """删除知识图谱及其所有相关节点和关系"""
    query = """
    // 首先找到图谱节点
    MATCH (g:图谱 {id: $graph_id})
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