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
ENTITY_TYPES = [
    "钢铁产品",      # 如螺纹钢、热轧板、冷轧板等
    "生产工艺",      # 如高炉炼铁、转炉炼钢、连铸等
    "原材料",       # 如铁矿石、焦炭、石灰石等
    "设备装置",      # 如高炉、转炉、轧机等
    "质量指标",      # 如强度、硬度、韧性等
    "技术标准",      # 如国标、行标、企标等
    "钢铁企业",      # 如宝钢、河钢、沙钢等
    "生产基地",      # 如钢铁厂、生产线等
    "市场应用",      # 如建筑、汽车、造船等
    "环保技术",      # 如脱硫、脱硝、除尘等
    "人员岗位",      # 如炼钢工、轧钢工、质检员等
    "地理位置",      # 如城市、省份、工业园区等
]

# --- 关系类型定义 ---
RELATION_TYPES = [
    "生产",         # 企业生产钢铁产品
    "使用",         # 生产工艺使用原材料
    "应用于",       # 钢铁产品应用于市场
    "检测",         # 质量指标检测产品
    "位于",         # 企业位于地理位置
    "操作",         # 人员操作设备
    "符合",         # 产品符合技术标准
    "包含",         # 生产基地包含设备
    "采用",         # 企业采用环保技术
    "隶属于",       # 人员隶属于企业
    "供应",         # 供应商供应原材料
    "加工"          # 设备加工原材料
]