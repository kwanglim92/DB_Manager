"""
사용자 모드 관리 클래스
장비 생산 엔지니어 모드와 QC 엔지니어 모드 전환 관리
"""

from typing import Callable, Optional
from tkinter import simpledialog, messagebox
from enum import Enum
import hashlib

class UserMode(Enum):
    """사용자 모드 열거형"""
    PRODUCTION_ENGINEER = "장비 생산 엔지니어"
    QC_ENGINEER = "QC 엔지니어"

class ModeManager:
    """사용자 모드 관리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.current_mode = UserMode.PRODUCTION_ENGINEER
        self.is_authenticated = False
        self.mode_change_callbacks = []
        
        # 기본 비밀번호 해시 (password: '1')
        self.password_hash = "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b"
    
    def get_current_mode(self) -> UserMode:
        """현재 모드 반환"""
        return self.current_mode
    
    def is_qc_mode(self) -> bool:
        """QC 엔지니어 모드인지 확인"""
        return self.current_mode == UserMode.QC_ENGINEER
    
    def is_production_mode(self) -> bool:
        """장비 생산 엔지니어 모드인지 확인"""
        return self.current_mode == UserMode.PRODUCTION_ENGINEER
    
    def toggle_mode(self, parent_window=None) -> bool:
        """
        모드 전환
        
        Args:
            parent_window: 부모 윈도우 (다이얼로그용)
            
        Returns:
            모드 전환 성공 여부
        """
        if self.is_qc_mode():
            # QC 모드 -> 생산 모드로 전환
            return self._switch_to_production_mode()
        else:
            # 생산 모드 -> QC 모드로 전환 (인증 필요)
            return self._switch_to_qc_mode(parent_window)
    
    def _switch_to_production_mode(self) -> bool:
        """생산 엔지니어 모드로 전환"""
        self.current_mode = UserMode.PRODUCTION_ENGINEER
        self.is_authenticated = False
        self._notify_mode_change()
        return True
    
    def _switch_to_qc_mode(self, parent_window=None) -> bool:
        """QC 엔지니어 모드로 전환 (인증 필요)"""
        # 비밀번호 입력 다이얼로그
        password = simpledialog.askstring(
            "QC 엔지니어 모드",
            "QC 엔지니어 비밀번호를 입력하세요:",
            parent=parent_window,
            show="*"
        )
        
        if password is None:
            return False
        
        # 비밀번호 검증
        if self._verify_password(password):
            self.current_mode = UserMode.QC_ENGINEER
            self.is_authenticated = True
            self._notify_mode_change()
            return True
        else:
            messagebox.showerror(
                "인증 실패",
                "비밀번호가 일치하지 않습니다.",
                parent=parent_window
            )
            return False
    
    def _verify_password(self, password: str) -> bool:
        """비밀번호 검증"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.password_hash
    
    def set_password(self, new_password: str):
        """새 비밀번호 설정"""
        self.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    def register_mode_change_callback(self, callback: Callable):
        """모드 변경 콜백 등록"""
        if callback not in self.mode_change_callbacks:
            self.mode_change_callbacks.append(callback)
    
    def unregister_mode_change_callback(self, callback: Callable):
        """모드 변경 콜백 해제"""
        if callback in self.mode_change_callbacks:
            self.mode_change_callbacks.remove(callback)
    
    def _notify_mode_change(self):
        """모드 변경 알림"""
        for callback in self.mode_change_callbacks:
            try:
                callback(self.current_mode)
            except Exception as e:
                print(f"모드 변경 콜백 실행 중 오류: {e}")
    
    def get_mode_display_name(self) -> str:
        """현재 모드의 표시 이름 반환"""
        return self.current_mode.value + " 모드"
    
    def get_available_features(self) -> dict:
        """
        현재 모드에서 사용 가능한 기능 반환
        
        Returns:
            기능명과 활성화 여부 딕셔너리
        """
        if self.is_qc_mode():
            return {
                "db_comparison": True,
                "mother_db_management": True,
                "qc_inspection": True,
                "default_db_transfer": True,
                "report_generation": True,
                "advanced_analysis": True
            }
        else:
            return {
                "db_comparison": True,
                "mother_db_management": False,
                "qc_inspection": False,
                "default_db_transfer": False,
                "report_generation": True,
                "advanced_analysis": False
            }