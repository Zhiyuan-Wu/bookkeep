"""
初始化数据库脚本
清空所有数据表并创建初始管理员用户、示例数据
"""

from backend.database import init_db, SessionLocal, engine
from backend.models import Base, User, Supplier, Product, Order, ServiceRecord
from backend.utils import hash_password
from backend.config import USER_TYPE_ADMIN, USER_TYPE_NORMAL, USER_TYPE_SUPPLIER

def recreate_tables():
    """重新创建所有表"""
    # 删除所有表
    Base.metadata.drop_all(bind=engine)
    # 重新创建所有表
    Base.metadata.create_all(bind=engine)
    print("已重新创建所有数据表")

def create_initial_data():
    """创建初始数据"""
    db = SessionLocal()
    try:
        # 创建默认管理员
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            user_type=USER_TYPE_ADMIN
        )
        db.add(admin)
        db.flush()
        print("创建默认管理员: admin / admin123")
        
        print("数据库初始化完成！")
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("初始化数据库...")
    # 清空所有数据并重新创建表
    recreate_tables()
    # 创建初始数据
    create_initial_data()
