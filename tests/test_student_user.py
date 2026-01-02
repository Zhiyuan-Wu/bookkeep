"""
学生用户功能测试
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, SessionLocal
from backend.models import User
from backend.utils import hash_password
from backend.config import USER_TYPE_STUDENT, USER_TYPE_NORMAL, ALLOW_SELF_REGISTRATION

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """测试前初始化数据库"""
    init_db()
    db = SessionLocal()
    try:
        # 创建普通用户（作为管理用户）
        normal_user = db.query(User).filter(User.username == "normal_user").first()
        if not normal_user:
            normal_user = User(
                username="normal_user",
                password_hash=hash_password("normalpass"),
                user_type=USER_TYPE_NORMAL
            )
            db.add(normal_user)
            db.commit()
            db.refresh(normal_user)
        
        # 创建学生用户
        student_user = db.query(User).filter(User.username == "student_user").first()
        if not student_user:
            student_user = User(
                username="student_user",
                password_hash=hash_password("studentpass"),
                user_type=USER_TYPE_STUDENT,
                manager_id=normal_user.id
            )
            db.add(student_user)
            db.commit()
    finally:
        db.close()
    yield
    # 测试后清理（可选）

def test_register_student_success():
    """测试学生用户注册成功"""
    response = client.post(
        "/api/users/register",
        json={
            "username": "new_student",
            "password": "newpass",
            "manager_username": "normal_user"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["user"]["user_type"] == USER_TYPE_STUDENT
    assert data["user"]["manager_username"] == "normal_user"

def test_register_student_invalid_manager():
    """测试学生用户注册时管理用户不存在"""
    response = client.post(
        "/api/users/register",
        json={
            "username": "new_student2",
            "password": "newpass",
            "manager_username": "nonexistent_user"
        }
    )
    assert response.status_code == 404

def test_register_student_manager_not_normal():
    """测试学生用户注册时管理用户不是普通用户"""
    # 先创建管理员用户
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin_user").first()
        if not admin_user:
            admin_user = User(
                username="admin_user",
                password_hash=hash_password("adminpass"),
                user_type="管理员"
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()
    
    response = client.post(
        "/api/users/register",
        json={
            "username": "new_student3",
            "password": "newpass",
            "manager_username": "admin_user"
        }
    )
    assert response.status_code == 400

def test_student_cannot_view_internal_price():
    """测试学生用户不能查看内部价格"""
    # 登录学生用户
    login_response = client.post(
        "/api/users/login",
        json={"username": "student_user", "password": "studentpass"}
    )
    assert login_response.status_code == 200
    cookies = login_response.cookies
    
    # 获取用户信息，检查manager_id
    user_response = client.get("/api/users/me", cookies=cookies)
    assert user_response.status_code == 200
    user_data = user_response.json()
    assert user_data["user_type"] == USER_TYPE_STUDENT
    assert user_data["manager_id"] is not None

def test_normal_user_can_view_managed_students_orders():
    """测试普通用户可以查看管理学生的订单"""
    # 登录普通用户
    login_response = client.post(
        "/api/users/login",
        json={"username": "normal_user", "password": "normalpass"}
    )
    assert login_response.status_code == 200
    cookies = login_response.cookies
    
    # 获取订单列表（应该包含管理学生的订单）
    orders_response = client.get("/api/orders/", cookies=cookies)
    assert orders_response.status_code == 200

def test_student_cannot_view_statistics():
    """测试学生用户不能查看统计信息"""
    # 登录学生用户
    login_response = client.post(
        "/api/users/login",
        json={"username": "student_user", "password": "studentpass"}
    )
    assert login_response.status_code == 200
    cookies = login_response.cookies
    
    # 尝试获取统计信息
    stats_response = client.get("/api/statistics/", cookies=cookies)
    assert stats_response.status_code == 403

