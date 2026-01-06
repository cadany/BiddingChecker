"""
统一安全校验模块 - FastAPI风格重构
包含输入验证、清理、安全检查等功能
"""

import re
import html
import os
import secrets
import hashlib
import time
from functools import wraps
from typing import Dict, Any, Tuple, Optional, List
from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


class SecurityValidator:
    """安全验证器类 - FastAPI风格"""
    
    # 禁止的文件扩展名
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', 
        '.jar', '.sh', '.php', '.pl', '.py', '.rb', '.sql', '.jsp', 
        '.asp', '.aspx', '.cgi', '.msi', '.dll', '.so', '.dylib'
    }
    
    # 安全的文件扩展名
    SAFE_PDF_EXTENSIONS = {'.pdf'}
    
    # SQL注入检测模式
    SQL_INJECTION_PATTERNS = [
        r"(?i)(union\s+select)",
        r"(?i)(drop\s+table)",
        r"(?i)(create\s+table)",
        r"(?i)(insert\s+into)",
        r"(?i)(delete\s+from)",
        r"(?i)(update\s+\w+\s+set)",
        r"(?i)(exec\s*\()",
        r"(?i)(execute\s*\()",
        r"(?i)(sp_)",
        r"(?i)(;|--|/\*|\*/|xp_)",
        r"(?i)(\bselect\b|\bfrom\b|\bwhere\b|\border\s+by\b|\bgroup\s+by\b|\bhaving\b)",
    ]
    
    # XSS检测模式
    XSS_PATTERNS = [
        r"(?i)<script",
        r"(?i)</script>",
        r"(?i)javascript:",
        r"(?i)vbscript:",
        r"(?i)on\w+\s*=",
        r"(?i)expression\s*\()",
        r"(?i)eval\s*\()",
        r"(?i)alert\s*\()",
        r"(?i)<iframe",
        r"(?i)</iframe>",
        r"(?i)<object",
        r"(?i)</object>",
        r"(?i)<embed",
        r"(?i)</embed>",
        r"(?i)data:",
    ]
    
    # 命令注入检测模式
    COMMAND_INJECTION_PATTERNS = [
        r"(?i)(\|)",
        r"(?i)(;)",
        r"(?i)(`)",
        r"(?i)(&&)",
        r"(?i)(\|\|)",
        r"(?i)(\bcurl\b|\bwget\b|\bnc\b|\bncat\b|\btelnet\b)",
        r"(?i)(\bcat\b|\bless\b|\bmore\b|\bhead\b|\btail\b)",
        r"(?i)(\bsh\b|\bbash\b|\bpowershell\b|\bcmd\b)",
        r"(?i)(\bchmod\b|\bchown\b|\bkill\b|\bps\b|\bls\b|\bcp\b|\bm\b|\brm\b)",
        r"(?i)(\bnc\b|\bnetcat\b|\bsocat\b|\bnmap\b)",
        r"(?i)(\$\(|\${",
    ]
    
    @staticmethod
    def sanitize_input(input_data):
        """清理输入数据"""
        if isinstance(input_data, str):
            # HTML转义
            sanitized = html.escape(input_data)
            # 移除潜在的危险字符
            sanitized = re.sub(r'[<>"\']', '', sanitized)
            return sanitized
        elif isinstance(input_data, dict):
            sanitized_dict = {}
            for key, value in input_data.items():
                sanitized_dict[key] = SecurityValidator.sanitize_input(value)
            return sanitized_dict
        elif isinstance(input_data, list):
            return [SecurityValidator.sanitize_input(item) for item in input_data]
        else:
            return input_data
    
    @staticmethod
    def validate_sql_injection(input_data):
        """检测SQL注入"""
        if isinstance(input_data, str):
            for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
                if re.search(pattern, input_data):
                    return False
        elif isinstance(input_data, dict):
            for value in input_data.values():
                if not SecurityValidator.validate_sql_injection(value):
                    return False
        elif isinstance(input_data, list):
            for item in input_data:
                if not SecurityValidator.validate_sql_injection(item):
                    return False
        return True
    
    @staticmethod
    def validate_xss(input_data):
        """检测XSS攻击"""
        if isinstance(input_data, str):
            for pattern in SecurityValidator.XSS_PATTERNS:
                if re.search(pattern, input_data):
                    return False
        elif isinstance(input_data, dict):
            for value in input_data.values():
                if not SecurityValidator.validate_xss(value):
                    return False
        elif isinstance(input_data, list):
            for item in input_data:
                if not SecurityValidator.validate_xss(item):
                    return False
        return True
    
    @staticmethod
    def validate_command_injection(input_data):
        """检测命令注入"""
        if isinstance(input_data, str):
            for pattern in SecurityValidator.COMMAND_INJECTION_PATTERNS:
                if re.search(pattern, input_data):
                    return False
        elif isinstance(input_data, dict):
            for value in input_data.values():
                if not SecurityValidator.validate_command_injection(value):
                    return False
        elif isinstance(input_data, list):
            for item in input_data:
                if not SecurityValidator.validate_command_injection(item):
                    return False
        return True
    
    @staticmethod
    def validate_filename(filename):
        """验证文件名安全"""
        # 简单的文件名清理
        safe_filename = re.sub(r'[^\w\d\.\-_]', '', filename)
        
        # 检查扩展名
        _, ext = os.path.splitext(safe_filename.lower())
        if ext in SecurityValidator.DANGEROUS_EXTENSIONS:
            return False, "危险的文件类型"
        
        # 检查路径遍历
        if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
            return False, "非法文件名"
        
        return True, safe_filename
    
    @staticmethod
    def validate_pdf_file(filename):
        """验证PDF文件"""
        if not filename or filename == '':
            return False, "未选择文件"
        
        # 验证文件名
        is_valid, result = SecurityValidator.validate_filename(filename)
        if not is_valid:
            return False, result
        
        # 检查扩展名
        _, ext = os.path.splitext(result.lower())
        if ext not in SecurityValidator.SAFE_PDF_EXTENSIONS:
            return False, "仅支持PDF文件"
        
        return True, result
    
    @staticmethod
    def generate_csrf_token():
        """生成CSRF令牌"""
        return secrets.token_hex(32)
    
    @staticmethod
    def validate_csrf_token(request: Request, token: Optional[str] = None):
        """验证CSRF令牌"""
        # 从请求头或查询参数获取令牌
        if not token:
            token = request.headers.get('X-CSRF-Token') or request.query_params.get('csrf_token')
        
        if not token:
            return False
        
        # 在实际应用中，这里应该验证令牌是否有效
        # 简化实现：检查令牌格式
        if len(token) != 64:  # 32字节的十六进制字符串
            return False
        
        return True
    
    @staticmethod
    def validate_idor(user_id, resource_owner_id):
        """验证IDOR（不安全的直接对象引用）"""
        # 在实际应用中，这里应该根据业务逻辑验证用户是否有权限访问资源
        # 例如，验证当前用户是否是资源的所有者
        return str(user_id) == str(resource_owner_id)
    
    @staticmethod
    def validate_rate_limit(request: Request, limit: int = 100, window: int = 3600):
        """验证请求频率限制"""
        # 这是一个简化的实现，实际应用中需要使用Redis或数据库来跟踪请求
        # 这里我们简单地检查客户端IP的请求频率
        client_ip = request.client.host if request.client else "unknown"
        # 在实际应用中，这里会检查缓存或数据库中该IP的请求次数
        return True  # 简化返回，实际实现会更复杂


# FastAPI依赖项
security = HTTPBearer()


async def csrf_protect(request: Request) -> str:
    """CSRF保护依赖项"""
    # 对于非GET、HEAD、OPTIONS、TRACE请求，验证CSRF令牌
    if request.method not in ['GET', 'HEAD', 'OPTIONS', 'TRACE']:
        token = request.headers.get('X-CSRF-Token') or request.query_params.get('csrf_token')
        if not SecurityValidator.validate_csrf_token(request, token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF验证失败"
            )
    
    # 对于所有请求，生成新的CSRF令牌
    token = SecurityValidator.generate_csrf_token()
    
    # 在实际应用中，这里应该将令牌存储在会话或响应头中
    # 简化实现：返回令牌
    return token


async def security_check(request: Request) -> bool:
    """安全检查依赖项"""
    # 检查查询参数
    query_params = dict(request.query_params)
    if query_params:
        if not SecurityValidator.validate_sql_injection(query_params):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="检测到SQL注入尝试"
            )
        if not SecurityValidator.validate_xss(query_params):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="检测到XSS尝试"
            )
        if not SecurityValidator.validate_command_injection(query_params):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="检测到命令注入尝试"
            )
    
    # 检查请求频率限制（简化实现）
    if not SecurityValidator.validate_rate_limit(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求频率超限"
        )
    
    return True


def validate_input_types(data: Dict[str, Any], expected_types: Dict[str, type]) -> Tuple[bool, Optional[str]]:
    """
    验证输入数据类型
    :param data: 要验证的数据
    :param expected_types: 期望的类型列表，例如 {'name': str, 'age': int}
    :return: (is_valid, error_message)
    """
    for field, expected_type in expected_types.items():
        if field in data:
            value = data[field]
            if not isinstance(value, expected_type):
                # 尝试类型转换
                try:
                    if expected_type == int:
                        data[field] = int(value)
                    elif expected_type == float:
                        data[field] = float(value)
                    elif expected_type == str:
                        data[field] = str(value)
                    elif expected_type == bool:
                        data[field] = bool(value)
                except (ValueError, TypeError):
                    return False, f"字段 '{field}' 类型错误，期望 {expected_type.__name__}"
    
    return True, None