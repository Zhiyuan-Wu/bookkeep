"""
数据库迁移脚本
检查现有数据库是否和现在的数据模型匹配，并新增缺失的列
"""

import sqlite3
from pathlib import Path
from backend.config import DATABASE_URL
from backend.logger import get_logger

logger = get_logger(__name__)


def get_db_path():
    """获取数据库文件路径"""
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = Path(__file__).parent / db_path[2:]
        else:
            db_path = Path(db_path)
        return db_path
    return None


def get_table_columns(conn, table_name):
    """获取表的列信息"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {}
    for row in cursor.fetchall():
        columns[row[1]] = {
            "type": row[2],
            "notnull": row[3],
            "default": row[4],
            "pk": row[5]
        }
    return columns


def migrate_database():
    """执行数据库迁移"""
    db_path = get_db_path()
    if not db_path or not db_path.exists():
        logger.info("数据库文件不存在，将在首次运行时创建")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 检查users表
        users_columns = get_table_columns(conn, "users")
        logger.info(f"users表现有列: {list(users_columns.keys())}")
        
        # 检查并添加manager_id列
        if "manager_id" not in users_columns:
            logger.info("添加manager_id列到users表")
            cursor.execute("ALTER TABLE users ADD COLUMN manager_id INTEGER")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_manager_id ON users(manager_id)")
            logger.info("manager_id列添加成功")
        
        # 检查并添加email列
        if "email" not in users_columns:
            logger.info("添加email列到users表")
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(100)")
            logger.info("email列添加成功")
        
        # 检查并添加phone列
        if "phone" not in users_columns:
            logger.info("添加phone列到users表")
            cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
            logger.info("phone列添加成功")
        
        conn.commit()
        logger.info("数据库迁移完成")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"数据库迁移失败: {e}", exc_info=True)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()

