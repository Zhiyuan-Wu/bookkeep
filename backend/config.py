"""
配置文件
包含系统的重要配置常数
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据库配置
DATABASE_URL = "sqlite:///./bookkeep.db"

# Session配置
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "your-secret-key-change-in-production")
SESSION_COOKIE_NAME = "bookkeep_session"
SESSION_MAX_AGE = 86400  # 24小时

# 用户类型
USER_TYPE_ADMIN = "管理员"
USER_TYPE_NORMAL = "普通用户"
USER_TYPE_SUPPLIER = "厂家"
USER_TYPE_STUDENT = "学生用户"

# 自助注册配置
ALLOW_SELF_REGISTRATION = True

# 订单状态
ORDER_STATUS_DRAFT = "暂存"
ORDER_STATUS_SUBMITTED = "发起"
ORDER_STATUS_CONFIRMED = "确认"
ORDER_STATUS_INVALID = "无效"

# 服务记录状态
SERVICE_STATUS_DRAFT = "暂存"
SERVICE_STATUS_SUBMITTED = "发起"
SERVICE_STATUS_CONFIRMED = "确认"
SERVICE_STATUS_INVALID = "无效"

# 税率
TAX_RATE = 0.13  # 13%

# 分页配置
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 邮件服务器配置
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "86562713@qq.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = SMTP_USER
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Order Notification")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
