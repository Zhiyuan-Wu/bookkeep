"""
FastAPI应用主入口
"""

from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from backend.database import init_db
from backend.routers import users, products, orders, services, statistics, suppliers
from backend.logger import get_logger
import os
import traceback
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from migrate_db import migrate_database

logger = get_logger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    try:
        # 执行数据库迁移
        migrate_database()
        # 初始化数据库（创建表）
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        raise
    yield
    # 关闭时（可以在这里添加清理代码）

# 创建FastAPI应用
app = FastAPI(
    title="报价及记账系统",
    description="报价和记账系统的后端API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(services.router)
app.include_router(statistics.router)
app.include_router(suppliers.router)

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/")
async def root():
    """根路径，返回登录页面"""
    index_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "报价及记账系统 API"}


@app.get("/main")
async def main_page():
    """主页面"""
    main_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "main.html")
    if os.path.exists(main_path):
        return FileResponse(main_path)
    return {"message": "主页面"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器，记录所有未捕获的异常
    
    Args:
        request: FastAPI请求对象
        exc: 异常对象
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.error(
        f"未处理的异常: {exc.__class__.__name__}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "query_params": str(request.query_params),
            "client": request.client.host if request.client else None,
        }
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "服务器内部错误",
            "error_type": exc.__class__.__name__
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求验证异常处理器
    
    Args:
        request: FastAPI请求对象
        exc: 验证异常对象
        
    Returns:
        JSONResponse: 错误响应
    """
    logger.warning(
        f"请求验证失败: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "body": str(exc.body) if hasattr(exc, 'body') else None,
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

