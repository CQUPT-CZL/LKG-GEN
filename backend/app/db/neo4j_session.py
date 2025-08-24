# app/db/neo4j_session.py

from neo4j import GraphDatabase, Driver
from app.core.config import settings
from typing import Generator

# 创建Neo4j驱动实例
driver: Driver = GraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)

def get_neo4j_driver() -> Driver:
    """
    获取Neo4j驱动实例
    
    这个函数返回全局的Neo4j驱动实例，
    用于在API端点中进行图数据库操作。
    """
    return driver

def close_neo4j_driver():
    """
    关闭Neo4j驱动连接
    
    应该在应用关闭时调用此函数。
    """
    if driver:
        driver.close()