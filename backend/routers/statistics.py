"""
统计信息路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from backend.database import get_db
from backend.models import Order, ServiceRecord, Supplier, User
from backend.schemas import StatisticsResponse, StatisticsItem
from backend.auth import get_current_user, can_view_internal_price
from backend.utils import parse_order_content, calculate_order_totals
from backend.config import (
    USER_TYPE_ADMIN, USER_TYPE_NORMAL, USER_TYPE_SUPPLIER, USER_TYPE_STUDENT,
    ORDER_STATUS_CONFIRMED, SERVICE_STATUS_CONFIRMED, TAX_RATE
)

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


@router.get("/", response_model=StatisticsResponse)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取统计信息（课题组用户和管理员）
    按照供应商分组统计订单和服务记录
    
    Args:
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        StatisticsResponse: 统计信息响应
        
    Raises:
        HTTPException: 如果用户类型不允许
        
    使用样例:
        GET /api/statistics/
    """
    # 只有课题组用户和管理员可以查看统计信息（普通用户不能查看）
    if current_user.user_type == USER_TYPE_SUPPLIER or current_user.user_type == USER_TYPE_STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="供应商用户和普通用户不能查看统计信息"
        )
    
    can_view_internal = can_view_internal_price(current_user)
    
    # 构建订单查询（只统计确认状态的订单）
    order_query = db.query(Order).filter(Order.status == ORDER_STATUS_CONFIRMED)
    if current_user.user_type == USER_TYPE_NORMAL:
        # 课题组用户统计自己的订单以及其管理学生的订单
        from sqlalchemy import or_
        managed_students = db.query(User.id).filter(User.manager_id == current_user.id).all()
        managed_student_ids = [s[0] for s in managed_students]
        if managed_student_ids:
            order_query = order_query.filter(
                or_(
                    Order.user_id == current_user.id,
                    Order.user_id.in_(managed_student_ids)
                )
            )
        else:
            order_query = order_query.filter(Order.user_id == current_user.id)
    
    # 构建服务记录查询（只统计确认状态的服务）
    service_query = db.query(ServiceRecord).filter(ServiceRecord.status == SERVICE_STATUS_CONFIRMED)
    if current_user.user_type == USER_TYPE_NORMAL:
        # 课题组用户统计自己的服务记录以及其管理学生的服务记录
        from sqlalchemy import or_
        managed_students = db.query(User.id).filter(User.manager_id == current_user.id).all()
        managed_student_ids = [s[0] for s in managed_students]
        if managed_student_ids:
            service_query = service_query.filter(
                or_(
                    ServiceRecord.user_id == current_user.id,
                    ServiceRecord.user_id.in_(managed_student_ids)
                )
            )
        else:
            service_query = service_query.filter(ServiceRecord.user_id == current_user.id)
    
    # 获取所有相关的供应商ID
    supplier_ids = set()
    orders = order_query.all()
    services = service_query.all()
    
    for order in orders:
        supplier_ids.add(order.supplier_id)
    for service in services:
        supplier_ids.add(service.supplier_id)
    
    # 按供应商统计
    statistics_items = []
    total_order_count = 0
    total_product_count = 0
    total_internal_price = 0.0
    total_tax_included_price = 0.0
    total_service_amount = 0.0
    
    for supplier_id in supplier_ids:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            continue
        
        # 统计该供应商的订单
        supplier_orders = [o for o in orders if o.supplier_id == supplier_id]
        order_count = len(supplier_orders)
        product_count = 0
        supplier_internal_price = 0.0
        supplier_tax_included_price = 0.0
        
        for order in supplier_orders:
            items = parse_order_content(order.content)
            product_count += sum(item.get("quantity", 1) for item in items)
            totals = calculate_order_totals(items, include_internal=can_view_internal)
            if can_view_internal:
                supplier_internal_price += totals["total_internal_price"]
            supplier_tax_included_price += totals["total_tax_included_price"]
        
        # 统计该供应商的服务记录
        supplier_services = [s for s in services if s.supplier_id == supplier_id]
        supplier_service_amount = sum(s.amount for s in supplier_services)
        
        # 计算税额和结余
        # 总税额 = (订单总含税价格 - 订单总内部价格) * 13%
        supplier_tax = (supplier_tax_included_price - supplier_internal_price) * TAX_RATE
        # 总结余 = (订单总含税价格 - 订单总内部价格) - 总税额 - 总服务价格
        supplier_balance = (supplier_tax_included_price - supplier_internal_price) - supplier_tax - supplier_service_amount
        
        statistics_items.append(StatisticsItem(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            order_count=order_count,
            product_count=product_count,
            total_internal_price=supplier_internal_price,
            total_tax_included_price=supplier_tax_included_price,
            total_service_amount=supplier_service_amount,
            total_tax=supplier_tax,
            total_balance=supplier_balance
        ))
        
        # 累加总计
        total_order_count += order_count
        total_product_count += product_count
        total_internal_price += supplier_internal_price
        total_tax_included_price += supplier_tax_included_price
        total_service_amount += supplier_service_amount
    
    # 计算总计
    # 总税额 = (订单总含税价格 - 订单总内部价格) * 13%
    total_tax = (total_tax_included_price - total_internal_price) * TAX_RATE
    # 总结余 = (订单总含税价格 - 订单总内部价格) - 总税额 - 总服务价格
    total_balance = (total_tax_included_price - total_internal_price) - total_tax - total_service_amount
    
    total_item = StatisticsItem(
        supplier_id=0,
        supplier_name="总计",
        order_count=total_order_count,
        product_count=total_product_count,
        total_internal_price=total_internal_price,
        total_tax_included_price=total_tax_included_price,
        total_service_amount=total_service_amount,
        total_tax=total_tax,
        total_balance=total_balance
    )
    
    return StatisticsResponse(
        items=statistics_items,
        total=total_item
    )

