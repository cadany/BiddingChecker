#!/usr/bin/env python3
"""
测试新的日志配置，验证文件名和行号显示功能
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import LoggerFactory, get_service_logger

def test_logging_configuration():
    """测试日志配置"""
    print("=== 测试新的日志配置 ===")
    
    # 配置日志系统，使用绝对路径
    import os
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    
    LoggerFactory.configure({
        'level': 'DEBUG',
        'enable_file_log': True,
        'enable_console_log': True,
        'log_dir': log_dir  # 使用绝对路径
    })
    
    # 获取日志记录器
    logger = get_service_logger("TestService")
    
    # 测试不同级别的日志
    logger.debug("这是一条调试信息")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    
    # 测试带有文件名和行号的日志
    logger.info("测试日志源追踪功能")
    
    print("=== 日志测试完成 ===")

if __name__ == "__main__":
    test_logging_configuration()