# app/api/deps.py

from typing import Generator
from sqlalchemy.orm import Session
from neo4j import Driver
from app.db.sqlite_session import SessionLocal
from app.db.neo4j_session import get_neo4j_driver

def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖注入函数
    
    这个函数会在每个API请求中创建一个新的数据库会话，
    并在请求结束后自动关闭会话。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_neo4j() -> Driver:
    """
    Neo4j驱动依赖注入函数
    
    返回Neo4j驱动实例，用于图数据库操作。
    """
    return get_neo4j_driver()