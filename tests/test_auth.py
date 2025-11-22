"""
认证功能测试
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, SessionLocal
from backend.models import User
from backend.utils import hash_password

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """测试前初始化数据库"""
    init_db()
    db = SessionLocal()
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if not existing_user:
            # 创建测试用户
            test_user = User(
                username="testuser",
                password_hash=hash_password("testpass"),
                user_type="普通用户"
            )
            db.add(test_user)
            db.commit()
    finally:
        db.close()
    yield
    # 测试后清理（可选）

def test_login_success():
    """测试成功登录"""
    response = client.post(
        "/api/users/login",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "user" in data

def test_login_failure():
    """测试登录失败"""
    response = client.post(
        "/api/users/login",
        json={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False

def test_get_current_user_without_login():
    """测试未登录时获取用户信息"""
    # 使用新的客户端，确保没有session cookie
    from fastapi.testclient import TestClient
    from backend.main import app
    fresh_client = TestClient(app)
    response = fresh_client.get("/api/users/me")
    assert response.status_code == 401

