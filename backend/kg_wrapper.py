"""知识图谱构建的包装函数，简化原有脚本的调用"""

import os
import sys
import json
from pathlib import Path

# 添加src/scripts到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'scripts'))

try:
    import config
    from utils import save_json, load_json, load_text
    from step_chunk import run_chunk_on_file
    from step2_ner import run_ner_on_file
    from step3_re import run_relation_extraction_on_all
    from step_disambiguate import run_disambiguate_on_all_files
except ImportError as e:
    print(f"导入模块失败: {e}")

def run_disambiguation():
    """运行实体消歧的包装函数"""
    try:
        # 确保输出目录存在
        os.makedirs(config.NER_PRO_OUTPUT_DIR, exist_ok=True)
        
        # 调用原始的消歧函数
        run_disambiguate_on_all_files()
        
        return True
    except Exception as e:
        print(f"实体消歧失败: {e}")
        return False

def simple_entity_disambiguation():
    """简化的实体消歧函数"""
    try:
        # 读取所有NER输出文件
        all_entities = []
        
        for filename in os.listdir(config.NER_OUTPUT_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(config.NER_OUTPUT_DIR, filename)
                entities = load_json(file_path)
                if entities:
                    all_entities.extend(entities)
        
        # 简单的去重和规范化
        entity_dict = {}
        for entity in all_entities:
            entity_name = entity.get("entity_text", "").strip()
            entity_type = entity.get("entity_type", "")
            
            if entity_name and entity_type:
                key = f"{entity_name}_{entity_type}"
                
                if key in entity_dict:
                    # 合并chunk_id
                    existing_chunks = entity_dict[key].get("chunk_id", [])
                    new_chunks = entity.get("chunk_id", [])
                    entity_dict[key]["chunk_id"] = list(set(existing_chunks + new_chunks))
                else:
                    entity_dict[key] = {
                        "entity_text": entity_name,
                        "entity_type": entity_type,
                        "chunk_id": entity.get("chunk_id", []),
                        "description": entity.get("description", "")
                    }
        
        # 转换为列表格式
        disambiguated_entities = list(entity_dict.values())
        
        # 保存结果
        output_file = os.path.join(config.NER_PRO_OUTPUT_DIR, "all_entities_disambiguated.json")
        save_json(disambiguated_entities, output_file)
        
        print(f"实体消歧完成，处理了 {len(disambiguated_entities)} 个唯一实体")
        return True
        
    except Exception as e:
        print(f"简化实体消歧失败: {e}")
        return False

def ensure_output_files_exist():
    """确保输出文件存在，如果不存在则创建空文件"""
    try:
        # 确保消歧文件存在
        disambig_file = os.path.join(config.NER_PRO_OUTPUT_DIR, "all_entities_disambiguated.json")
        if not os.path.exists(disambig_file):
            save_json([], disambig_file)
        
        # 确保关系文件存在
        relations_file = os.path.join(config.RE_OUTPUT_DIR, "all_relations.json")
        if not os.path.exists(relations_file):
            save_json([], relations_file)
            
        return True
    except Exception as e:
        print(f"创建输出文件失败: {e}")
        return False

def get_entity_types():
    """获取实体类型列表"""
    try:
        return config.ENTITY_TYPES
    except:
        return [
            "钢铁材料", "生产工艺", "性能指标", "应用领域", "设备",
            "缺陷", "化学成分", "热处理工艺", "机械性能", "表面处理", "检测方法"
        ]

def get_relation_types():
    """获取关系类型列表"""
    try:
        return config.RELATION_TYPES
    except:
        return [
            "具有性能", "生产出", "应用于", "使用设备", "导致缺陷",
            "包含成分", "需要检测", "改善性能", "防止缺陷", "互相影响"
        ]