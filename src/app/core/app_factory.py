"""
애플리케이션 팩토리 - 기존 DBManager와 새 구조의 브리지
"""
from app.core.config import AppConfig
from app.utils.path_utils import PathManager
from app.utils.validation import ValidationUtils
import tkinter as tk
from typing import Optional, Dict, Any

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

"""
애플리케이션 팩토리
애플리케이션 인스턴스 생성 및 초기화
"""

def create_app(config: Optional[AppConfig] = None, use_mvvm: bool = True) -> Dict[str, Any]:
    """
    애플리케이션 생성
    
    Args:
        config: 애플리케이션 설정
        use_mvvm: MVVM 패턴 사용 여부
        
    Returns:
        애플리케이션 컴포넌트들을 포함한 딕셔너리
    """
    if config is None:
        config = AppConfig()
    
    # 메인 윈도우 생성
    root = tk.Tk()
    root.title("DB Manager")
    root.geometry("1300x800")
    
    app_components = {
        'root': root,
        'config': config,
        'mvvm_enabled': use_mvvm
    }
    
    if use_mvvm:
        try:
            from .. import MVVMAdapter
            
            # MVVM 어댑터 생성
            adapter = MVVMAdapter()
            success = adapter.enable_mvvm(root)
            
            if success:
                app_components['mvvm_adapter'] = adapter
                app_components['viewmodel'] = adapter.get_viewmodel()
                app_components['controller'] = adapter.get_controller()
            else:
                app_components['mvvm_enabled'] = False
                
        except Exception as e:
            print(f"MVVM 초기화 실패, 기본 모드로 실행: {e}")
            app_components['mvvm_enabled'] = False
    
    return app_components


def cleanup_app(app_components: Dict[str, Any]):
    """애플리케이션 정리"""
    try:
        if 'mvvm_adapter' in app_components:
            app_components['mvvm_adapter'].cleanup()
        
        if 'root' in app_components:
            app_components['root'].destroy()
            
    except Exception as e:
        print(f"애플리케이션 정리 중 오류: {e}")