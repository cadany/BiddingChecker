from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from typing import Optional
import os
import tempfile
from security import security_check, csrf_protect
from service.pdf_page_analyze import analyze_pdf_page

# 创建FastAPI路由器
pdf_router = APIRouter(prefix="/pdf", tags=["pdf"])

# 定义数据模型
class PDFAnalysisResponse(BaseModel):
    message: str = Field(..., description="处理结果消息")
    analysis: dict = Field(..., description="分析结果")

class PDFUploadResponse(BaseModel):
    message: str = Field(..., description="上传结果消息")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    page_count: Optional[int] = Field(None, description="页数")

@pdf_router.post(
    "/analyze",
    response_model=PDFAnalysisResponse,
    summary="分析PDF文件",
    description="分析PDF文件的指定页面内容"
)
async def analyze_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    page_num: int = Form(1, gt=0, description="页码"),
    _: bool = Depends(security_check),
    csrf_token: str = Depends(csrf_protect)
) -> PDFAnalysisResponse:
    """分析PDF文件的指定页面"""
    # 验证文件
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未提供PDF文件"
        )
    
    if file.filename == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未选择文件"
        )
    
    # 验证文件扩展名
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件不是PDF格式"
        )
    
    # 使用临时文件处理上传
    temp_file_path = None
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        result = await analyze_pdf_page(temp_file_path, page_num)
        
        return PDFAnalysisResponse(
            message=f"PDF第{page_num}页分析成功",
            analysis=result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理错误: {str(e)}"
        )
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@pdf_router.post(
    "/upload",
    response_model=PDFUploadResponse,
    summary="上传PDF文件",
    description="上传PDF文件并返回基本信息"
)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF文件"),
    _: bool = Depends(security_check),
    csrf_token: str = Depends(csrf_protect)
) -> PDFUploadResponse:
    """上传PDF文件"""
    # 验证文件
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未提供PDF文件"
        )
    
    if file.filename == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未选择文件"
        )
    
    # 验证文件扩展名
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件不是PDF格式"
        )
    
    # 获取文件大小
    file_size = len(await file.read())
    await file.seek(0)  # 重置文件指针
    
    return PDFUploadResponse(
        message="PDF文件上传成功",
        filename=file.filename,
        file_size=file_size,
        page_count=None  # 可以添加PDF页数检测功能
    )