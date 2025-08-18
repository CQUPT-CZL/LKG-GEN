import os
import json
from collections import defaultdict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config
from .utils import call_llm, load_json, save_json, load_prompt
from difflib import SequenceMatcher
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import tqdm

def calculate_similarity(text1, text2):
    """计算两个文本的相似度"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def group_entities_by_type(entities):
    """按实体类型分组"""
    type_groups = defaultdict(list)
    for entity in entities:
        type_groups[entity["entity_type"]].append(entity)
    return type_groups

def find_similar_entities(entities, similarity_threshold=0.6):
    """基于文本相似度预筛选可能需要合并的实体组"""
    similar_groups = []
    processed = set()
    
    for i, entity1 in enumerate(entities):
        if i in processed:
            continue
            
        current_group = [entity1]
        processed.add(i)
        
        for j, entity2 in enumerate(entities[i+1:], i+1):
            if j in processed:
                continue
                
            similarity = calculate_similarity(entity1["entity_text"], entity2["entity_text"])
            if similarity >= similarity_threshold:
                current_group.append(entity2)
                processed.add(j)
        
        similar_groups.append(current_group)
    
    return similar_groups

def smart_entity_filtering(entities, min_frequency=2):
    """智能实体筛选：优先处理高频实体，过滤噪声"""
    # 统计实体频率（基于chunk_id数量）
    entity_freq = {}
    for entity in entities:
        text = entity["entity_text"]
        freq = len(entity.get("chunk_id", []))
        if text in entity_freq:
            entity_freq[text] += freq
        else:
            entity_freq[text] = freq
    
    # 按频率分组
    high_freq_entities = []
    low_freq_entities = []
    
    for entity in entities:
        text = entity["entity_text"]
        if entity_freq[text] >= min_frequency:
            high_freq_entities.append(entity)
        else:
            low_freq_entities.append(entity)
    
    print(f"   📊 实体筛选: 高频实体 {len(high_freq_entities)} 个，低频实体 {len(low_freq_entities)} 个")
    
    return high_freq_entities, low_freq_entities

def disambiguate_entities_with_llm(entity_list: list, max_entities_per_batch=20):
    """
    使用LLM对实体列表进行分批聚类消歧。
    采用分批处理策略避免上下文过长导致的效果下降。
    """
    if len(entity_list) <= max_entities_per_batch:
        # 如果实体数量不多，直接处理
        return _process_single_batch(entity_list)
    
    print(f"🔄 实体数量较多({len(entity_list)})，采用分批处理策略...")
    
    # 1. 按相似度预分组
    similar_groups = find_similar_entities(entity_list, similarity_threshold=0.6)
    print(f"📊 基于相似度预分组，得到 {len(similar_groups)} 个候选组")
    
    all_clusters = []
    
    # 2. 对每个相似组进行处理
    for i, group in enumerate(tqdm.tqdm(similar_groups, desc="处理相似组")):
        if len(group) == 1:
            # 单个实体，无需聚类
            continue
        elif len(group) <= max_entities_per_batch:
            # 组内实体数量适中，直接处理
            batch_clusters = _process_single_batch(group)
            if batch_clusters:
                all_clusters.extend(batch_clusters)
        else:
            # 组内实体过多，进一步分批
            for j in range(0, len(group), max_entities_per_batch):
                batch = group[j:j + max_entities_per_batch]
                batch_clusters = _process_single_batch(batch)
                if batch_clusters:
                    all_clusters.extend(batch_clusters)
    
    return all_clusters

def _process_single_batch(entity_list: list):
    """
    处理单个批次的实体聚类
    """
    if len(entity_list) <= 1:
        return None
        
    try:
        prompt_template = load_prompt(config.DISAMBIGUATION_PROMPT_PATH)
        
        # 为了让Prompt更简洁，可以只发送必要的字段给LLM
        simplified_entities = [
            {"entity_text": e["entity_text"], "entity_description": e["entity_description"]} 
            for e in entity_list
        ]
        prompt = prompt_template.replace("{{ENTITY_LIST_JSON}}", json.dumps(simplified_entities, ensure_ascii=False, indent=2))
        
        llm_response = call_llm(prompt, model_name="qwen-plus-latest")
        
        # 关键：我们期望的输出是包含 "clusters" 键的字典
        if llm_response and "clusters" in llm_response and isinstance(llm_response["clusters"], list):
            return llm_response["clusters"]
        else:
            print(f"⚠️ LLM返回格式不正确，批次大小: {len(entity_list)}")
            return None
    except Exception as e:
        print(f"❌ 处理批次时出错: {e}")
        return None

def process_llm_clusters(original_entities: list, clusters: list):
    """
    根据LLM返回的聚类结果，精确地合并原始实体列表，特别是chunk_id。
    """
    if not clusters:
        print("没有聚类信息，返回原始实体列表。")
        return original_entities

    print("🔧 正在根据聚类配方，在Python中精确合并实体...")
    
    final_entities = []
    # 创建一个从 entity_text 到其完整对象的映射，支持一个text对应多个对象（因为输入中可能有重复）
    entity_map = defaultdict(list)
    for e in original_entities:
        entity_map[e["entity_text"]].append(e)

    processed_texts = set()

    for cluster in clusters:
        aliases = cluster.get("aliases", [])
        canonical_name = cluster.get("canonical_name")

        if not aliases or not canonical_name:
            continue
        
        # 确保规范名称本身也在别名列表中，便于处理
        if canonical_name not in aliases:
            aliases.append(canonical_name)

        merged_chunk_ids = set()
        
        # 找到规范名称对应的那个实体，以它的类型和描述为准
        # 优先使用与canonical_name完全匹配的实体作为模板
        canonical_entity_template = entity_map.get(canonical_name, [None])[0]
        if not canonical_entity_template:
            # 如果LLM生成的规范名不在原文中，就用别名列表里的第一个
            canonical_entity_template = entity_map.get(aliases[0], [None])[0]
            if not canonical_entity_template: continue # 极端情况，跳过

        for alias in aliases:
            # 一个别名可能对应多个实体对象（例如 "炼铁系统" 在原文出现多次）
            if alias in entity_map:
                for entity_obj in entity_map[alias]:
                    merged_chunk_ids.update(entity_obj["chunk_id"])
                processed_texts.add(alias)
        
        # 创建合并后的新实体
        new_entity = {
            "entity_text": canonical_name,
            "entity_type": canonical_entity_template["entity_type"],
            "entity_description": canonical_entity_template["entity_description"],
            "chunk_id": sorted(list(merged_chunk_ids)), # 合并并排序chunk_id
            "aliases": aliases 
        }
        final_entities.append(new_entity)

    # 添加那些未被聚类的独立实体
    for entity_text, entity_objects in entity_map.items():
        if entity_text not in processed_texts:
            # 即使是独立实体，也可能在原文出现多次，需要合并其chunk_id
            merged_chunk_ids = set()
            for entity_obj in entity_objects:
                merged_chunk_ids.update(entity_obj["chunk_id"])
            
            # 使用第一个对象作为模板
            template_obj = entity_objects[0].copy()  # 创建副本避免修改原对象
            template_obj["chunk_id"] = sorted(list(merged_chunk_ids))
            final_entities.append(template_obj)

    print(f"✅ 实体合并完成。原始实体数: {len(original_entities)}, 合并后实体数: {len(final_entities)}")
    return final_entities

def run_disambiguate_on_all_files():
    """对整个目录下的所有NER文件进行实体消歧，采用分类型分批处理策略"""
    print("🚀 开始智能实体消歧处理...")
    
    # 收集所有文件的实体
    all_entities = []
    processed_files = []
    
    # 遍历所有NER输出文件
    for filename in os.listdir(config.NER_OUTPUT_DIR):
        if filename.endswith(".json"):
            input_path = os.path.join(config.NER_OUTPUT_DIR, filename)
            print(f"📄 正在加载文件: {filename}")
            
            entities = load_json(input_path)
            if entities:
                all_entities.extend(entities)
                processed_files.append(filename)
                print(f"✅ 从 {filename} 加载了 {len(entities)} 个实体")
            else:
                print(f"⚠️ 文件 {filename} 实体数据为空，跳过")
    
    if not all_entities:
        print("❌ 没有找到任何实体数据")
        return None
    
    print(f"📊 总共收集到 {len(all_entities)} 个实体，来自 {len(processed_files)} 个文件")
    
    # 1. 按实体类型分组处理
    print("🔍 按实体类型分组处理...")
    type_groups = group_entities_by_type(all_entities)
    
    print(f"📋 发现 {len(type_groups)} 种实体类型:")
    for entity_type, entities in type_groups.items():
        print(f"   🏷️ {entity_type}: {len(entities)} 个实体")
    
    # 2. 分类型进行消歧处理
    all_clusters = []
    type_stats = {}
    
    for entity_type, entities in type_groups.items():
         print(f"\n🔄 正在处理类型: {entity_type} ({len(entities)} 个实体)")
         
         if len(entities) <= 1:
             print(f"   ⏭️ 实体数量过少，跳过消歧")
             type_stats[entity_type] = {"original": len(entities), "clusters": 0, "processed": len(entities)}
             continue
         
         # 智能筛选：优先处理高频实体
         high_freq_entities, low_freq_entities = smart_entity_filtering(entities, min_frequency=2)
         
         type_clusters = []
         
         # 优先处理高频实体（更可能需要消歧）
         if high_freq_entities:
             print(f"   🎯 优先处理高频实体 ({len(high_freq_entities)} 个)")
             high_freq_clusters = disambiguate_entities_with_llm(high_freq_entities, max_entities_per_batch=12)
             if high_freq_clusters:
                 type_clusters.extend(high_freq_clusters)
                 print(f"   ✅ 高频实体生成了 {len(high_freq_clusters)} 个聚类")
         
         # 处理低频实体（批量较大，减少API调用）
         if low_freq_entities and len(low_freq_entities) >= 3:  # 只有足够数量才处理
             print(f"   🔍 处理低频实体 ({len(low_freq_entities)} 个)")
             low_freq_clusters = disambiguate_entities_with_llm(low_freq_entities, max_entities_per_batch=20)
             if low_freq_clusters:
                 type_clusters.extend(low_freq_clusters)
                 print(f"   ✅ 低频实体生成了 {len(low_freq_clusters)} 个聚类")
         
         if type_clusters:
             all_clusters.extend(type_clusters)
             type_stats[entity_type] = {
                 "original": len(entities), 
                 "clusters": len(type_clusters), 
                 "high_freq": len(high_freq_entities),
                 "low_freq": len(low_freq_entities)
             }
             print(f"   🎉 类型 {entity_type} 总共生成了 {len(type_clusters)} 个聚类")
         else:
             print(f"   ⚠️ 该类型未生成有效聚类")
             type_stats[entity_type] = {
                 "original": len(entities), 
                 "clusters": 0, 
                 "high_freq": len(high_freq_entities),
                 "low_freq": len(low_freq_entities)
             }
    
    # 3. 在Python中根据所有聚类配方进行处理
    print(f"\n🔧 正在根据 {len(all_clusters)} 个聚类结果合并实体...")
    final_disambiguated_entities = process_llm_clusters(all_entities, all_clusters)
    
    # 4. 保存合并后的结果到单个文件
    output_filepath = os.path.join(config.NER_PRO_OUTPUT_DIR, "all_entities_disambiguated.json")
    save_json(final_disambiguated_entities, output_filepath)
    
    # 5. 输出详细统计信息
    print(f"\n" + "="*60)
    print(f"🎉 实体消歧处理完成！")
    print(f"📈 总体统计:")
    print(f"   📄 处理文件数: {len(processed_files)}")
    print(f"   🏷️ 原始实体数: {len(all_entities)}")
    print(f"   🔗 消歧后实体数: {len(final_disambiguated_entities)}")
    print(f"   📉 压缩率: {(1 - len(final_disambiguated_entities)/len(all_entities))*100:.1f}%")
    print(f"   💾 结果保存到: {output_filepath}")
    
    print(f"\n📊 分类型详细统计:")
    for entity_type, stats in type_stats.items():
        if 'high_freq' in stats:
            print(f"   🏷️ {entity_type}: {stats['original']} 个实体 → {stats['clusters']} 个聚类")
            print(f"      📈 高频: {stats['high_freq']} 个, 低频: {stats['low_freq']} 个")
        else:
            print(f"   🏷️ {entity_type}: {stats['original']} 个实体 → {stats['clusters']} 个聚类")
    print("="*60)
    
    return output_filepath

def simple_entity_disambiguation(entities):
    """简化版实体消歧，用于快速处理"""
    return run_disambiguate_on_all_files()

def ensure_output_files_exist():
    """确保输出目录存在"""
    directories = [
        config.DATA_DIR,
        config.RAW_PAPERS_DIR,
        config.PROCESSED_TEXT_DIR,
        config.CHUNK_OUTPUT_DIR,
        config.NER_OUTPUT_DIR,
        config.NER_PRO_OUTPUT_DIR,
        config.RE_OUTPUT_DIR,
        config.GRAPH_TRIPLES_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ 所有必要的输出目录已创建")

if __name__ == "__main__":
    # 确保输出目录存在
    ensure_output_files_exist()
    
    # 处理所有文件并合并结果
    result = run_disambiguate_on_all_files()
    
    if result:
        print("\n🎉 所有NER文件的实体消歧处理完成！")
    else:
        print("\n❌ 实体消歧处理失败！")