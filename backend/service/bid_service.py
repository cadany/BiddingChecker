"""
竞价服务模块
使用重构后的统一日志系统 - 纯LogMixin模式
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import LogMixin


class BidService(LogMixin):
    """竞价服务类，使用纯LogMixin模式"""
    
    def __init__(self):
        super().__init__()
        self.bids_data = []
        self.bid_counter = 1
        self.log_info("BidService初始化完成")
    
    def get_all_bids(self, sort_by: str = 'created_at', order: str = 'desc') -> tuple:
        """获取所有竞价信息"""
        self.log_info(f"获取所有竞价，排序方式: {sort_by}, 顺序: {order}")
        
        sorted_bids = sorted(self.bids_data, key=lambda x: x[sort_by], reverse=(order == 'desc'))
        total_count = len(sorted_bids)
        
        self.log_info(f"成功获取 {total_count} 条竞价记录")
        return sorted_bids, total_count
    
    def create_bid(self, item_name: str, bid_amount: float, 
                   bidder_name: str = 'Anonymous', status: str = 'active') -> Dict[str, Any]:
        """创建新的竞价"""
        self.log_info(f"创建竞价 - 物品: {item_name}, 金额: {bid_amount}, 竞价者: {bidder_name}")
        
        new_bid = {
            'id': self.bid_counter,
            'item_name': item_name,
            'bid_amount': bid_amount,
            'bidder_name': bidder_name,
            'created_at': datetime.now().isoformat(),
            'status': status
        }
        
        self.bids_data.append(new_bid)
        self.bid_counter += 1
        
        self.log_info(f"竞价创建成功，ID: {new_bid['id']}")
        return new_bid
    
    def get_bid_by_id(self, bid_id: int) -> Optional[Dict[str, Any]]:
        """获取特定竞价信息"""
        self.log_info(f"查询竞价信息，ID: {bid_id}")
        
        bid = next((bid for bid in self.bids_data if bid['id'] == bid_id), None)
        
        if bid:
            self.log_info(f"找到竞价信息: {bid['item_name']}")
        else:
            self.log_warning(f"未找到ID为 {bid_id} 的竞价")
        
        return bid
    
    def update_bid(self, bid_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新特定竞价信息"""
        self.log_info(f"更新竞价信息，ID: {bid_id}, 数据: {data}")
        
        # 找到要更新的竞价
        bid_index = next((i for i, bid in enumerate(self.bids_data) if bid['id'] == bid_id), None)
        
        if bid_index is None:
            self.log_error(f"更新失败，未找到ID为 {bid_id} 的竞价")
            return None
        
        # 更新允许的字段
        updatable_fields = ['item_name', 'bid_amount', 'bidder_name', 'status']
        updated_fields = []
        
        for field in updatable_fields:
            if field in data:
                if field == 'bid_amount':
                    self.bids_data[bid_index][field] = float(data[field])
                else:
                    self.bids_data[bid_index][field] = data[field]
                updated_fields.append(field)
        
        self.log_info(f"竞价更新成功，更新的字段: {updated_fields}")
        return self.bids_data[bid_index]
    
    def delete_bid(self, bid_id: int) -> bool:
        """删除特定竞价"""
        self.log_info(f"删除竞价，ID: {bid_id}")
        
        bid = next((bid for bid in self.bids_data if bid['id'] == bid_id), None)
        
        if not bid:
            self.log_error(f"删除失败，未找到ID为 {bid_id} 的竞价")
            return False
        
        self.bids_data = [bid for bid in self.bids_data if bid['id'] != bid_id]
        self.log_info(f"竞价删除成功，物品: {bid['item_name']}")
        return True
    
    def get_bid_analysis(self) -> Optional[Dict[str, Any]]:
        """获取竞价分析"""
        self.log_info("开始竞价分析")
        
        if not self.bids_data:
            self.log_warning("竞价数据为空，无法进行分析")
            return None
        
        total_bids = len(self.bids_data)
        total_amount = sum(bid['bid_amount'] for bid in self.bids_data)
        avg_amount = total_amount / total_bids if total_bids > 0 else 0
        
        # 找出最高和最低竞价
        highest_bid = max(self.bids_data, key=lambda x: x['bid_amount'])
        lowest_bid = min(self.bids_data, key=lambda x: x['bid_amount'])
        
        # 按状态分组
        status_counts = {}
        for bid in self.bids_data:
            status = bid['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        analysis = {
            'total_bids': total_bids,
            'total_amount': total_amount,
            'average_bid_amount': avg_amount,
            'highest_bid': highest_bid,
            'lowest_bid': lowest_bid,
            'status_distribution': status_counts
        }
        
        self.log_info(f"竞价分析完成，总计: {total_bids} 条记录")
        return analysis
    
    def clear_bids(self):
        """清空所有竞价数据"""
        self.log_warning("清空所有竞价数据")
        
        original_count = len(self.bids_data)
        self.bids_data = []
        self.bid_counter = 1
        
        self.log_info(f"竞价数据已清空，原数据量: {original_count}")


# 测试代码
if __name__ == "__main__":
    # 测试纯LogMixin模式
    print("=== 测试纯LogMixin模式 ===")
    
    # 创建服务实例
    bid_service = BidService()
    
    # 创建一些测试数据
    bid_service.create_bid("笔记本电脑", 5000.0, "张三")
    bid_service.create_bid("智能手机", 3000.0, "李四")
    bid_service.create_bid("平板电脑", 2000.0, "王五")
    
    # 测试功能
    bids, count = bid_service.get_all_bids()
    print(f"竞价数量: {count}")
    
    analysis = bid_service.get_bid_analysis()
    print("竞价分析结果:", analysis)
    
    print("=== 测试完成 ===")