# app/worker/tasks.py

from typing import List

from app.crud import crud_sqlite
from app.crud.crud_sqlite import create_text_chunk
from app.crud.crud_graph import create_entity, create_relation, create_document_entity_relation, create_resource_node, update_entity, get_entity_by_id
from app.schemas.entity import EntityCreate, RelationCreate, DocumentEntityRelationCreate
from app.schemas.resource import ResourceCreate
from app.db.sqlite_session import SessionLocal
from app.db.neo4j_session import get_neo4j_driver
from app.core.chunker import chunk_document_by_strategy, ChunkStrategy
from app.crud.crud_system_config import crud_system_config
from app.core.entity_extractor import extract_entities_from_chunk
from app.core.relation_extractor import extract_relations_from_entities
from app.core.document_cleaner import clean_document_content
import time
from app.core.disambiguation import disambiguate_entities_against_graph

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
        
        # === 1. 文档内容净化 ===
        print("🧹 开始文档内容净化...")
        cleaned_content = clean_document_content(document.content)
        print(f"✅ 文档内容净化完成，净化后长度: {len(cleaned_content)} 字符")
        # print(cleaned_content)
        
        # === 2. 真实文档分块 ===
        print("🔪 开始文档分块...")
        
        # 获取当前配置的分块策略
        strategy_str = crud_system_config.get_chunk_strategy(db_session)
        strategy = ChunkStrategy(strategy_str)
        print(f"📋 使用分块策略: {strategy.value}")
        
        chunks = chunk_document_by_strategy(cleaned_content, strategy)
        print(f"✅ 文档分块完成，共生成 {len(chunks)} 个分块")
        
        # === 3. 保存分块到SQLite数据库并提取实体 ===
        all_entities = {}  # 用于去重的实体字典
        all_entities_list = []  # 保存所有原始实体（包含chunk_id）
        chunk_entities_map = {}  # 保存每个chunk对应的实体列表
        
        # 第一阶段：对所有chunk进行实体提取
        print("📊 第一阶段：开始实体提取...")
        for i, chunk in enumerate(chunks, 1):
            chunk_id = f"{document.id}_chunk_{i}"  # 生成分块ID
            print(f"🔍 处理第 {i} 个分块: {chunk[:50]}...")
            
            # 💾 保存分块到SQLite数据库
            try:
                saved_chunk = create_text_chunk(
                    db=db_session,
                    document_id=document.id,
                    chunk_text=chunk,
                    chunk_index=i
                )
                print(f"  💾 分块已保存到数据库，分块ID: {saved_chunk.id}")
            except Exception as e:
                print(f"  ❌ 保存分块到数据库失败: {e}")
                # 继续处理，不因为保存失败而中断整个流程
            
            # 实体提取
            entities = extract_entities_from_chunk(chunk, chunk_id)
            print(f"  📊 提取到 {len(entities)} 个实体: {[e.get('text', e.get('name', '未知')) for e in entities]}")
            
            # 保存该chunk的实体列表
            chunk_entities_map[chunk_id] = {
                'entities': entities,
                'chunk_text': chunk
            }
            
            # 收集所有原始实体（保留chunk_id信息）
            all_entities_list.extend(entities)
            
            # 收集实体（去重）
            for entity in entities:
                entity_key = f"{entity.get('text', entity.get('name', '未知'))}_{entity.get('type', entity.get('entity_type', '未知'))}"
                if entity_key not in all_entities:
                    all_entities[entity_key] = entity
                else:
                    # 增加频次
                    all_entities[entity_key]['frequency'] = all_entities[entity_key].get('frequency', 1) + 1
        
        # 第二阶段：对每个chunk进行关系提取
        print("🔗 第二阶段：开始关系提取...")
        all_relations = []
        for chunk_id, chunk_data in chunk_entities_map.items():
            entities = chunk_data['entities']
            chunk_text = chunk_data['chunk_text']
            
            if len(entities) >= 2:  # 只有当chunk中有2个或以上实体时才进行关系提取
                 print(f"🔍 为 {chunk_id} 提取关系，实体数: {len(entities)}")
                 relations = extract_relations_from_entities(entities, chunk_text)
                 print(f"  🔗 提取到 {len(relations)} 个关系")
                 all_relations.extend(relations)
            else:
                print(f"⚠️ {chunk_id} 实体数不足，跳过关系提取")
            
        
        # === 3. 实体链接与消歧 ===
        print("🔗 开始实体链接与消歧(全图谱范围)...")
        disambiguated_entities = disambiguate_entities_against_graph(all_entities, neo4j_driver, graph_id)
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
        
        # 4.1 创建实体节点（若已存在，则不重复创建，只建立文档关系）
        for entity_data in disambiguated_entities.values():
            # 收集该实体的所有chunk_ids
            chunk_ids = []
            for orig_entity in all_entities_list:
                orig_name = orig_entity.get('text', orig_entity.get('name', ''))
                entity_name = entity_data.get('text', entity_data.get('name', ''))
                if orig_name == entity_name and orig_entity.get("chunk_id"):
                    chunk_ids.append(orig_entity["chunk_id"])
            
            existing_id = entity_data.get('existing_id')
            entity_name = entity_data.get('text', entity_data.get('name', '未知'))
            entity_type = entity_data.get('type', entity_data.get('entity_type', '未知'))

            if existing_id:
                # 已存在：更新实体的chunk_ids和document_ids，然后建立文档-实体关系
                entity_id_mapping[f"{entity_name}_{entity_type}"] = existing_id
                print(f"  ♻️ 复用已有实体: {entity_name} ({entity_type}) -> {existing_id}")
                
                try:
                    # 先获取现有实体的信息，特别是已有的document_ids
                    existing_entity = get_entity_by_id(neo4j_driver, existing_id)
                    existing_document_ids = existing_entity.get('document_ids', []) if existing_entity else []
                    
                    # 合并document_ids：现有的 + 当前文档ID
                    merged_document_ids = existing_document_ids + [document.id]
                    
                    # 更新现有实体的chunk_ids和document_ids
                    updated_entity = update_entity(
                        neo4j_driver, 
                        existing_id, 
                        new_chunk_ids=chunk_ids,
                        new_document_ids=[document.id],  # 只传递新的document_id，让update_entity函数处理合并
                        frequency=entity_data.get('frequency', 1)
                    )
                    if updated_entity:
                        print(f"  ✅ 更新实体成功: {entity_name} - 新增分块: {chunk_ids}, 文档IDs: {merged_document_ids}")
                    else:
                        print(f"  ⚠️ 更新实体失败: {entity_name}")
                    
                    # 建立文档-实体关系
                    doc_entity_relation = DocumentEntityRelationCreate(
                        document_id=neo4j_document_id,
                        entity_id=existing_id,
                        relation_type="HAS_ENTITY"
                    )
                    create_document_entity_relation(neo4j_driver, doc_entity_relation)
                except Exception as e:
                    print(f"  ❌ 更新实体或建立文档-实体关系失败(已有实体): {entity_name} - {e}")
                continue

            # 否则创建新实体
            entity_create = EntityCreate(
                name=entity_name,
                entity_type=entity_type,
                description=entity_data.get('description'),
                graph_id=graph_id or "default-graph-id",
                chunk_ids=list(set(chunk_ids)),  # 去重
                document_ids=[document.id],
                frequency=entity_data.get('frequency', 1)
            )
            
            try:
                created_entity = create_entity(neo4j_driver, entity_create)
                entity_id_mapping[f"{entity_name}_{entity_type}"] = created_entity['id']
                print(f"  ✅ 创建实体: {entity_name} ({entity_type}) - 分块: {chunk_ids}")
                
                # 创建文档-实体关系（使用Neo4j资源节点ID）
                doc_entity_relation = DocumentEntityRelationCreate(
                    document_id=neo4j_document_id,  # 直接使用Neo4j资源节点的UUID
                    entity_id=created_entity["id"],
                    relation_type="HAS_ENTITY"
                )
                create_document_entity_relation(neo4j_driver, doc_entity_relation)
            except Exception as e:
                print(f"  ❌ 创建实体失败: {entity_name} - {e}")
        
        # 4.2 创建关系
        created_relations_count = 0
        for relation_data in all_relations:
            # 通过实体名称查找对应的实体类型
            source_name = relation_data['source_name']
            target_name = relation_data['target_name']
            
            # 在disambiguated_entities中查找匹配的实体
            source_entity = None
            target_entity = None
            
            for entity_key, entity_data in disambiguated_entities.items():
                entity_name = entity_data.get('text', entity_data.get('name', ''))
                if entity_name == source_name:
                    source_entity = entity_data
                elif entity_name == target_name:
                    target_entity = entity_data
            
            if source_entity and target_entity:
                source_type = source_entity.get('type', source_entity.get('entity_type', '未知'))
                target_type = target_entity.get('type', target_entity.get('entity_type', '未知'))
                
                source_key = f"{source_name}_{source_type}"
                target_key = f"{target_name}_{target_type}"
                
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
            else:
                print(f"  ⚠️ 跳过关系（实体未找到）: {source_name} -> {target_name}")
        
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

def run_batch_knowledge_extraction(document_ids: List[int], graph_id: str = None, parent_id: str = None):
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