"""
Pydantic模型定义，用于API请求和响应验证
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# 用户相关
class UserCreate(BaseModel):
    """创建用户请求模型"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")
    user_type: str = Field(..., description="用户类型: 管理员、普通用户、厂家")


class UserUpdate(BaseModel):
    """更新用户密码请求模型"""
    password: str = Field(..., min_length=1, description="新密码")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    user_type: str
    supplier_id: Optional[int] = None  # 厂家用户关联的supplier_id
    created_at: datetime
    
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool
    message: str
    user: Optional[UserResponse] = None


# 厂家相关
class SupplierCreate(BaseModel):
    """创建厂家请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="厂家名称")


class SupplierResponse(BaseModel):
    """厂家响应模型"""
    id: int
    name: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


# 商品相关
class ProductCreate(BaseModel):
    """创建商品请求模型"""
    name: str = Field(..., min_length=1, max_length=200, description="商品名")
    model: Optional[str] = Field(None, max_length=100, description="型号")
    specification: Optional[str] = Field(None, max_length=500, description="规格")
    internal_price: Optional[float] = Field(None, ge=0, description="内部价格")
    tax_included_price: float = Field(..., ge=0, description="含税价格")
    supplier_id: int = Field(..., description="厂家ID")


class ProductUpdate(BaseModel):
    """更新商品请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="商品名")
    model: Optional[str] = Field(None, max_length=100, description="型号")
    specification: Optional[str] = Field(None, max_length=500, description="规格")
    internal_price: Optional[float] = Field(None, ge=0, description="内部价格")
    tax_included_price: Optional[float] = Field(None, ge=0, description="含税价格")


class ProductResponse(BaseModel):
    """商品响应模型"""
    id: int
    name: str
    model: Optional[str]
    specification: Optional[str]
    internal_price: Optional[float]  # 厂家用户看不到此字段
    tax_included_price: float
    supplier_id: int
    supplier_name: Optional[str] = None
    is_deleted: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """商品列表响应模型"""
    total: int
    items: List[ProductResponse]
    page: int
    page_size: int


class ProductFilter(BaseModel):
    """商品筛选模型"""
    name: Optional[str] = None
    model: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    supplier_id: Optional[int] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# 订单相关
class OrderItem(BaseModel):
    """订单项模型"""
    product_id: int
    name: str
    model: Optional[str] = None
    specification: Optional[str] = None
    internal_price: Optional[float] = None
    tax_included_price: float
    quantity: int = Field(..., ge=1)
    muted: bool = False  # 是否静音


class OrderCreate(BaseModel):
    """创建订单请求模型"""
    supplier_id: int = Field(..., description="厂家ID")
    items: List[OrderItem] = Field(..., min_length=1, description="订单项列表")


class OrderResponse(BaseModel):
    """订单响应模型"""
    id: int
    user_id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    content: str  # JSON字符串
    status: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class OrderDetailResponse(BaseModel):
    """订单详情响应模型"""
    id: int
    user_id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    items: List[OrderItem]  # 解析后的订单内容
    status: str
    created_at: datetime
    total_internal_price: Optional[float] = None
    total_tax_included_price: float


class OrderListResponse(BaseModel):
    """订单列表响应模型"""
    total: int
    items: List[OrderResponse]
    page: int
    page_size: int


class OrderFilter(BaseModel):
    """订单筛选模型"""
    supplier_id: Optional[int] = None
    content: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# 服务记录相关
class ServiceRecordCreate(BaseModel):
    """创建服务记录请求模型"""
    supplier_id: int = Field(..., description="厂家ID")
    content: str = Field(..., min_length=1, description="服务内容")
    amount: float = Field(..., ge=0, description="金额")
    user_username: Optional[str] = Field(None, description="关联的用户名（普通用户或管理员），厂家创建服务记录时必须提供")


class ServiceRecordUpdate(BaseModel):
    """更新服务记录请求模型"""
    content: Optional[str] = Field(None, min_length=1, description="服务内容")
    amount: Optional[float] = Field(None, ge=0, description="金额")


class ServiceRecordResponse(BaseModel):
    """服务记录响应模型"""
    id: int
    user_id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    content: str
    amount: float
    status: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ServiceRecordListResponse(BaseModel):
    """服务记录列表响应模型"""
    total: int
    items: List[ServiceRecordResponse]
    page: int
    page_size: int


class ServiceRecordFilter(BaseModel):
    """服务记录筛选模型"""
    supplier_id: Optional[int] = None
    content: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# 统计相关
class StatisticsItem(BaseModel):
    """统计项模型"""
    supplier_id: int
    supplier_name: str
    order_count: int
    product_count: int
    total_internal_price: float
    total_tax_included_price: float
    total_service_amount: float
    total_tax: float
    total_balance: float


class StatisticsResponse(BaseModel):
    """统计响应模型"""
    items: List[StatisticsItem]
    total: StatisticsItem

