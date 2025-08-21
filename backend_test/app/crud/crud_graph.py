# app/crud/crud_graph.py

from neo4j import Driver
from app.schemas.graph import GraphCreate, CategoryCreate
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