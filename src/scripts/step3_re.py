# 02_scripts/step3_relation_extraction.py

import os
import json
from collections import defaultdict
import config
from utils import call_llm, load_json, save_json, load_prompt

def create_chunk_to_entities_map(disambiguated_entities: list):
    """
    创建一个从 chunk_id 到实体名称列表的反向索引。
    """
    chunk_map = defaultdict(list)
    for entity in disambiguated_entities:
        # 我们只关心规范名称
        canonical_name = entity["entity_text"]
        for chunk_id in entity["chunk_id"]:
            if canonical_name not in chunk_map[chunk_id]:
                chunk_map[chunk_id].append(canonical_name)
    return chunk_map

def extract_relations_for_chunk(chunk_id: str, chunk_text: str, entities_in_chunk: list):
    """
    为单个文本块调用LLM进行关系抽取。
    """
    print(f"--- 正在处理 Chunk {chunk_id} ---")
    if len(entities_in_chunk) < 2:
        print("实体数量少于2个，无法形成关系，跳过。")
        return []

    prompt_template = load_prompt(os.path.join(config.BASE_DIR, "prompts", "re_prompt.txt"))
    
    # 填充Prompt
    prompt = prompt_template.replace("{{CHUNK_TEXT}}", chunk_text)
    prompt = prompt.replace("{{ENTITIES_IN_CHUNK}}", json.dumps(entities_in_chunk, ensure_ascii=False))
    prompt = prompt.replace("{{RELATION_TYPES}}", json.dumps(config.RELATION_TYPES, ensure_ascii=False))
    
    # 调用LLM
    # 注意：这里我们期待一个列表作为返回值，需要确保 call_llm 能处理这种情况
    # 我们可以让 call_llm 总是尝试解析JSON，如果失败则返回None
    triples = call_llm(prompt, model_name="qwen-plus-latest") # 您可以指定模型

    if triples and isinstance(triples, list):
        print(f"成功抽取到 {len(triples)} 个关系三元组。")
        return triples
    else:
        print("未抽取到关系或LLM返回格式错误。")
        return []

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs(config.RE_OUTPUT_DIR, exist_ok=True)
    
    # 遍历所有消歧后的实体文件
    for filename in os.listdir(config.NER_PRO_OUTPUT_DIR):
        if filename.endswith(".json"):
            disambiguated_entities_path = os.path.join(config.NER_PRO_OUTPUT_DIR, filename)
            chunk_path = os.path.join(config.CHUNK_OUTPUT_DIR, filename)  # 假设 chunk 文件与实体文件同名
            
            if not os.path.exists(chunk_path):
                print(f"警告: 找不到 chunk 文件 {chunk_path}，跳过文件 {filename}")
                continue
            
            disambiguated_entities = load_json(disambiguated_entities_path)
            chunks = load_json(chunk_path)  # 加载整个 chunk JSON
            
            # 创建 chunk_id -> entities 的映射
            chunk_to_entities_map = create_chunk_to_entities_map(disambiguated_entities)
            
            extracted_triples = []
            
            print(f"开始处理文件: {filename}，包含 {len(chunk_to_entities_map)} 个文本块")
            for chunk_id, entities in chunk_to_entities_map.items():
                chunk_text = chunks.get(chunk_id, "")  # 从 JSON 中获取对应 chunk 文本
                if not chunk_text:
                    print(f"警告: Chunk {chunk_id} 在 {chunk_path} 中不存在，跳过")
                    continue
                
                # 为当前块抽取关系
                triples_from_chunk = extract_relations_for_chunk(chunk_id, chunk_text, entities)

                validated_triples = []
                # 将实体列表转为集合，便于快速查找
                valid_entity_set = set(entities)        

                for triple in triples_from_chunk:
                    if len(triple) == 3:
                        head, relation, tail = triple
                        # 检查头实体和尾实体是否都在合法的实体列表中
                        if head in valid_entity_set and tail in valid_entity_set:
                            validated_triples.append(triple)
                        else:
                            print(f"--- [已过滤] 发现幻觉实体，已丢弃: {triple}")
                
                # 为每个三元组添加来源信息
                for triple in validated_triples:
                    if len(triple) == 3:
                        extracted_triples.append({
                            "head": triple[0],
                            "relation": triple[1],
                            "tail": triple[2],
                            "source_chunk_id": chunk_id
                        })
            
            # 保存该文件的所有抽取结果（可选：去重）
            unique_triples_str = {json.dumps(d, sort_keys=True) for d in extracted_triples}
            final_triples = [json.loads(s) for s in unique_triples_str]
            
            output_path = os.path.join(config.RE_OUTPUT_DIR, filename)
            save_json(final_triples, output_path)
            
            print(f"文件 {filename} 处理完成！共抽取到 {len(final_triples)} 个唯一的关系三元组。\n")
    
    print("所有文件的关系统计抽取完成！")