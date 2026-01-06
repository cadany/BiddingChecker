from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from security import security_check, csrf_protect
from service.bid_service import BidService

# 创建FastAPI路由器
bid_router = APIRouter(prefix="/bids", tags=["bids"])

# 依赖注入BidService实例
_bid_service_instance = None

def get_bid_service() -> BidService:
    """获取BidService实例（单例模式）"""
    global _bid_service_instance
    if _bid_service_instance is None:
        _bid_service_instance = BidService()
    return _bid_service_instance

# 定义数据模型
class BidCreate(BaseModel):
    item_name: str = Field(..., max_length=255, description="物品名称")
    bid_amount: float = Field(..., gt=0, description="竞价金额")
    bidder_name: Optional[str] = Field(None, max_length=100, description="竞价者名称")
    status: Optional[str] = Field("active", pattern="^(active|inactive|won|lost)$", description="竞价状态")

class BidUpdate(BaseModel):
    item_name: Optional[str] = Field(None, max_length=255, description="物品名称")
    bid_amount: Optional[float] = Field(None, gt=0, description="竞价金额")
    bidder_name: Optional[str] = Field(None, max_length=100, description="竞价者名称")
    status: Optional[str] = Field(None, pattern="^(active|inactive|won|lost)$", description="竞价状态")

class BidResponse(BaseModel):
    id: int
    item_name: str
    bid_amount: float
    bidder_name: str
    created_at: str
    status: str

class BidsListResponse(BaseModel):
    bids: List[BidResponse]
    count: int

@bid_router.get(
    "/",
    response_model=BidsListResponse,
    summary="获取所有竞价",
    description="获取系统中的所有竞价信息，支持排序"
)
async def get_bids(
    sort: str = Query("created_at", description="排序字段"),
    order: str = Query("desc", description="排序顺序: asc/desc"),
    bid_service: BidService = Depends(get_bid_service),
    _: bool = Depends(security_check),
    csrf_token: str = Depends(csrf_protect)
) -> BidsListResponse:
    """获取所有竞价信息"""
    bids, count = await bid_service.get_all_bids(sort, order)
    
    # 将字典数据转换为BidResponse对象
    bid_responses = [
        BidResponse(
            id=bid['id'],
            item_name=bid['item_name'],
            bid_amount=bid['bid_amount'],
            bidder_name=bid['bidder_name'],
            created_at=bid['created_at'],
            status=bid['status']
        ) for bid in bids
    ]
    
    # 在实际应用中，应该将CSRF令牌添加到响应头中
    # 这里简化实现，直接返回响应
    return BidsListResponse(bids=bid_responses, count=count)

@bid_router.post(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="创建新竞价",
    description="创建一个新的竞价记录"
)
async def create_bid(
    bid: BidCreate,
    bid_service: BidService = Depends(get_bid_service),
    _: bool = Depends(security_check),
    csrf_token: str = Depends(csrf_protect)
) -> Dict[str, Any]:
    """创建新的竞价"""
    new_bid = await bid_service.create_bid(
        item_name=bid.item_name,
        bid_amount=bid.bid_amount,
        bidder_name=bid.bidder_name or "Anonymous",
        status=bid.status or "active"
    )
    
    return {
        "message": "Bid created successfully",
        "bid": new_bid
    }

@bid_router.get(
    "/{bid_id}",
    response_model=Dict[str, Any],
    summary="获取特定竞价",
    description="根据ID获取特定的竞价信息"
)
async def get_bid(
    bid_id: int = Path(..., gt=0, description="竞价ID"),
    bid_service: BidService = Depends(get_bid_service),
    _: bool = Depends(security_check)
) -> Dict[str, Any]:
    """获取特定竞价信息"""
    bid = await bid_service.get_bid_by_id(bid_id)
    
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid not found"
        )
    
    return {"bid": bid}

@bid_router.put(
    "/{bid_id}",
    response_model=Dict[str, Any],
    summary="更新竞价",
    description="更新特定竞价的详细信息"
)
async def update_bid(
    bid_id: int = Path(..., gt=0, description="竞价ID"),
    bid_update: BidUpdate = None,
    bid_service: BidService = Depends(get_bid_service),
    _: bool = Depends(security_check),
    csrf_token: str = Depends(csrf_protect)
) -> Dict[str, Any]:
    """更新特定竞价信息"""
    bid = await bid_service.get_bid_by_id(bid_id)
    
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid not found"
        )
    
    if bid_update is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )
    
    # 将Pydantic模型转换为字典
    update_data = bid_update.dict(exclude_unset=True)
    
    updated_bid = await bid_service.update_bid(bid_id, update_data)
    
    return {
        "message": "Bid updated successfully",
        "bid": updated_bid
    }

@bid_router.delete(
    "/{bid_id}",
    response_model=Dict[str, Any],
    summary="删除竞价",
    description="删除特定的竞价记录"
)
async def delete_bid(
    bid_id: int = Path(..., gt=0, description="竞价ID"),
    bid_service: BidService = Depends(get_bid_service),
    _: bool = Depends(security_check),
    csrf_token: str = Depends(csrf_protect)
) -> Dict[str, Any]:
    """删除特定竞价"""
    success = await bid_service.delete_bid(bid_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid not found"
        )
    
    return {"message": f"Bid {bid_id} deleted successfully"}

@bid_router.get("/analysis", dependencies=[Depends(security_check)])
async def get_bid_analysis_endpoint(bid_service: BidService = Depends(get_bid_service)):
    """获取竞价分析"""
    analysis = await bid_service.get_bid_analysis()
    
    if analysis is None:
        return {
            "message": "No bids available for analysis",
            "analysis": {}
        }
    
    return {
        "analysis": analysis,
        "message": "Bid analysis generated successfully"
    }

@bid_router.post("/clear", dependencies=[Depends(security_check), Depends(csrf_protect)])
async def clear_bids_endpoint(bid_service: BidService = Depends(get_bid_service)):
    """清空所有竞价数据（仅用于测试）"""
    await bid_service.clear_bids()
    
    return {"message": "All bids cleared successfully"}