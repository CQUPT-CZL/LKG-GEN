# app/services/graph_service.py

from neo4j import Driver
from app.crud import crud_graph
from app.schemas.graph import GraphCreate, CategoryCreate
from app.core.logging_config import get_logger
from fastapi import HTTPException

logger = get_logger(__name__)

def create_new_graph(driver: Driver, graph: GraphCreate) -> dict:
    """业务逻辑：创建一个新的图谱项目"""
    logger.info(f"创建新图谱: name={graph.name}")
    try:
        result = crud_graph.create_knowledge_graph(driver=driver, graph=graph)
        logger.info(f"图谱创建成功: id={result['id']}, name={result['name']}")
        return result
    except Exception as e:
        logger.error(f"创建图谱失败: name={graph.name}, error={str(e)}", exc_info=True)
        raise

def create_new_category(driver: Driver, category: CategoryCreate, graph_id: str) -> dict:
    """业务逻辑：创建一个新的分类"""
    logger.info(f"创建新分类: name={category.name}, parent_id={category.parent_id}, graph_id={graph_id}")
    try:
        # 业务检查：确保父节点是真实存在的
        parent_node = crud_graph.get_node_by_id(driver=driver, node_id=category.parent_id)
        if not parent_node:
            logger.warning(f"创建分类失败 - 父节点不存在: parent_id={category.parent_id}")
            raise HTTPException(status_code=404, detail="父节点不存在")

        # 业务检查：确保父节点属于当前操作的图谱
        if parent_node.get("graph_id") != graph_id:
            logger.warning(
                f"创建分类失败 - 跨图谱操作: parent_graph_id={parent_node.get('graph_id')}, "
                f"target_graph_id={graph_id}"
            )
            raise HTTPException(status_code=400, detail="不能跨图谱创建子分类")

        result = crud_graph.create_category(driver=driver, category=category, graph_id=graph_id)
        logger.info(f"分类创建成功: id={result['id']}, name={result['name']}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"创建分类失败: name={category.name}, parent_id={category.parent_id}, error={str(e)}",
            exc_info=True
        )
        raise