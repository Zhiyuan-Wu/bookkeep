"""
商品管理功能测试
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, SessionLocal
from backend.models import User, Supplier, Product
from backend.utils import hash_password
from backend.config import USER_TYPE_ADMIN, USER_TYPE_SUPPLIER, USER_TYPE_NORMAL

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """测试前初始化数据库"""
    init_db()
    db = SessionLocal()
    try:
        # 创建测试供应商（先创建供应商，因为supplier_id是外键）
        existing_supplier = db.query(Supplier).filter(Supplier.name == "测试供应商").first()
        if not existing_supplier:
            supplier = Supplier(name="测试供应商")
            db.add(supplier)
            db.flush()  # 获取supplier.id
        
        # 创建测试用户（检查是否已存在）
        if not db.query(User).filter(User.username == "testadmin").first():
            admin = User(
                username="testadmin",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_ADMIN
            )
            db.add(admin)
        if not db.query(User).filter(User.username == "testsupplier").first():
            # 获取或创建supplier
            supplier = db.query(Supplier).filter(Supplier.name == "测试供应商").first()
            if not supplier:
                supplier = Supplier(name="测试供应商")
                db.add(supplier)
                db.flush()
            supplier_user = User(
                username="testsupplier",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_SUPPLIER,
                supplier_id=supplier.id  # 关联到supplier
            )
            db.add(supplier_user)
        if not db.query(User).filter(User.username == "testnormal").first():
            normal_user = User(
                username="testnormal",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_NORMAL
            )
            db.add(normal_user)
        db.commit()
    finally:
        db.close()
    yield
    # 测试后清理（可选）

def get_auth_headers(username="testadmin", password="testpass"):
    """获取认证headers"""
    response = client.post(
        "/api/users/login",
        json={"username": username, "password": password}
    )
    if response.status_code == 200 and response.json().get("success"):
        cookies = response.cookies
        return {"Cookie": f"bookkeep_session={cookies.get('bookkeep_session')}"}
    return {}

def test_create_product_as_admin():
    """测试管理员创建商品"""
    headers = get_auth_headers("testadmin")
    
    response = client.post(
        "/api/products/",
        json={
            "name": "测试商品",
            "model": "型号001",
            "specification": "规格说明",
            "internal_price": 80.0,
            "tax_included_price": 100.0,
            "supplier_id": 1
        },
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试商品"
    assert data["internal_price"] == 80.0

def test_create_product_as_supplier():
    """测试供应商用户创建商品"""
    headers = get_auth_headers("testsupplier")
    
    # 获取supplier用户的ID（供应商用户创建商品时，supplier_id必须等于自己的user_id）
    # 但supplier_id实际上指向suppliers表，所以我们需要先获取supplier的ID
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(Supplier.name == "测试供应商").first()
        supplier_id = supplier.id if supplier else 1
        
        # 获取supplier用户的ID
        supplier_user = db.query(User).filter(User.username == "testsupplier").first()
        # 注意：在实际系统中，supplier_user.id应该等于supplier.id
        # 但测试中可能不匹配，所以我们使用supplier_id
    finally:
        db.close()
    
    response = client.post(
        "/api/products/",
        json={
            "name": "供应商商品",
            "tax_included_price": 120.0,
            "supplier_id": supplier_id
        },
        headers=headers
    )
    # 供应商用户创建商品应该成功
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "供应商商品"
    # 供应商用户看不到内部价格（返回None）
    assert data["internal_price"] is None
    assert data["tax_included_price"] == 120.0

def test_create_product_as_normal_user():
    """测试课题组用户不能创建商品"""
    headers = get_auth_headers("testnormal")
    
    response = client.post(
        "/api/products/",
        json={
            "name": "课题组用户商品",
            "tax_included_price": 100.0,
            "supplier_id": 1
        },
        headers=headers
    )
    assert response.status_code == 403

def test_list_products():
    """测试获取商品列表"""
    headers = get_auth_headers("testadmin")
    
    response = client.get("/api/products/?page=1&page_size=20", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data

def test_get_product_detail():
    """测试获取商品详情"""
    headers = get_auth_headers("testadmin")
    
    # 先创建一个商品
    create_response = client.post(
        "/api/products/",
        json={
            "name": "详情测试商品",
            "tax_included_price": 150.0,
            "supplier_id": 1,
            "internal_price": 120.0
        },
        headers=headers
    )
    product_id = create_response.json()["id"]
    
    # 获取商品详情
    response = client.get(f"/api/products/{product_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == "详情测试商品"

def test_update_product():
    """测试更新商品"""
    headers = get_auth_headers("testadmin")
    
    # 先创建一个商品
    create_response = client.post(
        "/api/products/",
        json={
            "name": "更新测试商品",
            "tax_included_price": 100.0,
            "supplier_id": 1,
            "internal_price": 80.0
        },
        headers=headers
    )
    product_id = create_response.json()["id"]
    
    # 更新商品
    response = client.put(
        f"/api/products/{product_id}",
        json={
            "name": "更新后的商品名",
            "tax_included_price": 120.0
        },
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后的商品名"
    assert data["tax_included_price"] == 120.0

def test_delete_product():
    """测试删除商品（软删除）"""
    headers = get_auth_headers("testadmin")
    
    # 先创建一个商品
    create_response = client.post(
        "/api/products/",
        json={
            "name": "删除测试商品",
            "tax_included_price": 100.0,
            "supplier_id": 1,
            "internal_price": 80.0
        },
        headers=headers
    )
    product_id = create_response.json()["id"]
    
    # 删除商品
    response = client.delete(f"/api/products/{product_id}", headers=headers)
    assert response.status_code == 200
    
    # 验证商品已软删除（查询时应该被过滤）
    list_response = client.get("/api/products/", headers=headers)
    items = list_response.json()["items"]
    assert not any(item["id"] == product_id for item in items)

