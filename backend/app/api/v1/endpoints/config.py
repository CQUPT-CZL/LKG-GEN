# app/api/v1/endpoints/config.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import app.core.config as core_config
import json
import os

router = APIRouter()

# 配置数据模型
class EntityTypesConfig(BaseModel):
    entity_types: List[str]

class RelationTypesConfig(BaseModel):
    relation_types: List[str]

class KnowledgeGraphConfig(BaseModel):
    entity_types: List[str]
    relation_types: List[str]

# 配置文件路径
CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "kg_config.json")

def load_config_from_file() -> Dict[str, Any]:
    """从文件加载配置"""
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
    
    # 返回默认配置
    return {
        "entity_types": core_config.ENTITY_TYPES,
        "relation_types": core_config.RELATION_TYPES
    }

def save_config_to_file(config: Dict[str, Any]) -> bool:
    """保存配置到文件"""
    try:
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

@router.get("/knowledge-graph", response_model=KnowledgeGraphConfig)
def get_knowledge_graph_config():
    """
    获取知识图谱配置（实体类型和关系类型）
    """
    try:
        config = load_config_from_file()
        return KnowledgeGraphConfig(
            entity_types=config.get("entity_types", core_config.ENTITY_TYPES),
            relation_types=config.get("relation_types", core_config.RELATION_TYPES)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {e}")

@router.put("/knowledge-graph", response_model=Dict[str, str])
def update_knowledge_graph_config(config: KnowledgeGraphConfig):
    """
    更新知识图谱配置（实体类型和关系类型）
    """
    try:
        # 验证输入
        if not config.entity_types:
            raise HTTPException(status_code=400, detail="实体类型列表不能为空")
        if not config.relation_types:
            raise HTTPException(status_code=400, detail="关系类型列表不能为空")
        
        # 保存配置
        config_data = {
            "entity_types": config.entity_types,
            "relation_types": config.relation_types
        }
        
        if save_config_to_file(config_data):
            # 动态更新内存中的配置
            import app.core.config as config_module
            config_module.ENTITY_TYPES = config.entity_types
            config_module.RELATION_TYPES = config.relation_types
            
            return {"message": "知识图谱配置更新成功"}
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {e}")

@router.get("/entity-types", response_model=EntityTypesConfig)
def get_entity_types():
    """
    获取实体类型配置
    """
    try:
        config = load_config_from_file()
        return EntityTypesConfig(entity_types=config.get("entity_types", core_config.ENTITY_TYPES))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实体类型失败: {e}")

@router.put("/entity-types", response_model=Dict[str, str])
def update_entity_types(config: EntityTypesConfig):
    """
    更新实体类型配置
    """
    try:
        if not config.entity_types:
            raise HTTPException(status_code=400, detail="实体类型列表不能为空")
        
        # 加载现有配置
        current_config = load_config_from_file()
        current_config["entity_types"] = config.entity_types
        
        if save_config_to_file(current_config):
            # 动态更新内存中的配置
            import app.core.config as config_module
            config_module.ENTITY_TYPES = config.entity_types
            
            return {"message": "实体类型配置更新成功"}
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新实体类型失败: {e}")

@router.get("/relation-types", response_model=RelationTypesConfig)
def get_relation_types():
    """
    获取关系类型配置
    """
    try:
        config = load_config_from_file()
        return RelationTypesConfig(relation_types=config.get("relation_types", core_config.RELATION_TYPES))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关系类型失败: {e}")

@router.put("/relation-types", response_model=Dict[str, str])
def update_relation_types(config: RelationTypesConfig):
    """
    更新关系类型配置
    """
    try:
        if not config.relation_types:
            raise HTTPException(status_code=400, detail="关系类型列表不能为空")
        
        # 加载现有配置
        current_config = load_config_from_file()
        current_config["relation_types"] = config.relation_types
        
        if save_config_to_file(current_config):
            # 动态更新内存中的配置
            import app.core.config as config_module
            config_module.RELATION_TYPES = config.relation_types
            
            return {"message": "关系类型配置更新成功"}
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新关系类型失败: {e}")

@router.post("/reset-defaults", response_model=Dict[str, str])
def reset_to_defaults():
    """
    重置为默认配置
    """
    try:
        default_config = {
            "entity_types": core_config.ENTITY_TYPES,
            "relation_types": core_config.RELATION_TYPES
        }
        
        if save_config_to_file(default_config):
            # 动态更新内存中的配置
            import app.core.config as config_module
            config_module.ENTITY_TYPES = core_config.ENTITY_TYPES
            config_module.RELATION_TYPES = core_config.RELATION_TYPES
            
            return {"message": "配置已重置为默认值"}
        else:
            raise HTTPException(status_code=500, detail="重置配置失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置配置失败: {e}")