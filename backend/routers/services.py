"""
服务记录管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from backend.database import get_db
from backend.models import ServiceRecord, Supplier, User
from backend.schemas import (
    ServiceRecordCreate, ServiceRecordUpdate, ServiceRecordResponse,
    ServiceRecordListResponse, ServiceRecordFilter
)
from backend.auth import get_current_user, require_admin
from backend.config import (
    USER_TYPE_ADMIN, USER_TYPE_NORMAL, USER_TYPE_SUPPLIER, USER_TYPE_STUDENT,
    SERVICE_STATUS_DRAFT, SERVICE_STATUS_SUBMITTED, SERVICE_STATUS_CONFIRMED, SERVICE_STATUS_INVALID
)
from backend.logger import get_logger
from backend.email_sender import send_service_notification
from typing import Optional
from datetime import datetime

logger = get_logger(__name__)
router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("/", response_model=ServiceRecordListResponse)
async def list_services(
    supplier_id: Optional[int] = Query(None, description="厂家ID筛选"),
    content: Optional[str] = Query(None, description="服务内容筛选"),
    min_amount: Optional[float] = Query(None, ge=0, description="最低金额"),
    max_amount: Optional[float] = Query(None, ge=0, description="最高金额"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    status: Optional[str] = Query(None, description="服务状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取服务记录列表（支持筛选和分页）
    
    Args:
        supplier_id: 厂家ID筛选
        content: 服务内容筛选
        min_amount: 最低金额
        max_amount: 最高金额
        start_date: 开始日期
        end_date: 结束日期
        status: 服务状态
        page: 页码
        page_size: 每页数量
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        ServiceRecordListResponse: 服务记录列表响应
        
    使用样例:
        GET /api/services/?page=1&page_size=20
    """
    # 构建查询
    query = db.query(ServiceRecord)
    
    # 权限控制
    if current_user.user_type == USER_TYPE_ADMIN:
        # 管理员可以看到所有服务记录
        pass
    elif current_user.user_type == USER_TYPE_NORMAL:
        # 普通用户可以看到自己的服务记录以及其管理学生的服务记录，且不能看到暂存状态的服务记录
        from sqlalchemy import or_
        # 查询管理的学生用户ID列表
        managed_students = db.query(User.id).filter(User.manager_id == current_user.id).all()
        managed_student_ids = [s[0] for s in managed_students]
        # 自己的服务记录 + 管理学生的服务记录
        if managed_student_ids:
            query = query.filter(
                or_(
                    ServiceRecord.user_id == current_user.id,
                    ServiceRecord.user_id.in_(managed_student_ids)
                )
            )
        else:
            query = query.filter(ServiceRecord.user_id == current_user.id)

        query = query.filter(ServiceRecord.status != SERVICE_STATUS_DRAFT)
    elif current_user.user_type == USER_TYPE_STUDENT:
        # 学生用户只能看到自己的服务记录
        query = query.filter(ServiceRecord.user_id == current_user.id)
        query = query.filter(ServiceRecord.status != SERVICE_STATUS_DRAFT)
    elif current_user.user_type == USER_TYPE_SUPPLIER:
        # 厂家用户只能看到自己的服务记录
        if not current_user.supplier_id:
            # 如果厂家用户没有关联的supplier_id，返回空结果
            query = query.filter(ServiceRecord.id == -1)  # 永远不匹配的条件
        else:
            query = query.filter(ServiceRecord.supplier_id == current_user.supplier_id)
    
    # 筛选条件
    if supplier_id:
        query = query.filter(ServiceRecord.supplier_id == supplier_id)
    if status:
        query = query.filter(ServiceRecord.status == status)
    if content:
        query = query.filter(ServiceRecord.content.contains(content))
    if min_amount is not None:
        query = query.filter(ServiceRecord.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(ServiceRecord.amount <= max_amount)
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(ServiceRecord.created_at >= start_dt)
        except:
            pass
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(ServiceRecord.created_at <= end_dt)
        except:
            pass
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    services = query.order_by(ServiceRecord.created_at.desc()).offset(offset).limit(page_size).all()
    
    # 加载关联的厂家信息
    for service in services:
        if not service.supplier:
            service.supplier = db.query(Supplier).filter(Supplier.id == service.supplier_id).first()
    
    items = []
    for service in services:
        supplier_name = service.supplier.name if service.supplier else None
        user = db.query(User).filter(User.id == service.user_id).first()
        username = user.username if user else None
        items.append(ServiceRecordResponse(
            id=service.id,
            user_id=service.user_id,
            username=username,
            supplier_id=service.supplier_id,
            supplier_name=supplier_name,
            content=service.content,
            amount=service.amount,
            status=service.status,
            created_at=service.created_at
        ))
    
    return ServiceRecordListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size
    )


@router.get("/{service_id}", response_model=ServiceRecordResponse)
async def get_service_detail(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取服务记录详情
    
    Args:
        service_id: 服务记录ID
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        ServiceRecordResponse: 服务记录信息
        
    Raises:
        HTTPException: 如果服务记录不存在或无权访问
        
    使用样例:
        GET /api/services/1
    """
    service = db.query(ServiceRecord).filter(ServiceRecord.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务记录不存在"
        )
    
    # 权限控制
    if current_user.user_type == USER_TYPE_NORMAL:
        # 普通用户可以访问自己的服务记录以及其管理学生的服务记录
        if service.user_id != current_user.id:
            # 检查是否是管理的学生
            student = db.query(User).filter(
                User.id == service.user_id,
                User.manager_id == current_user.id
            ).first()
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此服务记录"
                )
    elif current_user.user_type == USER_TYPE_STUDENT:
        # 学生用户只能访问自己的服务记录
        if service.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此服务记录"
            )
    elif current_user.user_type == USER_TYPE_SUPPLIER:
        if not current_user.supplier_id or service.supplier_id != current_user.supplier_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此服务记录"
            )
    
    # 加载厂家信息
    if not service.supplier:
        service.supplier = db.query(Supplier).filter(Supplier.id == service.supplier_id).first()
    
    # 加载用户信息
    user = db.query(User).filter(User.id == service.user_id).first()
    username = user.username if user else None
    
    return ServiceRecordResponse(
        id=service.id,
        user_id=service.user_id,
        username=username,
        supplier_id=service.supplier_id,
        supplier_name=service.supplier.name if service.supplier else None,
        content=service.content,
        amount=service.amount,
        status=service.status,
        created_at=service.created_at
    )


@router.post("/", response_model=ServiceRecordResponse)
async def create_service(
    service_data: ServiceRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建服务记录（厂家用户）
    
    厂家创建服务记录时，需要指定关联的普通用户或管理员用户名。
    语义：厂家向对应用户提供了服务。
    
    Args:
        service_data: 服务记录创建信息（包含 supplier_id, content, amount, user_username）
        current_user: 当前登录用户（必须是厂家用户）
        db: 数据库会话
        
    Returns:
        ServiceRecordResponse: 创建的服务记录信息
        
    Raises:
        HTTPException: 如果用户类型不允许、厂家ID无效、用户名不存在或用户类型不正确
        
    使用样例:
        POST /api/services/
        {
            "supplier_id": 1,
            "content": "服务内容",
            "amount": 1000.0,
            "user_username": "普通用户1"
        }
    """
    print(service_data)
    print(current_user)
    # 只有厂家用户可以创建服务记录
    if current_user.user_type != USER_TYPE_SUPPLIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有厂家用户可以创建服务记录"
        )
    
    # 厂家用户只能为自己创建服务记录
    if not current_user.supplier_id or service_data.supplier_id != current_user.supplier_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能为自己创建服务记录"
        )
    
    # 验证厂家是否存在
    supplier = db.query(Supplier).filter(Supplier.id == service_data.supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="厂家不存在"
        )
    
    # 厂家创建服务记录时，必须提供关联的用户名（普通用户或管理员）
    if not service_data.user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供关联的用户名（普通用户或管理员）"
        )
    
    # 查找关联的用户
    target_user = db.query(User).filter(User.username == service_data.user_username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 '{service_data.user_username}' 不存在"
        )
    
    # 验证用户类型：必须是普通用户或管理员，不能是厂家
    if target_user.user_type == USER_TYPE_SUPPLIER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="服务记录只能关联到普通用户或管理员，不能关联到厂家用户"
        )
    
    # 创建服务记录（暂存状态）
    # 厂家向对应用户提供服务，将服务记录关联到该用户
    new_service = ServiceRecord(
        user_id=target_user.id,  # 关联到普通用户或管理员
        supplier_id=service_data.supplier_id,
        content=service_data.content,
        amount=service_data.amount,
        status=SERVICE_STATUS_DRAFT
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    new_service.supplier = supplier
    
    logger.info(
        f"厂家用户创建服务记录: 服务ID={new_service.id}, 厂家ID={supplier.id}, 关联用户={target_user.username}",
        extra={
            "service_id": new_service.id,
            "supplier_id": supplier.id,
            "user_id": target_user.id,
            "user_username": target_user.username,
            "current_user_id": current_user.id,
        }
    )
    
    return ServiceRecordResponse(
        id=new_service.id,
        user_id=new_service.user_id,
        username=target_user.username,
        supplier_id=new_service.supplier_id,
        supplier_name=supplier.name,
        content=new_service.content,
        amount=new_service.amount,
        status=new_service.status,
        created_at=new_service.created_at
    )


@router.put("/{service_id}", response_model=ServiceRecordResponse)
async def update_service(
    service_id: int,
    service_data: ServiceRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新服务记录（厂家用户）
    
    Args:
        service_id: 服务记录ID
        service_data: 服务记录更新信息
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        ServiceRecordResponse: 更新后的服务记录信息
        
    Raises:
        HTTPException: 如果服务记录不存在或无权访问
        
    使用样例:
        PUT /api/services/1
        {
            "content": "更新后的服务内容",
            "amount": 1200.0
        }
    """
    service = db.query(ServiceRecord).filter(ServiceRecord.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务记录不存在"
        )
    
    # 只有厂家用户可以更新自己的服务记录
    if current_user.user_type != USER_TYPE_SUPPLIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有厂家用户可以更新服务记录"
        )
    
    if not current_user.supplier_id or service.supplier_id != current_user.supplier_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新此服务记录"
        )
    
    # 只能更新暂存状态的服务记录
    if service.status != SERVICE_STATUS_DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能更新暂存状态的服务记录"
        )
    
    # 更新字段
    if service_data.content is not None:
        service.content = service_data.content
    if service_data.amount is not None:
        service.amount = service_data.amount
    
    db.commit()
    db.refresh(service)
    
    if not service.supplier:
        service.supplier = db.query(Supplier).filter(Supplier.id == service.supplier_id).first()
    
    # 加载用户信息
    user = db.query(User).filter(User.id == service.user_id).first()
    username = user.username if user else None
    
    return ServiceRecordResponse(
        id=service.id,
        user_id=service.user_id,
        username=username,
        supplier_id=service.supplier_id,
        supplier_name=service.supplier.name if service.supplier else None,
        content=service.content,
        amount=service.amount,
        status=service.status,
        created_at=service.created_at
    )


@router.put("/{service_id}/status")
async def update_service_status(
    service_id: int,
    new_status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新服务记录状态（普通用户和管理员可以确认）
    
    Args:
        service_id: 服务记录ID
        new_status: 新状态
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        dict: 更新结果
        
    Raises:
        HTTPException: 如果服务记录不存在或状态转换无效
        
    使用样例:
        PUT /api/services/1/status?new_status=确认
    """
    service = db.query(ServiceRecord).filter(ServiceRecord.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务记录不存在"
        )
    
    # 权限控制
    if current_user.user_type == USER_TYPE_NORMAL:
        # 普通用户可以操作自己的服务记录以及其管理学生的服务记录
        # 检查是否有权限操作此服务记录
        has_permission = (service.user_id == current_user.id)
        if not has_permission:
            # 检查是否是管理的学生
            student = db.query(User).filter(
                User.id == service.user_id,
                User.manager_id == current_user.id
            ).first()
            has_permission = (student is not None)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此服务记录"
            )
        
        if new_status == SERVICE_STATUS_CONFIRMED:
            if service.status != SERVICE_STATUS_SUBMITTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能确认处于发起状态的服务记录"
                )
        elif new_status == SERVICE_STATUS_INVALID:
            # 普通用户可以删除服务记录（转为无效）
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="普通用户只能确认或删除服务记录"
            )
    elif current_user.user_type == USER_TYPE_STUDENT:
        # 学生用户可以操作自己的服务记录
        if service.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此服务记录"
            )
        if new_status == SERVICE_STATUS_CONFIRMED:
            if service.status != SERVICE_STATUS_SUBMITTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能确认处于发起状态的服务记录"
                )
        elif new_status == SERVICE_STATUS_INVALID:
            # 学生用户可以删除服务记录（转为无效）
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="学生用户只能确认或删除服务记录"
            )
    elif current_user.user_type == USER_TYPE_SUPPLIER:
        # 厂家用户只能发起自己的服务记录
        if new_status == SERVICE_STATUS_SUBMITTED:
            if service.status != SERVICE_STATUS_DRAFT:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能发起处于暂存状态的服务记录"
                )
            if not current_user.supplier_id or service.supplier_id != current_user.supplier_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权操作此服务记录"
                )
        elif new_status == SERVICE_STATUS_INVALID:
            # 厂家用户可以删除服务记录（转为无效）
            if not current_user.supplier_id or service.supplier_id != current_user.supplier_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权操作此服务记录"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="厂家用户只能发起或删除服务记录"
            )
    # 管理员可以执行任何状态转换
    
    # 验证状态
    valid_statuses = [SERVICE_STATUS_DRAFT, SERVICE_STATUS_SUBMITTED, SERVICE_STATUS_CONFIRMED, SERVICE_STATUS_INVALID]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态，必须是: {', '.join(valid_statuses)}"
        )
    
    # 加载关联信息（用于邮件通知）
    if not service.supplier:
        service.supplier = db.query(Supplier).filter(Supplier.id == service.supplier_id).first()
    if not service.user:
        service.user = db.query(User).filter(User.id == service.user_id).first()
    
    service.status = new_status
    db.commit()
    db.refresh(service)
    
    # 发送邮件通知
    if new_status == SERVICE_STATUS_SUBMITTED:
        # 发起服务记录：向服务接收用户发送通知
        if service.user and service.user.email:
            await send_service_notification(
                to_email=service.user.email,
                to_name=service.user.username,
                service_id=service.id,
                service_status=SERVICE_STATUS_SUBMITTED,
                supplier_name=service.supplier.name if service.supplier else None,
                service_content=service.content,
                service_amount=service.amount
            )
    elif new_status == SERVICE_STATUS_CONFIRMED:
        # 确认服务记录：向厂家用户发送通知
        if service.supplier and service.supplier.user and service.supplier.user.email:
            await send_service_notification(
                to_email=service.supplier.user.email,
                to_name=service.supplier.user.username,
                service_id=service.id,
                service_status=SERVICE_STATUS_CONFIRMED,
                supplier_name=service.supplier.name,
                service_content=service.content,
                service_amount=service.amount
            )
    
    logger.info(
        f"服务记录状态更新成功: 服务ID={service_id}, 新状态={new_status}, 用户={current_user.username}",
        extra={
            "service_id": service_id,
            "new_status": new_status,
            "user_id": current_user.id,
            "user_type": current_user.user_type
        }
    )
    
    return {"success": True, "message": "服务记录状态更新成功"}


@router.delete("/{service_id}")
async def delete_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除服务记录（普通用户、学生用户和管理员）
    暂存和发起状态的服务可以直接删除，确认状态的服务删除后将转移到无效状态
    
    Args:
        service_id: 服务记录ID
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        dict: 删除结果
        
    Raises:
        HTTPException: 如果服务记录不存在或无权访问
        
    使用样例:
        DELETE /api/services/1
    """
    service = db.query(ServiceRecord).filter(ServiceRecord.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务记录不存在"
        )
    
    # 权限控制
    if current_user.user_type == USER_TYPE_NORMAL:
        # 普通用户可以删除自己的服务记录以及其管理学生的服务记录
        if service.user_id != current_user.id:
            # 检查是否是管理的学生
            student = db.query(User).filter(
                User.id == service.user_id,
                User.manager_id == current_user.id
            ).first()
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权删除此服务记录"
                )
    elif current_user.user_type == USER_TYPE_STUDENT:
        # 学生用户只能删除自己的服务记录
        if service.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此服务记录"
            )
    
    # 无效的服务记录不能删除
    if current_user.user_type != USER_TYPE_ADMIN and service.status == SERVICE_STATUS_INVALID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="服务记录已失效"
        )
    
    # 确认状态的服务转移到无效状态，其他状态直接删除
    if service.status == SERVICE_STATUS_CONFIRMED:
        service.status = SERVICE_STATUS_INVALID
        db.commit()
        return {"success": True, "message": "服务记录已标记为无效"}
    else:
        db.delete(service)
        db.commit()
        return {"success": True, "message": "服务记录删除成功"}

