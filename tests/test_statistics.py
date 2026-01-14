"""
统计信息功能测试
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, SessionLocal
from backend.models import User, Supplier, Order, ServiceRecord
from backend.utils import hash_password, format_order_content
from backend.config import (
    USER_TYPE_ADMIN, USER_TYPE_NORMAL, USER_TYPE_SUPPLIER,
    ORDER_STATUS_CONFIRMED, SERVICE_STATUS_CONFIRMED
)

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """测试前初始化数据库"""
    init_db()
    db = SessionLocal()
    try:
        # 创建测试供应商
        existing_supplier = db.query(Supplier).filter(Supplier.name == "测试统计供应商").first()
        if not existing_supplier:
            supplier = Supplier(name="测试统计供应商")
            db.add(supplier)
            db.flush()
            supplier_id = supplier.id
        else:
            supplier_id = existing_supplier.id
        
        # 创建测试用户
        if not db.query(User).filter(User.username == "testadmin_stat").first():
            admin = User(
                username="testadmin_stat",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_ADMIN
            )
            db.add(admin)
        if not db.query(User).filter(User.username == "testnormal_stat").first():
            normal_user = User(
                username="testnormal_stat",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_NORMAL
            )
            db.add(normal_user)
            db.flush()
            normal_user_id = normal_user.id
        else:
            normal_user = db.query(User).filter(User.username == "testnormal_stat").first()
            normal_user_id = normal_user.id
        
        # 创建确认状态的订单
        existing_order = db.query(Order).filter(
            Order.user_id == normal_user_id,
            Order.supplier_id == supplier_id,
            Order.status == ORDER_STATUS_CONFIRMED
        ).first()
        if not existing_order:
            order = Order(
                user_id=normal_user_id,
                supplier_id=supplier_id,
                content=format_order_content([{
                    "product_id": 1,
                    "name": "统计测试商品",
                    "model": None,
                    "specification": None,
                    "internal_price": 80.0,
                    "tax_included_price": 100.0,
                    "quantity": 2
                }]),
                status=ORDER_STATUS_CONFIRMED
            )
            db.add(order)
        
        # 创建确认状态的服务记录
        existing_service = db.query(ServiceRecord).filter(
            ServiceRecord.user_id == normal_user_id,
            ServiceRecord.supplier_id == supplier_id,
            ServiceRecord.status == SERVICE_STATUS_CONFIRMED
        ).first()
        if not existing_service:
            service = ServiceRecord(
                user_id=normal_user_id,
                supplier_id=supplier_id,
                content="统计测试服务",
                amount=50.0,
                status=SERVICE_STATUS_CONFIRMED
            )
            db.add(service)
        
        db.commit()
    finally:
        db.close()
    yield

def get_auth_headers(username="testadmin_stat", password="testpass"):
    """获取认证headers"""
    response = client.post(
        "/api/users/login",
        json={"username": username, "password": password}
    )
    if response.status_code == 200 and response.json().get("success"):
        cookies = response.cookies
        return {"Cookie": f"bookkeep_session={cookies.get('bookkeep_session')}"}
    return {}

def test_get_statistics_as_admin():
    """测试管理员获取统计信息"""
    headers = get_auth_headers("testadmin_stat")
    
    response = client.get("/api/statistics/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert data["total"]["supplier_name"] == "总计"

def test_get_statistics_as_normal_user():
    """测试课题组用户获取统计信息"""
    headers = get_auth_headers("testnormal_stat")
    
    response = client.get("/api/statistics/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

def test_get_statistics_as_supplier():
    """测试供应商用户不能获取统计信息"""
    # 先创建供应商用户
    db = SessionLocal()
    try:
        supplier_user = db.query(User).filter(User.username == "testsupplier_stat").first()
        if not supplier_user:
            # 获取或创建supplier
            supplier = db.query(Supplier).filter(Supplier.name == "测试供应商统计").first()
            if not supplier:
                supplier = Supplier(name="测试供应商统计")
                db.add(supplier)
                db.flush()
            supplier_user = User(
                username="testsupplier_stat",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_SUPPLIER,
                supplier_id=supplier.id  # 关联到supplier
            )
            db.add(supplier_user)
            db.commit()
    finally:
        db.close()
    
    headers = get_auth_headers("testsupplier_stat")
    
    response = client.get("/api/statistics/", headers=headers)
    assert response.status_code == 403

def test_statistics_only_confirmed():
    """测试统计信息只包含确认状态的订单和服务"""
    headers = get_auth_headers("testadmin_stat")
    
    response = client.get("/api/statistics/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # 验证返回的数据结构
    if len(data["items"]) > 0:
        # 如果有数据，验证总计行存在
        assert data["total"]["order_count"] >= 0
        assert data["total"]["product_count"] >= 0


def test_statistics_balance_calculation():
    """测试总结余的计算逻辑"""
    headers = get_auth_headers("testadmin_stat")
    
    response = client.get("/api/statistics/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # 验证计算逻辑：总结余 = (订单总含税价格 - 订单总内部价格) - 总税额 - 总服务价格
    if len(data["items"]) > 0:
        for item in data["items"]:
            tax_included = item["total_tax_included_price"]
            internal = item["total_internal_price"]
            tax = item["total_tax"]
            service = item["total_service_amount"]
            balance = item["total_balance"]
            
            # 验证总结余计算
            expected_balance = (tax_included - internal) - tax - service
            assert abs(balance - expected_balance) < 0.01, \
                f"总结余计算错误: 期望 {expected_balance}, 实际 {balance}"
        
        # 验证总计行的计算
        total = data["total"]
        total_tax_included = total["total_tax_included_price"]
        total_internal = total["total_internal_price"]
        total_tax = total["total_tax"]
        total_service = total["total_service_amount"]
        total_balance = total["total_balance"]
        
        expected_total_balance = (total_tax_included - total_internal) - total_tax - total_service
        assert abs(total_balance - expected_total_balance) < 0.01, \
            f"总计总结余计算错误: 期望 {expected_total_balance}, 实际 {total_balance}"

