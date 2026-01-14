"""
商品管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.database import get_db
from backend.models import Product, Supplier, User
from backend.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, ProductFilter
)
from backend.auth import get_current_user, require_admin, require_supplier, can_view_internal_price
from backend.config import USER_TYPE_ADMIN, USER_TYPE_SUPPLIER
from backend.logger import get_logger
from typing import Optional

logger = get_logger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"])


def get_product_response(product: Product, can_view_internal: bool) -> ProductResponse:
    """
    获取商品响应对象（根据权限决定是否包含内部价格）
    
    Args:
        product: 商品对象
        can_view_internal: 是否可以查看内部价格
        
    Returns:
        ProductResponse: 商品响应对象
    """
    supplier_name = None
    if product.supplier_obj:
        supplier_name = product.supplier_obj.name
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        brand=product.brand,
        model=product.model,
        specification=product.specification,
        internal_price=product.internal_price if can_view_internal else None,
        tax_included_price=product.tax_included_price,
        supplier_id=product.supplier_id,
        supplier_name=supplier_name,
        is_deleted=product.is_deleted,
        created_at=product.created_at
    )


@router.get("/", response_model=ProductListResponse)
async def list_products(
    name: Optional[str] = Query(None, description="商品名称筛选"),
    model: Optional[str] = Query(None, description="型号筛选"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取商品列表（支持筛选和分页）
    
    Args:
        name: 商品名称筛选
        model: 型号筛选
        min_price: 最低价格
        max_price: 最高价格
        page: 页码
        page_size: 每页数量
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        ProductListResponse: 商品列表响应
        
    使用样例:
        GET /api/products/?name=商品&page=1&page_size=20
    """
    can_view_internal = can_view_internal_price(current_user)
    
    # 构建查询
    query = db.query(Product).filter(Product.is_deleted == False)
    
    # 供应商用户只能看到自己的商品
    if current_user.user_type == USER_TYPE_SUPPLIER:
        if not current_user.supplier_id:
            # 如果供应商用户没有关联的supplier_id，返回空结果
            query = query.filter(Product.id == -1)  # 永远不匹配的条件
        else:
            query = query.filter(Product.supplier_id == current_user.supplier_id)
    
    # 筛选条件
    if name:
        query = query.filter(Product.name.contains(name))
    if model:
        query = query.filter(Product.model.contains(model))
    if min_price is not None:
        query = query.filter(Product.tax_included_price >= min_price)
    if max_price is not None:
        query = query.filter(Product.tax_included_price <= max_price)
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    products = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()
    
    # 加载关联的供应商信息
    for product in products:
        if not product.supplier_obj:
            product.supplier_obj = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
    
    items = [get_product_response(p, can_view_internal) for p in products]
    
    return ProductListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单个商品详情
    
    Args:
        product_id: 商品ID
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        ProductResponse: 商品信息
        
    Raises:
        HTTPException: 如果商品不存在或无权访问
        
    使用样例:
        GET /api/products/1
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or product.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 供应商用户只能查看自己的商品
    if current_user.user_type == USER_TYPE_SUPPLIER:
        if not current_user.supplier_id or product.supplier_id != current_user.supplier_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此商品"
            )
    
    if not product.supplier_obj:
        product.supplier_obj = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
    
    can_view_internal = can_view_internal_price(current_user)
    return get_product_response(product, can_view_internal)


@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新商品（管理员和供应商用户）
    
    Args:
        product_data: 商品创建信息
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        ProductResponse: 创建的商品信息
        
    Raises:
        HTTPException: 如果用户类型不允许或供应商ID无效
        
    使用样例:
        POST /api/products/
        {
            "name": "商品名",
            "model": "型号",
            "specification": "规格",
            "tax_included_price": 100.0,
            "supplier_id": 1
        }
    """
    try:
        # 检查权限
        if current_user.user_type not in [USER_TYPE_ADMIN, USER_TYPE_SUPPLIER]:
            logger.warning(
                f"用户尝试创建商品但无权限: {current_user.username}",
                extra={"user_id": current_user.id, "user_type": current_user.user_type}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权创建商品"
            )
    
        # 供应商用户只能为自己创建商品，且不能设置内部价格
        if current_user.user_type == USER_TYPE_SUPPLIER:
            if not current_user.supplier_id or product_data.supplier_id != current_user.supplier_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只能为自己创建商品"
                )
            # 供应商用户创建商品时，内部价格默认为含税价格
            internal_price = product_data.tax_included_price
        else:
            # 管理员可以不提供内部价格，如果不提供则默认为含税价格
            if product_data.internal_price is None:
                internal_price = product_data.tax_included_price
            else:
                internal_price = product_data.internal_price
        
        # 验证供应商是否存在
        supplier = db.query(Supplier).filter(Supplier.id == product_data.supplier_id).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="供应商不存在"
            )
        
        # 创建商品
        new_product = Product(
            name=product_data.name,
            brand=product_data.brand,
            model=product_data.model,
            specification=product_data.specification,
            internal_price=internal_price,
            tax_included_price=product_data.tax_included_price,
            supplier_id=product_data.supplier_id,
            is_deleted=False
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        new_product.supplier_obj = supplier
        
        can_view_internal = can_view_internal_price(current_user)
        
        logger.info(
            f"商品创建成功: {new_product.name} (ID: {new_product.id})",
            extra={
                "product_id": new_product.id,
                "user_id": current_user.id,
                "supplier_id": new_product.supplier_id
            }
        )
        
        return get_product_response(new_product, can_view_internal)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"创建商品失败: {e}",
            exc_info=True,
            extra={
                "user_id": current_user.id,
                "product_name": product_data.name
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建商品失败"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新商品信息（管理员和供应商用户）
    
    Args:
        product_id: 商品ID
        product_data: 商品更新信息
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        ProductResponse: 更新后的商品信息
        
    Raises:
        HTTPException: 如果商品不存在或无权访问
        
    使用样例:
        PUT /api/products/1
        {
            "name": "新商品名",
            "tax_included_price": 120.0
        }
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or product.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 检查权限
    if current_user.user_type == USER_TYPE_SUPPLIER:
        if not current_user.supplier_id or product.supplier_id != current_user.supplier_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此商品"
            )
        # 供应商用户不能修改内部价格
        if product_data.internal_price is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="供应商用户不能修改内部价格"
            )
    elif current_user.user_type != USER_TYPE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改商品"
        )
    
    # 更新字段
    if product_data.name is not None:
        product.name = product_data.name
    if product_data.brand is not None:
        product.brand = product_data.brand
    if product_data.model is not None:
        product.model = product_data.model
    if product_data.specification is not None:
        product.specification = product_data.specification
    if product_data.tax_included_price is not None:
        product.tax_included_price = product_data.tax_included_price
    if product_data.internal_price is not None and current_user.user_type == USER_TYPE_ADMIN:
        product.internal_price = product_data.internal_price
    
    db.commit()
    db.refresh(product)
    
    if not product.supplier_obj:
        product.supplier_obj = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
    
    can_view_internal = can_view_internal_price(current_user)
    return get_product_response(product, can_view_internal)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除商品（软删除，仅管理员和供应商用户）
    
    Args:
        product_id: 商品ID
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        dict: 删除结果
        
    Raises:
        HTTPException: 如果商品不存在或无权访问
        
    使用样例:
        DELETE /api/products/1
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or product.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 检查权限
    if current_user.user_type == USER_TYPE_SUPPLIER:
        if not current_user.supplier_id or product.supplier_id != current_user.supplier_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此商品"
            )
    elif current_user.user_type != USER_TYPE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除商品"
        )
    
    # 软删除
    product.is_deleted = True
    db.commit()
    
    return {"success": True, "message": "商品删除成功"}

