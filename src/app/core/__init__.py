"""
Core 모듈
애플리케이션 핵심 기능과 설정 관리
"""

from .app_factory import create_app
from .config import AppConfig

# 🎯 3단계: MVVM 통합 어댑터
class MVVMAdapter:
    """
    기존 manager.py와 새로운 MVVM 시스템 간의 어댑터
    점진적 전환을 위한 호환성 레이어
    """
    
    def __init__(self, manager_instance=None):
        """어댑터 초기화"""
        self.manager = manager_instance
        self.viewmodel = None
        self.controller = None
        self._use_mvvm = False
    
    def enable_mvvm(self, main_window=None):
        """MVVM 시스템 활성화"""
        try:
            from ..ui import MainViewModel, MainController
            
            # ViewModel 생성
            self.viewmodel = MainViewModel()
            
            # 기존 manager 상태 동기화
            if self.manager:
                self._sync_from_manager()
            
            # Controller 생성 (main_window가 있으면)
            if main_window:
                self.controller = MainController(main_window, self.viewmodel)
            
            self._use_mvvm = True
            print("✅ MVVM 시스템 활성화 완료")
            
            return True
            
        except Exception as e:
            print(f"❌ MVVM 시스템 활성화 실패: {e}")
            return False
    
    def _sync_from_manager(self):
        """기존 manager의 상태를 ViewModel로 동기화"""
        if not self.manager or not self.viewmodel:
            return
        
        try:
            # 유지보수 모드 동기화
            if hasattr(self.manager, 'maint_mode'):
                self.viewmodel.maint_mode = self.manager.maint_mode
            
            # 선택된 장비 유형 동기화
            if hasattr(self.manager, 'selected_equipment_type_id'):
                self.viewmodel.selected_equipment_type_id = self.manager.selected_equipment_type_id
            
            # 파일 목록 동기화
            if hasattr(self.manager, 'file_names'):
                for filename in self.manager.file_names:
                    self.viewmodel.add_file(filename)
            
            # 폴더 경로 동기화
            if hasattr(self.manager, 'folder_path'):
                self.viewmodel.folder_path = self.manager.folder_path
            
            print("✅ Manager 상태 동기화 완료")
            
        except Exception as e:
            print(f"❌ Manager 상태 동기화 실패: {e}")
    
    def _sync_to_manager(self):
        """ViewModel의 상태를 기존 manager로 동기화"""
        if not self.manager or not self.viewmodel:
            return
        
        try:
            # 유지보수 모드 동기화
            if hasattr(self.manager, 'maint_mode'):
                self.manager.maint_mode = self.viewmodel.maint_mode
            
            # 선택된 장비 유형 동기화
            if hasattr(self.manager, 'selected_equipment_type_id'):
                self.manager.selected_equipment_type_id = self.viewmodel.selected_equipment_type_id
            
            print("✅ ViewModel 상태 동기화 완료")
            
        except Exception as e:
            print(f"❌ ViewModel 상태 동기화 실패: {e}")
    
    def get_viewmodel(self):
        """ViewModel 반환"""
        return self.viewmodel
    
    def get_controller(self):
        """Controller 반환"""
        return self.controller
    
    def is_mvvm_enabled(self):
        """MVVM 시스템 활성화 여부"""
        return self._use_mvvm
    
    def cleanup(self):
        """리소스 정리"""
        if self.viewmodel:
            self.viewmodel.cleanup()
        if self.controller:
            self.controller.cleanup()

__all__ = [
    'create_app',
    'AppConfig',
    'MVVMAdapter',
]