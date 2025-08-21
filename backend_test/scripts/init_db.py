# scripts/init_db.py

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.db.sqlite_session import engine
from app.models.sqlite_models import Base

def init_db():
    print("正在创建所有数据表...")
    # Base.metadata.create_all() 会找到所有继承自Base的类，并在数据库中创建对应的表
    Base.metadata.create_all(bind=engine)
    print("数据表创建成功！")

if __name__ == "__main__":
    init_db()