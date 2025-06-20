"""
툴바 컴포넌트
버튼, 구분선 등을 포함한 툴바 UI 컴포넌트
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict, Optional

from .base_component import BaseComponent


class ToolbarComponent(BaseComponent):
    """툴바 컴포넌트"""
    
    def __init__(self, parent=None):
        """ToolbarComponent 초기화"""
        super().__init__(parent)
        
        # 툴바 요소들
        self.buttons = []
        self.separators = []
        self.current_column = 0
        
        # 위젯 생성
        self.widget = self.create_widget()
    
    def create_widget(self):
        """툴바 위젯 생성"""
        toolbar_frame = ttk.Frame(self.parent)
        toolbar_frame.pack(fill=tk.X)
        return toolbar_frame
    
    def add_button(self, text: str, command: Callable, tooltip: str = "", 
                   style: str = "default", width: Optional[int] = None) -> ttk.Button:
        """버튼 추가"""
        button_style = self._get_button_style(style)
        
        button = ttk.Button(self.widget, text=text, command=command, style=button_style)
        
        if width:
            button.configure(width=width)
        
        button.grid(row=0, column=self.current_column, padx=2, pady=2, sticky="ew")
        
        # 툴팁 추가
        if tooltip:
            self._add_tooltip(button, tooltip)
        
        self.buttons.append({
            'widget': button,
            'text': text,
            'command': command,
            'tooltip': tooltip,
            'column': self.current_column
        })
        
        self.current_column += 1
        return button
    
    def add_separator(self):
        """구분선 추가"""
        separator = ttk.Separator(self.widget, orient=tk.VERTICAL)
        separator.grid(row=0, column=self.current_column, padx=5, pady=2, sticky="ns")
        
        self.separators.append({
            'widget': separator,
            'column': self.current_column
        })
        
        self.current_column += 1
    
    def add_label(self, text: str, style: str = "default") -> ttk.Label:
        """라벨 추가"""
        label = ttk.Label(self.widget, text=text)
        label.grid(row=0, column=self.current_column, padx=5, pady=2, sticky="ew")
        
        self.current_column += 1
        return label
    
    def add_combobox(self, values: List[str], callback: Callable[[str], None], 
                     default_value: str = "", width: int = 15) -> ttk.Combobox:
        """콤보박스 추가"""
        combobox_var = tk.StringVar(value=default_value)
        
        combobox = ttk.Combobox(self.widget, textvariable=combobox_var, 
                               values=values, width=width, state="readonly")
        combobox.grid(row=0, column=self.current_column, padx=2, pady=2, sticky="ew")
        
        # 콜백 바인딩
        combobox.bind('<<ComboboxSelected>>', 
                     lambda e: callback(combobox_var.get()))
        
        self.current_column += 1
        return combobox
    
    def add_progress_bar(self, length: int = 100) -> ttk.Progressbar:
        """진행률 표시줄 추가"""
        progress = ttk.Progressbar(self.widget, length=length, mode='determinate')
        progress.grid(row=0, column=self.current_column, padx=5, pady=2, sticky="ew")
        
        self.current_column += 1
        return progress
    
    def add_spacer(self, expand: bool = True):
        """여백 추가"""
        spacer = ttk.Frame(self.widget)
        spacer.grid(row=0, column=self.current_column, sticky="ew")
        
        if expand:
            self.widget.columnconfigure(self.current_column, weight=1)
        
        self.current_column += 1
    
    def enable_button(self, button_text: str):
        """버튼 활성화"""
        for button_info in self.buttons:
            if button_info['text'] == button_text:
                button_info['widget'].configure(state=tk.NORMAL)
                break
    
    def disable_button(self, button_text: str):
        """버튼 비활성화"""
        for button_info in self.buttons:
            if button_info['text'] == button_text:
                button_info['widget'].configure(state=tk.DISABLED)
                break
    
    def set_button_text(self, old_text: str, new_text: str):
        """버튼 텍스트 변경"""
        for button_info in self.buttons:
            if button_info['text'] == old_text:
                button_info['widget'].configure(text=new_text)
                button_info['text'] = new_text
                break
    
    def remove_button(self, button_text: str):
        """버튼 제거"""
        for i, button_info in enumerate(self.buttons):
            if button_info['text'] == button_text:
                button_info['widget'].destroy()
                self.buttons.pop(i)
                break
    
    def clear_toolbar(self):
        """툴바 모든 요소 제거"""
        for button_info in self.buttons:
            button_info['widget'].destroy()
        
        for separator_info in self.separators:
            separator_info['widget'].destroy()
        
        self.buttons.clear()
        self.separators.clear()
        self.current_column = 0
    
    def get_button_count(self) -> int:
        """버튼 개수 반환"""
        return len(self.buttons)
    
    def update_button_states(self, button_states: Dict[str, bool]):
        """여러 버튼 상태 일괄 업데이트"""
        for button_text, enabled in button_states.items():
            if enabled:
                self.enable_button(button_text)
            else:
                self.disable_button(button_text)
    
    def _get_button_style(self, style: str) -> str:
        """버튼 스타일 반환"""
        style_map = {
            "default": "",
            "primary": "Accent.TButton",
            "success": "Success.TButton", 
            "warning": "Warning.TButton",
            "danger": "Danger.TButton"
        }
        return style_map.get(style, "")
    
    def _add_tooltip(self, widget: tk.Widget, text: str):
        """툴팁 추가"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            label = tk.Label(tooltip, text=text, background="lightyellow",
                           relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            
            # 3초 후 툴팁 제거
            tooltip.after(3000, tooltip.destroy)
            
            # 마우스가 벗어나면 툴팁 제거
            def hide_tooltip(event):
                tooltip.destroy()
            
            widget.bind('<Leave>', hide_tooltip, add=True)
        
        widget.bind('<Enter>', show_tooltip)


class ContextualToolbar(ToolbarComponent):
    """상황별 툴바 (동적으로 버튼이 변경되는 툴바)"""
    
    def __init__(self, parent=None):
        """ContextualToolbar 초기화"""
        super().__init__(parent)
        self.contexts = {}
        self.current_context = None
    
    def add_context(self, context_name: str, buttons: List[Dict]):
        """상황별 버튼 구성 추가"""
        self.contexts[context_name] = buttons
    
    def switch_context(self, context_name: str):
        """상황 전환"""
        if context_name not in self.contexts:
            return
        
        if context_name == self.current_context:
            return
        
        # 현재 툴바 클리어
        self.clear_toolbar()
        
        # 새 상황의 버튼들 추가
        for button_config in self.contexts[context_name]:
            if button_config.get('type') == 'separator':
                self.add_separator()
            elif button_config.get('type') == 'spacer':
                self.add_spacer(button_config.get('expand', True))
            else:
                self.add_button(
                    text=button_config['text'],
                    command=button_config['command'],
                    tooltip=button_config.get('tooltip', ''),
                    style=button_config.get('style', 'default'),
                    width=button_config.get('width')
                )
        
        self.current_context = context_name
    
    def get_available_contexts(self) -> List[str]:
        """사용 가능한 상황 목록 반환"""
        return list(self.contexts.keys())
    
    def get_current_context(self) -> Optional[str]:
        """현재 상황 반환"""
        return self.current_context


class StatusToolbar(ToolbarComponent):
    """상태 표시 툴바"""
    
    def __init__(self, parent=None):
        """StatusToolbar 초기화"""
        super().__init__(parent)
        
        # 상태 요소들
        self.status_labels = {}
        self.progress_bars = {}
    
    def add_status_label(self, name: str, text: str = "", style: str = "default") -> ttk.Label:
        """상태 라벨 추가"""
        label = self.add_label(text, style)
        self.status_labels[name] = label
        return label
    
    def add_status_progress(self, name: str, length: int = 100) -> ttk.Progressbar:
        """상태 진행률 표시줄 추가"""
        progress = self.add_progress_bar(length)
        self.progress_bars[name] = progress
        return progress
    
    def update_status_label(self, name: str, text: str):
        """상태 라벨 업데이트"""
        if name in self.status_labels:
            self.status_labels[name].configure(text=text)
    
    def update_progress(self, name: str, value: int):
        """진행률 업데이트"""
        if name in self.progress_bars:
            self.progress_bars[name]['value'] = value
    
    def set_progress_range(self, name: str, maximum: int):
        """진행률 범위 설정"""
        if name in self.progress_bars:
            self.progress_bars[name]['maximum'] = maximum