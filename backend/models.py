"""
数据库模型定义
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    user_type = Column(String(20), nullable=False)  # 管理员、课题组用户、供应商、普通用户
    password_hash = Column(String(255), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)  # 供应商用户关联的supplier_id
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # 普通用户关联的管理用户ID
    email = Column(String(100), nullable=True)  # 邮箱
    phone = Column(String(20), nullable=True)  # 手机号
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关联关系
    # 供应商用户通过supplier_id关联到suppliers表
    supplier = relationship("Supplier", foreign_keys=[supplier_id], back_populates="user")
    # 普通用户通过manager_id关联到管理用户（课题组用户）
    manager = relationship("User", foreign_keys=[manager_id], remote_side=[id], backref="managed_students")
    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    services = relationship("ServiceRecord", back_populates="user", foreign_keys="ServiceRecord.user_id")


class Supplier(Base):
    """供应商表"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关联关系
    user = relationship("User", foreign_keys="User.supplier_id", back_populates="supplier", uselist=False)
    products = relationship("Product", back_populates="supplier_obj", foreign_keys="Product.supplier_id")
    orders = relationship("Order", back_populates="supplier", foreign_keys="Order.supplier_id")
    services = relationship("ServiceRecord", back_populates="supplier", foreign_keys="ServiceRecord.supplier_id")


class Product(Base):
    """商品表"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    brand = Column(String(100), nullable=True, index=True)  # 品牌（可选）
    model = Column(String(100), index=True)  # 型号
    specification = Column(String(500))  # 规格
    internal_price = Column(Float, nullable=False)  # 内部价格
    tax_included_price = Column(Float, nullable=False)  # 含税价格
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)  # 删除状态
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 关联关系
    # supplier_id指向suppliers表，不是users表
    supplier_obj = relationship("Supplier", foreign_keys=[supplier_id], back_populates="products")


class Order(Base):
    """订单表"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)  # JSON字符串，存储订单内容
    status = Column(String(20), nullable=False, index=True)  # 暂存、发起、确认、无效
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # 关联关系
    user = relationship("User", foreign_keys=[user_id], back_populates="orders")
    supplier = relationship("Supplier", foreign_keys=[supplier_id], back_populates="orders")


class ServiceRecord(Base):
    """服务记录表"""
    __tablename__ = "service_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)  # 服务内容
    amount = Column(Float, nullable=False)  # 金额
    status = Column(String(20), nullable=False, index=True)  # 暂存、发起、确认、无效
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # 关联关系
    user = relationship("User", foreign_keys=[user_id], back_populates="services")
    supplier = relationship("Supplier", foreign_keys=[supplier_id], back_populates="services")

