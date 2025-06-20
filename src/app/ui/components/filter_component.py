"""
필터 컴포넌트
검색, 필터링, 옵션 선택을 위한 재사용 가능한 컴포넌트
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Tuple, Dict, Any

from .base_component import BaseComponent


class FilterComponent(BaseComponent):
    """필터 및 검색 컴포넌트"""
    
    def __init__(self, parent=None):
        """FilterComponent 초기화"""
        super().__init__(parent)
        
        # 컴포넌트 요소들
        self.search_var = tk.StringVar()
        self.search_entry = None
        self.checkboxes = {}
        self.checkbox_vars = {}
        self.quick_filter_buttons = []
        
        # 콜백 함수들
        self.search_callback = None
        self.checkbox_callbacks = {}
        self.quick_filter_callback = None
        
        # 위젯 생성
        self.widget = self.create_widget()
    
    def create_widget(self):
        """필터 위젯 생성"""
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.X, padx=5, pady=5)
        return main_frame
    
    def add_search_filter(self, label: str, callback: Callable[[str], None]):
        """검색 필터 추가"""
        self.search_callback = callback
        
        # 검색 프레임
        search_frame = ttk.Frame(self.widget)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 라벨
        search_label = ttk.Label(search_frame, text=label)
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 검색 입력 필드
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 검색 버튼
        search_button = ttk.Button(search_frame, text="🔍", width=3, 
                                  command=self._handle_search)
        search_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 클리어 버튼
        clear_button = ttk.Button(search_frame, text="❌", width=3,
                                 command=self._handle_clear_search)
        clear_button.pack(side=tk.LEFT)
        
        # 엔터 키 바인딩
        self.search_entry.bind('<Return>', lambda e: self._handle_search())
        self.search_entry.bind('<KeyRelease>', self._handle_search_key_release)
    
    def add_checkbox(self, label: str, callback: Callable[[bool], None], initial_value: bool = False):
        """체크박스 옵션 추가"""
        self.checkbox_callbacks[label] = callback
        
        # 체크박스 변수
        checkbox_var = tk.BooleanVar(value=initial_value)
        self.checkbox_vars[label] = checkbox_var
        
        # 체크박스 위젯
        checkbox = ttk.Checkbutton(self.widget, text=label, variable=checkbox_var,
                                  command=lambda: self._handle_checkbox_change(label))
        checkbox.pack(anchor=tk.W, pady=2)
        
        self.checkboxes[label] = checkbox
    
    def add_quick_filter_buttons(self, filters: List[Tuple[str, str]], 
                                callback: Callable[[str], None]):
        """빠른 필터 버튼들 추가"""
        self.quick_filter_callback = callback
        
        # 빠른 필터 프레임
        quick_frame = ttk.LabelFrame(self.widget, text="빠른 필터")
        quick_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 버튼들을 그리드로 배치
        button_frame = ttk.Frame(quick_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        for i, (display_text, filter_value) in enumerate(filters):
            button = ttk.Button(button_frame, text=display_text,
                               command=lambda v=filter_value: self._handle_quick_filter(v))
            button.grid(row=i//4, column=i%4, padx=2, pady=2, sticky="ew")
            self.quick_filter_buttons.append(button)
        
        # 컬럼 가중치 설정
        for i in range(4):
            button_frame.columnconfigure(i, weight=1)
    
    def set_filter_text(self, text: str):
        """필터 텍스트 설정"""
        self.search_var.set(text)
    
    def get_filter_text(self) -> str:
        """현재 필터 텍스트 반환"""
        return self.search_var.get()
    
    def set_checkbox_state(self, label: str, checked: bool):
        """체크박스 상태 설정"""
        if label in self.checkbox_vars:
            self.checkbox_vars[label].set(checked)
    
    def get_checkbox_state(self, label: str) -> bool:
        """체크박스 상태 반환"""
        if label in self.checkbox_vars:
            return self.checkbox_vars[label].get()
        return False
    
    def focus_search(self):
        """검색 필드에 포커스"""
        if self.search_entry:
            self.search_entry.focus_set()
            self.search_entry.select_range(0, tk.END)
    
    def clear_all_filters(self):
        """모든 필터 클리어"""
        # 검색 텍스트 클리어
        self.search_var.set("")
        
        # 모든 체크박스 해제
        for var in self.checkbox_vars.values():
            var.set(False)
        
        # 콜백 호출
        if self.search_callback:
            self.search_callback("")
        
        for label, callback in self.checkbox_callbacks.items():
            callback(False)
    
    def _handle_search(self):
        """검색 처리"""
        if self.search_callback:
            search_text = self.search_var.get().strip()
            self.search_callback(search_text)
    
    def _handle_clear_search(self):
        """검색 클리어 처리"""
        self.search_var.set("")
        self._handle_search()
    
    def _handle_search_key_release(self, event):
        """검색 키 릴리즈 처리 (실시간 검색)"""
        # 짧은 지연 후 검색 실행 (너무 빈번한 검색 방지)
        if hasattr(self, '_search_after_id'):
            self.widget.after_cancel(self._search_after_id)
        
        self._search_after_id = self.widget.after(300, self._handle_search)
    
    def _handle_checkbox_change(self, label: str):
        """체크박스 변경 처리"""
        if label in self.checkbox_callbacks:
            checked = self.checkbox_vars[label].get()
            self.checkbox_callbacks[label](checked)
    
    def _handle_quick_filter(self, filter_value: str):
        """빠른 필터 처리"""
        if self.quick_filter_callback:
            self.quick_filter_callback(filter_value)
    
    def update_button_states(self, enabled_buttons: List[str] = None):
        """버튼 상태 업데이트"""
        if enabled_buttons is None:
            # 모든 버튼 활성화
            for button in self.quick_filter_buttons:
                button.configure(state=tk.NORMAL)
        else:
            # 지정된 버튼들만 활성화
            for i, button in enumerate(self.quick_filter_buttons):
                if i < len(enabled_buttons):
                    button.configure(state=tk.NORMAL if enabled_buttons[i] else tk.DISABLED)
    
    def get_current_filters(self) -> Dict[str, Any]:
        """현재 필터 상태 반환"""
        return {
            'search_text': self.get_filter_text(),
            'checkboxes': {label: var.get() for label, var in self.checkbox_vars.items()}
        }
    
    def apply_filters(self, filters: Dict[str, Any]):
        """필터 상태 적용"""
        if 'search_text' in filters:
            self.set_filter_text(filters['search_text'])
        
        if 'checkboxes' in filters:
            for label, checked in filters['checkboxes'].items():
                self.set_checkbox_state(label, checked)