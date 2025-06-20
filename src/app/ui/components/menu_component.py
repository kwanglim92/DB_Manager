"""
메뉴 컴포넌트
재사용 가능한 메뉴 UI 컴포넌트
"""

import tkinter as tk
from .base_component import BaseComponent


class MenuComponent(BaseComponent):
    """메뉴 컴포넌트 클래스"""
    
    def __init__(self, parent=None):
        """MenuComponent 초기화"""
        super().__init__(parent)
        self.menu_items = []
    
    def create_widget(self):
        """메뉴 위젯 생성"""
        return tk.Menu(self.parent)
    
    def add_menu_item(self, label: str, command=None, **kwargs):
        """메뉴 항목 추가"""
        if self.widget:
            self.widget.add_command(label=label, command=command, **kwargs)
            self.menu_items.append({'label': label, 'command': command})
    
    def add_separator(self):
        """구분선 추가"""
        if self.widget:
            self.widget.add_separator()
    
    def clear_menu(self):
        """모든 메뉴 항목 제거"""
        if self.widget:
            self.widget.delete(0, tk.END)
            self.menu_items.clear() 