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
    "钢铁产品",      # 如螺纹钢、热轧卷板、冷轧薄板、中厚板、H型钢、角钢、槽钢等
    "炼铁工艺",      # 如高炉炼铁、直接还原、熔融还原等
    "炼钢工艺",      # 如转炉炼钢、电炉炼钢、精炼炉、连铸等
    "轧制工艺",      # 如热轧、冷轧、中厚板轧制、型钢轧制等
    "铁矿原料",      # 如铁矿石、球团矿、烧结矿、废钢等
    "燃料辅料",      # 如焦炭、煤粉、石灰石、萤石、硅铁等
    "冶金设备",      # 如高炉、转炉、电炉、轧机、连铸机等
    "化学成分",      # 如碳含量、硅含量、锰含量、磷含量、硫含量等
    "力学性能",      # 如屈服强度、抗拉强度、延伸率、冲击韧性、硬度等
    "钢铁标准",      # 如GB/T、JIS、ASTM、EN、API等标准
    "钢铁集团",      # 如中国宝武、河钢集团、鞍钢集团、首钢集团等
    "生产厂区",      # 如钢铁联合企业、专业化钢厂、特钢厂等
    "下游行业",      # 如建筑钢结构、汽车制造、造船工业、机械制造等
    "环保设施",      # 如烧结脱硫、焦炉脱硫脱硝、高炉煤气净化、污水处理等
    "技术岗位",      # 如高炉工、转炉工、轧钢工、化验员、设备维护工等
    "产业基地",      # 如钢铁工业园区、临港钢铁基地、内陆钢铁基地等
]

# --- 关系类型定义 ---
RELATION_TYPES = [
    "冶炼生产",      # 钢铁企业冶炼生产钢铁产品
    "消耗原料",      # 炼铁炼钢工艺消耗铁矿石、焦炭等原料
    "轧制成材",      # 轧制工艺将钢坯轧制成钢材产品
    "供应下游",      # 钢铁产品供应建筑、汽车等下游行业
    "检验指标",      # 化学成分、力学性能检验钢铁产品
    "执行标准",      # 钢铁产品执行国家标准或行业标准
    "配置设备",      # 生产厂区配置高炉、转炉等冶金设备
    "操作设备",      # 技术岗位人员操作冶金设备
    "建设基地",      # 钢铁集团在产业基地建设钢铁厂
    "配套环保",      # 钢铁企业配套脱硫脱硝等环保设施
    "隶属集团",      # 钢铁厂隶属于钢铁集团
    "采购供应",      # 钢铁企业采购铁矿石等原燃料
    "含有成分",      # 钢铁产品含有碳、硅、锰等化学成分
    "具备性能"       # 钢铁产品具备屈服强度、延伸率等力学性能
]