import os
import json
from collections import defaultdict
from . import config
from .utils import call_llm, load_json, save_json, load_prompt

def create_chunk_to_entities_map(disambiguated_entities: list):
    """
    创建一个从 chunk_id 到实体名称列表的反向索引。
    现在chunk_id格式为：文件名_chunk编号
    """
    chunk_map = defaultdict(list)
    for entity in disambiguated_entities:
        # 我们只关心规范名称
        canonical_name = entity["entity_text"]
        for chunk_id in entity["chunk_id"]:
            if canonical_name not in chunk_map[chunk_id]:
                chunk_map[chunk_id].append(canonical_name)
    return chunk_map

def load_all_chunks():
    """
    加载所有chunk文件的内容，返回一个统一的字典
    格式：{"文件名_chunk编号": "chunk内容"}
    """
    all_chunks = {}
    
    for filename in os.listdir(config.CHUNK_OUTPUT_DIR):
        if filename.endswith(".json"):
            chunk_path = os.path.join(config.CHUNK_OUTPUT_DIR, filename)
            file_prefix = filename.replace('.json', '')
            
            chunks = load_json(chunk_path)
            if chunks:
                # 为每个chunk_id添加文件名前缀
                for chunk_id, chunk_text in chunks.items():
                    prefixed_chunk_id = f"{file_prefix}_{chunk_id}"
                    all_chunks[prefixed_chunk_id] = chunk_text
                    
                print(f"📄 加载了文件 {filename}，包含 {len(chunks)} 个chunks")
    
    print(f"📊 总共加载了 {len(all_chunks)} 个chunks")
    return all_chunks

def extract_relations_for_chunk(chunk_id: str, chunk_text: str, entities_in_chunk: list):
    """
    为单个文本块调用LLM进行关系抽取。
    """
    print(f"🔄 正在处理 Chunk {chunk_id}")
    if len(entities_in_chunk) < 2:
        print("⚠️ 实体数量少于2个，无法形成关系，跳过。")
        return []

    prompt_template = load_prompt(config.RE_PROMPT_PATH)
    
    # 填充Prompt
    prompt = prompt_template.replace("{{CHUNK_TEXT}}", chunk_text)
    prompt = prompt.replace("{{ENTITIES_IN_CHUNK}}", json.dumps(entities_in_chunk, ensure_ascii=False))
    prompt = prompt.replace("{{RELATION_TYPES}}", json.dumps(config.RELATION_TYPES, ensure_ascii=False))
    
    # 调用LLM
    triples = call_llm(prompt, model_name="qwen-plus-latest")
    
    if triples and isinstance(triples, list):
        print(f"✅ 成功抽取到 {len(triples)} 个关系三元组。")
        return triples
    else:
        print("⚠️ 未抽取到关系或LLM返回格式错误。")
        return []

def run_relation_extraction_on_all():
    """
    对所有消歧后的实体进行关系抽取，生成统一的关系文件
    """
    print("🚀 开始关系抽取处理...")
    
    # 加载消歧后的实体文件
    disambiguated_entities_path = os.path.join(config.NER_PRO_OUTPUT_DIR, "all_entities_disambiguated.json")
    
    if not os.path.exists(disambiguated_entities_path):
        print(f"❌ 找不到消歧实体文件: {disambiguated_entities_path}")
        return None
    
    print(f"📄 正在加载消歧实体文件: all_entities_disambiguated.json")
    disambiguated_entities = load_json(disambiguated_entities_path)
    
    if not disambiguated_entities:
        print("⚠️ 消歧实体数据为空")
        return None
    
    print(f"✅ 加载了 {len(disambiguated_entities)} 个消歧后的实体")
    
    # 加载所有chunk文件的内容
    print("📚 正在加载所有chunk文件...")
    all_chunks = load_all_chunks()
    
    if not all_chunks:
        print("❌ 没有找到任何chunk数据")
        return None
    
    # 创建 chunk_id -> entities 的映射
    chunk_to_entities_map = create_chunk_to_entities_map(disambiguated_entities)
    
    extracted_triples = []
    
    print(f"🔗 开始处理 {len(chunk_to_entities_map)} 个文本块的关系抽取")
    
    for chunk_id, entities in chunk_to_entities_map.items():
        chunk_text = all_chunks.get(chunk_id, "")
        if not chunk_text:
            print(f"⚠️ Chunk {chunk_id} 在chunk数据中不存在，跳过")
            continue
        
        if len(entities) < 2:
            continue  # 实体数量少于2个，无法形成关系
        
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
                    print(f"🚫 [已过滤] 发现幻觉实体，已丢弃: {triple}")
        
        # 为每个三元组添加来源信息
        for triple in validated_triples:
            if len(triple) == 3:
                extracted_triples.append({
                    "head": triple[0],
                    "relation": triple[1],
                    "tail": triple[2],
                    "source_chunk_id": chunk_id
                })
    
    # 去重处理
    unique_triples_str = {json.dumps(d, sort_keys=True) for d in extracted_triples}
    final_triples = [json.loads(s) for s in unique_triples_str]
    
    # 保存所有关系抽取结果到统一文件
    output_path = os.path.join(config.RE_OUTPUT_DIR, "all_relations.json")
    save_json(final_triples, output_path)
    
    print(f"✅ 关系抽取处理完成！")
    print(f"📈 统计信息:")
    print(f"   🏷️ 处理实体数: {len(disambiguated_entities)}")
    print(f"   📄 处理chunk数: {len(chunk_to_entities_map)}")
    print(f"   🔗 抽取关系数: {len(final_triples)}")
    print(f"   💾 结果保存到: {output_path}")
    
    return output_path

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs(config.RE_OUTPUT_DIR, exist_ok=True)
    
    # 处理所有文件的关系抽取
    result = run_relation_extraction_on_all()
    
    if result:
        print("\n🎉 所有文件的关系抽取处理完成！")
    else:
        print("\n❌ 关系抽取处理失败！")