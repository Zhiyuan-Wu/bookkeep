"""
供应商管理路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Supplier
from backend.schemas import SupplierResponse
from backend.auth import get_current_user
from backend.logger import get_logger
from typing import List

logger = get_logger(__name__)
router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("/", response_model=List[SupplierResponse])
async def list_suppliers(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有供应商列表
    
    Args:
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        List[SupplierResponse]: 供应商列表
        
    使用样例:
        GET /api/suppliers/
    """
    try:
        suppliers = db.query(Supplier).all()
        logger.info(f"获取供应商列表，共{len(suppliers)}个供应商")
        return [SupplierResponse.model_validate(s) for s in suppliers]
    except Exception as e:
        logger.error(f"获取供应商列表失败: {e}", exc_info=True)
        raise

