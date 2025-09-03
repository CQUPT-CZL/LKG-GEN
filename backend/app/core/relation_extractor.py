# app/core/relation_extractor.py

from typing import List, Dict
import random
import re
import json
from .utils import call_llm
from .config import RELATION_TYPES
from app.services.prompt_service import get_re_prompt_content

def extract_relations_from_entities(entities: List[Dict], text: str = None) -> List[Dict]:
    """
    从实体列表中提取关系（仅使用LLM方法）
    
    Args:
        entities: 实体列表
        text: 原始文本（用于LLM提取）
    
    Returns:
        提取到的关系列表
    """
    if len(entities) < 2:
        return []
    
    if not text:
        print("⚠️ 未提供文本，无法进行LLM关系提取")
        return []
    
    relations = []
    
    # 使用LLM进行关系提取
    try:
        llm_relations = _extract_relations_with_llm(entities, text)
        if llm_relations:
            relations.extend(llm_relations)
            print(f"✅ LLM成功提取到 {len(llm_relations)} 个关系")
        else:
            print("⚠️ LLM未提取到任何关系")
    except Exception as e:
        print(f"❌ LLM关系提取失败: {e}")
        return []
    
    # 去重处理
    unique_relations = _deduplicate_relations(relations)
    
    return unique_relations


def _extract_relations_with_llm(entities: List[Dict], text: str) -> List[Dict]:
    """
    使用LLM从文本中提取实体间关系
    
    Args:
        entities: 实体列表
        text: 原始文本
    
    Returns:
        提取到的关系列表
    """
    try:
        # 从数据库加载prompt模板
        prompt_template = get_re_prompt_content()
        if not prompt_template:
            print("❌ 无法加载关系提取prompt模板")
            return []
        
        # 提取实体名称列表
        entity_names = [entity.get('text', entity.get('name', '')) for entity in entities]
        entity_names = [name for name in entity_names if name]  # 过滤空名称
        
        if len(entity_names) < 2:
            return []
        
        # 格式化prompt
        formatted_prompt = prompt_template.format(
            text=text,
            entities=json.dumps(entity_names, ensure_ascii=False, indent=2),
            relation_types=json.dumps(RELATION_TYPES, ensure_ascii=False, indent=2)
        )
        
        # 调用LLM
        response = call_llm(formatted_prompt)
        
        if not response:
            return []
        
        # 解析LLM响应
        if isinstance(response, list):
            relations = response
        elif isinstance(response, dict) and 'relations' in response:
            relations = response['relations']
        else:
            print(f"⚠️ LLM响应格式不正确: {type(response)}")
            return []
        
        # 验证和转换关系格式
        valid_relations = []
        valid_entity_set = set(entity_names)
        
        for relation in relations:
            if not isinstance(relation, dict):
                continue
                
            head = relation.get('head', '')
            tail = relation.get('tail', '')
            relation_type = relation.get('relation', '')
            description = relation.get('description', '')
            
            # 验证实体是否在合法列表中
            if head in valid_entity_set and tail in valid_entity_set and relation_type in RELATION_TYPES:
                valid_relations.append({
                    'source_name': head,
                    'target_name': tail,
                    'relation_type': relation_type,
                    'description': description,
                    'confidence': 0.8  # 默认置信度
                })
            else:
                print(f"🚫 过滤无效关系: {relation}")
        
        return valid_relations
        
    except Exception as e:
        print(f"❌ LLM关系提取异常: {e}")
        return []


def _deduplicate_relations(relations: List[Dict]) -> List[Dict]:
    """去重关系列表"""
    unique_relations = {}
    
    for relation in relations:
        # 创建关系的唯一键
        key = f"{relation['source_name']}_{relation['target_name']}_{relation['relation_type']}"
        if key not in unique_relations:
            unique_relations[key] = relation
        else:
            # 如果存在重复关系，保留置信度更高的
            if relation['confidence'] > unique_relations[key]['confidence']:
                unique_relations[key] = relation
    
    return list(unique_relations.values())