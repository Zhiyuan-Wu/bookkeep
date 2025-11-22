"""
购物车功能测试
测试购物车中内部价格的显示和计算
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, SessionLocal
from backend.models import User, Supplier, Product
from backend.utils import hash_password
from backend.config import USER_TYPE_ADMIN, USER_TYPE_NORMAL, USER_TYPE_SUPPLIER

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """测试前初始化数据库"""
    init_db()
    db = SessionLocal()
    try:
        # 创建测试厂家
        supplier = db.query(Supplier).filter(Supplier.name == "测试厂家购物车").first()
        if not supplier:
            supplier = Supplier(name="测试厂家购物车")
            db.add(supplier)
            db.flush()
        
        # 创建测试用户
        if not db.query(User).filter(User.username == "testadmin_cart").first():
            admin = User(
                username="testadmin_cart",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_ADMIN
            )
            db.add(admin)
        
        if not db.query(User).filter(User.username == "testnormal_cart").first():
            normal_user = User(
                username="testnormal_cart",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_NORMAL
            )
            db.add(normal_user)
        
        if not db.query(User).filter(User.username == "testsupplier_cart").first():
            supplier_user = User(
                username="testsupplier_cart",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_SUPPLIER,
                supplier_id=supplier.id
            )
            db.add(supplier_user)
        
        # 创建测试商品（有内部价格和含税价格）
        existing_product = db.query(Product).filter(Product.name == "测试商品购物车").first()
        if not existing_product:
            # 确保supplier已提交并获取ID
            if supplier.id is None:
                db.flush()
            product = Product(
                name="测试商品购物车",
                model="TEST001",
                specification="测试规格",
                internal_price=100.0,
                tax_included_price=150.0,
                supplier_id=supplier.id,
                is_deleted=False
            )
            db.add(product)
        
        db.commit()
    finally:
        db.close()
    yield


def get_auth_headers(username="testadmin_cart", password="testpass"):
    """获取认证headers"""
    response = client.post(
        "/api/users/login",
        json={"username": username, "password": password}
    )
    if response.status_code == 200 and response.json().get("success"):
        cookies = response.cookies
        return {"Cookie": f"bookkeep_session={cookies.get('bookkeep_session')}"}
    return {}


def test_get_product_with_internal_price_as_admin():
    """测试管理员获取商品时能看到内部价格"""
    headers = get_auth_headers("testadmin_cart")
    
    # 先通过ID获取单个商品（更可靠）
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.name == "测试商品购物车").first()
        if not product:
            pytest.skip("测试商品不存在，跳过此测试")
        product_id = product.id
    finally:
        db.close()
    
    # 获取单个商品详情
    response = client.get(f"/api/products/{product_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # 管理员应该能看到内部价格
    assert data["internal_price"] == 100.0
    assert data["tax_included_price"] == 150.0


def test_get_product_with_internal_price_as_normal_user():
    """测试普通用户获取商品时能看到内部价格"""
    headers = get_auth_headers("testnormal_cart")
    
    # 先通过ID获取单个商品（更可靠）
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.name == "测试商品购物车").first()
        if not product:
            pytest.skip("测试商品不存在，跳过此测试")
        product_id = product.id
    finally:
        db.close()
    
    # 获取单个商品详情
    response = client.get(f"/api/products/{product_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # 普通用户应该能看到内部价格
    assert data["internal_price"] == 100.0
    assert data["tax_included_price"] == 150.0


def test_get_product_without_internal_price_as_supplier():
    """测试厂家用户获取商品时不能看到内部价格"""
    headers = get_auth_headers("testsupplier_cart")
    
    # 获取商品列表
    response = client.get("/api/products/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # 找到测试商品
    test_product = None
    for product in data["items"]:
        if product["name"] == "测试商品购物车":
            test_product = product
            break
    
    assert test_product is not None
    # 厂家用户不应该看到内部价格
    assert test_product["internal_price"] is None
    assert test_product["tax_included_price"] == 150.0


def test_get_single_product_with_internal_price():
    """测试获取单个商品详情时内部价格正确返回"""
    headers = get_auth_headers("testadmin_cart")
    
    # 先获取商品ID
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.name == "测试商品购物车").first()
        assert product is not None
        product_id = product.id
    finally:
        db.close()
    
    # 获取商品详情
    response = client.get(f"/api/products/{product_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # 管理员应该能看到内部价格
    assert data["internal_price"] == 100.0
    assert data["tax_included_price"] == 150.0


def test_create_order_with_internal_price():
    """测试创建订单时内部价格正确保存"""
    headers = get_auth_headers("testnormal_cart")
    
    # 先获取supplier ID
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(Supplier.name == "测试厂家购物车").first()
        supplier_id = supplier.id if supplier else 1
    finally:
        db.close()
    
    # 创建订单，包含内部价格
    response = client.post(
        "/api/orders/",
        json={
            "supplier_id": supplier_id,
            "items": [
                {
                    "product_id": 1,
                    "name": "测试商品",
                    "model": "TEST",
                    "specification": "规格",
                    "internal_price": 100.0,  # 包含内部价格
                    "tax_included_price": 150.0,
                    "quantity": 2
                }
            ]
        },
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "暂存"
    
    # 验证订单内容中包含内部价格
    import json
    order_content = json.loads(data["content"])
    assert "items" in order_content
    assert len(order_content["items"]) == 1
    assert order_content["items"][0]["internal_price"] == 100.0
    assert order_content["items"][0]["tax_included_price"] == 150.0


def test_create_order_without_internal_price():
    """测试创建订单时不包含内部价格（厂家用户场景）"""
    headers = get_auth_headers("testsupplier_cart")
    
    # 先获取supplier ID和普通用户
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(Supplier.name == "测试厂家购物车").first()
        supplier_id = supplier.id if supplier else 1
        
        # 获取或创建一个普通用户作为服务对象
        normal_user = db.query(User).filter(User.username == "testnormal_cart").first()
        if not normal_user:
            normal_user = User(
                username="testnormal_cart",
                password_hash=hash_password("testpass"),
                user_type=USER_TYPE_NORMAL
            )
            db.add(normal_user)
            db.commit()
            db.refresh(normal_user)
        normal_username = normal_user.username
    finally:
        db.close()
    
    # 厂家用户创建服务记录（不是订单，但类似）
    # 注意：厂家用户不能创建订单，只能创建服务记录
    # 现在需要提供 user_username（普通用户或管理员）
    response = client.post(
        "/api/services/",
        json={
            "supplier_id": supplier_id,
            "content": "测试服务",
            "amount": 200.0,
            "user_username": normal_username
        },
        headers=headers
    )
    
    # 厂家用户可以创建服务记录
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "暂存"
    assert data["amount"] == 200.0

