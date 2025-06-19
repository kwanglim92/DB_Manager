"""
애플리케이션 팩토리 - 기존 DBManager와 새 구조의 브리지
"""
from app.core.config import AppConfig
from app.utils.path_utils import PathManager
from app.utils.validation import ValidationUtils

class AppFactory:
    """애플리케이션 구성 요소들을 생성하는 팩토리"""
    
    @staticmethod
    def create_config() -> AppConfig:
        """설정 객체 생성"""
        return AppConfig()
    
    @staticmethod
    def create_path_manager() -> PathManager:
        """경로 관리자 생성"""
        return PathManager()
    
    @staticmethod
    def create_validator() -> ValidationUtils:
        """검증 유틸리티 생성"""
        return ValidationUtils() 