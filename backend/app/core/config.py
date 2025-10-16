# app/core/config.py

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List
import os

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

# --- 实体类型定义 ---
# 实体类型
ENTITY_TYPES = [
    "问题",
    "原因",
    "解决方案",
]

# 关系类型
RELATION_TYPES = [
    "导致",
    "解决",
    "需要"
]