# 02_scripts/step2.5_disambiguate.py

import os
import json
from collections import defaultdict
import config
from utils import call_llm, load_json, save_json, load_prompt

def disambiguate_entities_with_llm(entity_list: list):
    """
    使用LLM对整个文档的实体列表进行聚类。
    它的任务是返回聚类的“配方”，而不是最终结果。
    """
    print("正在准备Prompt，调用LLM获取实体聚类配方...")
    
    prompt_template = load_prompt(os.path.join(config.BASE_DIR, "prompts", "disambiguation_prompt.txt"))
    
    # 为了让Prompt更简洁，可以只发送必要的字段给LLM
    simplified_entities = [
        {"entity_text": e["entity_text"], "entity_description": e["entity_description"]} 
        for e in entity_list
    ]
    prompt = prompt_template.replace("{{ENTITY_LIST_JSON}}", json.dumps(simplified_entities, ensure_ascii=False, indent=2))
    
    llm_response = call_llm(prompt, model_name="qwen-plus-latest")
    
    # 关键：我们期望的输出是包含 "clusters" 键的字典
    if llm_response and "clusters" in llm_response and isinstance(llm_response["clusters"], list):
        print("成功从LLM获取聚类结果。")
        return llm_response["clusters"]
    else:
        print("警告: LLM返回的格式不正确或为空。无法进行聚类。")
        print("LLM返回内容:", llm_response)
        return None

def process_llm_clusters(original_entities: list, clusters: list):
    """
    根据LLM返回的聚类结果，精确地合并原始实体列表，特别是chunk_id。
    """
    if not clusters:
        print("没有聚类信息，返回原始实体列表。")
        return original_entities

    print("正在根据聚类配方，在Python中精确合并实体...")
    
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
            "chunk_id": sorted(list(merged_chunk_ids), key=lambda x: int(x)), # 合并并按数字大小排序chunk_id
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
            template_obj = entity_objects[0]
            template_obj["chunk_id"] = sorted(list(merged_chunk_ids), key=lambda x: int(x))
            final_entities.append(template_obj)

    print(f"实体合并完成。原始实体数: {len(original_entities)}, 合并后实体数: {len(final_entities)}")
    return final_entities


def run_disambiguate_on_file(input_filepath):
    """对单个NER文件进行实体消歧"""
    print(f"正在处理文件: {input_filepath}")
    
    entities = load_json(input_filepath)
    if not entities:
        print("实体数据为空，跳过。")
        return

    # 1. 调用LLM获取聚类“配方”
    clusters_recipe = disambiguate_entities_with_llm(entities)
    
    # 2. 在Python中根据配方进行处理
    final_disambiguated_entities = process_llm_clusters(entities, clusters_recipe)
    
    # 3. 保存结果
    filename = os.path.basename(input_filepath)
    output_filepath = os.path.join(config.NER_PRO_OUTPUT_DIR, filename)
    save_json(final_disambiguated_entities, output_filepath)
    print(f"处理完成！消歧后的实体列表已保存到: {output_filepath}\n")

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs(config.NER_PRO_OUTPUT_DIR, exist_ok=True)
    
    # 遍历所有NER输出文件
    for filename in os.listdir(config.NER_OUTPUT_DIR):
        if filename.endswith(".json"):
            input_path = os.path.join(config.NER_OUTPUT_DIR, filename)
            run_disambiguate_on_file(input_path)
    
    print("\n所有NER文件的实体消歧处理完成！")