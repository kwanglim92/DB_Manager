"""
애플리케이션 설정 관리 모듈
기존 settings.json과 constants.py를 통합하여 관리하는 새로운 설정 시스템
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

class AppConfig:
    """
    애플리케이션 설정 관리 클래스
    기존 코드를 건드리지 않고 새로운 설정 시스템을 제공
    """
    
    def __init__(self):
        # 앱 기본 정보
        self.app_name = "DB Manager"
        self.version = "1.0.1"
        self.author = "kwanglim92"
        
        # 경로 설정
        self.project_root = self._get_project_root()
        self.config_path = self.project_root / "config" / "settings.json"
        self.data_path = self.project_root / "src" / "data"
        self.resources_path = self.project_root / "resources"
        
        # 설정 로드
        self._settings = self._load_settings()
    
    def _get_project_root(self) -> Path:
        """프로젝트 루트 디렉토리 반환"""
        current = Path(__file__).parent
        # core -> app -> src -> project_root
        return current.parent.parent.parent
    
    def _load_settings(self) -> Dict[str, Any]:
        """settings.json 파일 로드"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
        
        # 기본 설정 반환
        return {
            "maint_password_hash": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
            "page_size": 100,
            "auto_backup": True,
            "backup_interval_days": 7
        }
    
    def save_settings(self) -> bool:
        """설정을 파일에 저장"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")
            return False
    
    # 설정 접근 프로퍼티
    @property
    def maint_password_hash(self) -> str:
        """유지보수 모드 비밀번호 해시"""
        return self._settings.get("maint_password_hash", "")
    
    @maint_password_hash.setter
    def maint_password_hash(self, value: str):
        self._settings["maint_password_hash"] = value
    
    @property
    def page_size(self) -> int:
        """페이지 크기"""
        return self._settings.get("page_size", 100)
    
    @property
    def auto_backup(self) -> bool:
        """자동 백업 여부"""
        return self._settings.get("auto_backup", True)
    
    @property
    def backup_interval_days(self) -> int:
        """백업 간격 (일)"""
        return self._settings.get("backup_interval_days", 7)
    
    # UI 설정
    @property
    def window_geometry(self) -> str:
        """메인 윈도우 크기"""
        return "1300x800"
    
    @property
    def icon_path(self) -> Optional[Path]:
        """아이콘 파일 경로"""
        icon_path = self.resources_path / "icons" / "db_compare.ico"
        return icon_path if icon_path.exists() else None
    
    @property
    def db_path(self) -> Path:
        """데이터베이스 파일 경로"""
        self.data_path.mkdir(parents=True, exist_ok=True)
        return self.data_path / "local_db.sqlite"
    
    # 파일 타입 설정
    @property
    def supported_file_types(self) -> list:
        """지원하는 파일 형식"""
        return [
            ("DB 파일", "*.txt;*.db;*.csv"),
            ("텍스트 파일", "*.txt"),
            ("CSV 파일", "*.csv"),
            ("DB 파일", "*.db"),
            ("모든 파일", "*.*")
        ]
    
    # 새로운 설정 추가 메서드
    def get_setting(self, key: str, default=None):
        """설정값 가져오기"""
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """설정값 설정하기"""
        self._settings[key] = value
    
    def get_all_settings(self) -> Dict[str, Any]:
        """모든 설정 반환"""
        return self._settings.copy()


# 전역 설정 인스턴스 (필요시 사용)
_global_config = None

def get_app_config() -> AppConfig:
    """전역 설정 인스턴스 반환"""
    global _global_config
    if _global_config is None:
        _global_config = AppConfig()
    return _global_config 