# app/core/config.py

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List, Tuple, Dict, Any
import os
import json

class Settings(BaseSettings):
    # --- General App Settings ---
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Knowledge Graph Platform"

    # --- SQLite Database ---
    # 例如: "sqlite:///./kg_platform.db"
    SQLITE_DATABASE_URI: str

    # --- Neo4j Database ---
    NEO4J_URI: str
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str

    # --- LLM Service ---
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "qwen-max"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 创建一个全局可用的配置实例
settings = Settings()

# --- Prompt 文件路径 ---
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(APP_DIR, "prompts")
NER_PROMPT_PATH = os.path.join(PROMPTS_DIR, "ner_prompt.txt")
ENTITY_VALIDATION_PROMPT_PATH = os.path.join(PROMPTS_DIR, "entity_validation_prompt.txt")
RE_PROMPT_PATH = os.path.join(PROMPTS_DIR, "re_prompt.txt")
KG_CONFIG_PATH = os.path.join(APP_DIR, "kg_config.json")

# --- 实体/关系类型定义（从配置文件加载，带回退） ---
DEFAULT_ENTITY_TYPES = [
    "问题",
    "原因",
    "解决方案",
]

DEFAULT_RELATION_TYPES = [
    "导致",
    "解决",
    "需要",
]

def _load_kg_types_from_file() -> Tuple[List[str], List[str]]:
    """尝试从 kg_config.json 加载类型，失败时返回默认值。"""
    try:
        if os.path.exists(KG_CONFIG_PATH):
            with open(KG_CONFIG_PATH, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
                entity_types = data.get("entity_types", DEFAULT_ENTITY_TYPES)
                relation_types = data.get("relation_types", DEFAULT_RELATION_TYPES)
                # 仅保留字符串项，避免配置异常
                entity_types = [str(x) for x in entity_types]
                relation_types = [str(x) for x in relation_types]
                return entity_types, relation_types
    except Exception as e:
        # 读取失败则使用默认，避免影响运行
        print(f"⚠️ 加载 kg_config.json 失败，使用默认类型: {e}")
    return DEFAULT_ENTITY_TYPES, DEFAULT_RELATION_TYPES

# 初始化时加载一次（由接口更新时会动态覆盖这两个变量）
ENTITY_TYPES, RELATION_TYPES = _load_kg_types_from_file()

def get_entity_types() -> List[str]:
    """返回当前实体类型（始终读取最新模块变量）。"""
    return ENTITY_TYPES

def get_relation_types() -> List[str]:
    """返回当前关系类型（始终读取最新模块变量）。"""
    return RELATION_TYPES