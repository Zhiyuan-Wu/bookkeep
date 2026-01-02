"""
用户管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Product, Supplier
from backend.schemas import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse, RegisterRequest, UserContactUpdate
)
from backend.auth import (
    get_current_user, require_admin, create_session, delete_session,
    can_view_internal_price
)
from backend.utils import hash_password, verify_password
from backend.config import (
    USER_TYPE_ADMIN, USER_TYPE_NORMAL, USER_TYPE_SUPPLIER, USER_TYPE_STUDENT,
    ALLOW_SELF_REGISTRATION
)
from backend.logger import get_logger
from typing import List

logger = get_logger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    Args:
        login_data: 登录信息（用户名和密码）
        response: FastAPI响应对象
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        LoginResponse: 登录结果和用户信息
        
    使用样例:
        POST /api/users/login
        {
            "username": "admin",
            "password": "password123"
        }
    """
    try:
        user = db.query(User).filter(User.username == login_data.username).first()
        
        if not user or not verify_password(login_data.password, user.password_hash):
            logger.warning(
                f"登录失败: 用户名或密码错误",
                extra={
                    "username": login_data.username,
                    "client": request.client.host if request.client else None,
                }
            )
            return LoginResponse(
                success=False,
                message="用户名或密码错误"
            )
        
        # 创建session
        session_id = create_session(user.id, user.username, user.user_type)
        
        # 设置cookie
        response.set_cookie(
            key="bookkeep_session",
            value=session_id,
            max_age=86400,  # 24小时
            httponly=True,
            samesite="lax"
        )
        
        logger.info(
            f"用户登录成功: {user.username} (类型: {user.user_type})",
            extra={
                "user_id": user.id,
                "user_type": user.user_type,
                "client": request.client.host if request.client else None,
            }
        )
        
        # 构建响应，包含管理用户名称
        manager_username = None
        if user.manager_id:
            manager = db.query(User).filter(User.id == user.manager_id).first()
            if manager:
                manager_username = manager.username
        
        return LoginResponse(
            success=True,
            message="登录成功",
            user=UserResponse(
                id=user.id,
                username=user.username,
                user_type=user.user_type,
                supplier_id=user.supplier_id,
                manager_id=user.manager_id,
                manager_username=manager_username,
                email=user.email,
                phone=user.phone,
                created_at=user.created_at
            )
        )
    except Exception as e:
        logger.error(
            f"登录过程发生错误: {e}",
            exc_info=True,
            extra={
                "username": login_data.username,
                "client": request.client.host if request.client else None,
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程发生错误"
        )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    用户登出
    
    Args:
        response: FastAPI响应对象
        current_user: 当前登录用户
        
    Returns:
        dict: 登出结果
        
    使用样例:
        POST /api/users/logout
    """
    # 从请求中获取session_id
    from fastapi import Request
    # 注意：这里需要从request中获取，但为了简化，我们直接删除cookie
    response.delete_cookie(key="bookkeep_session")
    
    return {"success": True, "message": "登出成功"}


@router.post("/register", response_model=LoginResponse)
async def register(
    register_data: RegisterRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    学生用户自助注册
    
    Args:
        register_data: 注册信息（用户名、密码、管理用户名称）
        response: FastAPI响应对象
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        LoginResponse: 注册结果和用户信息
        
    Raises:
        HTTPException: 如果自助注册被禁用、用户名已存在、管理用户不存在或类型不正确
        
    使用样例:
        POST /api/users/register
        {
            "username": "student1",
            "password": "password123",
            "manager_username": "normal_user"
        }
    """
    # 检查是否允许自助注册
    if not ALLOW_SELF_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="自助注册功能已禁用"
        )
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == register_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 查找管理用户
    manager = db.query(User).filter(User.username == register_data.manager_username).first()
    
    # 验证管理用户类型：必须是普通用户
    if not manager or manager.user_type != USER_TYPE_NORMAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请咨询管理员并输入正确的管理用户名称"
        )
    
    # 创建学生用户
    new_user = User(
        username=register_data.username,
        password_hash=hash_password(register_data.password),
        user_type=USER_TYPE_STUDENT,
        manager_id=manager.id,
        email=register_data.email,
        phone=register_data.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 创建session
    session_id = create_session(new_user.id, new_user.username, new_user.user_type)
    
    # 设置cookie
    response.set_cookie(
        key="bookkeep_session",
        value=session_id,
        max_age=86400,  # 24小时
        httponly=True,
        samesite="lax"
    )
    
    logger.info(
        f"学生用户注册成功: {new_user.username} (管理用户: {manager.username})",
        extra={
            "user_id": new_user.id,
            "manager_id": manager.id,
            "client": request.client.host if request.client else None,
        }
    )
    
    # 构建响应，包含管理用户名称
    user_response = UserResponse(
        id=new_user.id,
        username=new_user.username,
        user_type=new_user.user_type,
        supplier_id=new_user.supplier_id,
        manager_id=new_user.manager_id,
        manager_username=manager.username,
        email=new_user.email,
        phone=new_user.phone,
        created_at=new_user.created_at
    )
    
    return LoginResponse(
        success=True,
        message="注册成功",
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        UserResponse: 用户信息
        
    使用样例:
        GET /api/users/me
    """
    # 如果是学生用户，加载管理用户信息
    manager_username = None
    if current_user.manager_id:
        manager = db.query(User).filter(User.id == current_user.manager_id).first()
        if manager:
            manager_username = manager.username
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        user_type=current_user.user_type,
        supplier_id=current_user.supplier_id,
        manager_id=current_user.manager_id,
        manager_username=manager_username,
        email=current_user.email,
        phone=current_user.phone,
        created_at=current_user.created_at
    )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取所有用户列表（仅管理员）
    
    Args:
        current_user: 当前登录用户（必须是管理员）
        db: 数据库会话
        
    Returns:
        List[UserResponse]: 用户列表
        
    使用样例:
        GET /api/users/
    """
    users = db.query(User).all()
    result = []
    for user in users:
        manager_username = None
        if user.manager_id:
            manager = db.query(User).filter(User.id == user.manager_id).first()
            if manager:
                manager_username = manager.username
        result.append(UserResponse(
            id=user.id,
            username=user.username,
            user_type=user.user_type,
            supplier_id=user.supplier_id,
            manager_id=user.manager_id,
            manager_username=manager_username,
            email=user.email,
            phone=user.phone,
            created_at=user.created_at
        ))
    return result


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    创建新用户（仅管理员）
    
    Args:
        user_data: 用户创建信息
        current_user: 当前登录用户（必须是管理员）
        db: 数据库会话
        
    Returns:
        UserResponse: 创建的用户信息
        
    Raises:
        HTTPException: 如果用户名已存在或用户类型无效
        
    使用样例:
        POST /api/users/
        {
            "username": "newuser",
            "password": "password123",
            "user_type": "普通用户"
        }
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 验证用户类型
    valid_types = [USER_TYPE_ADMIN, USER_TYPE_NORMAL, USER_TYPE_SUPPLIER, USER_TYPE_STUDENT]
    if user_data.user_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的用户类型，必须是: {', '.join(valid_types)}"
        )

    # 厂家用户自动创建厂家
    if user_data.user_type == USER_TYPE_SUPPLIER:
        supplier = Supplier(name=user_data.username)
        db.add(supplier)
        db.flush()
        supplier_id = supplier.id
    else:
        supplier_id = None
    
    # 学生用户需要管理用户
    manager_id = None
    if user_data.user_type == USER_TYPE_STUDENT:
        if not user_data.manager_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生用户必须指定管理用户ID"
            )
        # 验证管理用户是否存在且是普通用户
        manager = db.query(User).filter(User.id == user_data.manager_id).first()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="管理用户不存在"
            )
        if manager.user_type != USER_TYPE_NORMAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="管理用户必须是普通用户类型"
            )
        manager_id = user_data.manager_id
    
    # 创建用户
    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        user_type=user_data.user_type,
        supplier_id=supplier_id,
        manager_id=manager_id,
        email=user_data.email,
        phone=user_data.phone
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 构建响应，包含管理用户名称
    manager_username = None
    if new_user.manager_id:
        manager = db.query(User).filter(User.id == new_user.manager_id).first()
        if manager:
            manager_username = manager.username
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        user_type=new_user.user_type,
        supplier_id=new_user.supplier_id,
        manager_id=new_user.manager_id,
        manager_username=manager_username,
        email=new_user.email,
        phone=new_user.phone,
        created_at=new_user.created_at
    )


@router.put("/{user_id}/password", response_model=UserResponse)
async def update_user_password(
    user_id: int,
    password_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    修改用户密码（仅管理员）
    
    Args:
        user_id: 用户ID
        password_data: 新密码
        current_user: 当前登录用户（必须是管理员）
        db: 数据库会话
        
    Returns:
        UserResponse: 更新后的用户信息
        
    Raises:
        HTTPException: 如果用户不存在
        
    使用样例:
        PUT /api/users/1/password
        {
            "password": "newpassword123"
        }
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.password_hash = hash_password(password_data.password)
    db.commit()
    db.refresh(user)
    
    # 构建响应，包含管理用户名称
    manager_username = None
    if user.manager_id:
        manager = db.query(User).filter(User.id == user.manager_id).first()
        if manager:
            manager_username = manager.username
    
    return UserResponse(
        id=user.id,
        username=user.username,
        user_type=user.user_type,
        supplier_id=user.supplier_id,
        manager_id=user.manager_id,
        manager_username=manager_username,
        email=user.email,
        phone=user.phone,
        created_at=user.created_at
    )

@router.put("/{user_id}/contact")
async def update_user_contact(
    user_id: int,
    contact_data: UserContactUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    修改用户联系方式（仅管理员）
    
    Args:
        user_id: 用户ID
        contact_data: 新联系方式
        current_user: 当前登录用户（必须是管理员）
        db: 数据库会话
        
    Returns:
        UserResponse: 更新后的用户信息
        
    Raises:
        HTTPException: 如果用户不存在
        
    使用样例:
        PUT /api/users/1/password
        {
            "email": "newemail@example.com",
            "phone": "1234567890"
        }
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.email = contact_data.email
    user.phone = contact_data.phone
    db.commit()
    db.refresh(user)
    
    logger.info(
        f"用户联系方式修改成功: {user.username} (邮箱: {user.email}, 手机号: {user.phone})",
        extra={
            "user_id": user.id,
            "email": user.email,
            "phone": user.phone,
        }
    )
    return {"success": True, "message": "联系方式修改成功"}

@router.put("/me/password")
async def update_own_password(
    password_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改自己的密码
    
    Args:
        password_data: 新密码
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        dict: 更新结果
        
    使用样例:
        PUT /api/users/me/password
        {
            "password": "newpassword123"
        }
    """
    current_user.password_hash = hash_password(password_data.password)
    db.commit()
    
    return {"success": True, "message": "密码修改成功"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    删除用户（仅管理员）
    同时删除该用户关联的所有商品
    
    Args:
        user_id: 用户ID
        current_user: 当前登录用户（必须是管理员）
        db: 数据库会话
        
    Returns:
        dict: 删除结果
        
    Raises:
        HTTPException: 如果用户不存在或尝试删除自己
        
    使用样例:
        DELETE /api/users/1
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 删除关联的商品（软删除）
    # 注意：Product.supplier_id指向suppliers表，不是users表
    # 如果用户是厂家，需要先找到对应的supplier，然后删除该supplier的商品
    if user.user_type == "厂家" and user.supplier_id:
        products = db.query(Product).filter(Product.supplier_id == user.supplier_id).all()
        for product in products:
            product.is_deleted = True
    
    # 删除用户
    db.delete(user)
    db.commit()
    
    return {"success": True, "message": "用户删除成功"}

