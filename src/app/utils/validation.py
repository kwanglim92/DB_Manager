"""
데이터 검증 유틸리티 모듈
기존 코드를 건드리지 않고 새로운 검증 시스템을 제공
"""

import hashlib
import re
from typing import Optional, Any, List, Union
from pathlib import Path

class ValidationUtils:
    """
    데이터 검증을 위한 유틸리티 클래스
    기존 코드와 독립적으로 작동
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        비밀번호를 SHA-256으로 해시화
        
        Args:
            password: 원본 비밀번호
            
        Returns:
            str: 해시된 비밀번호
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(input_password: str, stored_hash: str) -> bool:
        """
        비밀번호 검증
        
        Args:
            input_password: 입력된 비밀번호
            stored_hash: 저장된 해시
            
        Returns:
            bool: 검증 결과
        """
        input_hash = ValidationUtils.hash_password(input_password)
        return input_hash == stored_hash
    
    @staticmethod
    def is_valid_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """
        파일 확장자 검증
        
        Args:
            filename: 파일명
            allowed_extensions: 허용된 확장자 리스트 (예: ['.txt', '.csv', '.db'])
            
        Returns:
            bool: 검증 결과
        """
        if not filename:
            return False
        
        file_path = Path(filename)
        file_ext = file_path.suffix.lower()
        return file_ext in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        파일명에서 특수문자 제거
        
        Args:
            filename: 원본 파일명
            
        Returns:
            str: 안전한 파일명
        """
        # 윈도우에서 사용할 수 없는 문자 제거
        invalid_chars = r'[<>:"/\\|?*]'
        return re.sub(invalid_chars, '_', filename)
    
    @staticmethod
    def validate_numeric_value(value: Any) -> Optional[float]:
        """
        숫자 값 검증 및 변환
        
        Args:
            value: 검증할 값
            
        Returns:
            float: 변환된 숫자 (실패시 None)
        """
        if value is None or value == "":
            return None
        
        try:
            # 쉼표 제거 후 float 변환
            return float(str(value).replace(',', ''))
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        이메일 주소 형식 검증
        
        Args:
            email: 이메일 주소
            
        Returns:
            bool: 검증 결과
        """
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def validate_range(value: Union[int, float], min_val: Optional[Union[int, float]] = None, 
                      max_val: Optional[Union[int, float]] = None) -> bool:
        """
        숫자 범위 검증
        
        Args:
            value: 검증할 값
            min_val: 최소값 (None이면 검증 안함)
            max_val: 최대값 (None이면 검증 안함)
            
        Returns:
            bool: 범위 내 여부
        """
        try:
            num_value = float(value)
            
            if min_val is not None and num_value < min_val:
                return False
            
            if max_val is not None and num_value > max_val:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_empty_or_whitespace(value: str) -> bool:
        """
        빈 문자열 또는 공백만 있는지 검증
        
        Args:
            value: 검증할 문자열
            
        Returns:
            bool: 빈 문자열 여부
        """
        return not value or value.isspace()
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: List[str]) -> List[str]:
        """
        필수 필드 검증
        
        Args:
            data: 검증할 데이터 딕셔너리
            required_fields: 필수 필드 리스트
            
        Returns:
            List[str]: 누락된 필드 리스트
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in data or ValidationUtils.is_empty_or_whitespace(str(data[field])):
                missing_fields.append(field)
        
        return missing_fields
    
    @staticmethod
    def clean_string(value: str) -> str:
        """
        문자열 정리 (앞뒤 공백 제거, 개행 문자 제거)
        
        Args:
            value: 원본 문자열
            
        Returns:
            str: 정리된 문자열
        """
        if not value:
            return ""
        
        return str(value).strip().replace('\n', ' ').replace('\r', ' ')
    
    @staticmethod
    def is_valid_database_name(name: str) -> bool:
        """
        데이터베이스/테이블명 검증
        
        Args:
            name: 데이터베이스명
            
        Returns:
            bool: 유효성 여부
        """
        if not name:
            return False
        
        # 영문자, 숫자, 언더스코어만 허용
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, name))
    
    @staticmethod
    def validate_file_size(file_path: Union[str, Path], max_size_mb: float = 100) -> bool:
        """
        파일 크기 검증
        
        Args:
            file_path: 파일 경로
            max_size_mb: 최대 크기 (MB)
            
        Returns:
            bool: 크기 제한 내 여부
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            file_size_mb = path.stat().st_size / (1024 * 1024)
            return file_size_mb <= max_size_mb
        except Exception:
            return False 