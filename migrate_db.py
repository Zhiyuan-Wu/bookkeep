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


def migrate_user_types(conn):
    """迁移用户类型：重命名用户类型值"""
    logger.info("开始迁移用户类型...")

    # 用户类型映射
    type_mapping = {
        "普通用户": "课题组用户",
        "学生用户": "普通用户",
        "厂家": "供应商"
    }

    # 检查是否已经迁移过（通过检查是否已有新值）
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_type FROM users")
    existing_types = {row[0] for row in cursor.fetchall()}  
    if "课题组用户" in existing_types:
        logger.info("数据库中存在课题组用户类型，跳过迁移")
        return

    # 执行批量更新
    for old_type, new_type in type_mapping.items():
        cursor.execute(
            "UPDATE users SET user_type = ? WHERE user_type = ?",
            (new_type, old_type)
        )
        affected = cursor.rowcount
        logger.info(f"  {old_type} → {new_type}: {affected} 条记录")

    logger.info("用户类型迁移完成")


def cleanup_deleted_products(conn):
    """清理已软删除的产品数据"""
    logger.info("开始清理软删除的产品...")

    cursor = conn.cursor()

    # 先统计要删除的数量
    cursor.execute("SELECT COUNT(*) FROM products WHERE is_deleted = 1")
    count = cursor.fetchone()[0]

    if count == 0:
        logger.info("没有需要清理的软删除产品")
        return

    logger.info(f"准备删除 {count} 条软删除的产品记录")

    # 执行删除
    cursor.execute("DELETE FROM products WHERE is_deleted = 1")
    affected = cursor.rowcount
    logger.info(f"已删除 {affected} 条软删除的产品记录")


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

        # 迁移用户类型
        migrate_user_types(conn)

        # 清理软删除的产品
        cleanup_deleted_products(conn)

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

