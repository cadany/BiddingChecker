from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import sys
from dotenv import load_dotenv

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routes.bid_routes import bid_router
from routes.pdf_routes import pdf_router
from routes.bidding_routes import bidding_router

# 加载环境变量
load_dotenv()

# FastAPI应用配置
app = FastAPI(
    title="BiddingChecker API",
    version="1.0.0",
    description="竞价检查系统API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义中间件：请求日志记录
@app.middleware("http")
async def log_requests(request, call_next):
    """记录请求日志的中间件"""
    import time
    
    start_time = time.time()
    
    # 记录请求信息
    print(f"Request: {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 记录响应信息
        print(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.2f}s")
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as exc:
        process_time = time.time() - start_time
        print(f"Error: {request.method} {request.url.path} - Exception: {str(exc)} - Time: {process_time:.2f}s")
        raise

# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """请求验证错误处理"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求参数验证失败",
            "errors": exc.errors(),
            "path": request.url.path,
            "method": request.method
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    import traceback
    
    # 记录详细错误信息到日志
    print(f"Unhandled exception: {str(exc)}")
    print(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "error": str(exc) if os.environ.get('DEBUG') == 'True' else "Internal server error",
            "path": request.url.path,
            "method": request.method
        }
    )

# 注册路由
app.include_router(bid_router, prefix="/api", tags=["bids"])
app.include_router(pdf_router, prefix="/api", tags=["pdf"])
app.include_router(bidding_router, prefix="/api", tags=["bidding"])

@app.get("/", summary="API根路径", description="返回API基本信息")
async def root():
    """API根路径"""
    return {
        "message": "Welcome to BiddingChecker API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", summary="健康检查", description="检查API服务状态")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": "2026-01-05T22:20:00Z"
    }

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 18080))
    uvicorn.run(app, host="0.0.0.0", port=port)

    