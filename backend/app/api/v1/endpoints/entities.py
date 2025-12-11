# app/api/v1/endpoints/entities.py

from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver
from neo4j.time import DateTime as Neo4jDateTime
from typing import List, Optional
from datetime import datetime
from app.api import deps
from app.schemas import entity as entity_schemas
from pydantic import BaseModel
from app.crud import crud_entity, crud_graph
from app.core.logging_config import get_logger
import asyncio
from openai import AsyncOpenAI

logger = get_logger(__name__)

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    # 手动计算以避免额外依赖
    for i in range(len(a)):
        va = float(a[i])
        vb = float(b[i])
        dot += va * vb
        na += va * va
        nb += vb * vb
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / ((na ** 0.5) * (nb ** 0.5))

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
    logger.info(f"获取实体列表: graph_id={graph_id}, skip={skip}, limit={limit}")
    try:
        entities = crud_entity.get_entities_by_graph(driver=driver, graph_id=graph_id, skip=skip, limit=limit)
        logger.info(f"成功获取 {len(entities)} 个实体")
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
        logger.error(f"获取实体列表失败: graph_id={graph_id}, error={str(e)}", exc_info=True)
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
    logger.info(f"创建实体: name={entity.name}, type={entity.entity_type}, graph_id={entity.graph_id}")
    try:
        created_entity = crud_graph.create_entity(driver=driver, entity=entity)
        logger.info(f"实体创建成功: id={created_entity['id']}, name={created_entity['name']}")
        return entity_schemas.Entity(
            id=created_entity["id"],
            name=created_entity["name"],
            entity_type=created_entity.get("entity_type", ""),
            description=created_entity.get("description", ""),
            graph_id=created_entity.get("graph_id"),
            frequency=created_entity.get("frequency", 0),
            created_at=convert_neo4j_datetime(created_entity.get("created_at")),
            updated_at=convert_neo4j_datetime(created_entity.get("updated_at")),
            chunk_ids=created_entity.get("chunk_ids", []),
            document_ids=created_entity.get("document_ids", [])
        )
    except Exception as e:
        logger.error(f"创建实体失败: name={entity.name}, error={str(e)}", exc_info=True)
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
    logger.info(f"删除实体: entity_id={entity_id}")
    try:
        success = crud_entity.delete_entity(driver=driver, entity_id=entity_id)
        if not success:
            logger.warning(f"删除实体失败 - 实体不存在: entity_id={entity_id}")
            raise HTTPException(status_code=404, detail="实体不存在")

        logger.info(f"实体删除成功: entity_id={entity_id}")
        return {"message": "实体删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除实体失败: entity_id={entity_id}, error={str(e)}", exc_info=True)
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
    logger.info(
        f"合并实体: source={merge_request.source_entity_id}, "
        f"target={merge_request.target_entity_id}, name={merge_request.merged_name}"
    )
    try:
        # 验证两个实体不能相同
        if merge_request.source_entity_id == merge_request.target_entity_id:
            logger.warning(f"合并实体失败 - 源实体和目标实体相同: {merge_request.source_entity_id}")
            raise HTTPException(status_code=400, detail="源实体和目标实体不能相同")

        # 执行合并操作
        merged_entity_data = crud_entity.merge_entities(
            driver=driver,
            source_entity_id=merge_request.source_entity_id,
            target_entity_id=merge_request.target_entity_id,
            merged_name=merge_request.merged_name,
            merged_description=merge_request.merged_description
        )

        logger.info(
            f"实体合并成功: source={merge_request.source_entity_id} -> "
            f"target={merge_request.target_entity_id}"
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
        logger.warning(f"实体合并失败 - 参数错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"实体合并失败: source={merge_request.source_entity_id}, "
            f"target={merge_request.target_entity_id}, error={str(e)}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"实体合并失败: {e}")


@router.get("/{entity_id}/subgraph", response_model=entity_schemas.EntitySubgraphResponse)
def get_entity_subgraph(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    entity_id: str,
    hops: int = 1
):
    """
    获取指定实体的x跳子图
    
    Args:
        entity_id: 实体ID
        hops: 跳数，支持1-10跳，默认为1
    
    Returns:
        包含中心实体、相关实体和关系的子图数据
    """
    try:
        # 验证跳数范围
        if hops < 1 or hops > 10:
            raise HTTPException(status_code=400, detail="跳数必须在1-10之间")
        
        # 获取子图数据
        subgraph_data = crud_entity.get_entity_subgraph(
            driver=driver,
            entity_id=entity_id,
            hops=10
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


# --- 嵌入相似度 Top-K 相似对检测 ---
class EmbeddingTopPairsRequest(BaseModel):
    graph_id: str
    top_k: int = 3
    max_entities: int = 200
    openai_base_url: Optional[str] = "http://113.249.91.14:8008/v1"

class BasicEntityInfo(BaseModel):
    id: str
    name: str
    entity_type: str
    description: Optional[str] = None
    frequency: Optional[int] = 0

class EmbeddingPairSuggestion(BaseModel):
    key: str
    entity_type: str
    a: BasicEntityInfo
    b: BasicEntityInfo
    score: float
    recommendedTargetId: str

class EmbeddingTopPairsResponse(BaseModel):
    pairs: List[EmbeddingPairSuggestion]


@router.post("/duplicates/topk-embedding", response_model=EmbeddingTopPairsResponse)
async def detect_topk_pairs_by_embedding(
    *,
    driver: Driver = Depends(deps.get_neo4j),
    req: EmbeddingTopPairsRequest
):
    """
    使用远程 OpenAI 兼容的嵌入服务，计算同类型实体之间的余弦相似度，并返回全局 Top-K 相似对。
    """
    
    # 加载实体列表（限制数量以避免过高计算负载）
    try:
        entities = crud_entity.get_entities_by_graph(driver=driver, graph_id=req.graph_id, skip=0, limit=req.max_entities)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体失败: {e}")

    # 组织同类型集合
    by_type: dict[str, list[dict]] = {}
    for ent in entities:
        t = ent.get("entity_type", "")
        by_type.setdefault(t, []).append(ent)

    # 构造需要生成嵌入的文本（名称+描述）
    def build_text(ent: dict) -> str:
        name = str(ent.get("name") or "")
        desc = str(ent.get("description") or "")
        text = name.strip()
        if desc:
            text = f"{text} {desc.strip()}"
        return text

    # 异步批量获取嵌入
    async def get_embeddings(texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
            
        client = AsyncOpenAI(
            base_url=req.openai_base_url,
            api_key="NOT_NEED"
        )
        
        try:
            # 使用 OpenAI 兼容接口批量获取 embeddings
            response = await client.embeddings.create(
                model="Embed",
                input=texts
            )
            
            # 提取向量列表，顺序与 input 一致
            return [data.embedding for data in response.data]
            
        except Exception as e:
            logger.error(f"Embedding 服务调用失败: {e}")
            raise HTTPException(status_code=500, detail=f"Embedding 服务调用失败: {e}")

    # 为每个类型分别计算相似对
    suggestions: List[EmbeddingPairSuggestion] = []
    for t, items in by_type.items():
        if len(items) < 2:
            continue
        texts = [build_text(ent) for ent in items]
        vectors = await get_embeddings(texts)

        n = len(items)
        for i in range(n):
            for j in range(i + 1, n):
                sim = _cosine_similarity(vectors[i], vectors[j])
                a = items[i]
                b = items[j]
                # 推荐目标：频次更高者（相同则选择 a）
                fa = int(a.get("frequency", 0) or 0)
                fb = int(b.get("frequency", 0) or 0)
                target_id = a.get("id") if fa >= fb else b.get("id")
                suggestions.append(
                    EmbeddingPairSuggestion(
                        key=f"{t}#{a.get('id')}-{b.get('id')}",
                        entity_type=t,
                        a=BasicEntityInfo(
                            id=str(a.get("id")),
                            name=str(a.get("name")),
                            entity_type=t,
                            description=a.get("description"),
                            frequency=fa,
                        ),
                        b=BasicEntityInfo(
                            id=str(b.get("id")),
                            name=str(b.get("name")),
                            entity_type=t,
                            description=b.get("description"),
                            frequency=fb,
                        ),
                        score=float(sim),
                        recommendedTargetId=str(target_id),
                    )
                )

    suggestions.sort(key=lambda s: s.score, reverse=True)
    top = suggestions[: max(1, req.top_k)]
    return EmbeddingTopPairsResponse(pairs=top)