# app/worker/tasks.py

from typing import List

from sqlalchemy.util import NoneType
from app.crud import crud_sqlite
from app.crud.crud_graph import create_entity, create_relation, create_document_entity_relation, create_resource_node
from app.schemas.entity import EntityCreate, RelationCreate, DocumentEntityRelationCreate
from app.schemas.resource import ResourceCreate
from app.db.sqlite_session import SessionLocal
from app.db.neo4j_session import get_neo4j_driver
import random
import time

def _run_single_document_extraction(document_id: int, db_session, neo4j_driver, graph_id: str = None, parent_id: str = None):
    """
    这是一个内部辅助函数，负责处理单个文档的完整流程。
    模拟文档分块、实体关系提取和Neo4j存储
    """
    try:
        print(f"📄 开始处理子任务：文档 ID: {document_id}")
        crud_sqlite.update_document_status(db_session, document_id=document_id, status="processing")
        
        document = crud_sqlite.get_source_document(db_session, document_id=document_id)
        if not document:
            print(f"❌ 文档 ID: {document_id} 不存在")
            return
            
        print(f"📖 文档信息: {document.filename} (文档ID: {document.id})")
        
        # === 1. 模拟文档分块 ===
        print("🔪 开始文档分块...")
        chunks = _simulate_document_chunking(document.filename)
        print(f"✅ 文档分块完成，共生成 {len(chunks)} 个分块")
        
        # === 2. 遍历分块，提取实体和关系 ===
        all_entities = {}  # 用于去重的实体字典
        all_entities_list = []  # 保存所有原始实体（包含chunk_id）
        all_relations = []
        
        for i, chunk in enumerate(chunks, 1):
            chunk_id = f"{document.id}_chunk_{i}"  # 生成分块ID
            print(f"🔍 处理第 {i} 个分块: {chunk[:50]}...")
            
            # 模拟实体提取
            entities = _simulate_entity_extraction(chunk, chunk_id)
            print(f"  📊 提取到 {len(entities)} 个实体: {[e['name'] for e in entities]}")
            
            # 模拟关系提取
            relations = _simulate_relation_extraction(entities)
            print(f"  🔗 提取到 {len(relations)} 个关系")
            
            # 收集所有原始实体（保留chunk_id信息）
            all_entities_list.extend(entities)
            
            # 收集实体（去重）
            for entity in entities:
                entity_key = f"{entity['name']}_{entity['entity_type']}"
                if entity_key not in all_entities:
                    all_entities[entity_key] = entity
                else:
                    # 增加频次
                    all_entities[entity_key]['frequency'] = all_entities[entity_key].get('frequency', 1) + 1
            
            # 收集关系
            all_relations.extend(relations)
            
            # 模拟处理延时
            time.sleep(0.5)
        
        # === 3. 实体链接与消歧（简化模拟）===
        print("🔗 开始实体链接与消歧...")
        disambiguated_entities = _simulate_entity_disambiguation(all_entities)
        print(f"✅ 实体消歧完成，最终实体数: {len(disambiguated_entities)}")
        
        # === 4. 图谱入库 ===
        print("💾 开始图谱入库...")
        
        # 验证父节点（如果提供了parent_id）
        if parent_id:
            from app.crud.crud_graph import get_node_by_id
            parent_node = get_node_by_id(driver=neo4j_driver, node_id=parent_id)
            if not parent_node:
                print(f"❌ 父节点 ID '{parent_id}' 不存在，跳过文档 {document.filename}")
                return
            if parent_node.get("graph_id") != graph_id:
                print(f"❌ 父节点不属于当前图谱，跳过文档 {document.filename}")
                return
        
        # 从数据库获取文档信息，包括资源类型
        document = crud_sqlite.get_source_document(db=db_session, document_id=document_id)
        if not document:
            print(f"❌ 文档 ID {document_id} 不存在")
            return
        
        # 首先创建文档资源节点
        # 直接使用数据库中的resource_type字符串值
        resource_create = ResourceCreate(
            filename=document.filename,
            content=document.content,
            type=document.resource_type,
            graph_id=graph_id or "default-graph-id",
            parent_id=parent_id or graph_id or "default-graph-id"
        )
        created_resource = create_resource_node(neo4j_driver, resource_create, document.id)
        print(f"  ✅ 创建文档资源节点: {document.filename} (ID: {created_resource['id']})")
        
        # 更新文档-实体关系中使用的文档ID为Neo4j中的资源节点ID
        neo4j_document_id = created_resource['id']
        
        entity_id_mapping = {}
        
        # 4.1 创建实体节点
        for entity_data in disambiguated_entities.values():
            # 收集该实体的所有chunk_ids
            chunk_ids = []
            for orig_entity in all_entities_list:
                if orig_entity["name"] == entity_data["name"] and orig_entity.get("chunk_id"):
                    chunk_ids.append(orig_entity["chunk_id"])
            
            entity_create = EntityCreate(
                name=entity_data['name'],
                entity_type=entity_data['entity_type'],
                description=entity_data.get('description'),
                graph_id=graph_id or "default-graph-id",
                chunk_ids=list(set(chunk_ids)),  # 去重
                document_id=document.id
            )
            
            try:
                created_entity = create_entity(neo4j_driver, entity_create)
                entity_id_mapping[f"{entity_data['name']}_{entity_data['entity_type']}"] = created_entity['id']
                print(f"  ✅ 创建实体: {entity_data['name']} ({entity_data['entity_type']}) - 分块: {chunk_ids}")
                
                # 创建文档-实体关系（使用Neo4j资源节点ID）
                doc_entity_relation = DocumentEntityRelationCreate(
                    document_id=neo4j_document_id,  # 直接使用Neo4j资源节点的UUID
                    entity_id=created_entity["id"],
                    relation_type="HAS_ENTITY"
                )
                create_document_entity_relation(neo4j_driver, doc_entity_relation)
            except Exception as e:
                print(f"  ❌ 创建实体失败: {entity_data['name']} - {e}")
        
        # 4.2 创建关系
        created_relations_count = 0
        for relation_data in all_relations:
            source_key = f"{relation_data['source_name']}_{relation_data['source_type']}"
            target_key = f"{relation_data['target_name']}_{relation_data['target_type']}"
            
            if source_key in entity_id_mapping and target_key in entity_id_mapping:
                relation_create = RelationCreate(
                    source_entity_id=entity_id_mapping[source_key],
                    target_entity_id=entity_id_mapping[target_key],
                    relation_type=relation_data['relation_type'],
                    description=relation_data.get('description'),
                    confidence=relation_data.get('confidence', 0.8),
                    graph_id=graph_id or "default-graph-id"
                )
                
                try:
                    created_relation = create_relation(neo4j_driver, relation_create)
                    if created_relation:
                        created_relations_count += 1
                        print(f"  ✅ 创建关系: {relation_data['source_name']} -[{relation_data['relation_type']}]-> {relation_data['target_name']}")
                except Exception as e:
                    print(f"  ❌ 创建关系失败: {relation_data['source_name']} -> {relation_data['target_name']} - {e}")
        
        print(f"💾 图谱入库完成！创建了 {len(entity_id_mapping)} 个实体，{created_relations_count} 个关系")
        
        crud_sqlite.update_document_status(db_session, document_id=document_id, status="completed")
        print(f"🎉 子任务成功：文档 ID: {document_id} 处理完毕！")
        
    except Exception as e:
        crud_sqlite.update_document_status(db_session, document_id=document_id, status="failed")
        print(f"❌ 子任务失败：处理文档 ID: {document_id} 时发生错误: {e}")
        import traceback
        traceback.print_exc()
        # 可以选择在这里抛出异常来中断整个批处理，或者继续处理下一个
        # raise e 

def run_batch_knowledge_extraction(document_ids: List[int], graph_id: str = NoneType, parent_id: str = None):
    """
    这是新的、在后台运行的【批量】知识提取主函数。
    它会按顺序串行处理列表中的每一个文档。
    
    Args:
        document_ids: 文档ID列表
        graph_id: 图谱ID
        parent_id: 父节点ID
        resource_type: 资源类型
    """
    print(f"批量后台任务启动：准备处理 {len(document_ids)} 个文档。")
    
    db_session = SessionLocal()
    neo4j_driver_instance = get_neo4j_driver()

    try:
        # 在一个任务中，按顺序循环处理每个文档
        for doc_id in document_ids:
            _run_single_document_extraction(
                document_id=doc_id,
                db_session=db_session,
                neo4j_driver=neo4j_driver_instance,
                graph_id=graph_id,
                parent_id=parent_id
            )
        
        print(f"批量后台任务成功：所有文档处理完毕。")

    except Exception as e:
        print(f"批量后台任务因某个子任务失败而中断: {e}")
    finally:
        db_session.close()


# === 模拟函数实现 ===
def _simulate_document_chunking(document_title: str) -> List[str]:
    """模拟文档分块，根据文档标题生成两个模拟分块"""
    chunks = [
        f"这是关于{document_title}的第一部分内容。在这个部分中，我们讨论了人工智能技术的发展历程，包括机器学习、深度学习等核心概念。人工智能已经成为现代科技发展的重要驱动力，在各个领域都有广泛的应用。",
        f"这是关于{document_title}的第二部分内容。本部分重点介绍了知识图谱技术在人工智能领域的应用。知识图谱通过实体和关系的结构化表示，能够有效地组织和管理大规模的知识信息，为智能系统提供强大的推理能力。"
    ]
    return chunks


def _simulate_entity_extraction(chunk_text: str, chunk_id: str = None) -> List[dict]:
    """模拟实体提取，根据分块内容返回模拟的实体列表"""
    # 根据分块内容的关键词来生成不同的实体
    entities = []
    
    if "人工智能" in chunk_text:
        entities.extend([
            {"name": "人工智能", "entity_type": "技术领域", "description": "模拟人类智能的技术", "frequency": 1, "chunk_id": chunk_id},
            {"name": "机器学习", "entity_type": "技术方法", "description": "让机器从数据中学习的方法", "frequency": 1, "chunk_id": chunk_id},
            {"name": "深度学习", "entity_type": "技术方法", "description": "基于神经网络的学习方法", "frequency": 1, "chunk_id": chunk_id}
        ])
    
    if "知识图谱" in chunk_text:
        entities.extend([
            {"name": "知识图谱", "entity_type": "技术领域", "description": "结构化知识表示方法", "frequency": 1, "chunk_id": chunk_id},
            {"name": "实体", "entity_type": "概念", "description": "知识图谱中的基本单元", "frequency": 1, "chunk_id": chunk_id},
            {"name": "关系", "entity_type": "概念", "description": "实体之间的连接", "frequency": 1, "chunk_id": chunk_id},
            {"name": "推理能力", "entity_type": "能力", "description": "基于知识进行逻辑推理的能力", "frequency": 1, "chunk_id": chunk_id}
        ])
    
    # 添加一些通用实体
    common_entities = [
        {"name": "科技发展", "entity_type": "概念", "description": "技术进步的过程", "frequency": 1, "chunk_id": chunk_id},
        {"name": "智能系统", "entity_type": "系统", "description": "具有智能特征的计算机系统", "frequency": 1, "chunk_id": chunk_id}
    ]
    entities.extend(common_entities)
    
    # 随机选择3-5个实体返回
    selected_count = random.randint(3, min(5, len(entities)))
    return random.sample(entities, selected_count)


def _simulate_relation_extraction(entities: List[dict]) -> List[dict]:
    """模拟关系提取，根据实体列表生成模拟的关系"""
    relations = []
    
    if len(entities) < 2:
        return relations
    
    # 预定义一些关系类型
    relation_types = [
        "包含", "属于", "应用于", "基于", "促进", "实现", "支持", "依赖"
    ]
    
    # 生成1-3个关系
    num_relations = random.randint(1, min(3, len(entities) - 1))
    
    for i in range(num_relations):
        # 随机选择两个不同的实体
        source_entity = random.choice(entities)
        target_entity = random.choice([e for e in entities if e != source_entity])
        
        relation = {
            "source_name": source_entity["name"],
            "source_type": source_entity["entity_type"],
            "target_name": target_entity["name"],
            "target_type": target_entity["entity_type"],
            "relation_type": random.choice(relation_types),
            "description": f"{source_entity['name']}与{target_entity['name']}之间的关系",
            "confidence": round(random.uniform(0.7, 0.95), 2)
        }
        relations.append(relation)
    
    return relations


def _simulate_entity_disambiguation(entities_dict: dict) -> dict:
    """模拟实体消歧，简化处理，主要是合并相似实体"""
    # 在实际应用中，这里会进行复杂的实体链接和消歧
    # 这里简化处理，只是返回原始实体字典
    disambiguated = {}
    
    for key, entity in entities_dict.items():
        # 简单的消歧逻辑：如果实体名称相似，合并频次
        found_similar = False
        for existing_key, existing_entity in disambiguated.items():
            if (
                entity["name"].lower() == existing_entity["name"].lower() and 
                entity["entity_type"] == existing_entity["entity_type"]
            ):
                # 合并频次
                existing_entity["frequency"] += entity.get("frequency", 1)
                found_similar = True
                break
        
        if not found_similar:
            disambiguated[key] = entity.copy()
    
    return disambiguated