"""
数据库连接和初始化
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base
from backend.config import DATABASE_URL
import os

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL.replace("sqlite:///", "sqlite:///") if DATABASE_URL.startswith("sqlite:///./") 
    else DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    初始化数据库，创建所有表
    
    使用样例:
        from backend.database import init_db
        init_db()
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    获取数据库会话
    
    Yields:
        Session: 数据库会话对象
        
    使用样例:
        from backend.database import get_db
        db = next(get_db())
        # 使用db进行数据库操作
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

