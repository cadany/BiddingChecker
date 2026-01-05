"""
文件上传服务模块
实现文件上传功能，将文件存储到uploads目录
"""

import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import LogMixin


class FileService(LogMixin):
    """文件上传服务类，使用纯LogMixin模式"""
    
    def __init__(self, upload_dir: str = "uploads"):
        """
        初始化文件上传服务
        
        Args:
            upload_dir: 上传文件存储目录
        """
        super().__init__()
        self.upload_dir = upload_dir
        self.file_records = {}  # 存储文件记录信息
        
        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)
        
        self.log_info(f"FileService初始化完成，上传目录: {self.upload_dir}")
    
    def generate_file_id(self) -> str:
        """生成唯一的文件ID"""
        return str(uuid.uuid4())
    
    def save_file(self, file_data: bytes, filename: str, file_type: str = None) -> Dict[str, Any]:
        """
        保存文件到uploads目录
        
        Args:
            file_data: 文件数据（字节）
            filename: 原始文件名
            file_type: 文件类型（可选，自动检测）
            
        Returns:
            Dict: 包含状态码和file_id的JSON响应
        """
        try:
            self.log_info(f"开始处理文件上传: {filename}")
            
            # 生成唯一文件ID
            file_id = self.generate_file_id()
            
            # 获取文件扩展名
            file_extension = os.path.splitext(filename)[1] if '.' in filename else ''
            
            # 构建存储文件名
            storage_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(self.upload_dir, storage_filename)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # 记录文件信息
            file_info = {
                'file_id': file_id,
                'original_filename': filename,
                'storage_filename': storage_filename,
                'file_path': file_path,
                'file_size': len(file_data),
                'file_type': file_type or self._detect_file_type(filename, file_extension),
                'upload_time': datetime.now().isoformat(),
                'status': 'uploaded'
            }
            
            self.file_records[file_id] = file_info
            
            self.log_info(f"文件上传成功 - ID: {file_id}, 文件名: {filename}, 大小: {len(file_data)} bytes")
            
            # 返回JSON格式响应
            return {
                'status_code': 200,
                'file_id': file_id,
                'message': '文件上传成功',
                'file_info': {
                    'original_filename': filename,
                    'file_size': len(file_data),
                    'file_type': file_info['file_type']
                }
            }
            
        except Exception as e:
            self.log_error(f"文件上传失败: {str(e)}")
            return {
                'status_code': 500,
                'file_id': None,
                'message': f'文件上传失败: {str(e)}',
                'error': str(e)
            }
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            Dict: 文件信息或None
        """
        if file_id in self.file_records:
            self.log_info(f"查询文件信息: {file_id}")
            return self.file_records[file_id]
        else:
            self.log_warning(f"文件不存在: {file_id}")
            return None
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            Dict: 删除结果
        """
        try:
            if file_id not in self.file_records:
                self.log_error(f"删除失败，文件不存在: {file_id}")
                return {
                    'status_code': 404,
                    'message': '文件不存在'
                }
            
            file_info = self.file_records[file_id]
            file_path = file_info['file_path']
            
            # 删除物理文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 删除记录
            del self.file_records[file_id]
            
            self.log_info(f"文件删除成功: {file_id}")
            
            return {
                'status_code': 200,
                'message': '文件删除成功',
                'file_id': file_id
            }
            
        except Exception as e:
            self.log_error(f"文件删除失败: {str(e)}")
            return {
                'status_code': 500,
                'message': f'文件删除失败: {str(e)}',
                'error': str(e)
            }
    
    def list_files(self) -> Dict[str, Any]:
        """
        列出所有已上传的文件
        
        Returns:
            Dict: 文件列表信息
        """
        self.log_info("获取文件列表")
        
        files = []
        for file_id, file_info in self.file_records.items():
            files.append({
                'file_id': file_id,
                'original_filename': file_info['original_filename'],
                'file_size': file_info['file_size'],
                'file_type': file_info['file_type'],
                'upload_time': file_info['upload_time']
            })
        
        return {
            'status_code': 200,
            'total_files': len(files),
            'files': files
        }
    
    def _detect_file_type(self, filename: str, extension: str) -> str:
        """
        检测文件类型
        
        Args:
            filename: 文件名
            extension: 文件扩展名
            
        Returns:
            str: 文件类型
        """
        # 常见文件类型映射
        file_type_mapping = {
            '.pdf': 'pdf',
            '.docx': 'document',
            '.xls': 'spreadsheet',
            '.xlsx': 'spreadsheet',
            '.zip': 'archive',
            '.rar': 'archive'
        }
        
        file_type = file_type_mapping.get(extension.lower(), 'unknown')
        
        # 特殊处理：如果文件名包含特定关键词
        if 'pdf' in filename.lower():
            file_type = 'pdf'
        elif any(img_ext in filename.lower() for img_ext in ['image', 'photo', 'picture']):
            file_type = 'image'
        
        return file_type

    def is_allowed_file(self, filename: str) -> bool:
        """
        检查文件类型是否允许，仅支持PDF
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否允许
        """
        extension = os.path.splitext(filename)[1].lower()
        return extension in ['.pdf']