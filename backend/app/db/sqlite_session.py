# app/db/sqlite_session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings # 假设您的配置都在这里

# 数据库文件的URL，例如 "sqlite:///./kg_platform.db"
SQLALCHEMY_DATABASE_URL = settings.SQLITE_DATABASE_URI

# 创建SQLAlchemy引擎
# connect_args 是专门为SQLite配置的，因为FastAPI的线程特性需要它
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建一个SessionLocal类，我们将在API的依赖项中使用它
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 这是给Alembic使用的
# from app.models.sqlite_models import Base
# target_metadata = Base.metadata