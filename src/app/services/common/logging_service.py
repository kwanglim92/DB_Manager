"""
로깅 서비스

중앙 집중식 로깅을 제공하며, 다양한 로그 레벨과 포맷을 지원합니다.
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

class LoggingService:
    """로깅 서비스"""
    
    _instance: Optional['LoggingService'] = None
    _configured = False
    
    def __new__(cls) -> 'LoggingService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._configured:
            self._setup_logging()
            self._configured = True
    
    def _setup_logging(self):
        """로깅 설정 초기화"""
        # 기본 포맷 설정
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        
        # 서비스 전용 로거 설정
        self._service_logger = logging.getLogger('ServiceLayer')
        self._service_logger.setLevel(logging.DEBUG)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        지정된 이름의 로거 반환
        
        Args:
            name: 로거 이름
            
        Returns:
            Logger 인스턴스
        """
        return logging.getLogger(f"ServiceLayer.{name}")
    
    def log_service_action(self, service_name: str, action: str, details: Optional[Dict[str, Any]] = None):
        """
        서비스 액션 로깅
        
        Args:
            service_name: 서비스 이름
            action: 수행된 액션
            details: 추가 상세 정보
        """
        message = f"{service_name} - {action}"
        if details:
            detail_str = ", ".join([f"{k}={v}" for k, v in details.items()])
            message += f" ({detail_str})"
        
        self._service_logger.info(message)
    
    def log_error(self, service_name: str, error: Exception, context: Optional[str] = None):
        """
        에러 로깅
        
        Args:
            service_name: 서비스 이름
            error: 발생한 예외
            context: 에러 발생 맥락
        """
        message = f"{service_name} - ERROR: {str(error)}"
        if context:
            message += f" (Context: {context})"
        
        self._service_logger.error(message, exc_info=True)
    
    def set_log_level(self, level: str):
        """
        로그 레벨 설정
        
        Args:
            level: 로그 레벨 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {level}')
        
        self._service_logger.setLevel(numeric_level)
    
    def add_file_handler(self, log_file_path: str, level: str = 'DEBUG'):
        """
        파일 핸들러 추가
        
        Args:
            log_file_path: 로그 파일 경로
            level: 파일 로그 레벨
        """
        # 로그 디렉토리 생성
        log_file = Path(log_file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 파일 핸들러 생성
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 레벨 설정
        numeric_level = getattr(logging, level.upper())
        file_handler.setLevel(numeric_level)
        
        # 로거에 핸들러 추가
        self._service_logger.addHandler(file_handler) 