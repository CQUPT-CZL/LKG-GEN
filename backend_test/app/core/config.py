# app/core/config.py

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List

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
    OPENAI_MODEL: str = "gpt-4-turbo"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 创建一个全局可用的配置实例
settings = Settings()