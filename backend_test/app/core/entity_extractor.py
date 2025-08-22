# app/core/entity_extractor.py

from typing import List, Dict, Optional
import random
import re
import json
from app.core.config import ENTITY_TYPES, NER_PROMPT_PATH, ENTITY_VALIDATION_PROMPT_PATH
from app.core.utils import load_prompt, call_llm

def extract_entities_from_chunk(chunk_text: str, chunk_id: str = None) -> List[Dict]:
    """
    从文本分块中提取实体
    
    Args:
        chunk_text: 分块文本内容
        chunk_id: 分块ID
    
    Returns:
        提取到的实体列表
    """
    if not chunk_text or not chunk_text.strip():
        return []
    
    entities = []
    
    # 使用 LLM 进行实体提取
    llm_entities = _extract_entities_with_llm(chunk_text, chunk_id)
    if llm_entities:
        entities.extend(llm_entities)
  
    # 去重处理
    unique_entities = entities
    
    return unique_entities


def _extract_entities_with_llm(chunk_text: str, chunk_id: str = None) -> List[Dict]:
    """
    使用 LLM 进行实体提取
    
    Args:
        chunk_text: 分块文本内容
        chunk_id: 分块ID
    
    Returns:
        提取到的实体列表
    """
    try:
        # 加载 NER prompt 模板
        prompt_template = load_prompt(NER_PROMPT_PATH)
        if not prompt_template:
            print(f"❌ 无法加载 NER prompt 模板")
            return []
        
        # 构建完整的 prompt
        entity_types_str = "\n".join([f"- {entity_type}" for entity_type in ENTITY_TYPES])
        prompt = prompt_template.format(
            entity_types=entity_types_str,
            text=chunk_text
        )
        # 调用 LLM
        print(f"🤖 正在调用 LLM 进行实体提取 (chunk_id: {chunk_id})...")
        response = call_llm(prompt)
        if not response:
            print(f"❌ LLM 调用失败 (chunk_id: {chunk_id})")
            print(f"📝 失败的文本内容: {chunk_text[:100]}...")
            return []
        
        # 解析响应
        entities = []
        if isinstance(response, list):
            # 如果响应直接是列表格式
            for entity_data in response:
                if isinstance(entity_data, dict) and all(key in entity_data for key in ["entity_text", "entity_type", "entity_description"]):
                    entity = {
                        "text": entity_data["entity_text"].strip(),
                        "type": entity_data["entity_type"].strip(),
                        "description": entity_data["entity_description"].strip(),
                        "chunk_id": chunk_id,
                    }
                    entities.append(entity)
  
        print(f"✅ LLM 提取到 {len(entities)} 个实体 (chunk_id: {chunk_id})")
        return entities
        
    except Exception as e:
        print(f"❌ LLM 实体提取异常: {e} (chunk_id: {chunk_id})")
        return []



def simulate_entity_disambiguation(entities_dict: dict) -> dict:
    """
    实体消歧处理
    
    Args:
        entities_dict: 实体字典
    
    Returns:
        消歧后的实体字典
    """
    disambiguated = {}
    
    for key, entity in entities_dict.items():
        # 简单的消歧逻辑：如果实体名称相似，合并频次
        found_similar = False
        for existing_key, existing_entity in disambiguated.items():
            entity_name = entity.get('text', entity.get('name', ''))
            entity_type = entity.get('type', entity.get('entity_type', ''))
            existing_name = existing_entity.get('text', existing_entity.get('name', ''))
            existing_type = existing_entity.get('type', existing_entity.get('entity_type', ''))
            if (
                entity_name.lower() == existing_name.lower() and 
                entity_type == existing_type
            ):
                # 合并频次
                existing_entity["frequency"] += entity.get("frequency", 1)
                found_similar = True
                break
        
        if not found_similar:
            disambiguated[key] = entity.copy()
    
    return disambiguated