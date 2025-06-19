"""
경로 관리 유틸리티 모듈
기존 코드를 건드리지 않고 새로운 경로 관리 시스템을 제공
"""

import os
import sys
from pathlib import Path
from typing import Optional

class PathManager:
    """
    경로 관리를 위한 유틸리티 클래스
    PyInstaller 빌드와 개발 환경 모두 지원
    """
    
    @staticmethod
    def get_application_path() -> Path:
        """
        애플리케이션 실행 경로 반환 (PyInstaller 호환)
        
        Returns:
            Path: 애플리케이션 경로
        """
        if getattr(sys, 'frozen', False):
            # PyInstaller로 빌드된 경우
            return Path(sys._MEIPASS)
        else:
            # 개발 환경: 현재 파일 기준으로 프로젝트 루트 찾기
            current_file = Path(__file__)
            # path_utils.py -> utils -> app -> src -> project_root
            return current_file.parent.parent.parent.parent
    
    @staticmethod
    def get_project_root() -> Path:
        """프로젝트 루트 디렉토리 반환"""
        return PathManager.get_application_path()
    
    @staticmethod
    def get_src_path() -> Path:
        """src 디렉토리 경로 반환"""
        return PathManager.get_project_root() / "src"
    
    @staticmethod
    def get_config_path() -> Path:
        """config 디렉토리 경로 반환"""
        return PathManager.get_project_root() / "config"
    
    @staticmethod
    def get_resources_path() -> Path:
        """resources 디렉토리 경로 반환"""
        return PathManager.get_project_root() / "resources"
    
    @staticmethod
    def get_data_path() -> Path:
        """data 디렉토리 경로 반환 (생성도 함께 수행)"""
        data_path = PathManager.get_src_path() / "data"
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path
    
    @staticmethod
    def get_icon_path(icon_name: str = "db_compare.ico") -> Optional[Path]:
        """
        아이콘 파일 경로 반환
        
        Args:
            icon_name: 아이콘 파일명
            
        Returns:
            Path: 아이콘 경로 (존재하지 않으면 None)
        """
        icon_path = PathManager.get_resources_path() / "icons" / icon_name
        return icon_path if icon_path.exists() else None
    
    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """
        디렉토리 존재 확인 및 생성
        
        Args:
            path: 생성할 디렉토리 경로
            
        Returns:
            Path: 생성된 디렉토리 경로
        """
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        안전한 파일명 생성 (특수문자 제거)
        
        Args:
            filename: 원본 파일명
            
        Returns:
            str: 안전한 파일명
        """
        import re
        # 윈도우에서 사용할 수 없는 문자 제거
        invalid_chars = r'[<>:"/\\|?*]'
        return re.sub(invalid_chars, '_', filename)
    
    @staticmethod
    def is_valid_path(path_str: str) -> bool:
        """
        유효한 경로인지 확인
        
        Args:
            path_str: 경로 문자열
            
        Returns:
            bool: 유효성 여부
        """
        try:
            Path(path_str)
            return True
        except Exception:
            return False 