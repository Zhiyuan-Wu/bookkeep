"""
认证和session管理
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.utils import verify_password, hash_password
from backend.config import USER_TYPE_ADMIN, USER_TYPE_NORMAL, USER_TYPE_SUPPLIER, USER_TYPE_STUDENT
import uuid
from typing import Optional, Dict

# Session存储 (生产环境应使用Redis等)
sessions: Dict[str, Dict] = {}

security = HTTPBearer(auto_error=False)


def create_session(user_id: int, username: str, user_type: str) -> str:
    """
    创建session
    
    Args:
        user_id: 用户ID
        username: 用户名
        user_type: 用户类型
        
    Returns:
        str: session ID
        
    使用样例:
        session_id = create_session(1, "admin", "管理员")
    """
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "user_id": user_id,
        "username": username,
        "user_type": user_type
    }
    return session_id


def get_session(session_id: Optional[str]) -> Optional[Dict]:
    """
    获取session信息
    
    Args:
        session_id: session ID
        
    Returns:
        dict: session信息，如果不存在则返回None
        
    使用样例:
        session = get_session(session_id)
        if session:
            print(session["username"])
    """
    if not session_id:
        return None
    return sessions.get(session_id)


def delete_session(session_id: str):
    """
    删除session
    
    Args:
        session_id: session ID
        
    使用样例:
        delete_session(session_id)
    """
    if session_id in sessions:
        del sessions[session_id]


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户（依赖注入）
    
    Args:
        request: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 如果用户未登录
        
    使用样例:
        @app.get("/api/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.username}
    """
    # 从cookie中获取session_id
    session_id = request.cookies.get("bookkeep_session")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )
    
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session已过期"
        )
    
    user = db.query(User).filter(User.id == session_data["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return user


def require_user_type(*allowed_types: str):
    """
    要求用户类型装饰器
    
    Args:
        *allowed_types: 允许的用户类型列表
        
    Returns:
        function: 装饰器函数
        
    使用样例:
        @app.get("/api/admin-only")
        @require_user_type(USER_TYPE_ADMIN)
        def admin_route(current_user: User = Depends(get_current_user)):
            return {"message": "管理员专用"}
    """
    def decorator(user: User = Depends(get_current_user)) -> User:
        if user.user_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下用户类型之一: {', '.join(allowed_types)}"
            )
        return user
    return decorator


def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    要求管理员权限（依赖注入）
    
    Args:
        user: 当前用户
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 如果不是管理员
        
    使用样例:
        @app.get("/api/admin")
        def admin_route(current_user: User = Depends(require_admin)):
            return {"message": "管理员专用"}
    """
    if user.user_type != USER_TYPE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


def require_supplier(user: User = Depends(get_current_user)) -> User:
    """
    要求供应商用户权限（依赖注入）
    
    Args:
        user: 当前用户
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 如果不是供应商用户
        
    使用样例:
        @app.get("/api/supplier")
        def supplier_route(current_user: User = Depends(require_supplier)):
            return {"message": "供应商专用"}
    """
    if user.user_type != USER_TYPE_SUPPLIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要供应商用户权限"
        )
    return user


def can_view_internal_price(user: User) -> bool:
    """
    判断用户是否可以查看内部价格
    
    普通用户不能查看内部价格，只有管理员和课题组用户可以查看
    
    Args:
        user: 用户对象
        
    Returns:
        bool: 是否可以查看内部价格
        
    使用样例:
        if can_view_internal_price(current_user):
            # 显示内部价格
    """
    return user.user_type in [USER_TYPE_ADMIN, USER_TYPE_NORMAL]

