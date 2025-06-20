"""
설정값 DB 탭 컨트롤러
설정값 관리를 위한 전용 탭 컨트롤러
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List, Optional

from ..base_controller import TabController


class DefaultDBTabController(TabController):
    """설정값 DB 탭 컨트롤러"""
    
    def __init__(self, tab_frame: tk.Frame, viewmodel, tab_name: str = "설정값 DB"):
        """DefaultDBTabController 초기화"""
        super().__init__(tab_frame, viewmodel, tab_name)
        
        # UI 생성
        self._create_tab_ui()
    
    def _create_tab_ui(self):
        """탭 UI 생성"""
        # 임시 구현
        label = ttk.Label(self.tab_frame, text="설정값 DB 관리 (향후 구현)")
        label.pack(pady=20)
    
    def on_tab_activated(self):
        """탭 활성화 시 호출"""
        super().on_tab_activated()
    
    def get_tab_title(self) -> str:
        """탭 제목 반환"""
        return "📝 설정값 DB"