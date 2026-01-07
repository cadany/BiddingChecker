"""
统一日志组件
提供可复用的日志功能，支持控制台输出、文件日志、日志轮转等功能
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional, Dict, Any


class LoggerFactory:
    """日志工厂类，统一管理日志配置和实例"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        'level': logging.INFO,
        'console_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S',
        'log_dir': 'logs',
        'max_file_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
        'enable_file_log': True,
        'enable_console_log': True
    }
    
    _config = DEFAULT_CONFIG.copy()
    _loggers = {}
    
    @classmethod
    def configure(cls, config: Optional[Dict[str, Any]] = None):
        """配置日志系统"""
        if config:
            cls._config.update(config)
        
        # 创建日志目录
        if cls._config['enable_file_log']:
            os.makedirs(cls._config['log_dir'], exist_ok=True)
    
    @classmethod
    def get_logger(cls, name: str, **kwargs) -> logging.Logger:
        """获取或创建日志记录器"""
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 合并配置
        config = cls._config.copy()
        config.update(kwargs)
        
        logger = logging.getLogger(name)
        logger.setLevel(config['level'])
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 控制台处理器
        if config['enable_console_log']:
            console_formatter = logging.Formatter(
                config['console_format'],
                datefmt=config['date_format']
            )
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # 文件处理器
        if config['enable_file_log']:
            file_formatter = logging.Formatter(
                config['file_format'],
                datefmt=config['date_format']
            )
            log_file = os.path.join(
                config['log_dir'], 
                f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            )
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=config['max_file_size'],
                backupCount=config['backup_count'],
                encoding='utf-8'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger
    
    @classmethod
    def get_service_logger(cls, service_name: str) -> logging.Logger:
        """为服务类获取专用日志记录器"""
        return cls.get_logger(f"service.{service_name}")
    
    @classmethod
    def get_route_logger(cls, route_name: str) -> logging.Logger:
        """为路由类获取专用日志记录器"""
        return cls.get_logger(f"route.{route_name}")


class LogMixin:
    """日志混入类，可以轻松添加到任何类中"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        class_name = self.__class__.__name__
        self.logger = LoggerFactory.get_service_logger(class_name)
    
    def log_info(self, message: str, **kwargs):
        """记录信息级别日志"""
        self.logger.info(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """记录错误级别日志"""
        self.logger.error(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """记录警告级别日志"""
        self.logger.warning(message, extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """记录调试级别日志"""
        self.logger.debug(message, extra=kwargs)


def setup_logging(config: Optional[Dict[str, Any]] = None):
    """快速设置日志系统"""
    LoggerFactory.configure(config)


def get_logger(name: str) -> logging.Logger:
    """快速获取日志记录器"""
    return LoggerFactory.get_logger(name)


def get_service_logger(service_name: str) -> logging.Logger:
    """快速获取服务日志记录器"""
    return LoggerFactory.get_service_logger(service_name)


# 默认配置
# setup_logging()  # 注释掉默认配置，由应用根据需要调用