"""
日志配置模块
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# 创建logs目录
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 配置日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 配置根日志记录器
logger = logging.getLogger("bookkeep")
logger.setLevel(logging.DEBUG)

# 避免重复添加handler
if not logger.handlers:
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件handler - 所有日志
    file_handler = logging.FileHandler(
        LOG_DIR / f"bookkeep_{datetime.now().strftime('%Y%m%d')}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 文件handler - 错误日志
    error_handler = logging.FileHandler(
        LOG_DIR / f"error_{datetime.now().strftime('%Y%m%d')}.log",
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)


def get_logger(name: str = None):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，默认为调用模块名
        
    Returns:
        logging.Logger: 日志记录器对象
        
    使用样例:
        from backend.logger import get_logger
        logger = get_logger(__name__)
        logger.info("这是一条信息日志")
        logger.error("这是一条错误日志", exc_info=True)
    """
    if name:
        return logging.getLogger(f"bookkeep.{name}")
    return logger

