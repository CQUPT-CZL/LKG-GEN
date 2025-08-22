# app/core/config.py

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List
import os

class Settings(BaseSettings):
    # --- General App Settings ---
    API_V1_STR: str = "/api/v1"
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
ENTITY_TYPES = [
    "技术方法",      # 如机器学习、深度学习等
    "技术领域",      # 如人工智能、自然语言处理等
    "算法模型",      # 如神经网络、决策树等
    "数据类型",      # 如文本数据、图像数据等
    "应用场景",      # 如推荐系统、智能客服等
    "性能指标",      # 如准确率、召回率等
    "工具平台",      # 如TensorFlow、PyTorch等
    "概念术语",      # 如特征工程、模型训练等
    "组织机构",      # 如公司、大学、研究所等
    "人物",         # 如研究者、专家等
    "地点",         # 如城市、国家等
]

# --- 关系类型定义 ---
RELATION_TYPES = [
    "属于",         # 技术方法属于技术领域
    "应用于",       # 技术应用于场景
    "使用",         # 使用工具或平台
    "评估",         # 使用指标评估
    "包含",         # 领域包含方法
    "基于",         # 基于某种技术
    "改进",         # 改进某种方法
    "相关",         # 概念间的相关关系
    "位于",         # 组织位于地点
    "隶属于"        # 人物隶属于组织
]