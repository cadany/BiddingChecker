
import asyncio
import uuid
import threading
import time
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from service.file_service import FileService
from service.pdf_converter_v2 import PDFConverterV2, ConversionConfig


class ConvertService:
    def __init__(self, file_service: FileService):
        self.file_service = file_service
        # 初始化PDF转换器
        config = ConversionConfig(
            table_detection_enabled=True,
            extract_images=True,
            preserve_formatting=True
        )
        self.pdf_converter = PDFConverterV2(config)
        # 任务状态存储
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def start_convert_task(self, file_id: str) -> str:
        """
        启动异步文件转换任务
        
        Args:
            file_id: 文件ID
            
        Returns:
            str: 任务ID
        """
        try:
            # 获取文件信息
            file_info = self.file_service.get_file_info(file_id)
            if not file_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"文件不存在: {file_id}"
                )
            
            # 检查文件类型，目前只支持PDF
            if file_info['file_type'] != 'pdf':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不支持的文件类型: {file_info['file_type']}，目前只支持PDF文件"
                )
            
            # 生成唯一任务ID
            task_id = str(uuid.uuid4())
            
            # 初始化任务状态
            self.tasks[task_id] = {
                'file_id': file_id,
                'file_path': file_info['file_path'],
                'status': 'pending',  # pending, processing, completed, failed
                'progress': 0,
                'result': None,
                'error': None,
                'start_time': None,
                'end_time': None
            }
            
            # 启动异步转换任务
            thread = threading.Thread(target=self._run_convert_task, args=(task_id,))
            thread.daemon = True
            thread.start()
            
            return task_id
            
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"启动转换任务失败: {str(e)}"
            )

    def _run_convert_task(self, task_id: str):
        """在后台线程中运行转换任务"""
        try:
            task = self.tasks[task_id]
            task['status'] = 'processing'
            task['start_time'] = time.time()
            
            file_path = task['file_path']
            
            # 使用PDF转换器进行转换
            result = self.pdf_converter.convert_pdf(file_path)
            
            if result.get('success', False):
                # 读取转换后的Markdown内容
                output_path = result['output_path']
                with open(output_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                
                task['status'] = 'completed'
                task['result'] = {
                    'file_id': task['file_id'],
                    'markdown_content': markdown_content,
                    'output_path': output_path,
                    'processing_time': result['processing_time'],
                    'pages_processed': result['pages_processed'],
                    'tables_found': result['tables_found']
                }
            else:
                task['status'] = 'failed'
                task['error'] = result.get('error', '转换失败')
            
            task['end_time'] = time.time()
            task['progress'] = 100
            
        except Exception as e:
            task['status'] = 'failed'
            task['error'] = str(e)
            task['end_time'] = time.time()

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict: 任务状态信息
        """
        if task_id not in self.tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {task_id}"
            )
        
        task = self.tasks[task_id]
        
        return {
            'task_id': task_id,
            'file_id': task['file_id'],
            'status': task['status'],
            'progress': task['progress'],
            'result': task['result'],
            'error': task['error'],
            'start_time': task['start_time'],
            'end_time': task['end_time']
        }

    def convert_file_to_markdown(self, file_id: str) -> Dict[str, Any]:
        """
        同步转换文件（保留原有接口，但不推荐使用）
        
        Args:
            file_id: 文件ID
            
        Returns:
            Dict: 转换结果信息
        """
        # 启动异步任务并等待完成
        task_id = self.start_convert_task(file_id)
        
        # 等待任务完成（简单轮询，不推荐在生产环境使用）
        import time
        max_wait_time = 300  # 5分钟超时
        wait_interval = 1    # 1秒轮询间隔
        
        for _ in range(max_wait_time):
            task_status = self.get_task_status(task_id)
            if task_status['status'] in ['completed', 'failed']:
                break
            time.sleep(wait_interval)
        
        final_status = self.get_task_status(task_id)
        
        if final_status['status'] == 'completed':
            return final_status['result']
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件转换失败: {final_status.get('error', '未知错误')}"
            )