"""
테마 매니저
애플리케이션 테마 관리 및 적용
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Type
from abc import ABC, abstractmethod


class BaseTheme(ABC):
    """기본 테마 추상 클래스"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """테마 이름"""
        pass
    
    @property
    @abstractmethod
    def colors(self) -> Dict[str, str]:
        """색상 팔레트"""
        pass
    
    @property
    @abstractmethod
    def fonts(self) -> Dict[str, tuple]:
        """폰트 설정"""
        pass
    
    @property
    @abstractmethod
    def styles(self) -> Dict[str, Dict[str, Any]]:
        """위젯 스타일"""
        pass
    
    def apply_to_root(self, root: tk.Tk):
        """루트 윈도우에 테마 적용"""
        root.configure(bg=self.colors.get('background', '#ffffff'))


class ThemeManager:
    """테마 관리자"""
    
    def __init__(self):
        """ThemeManager 초기화"""
        self.current_theme = None
        self.root_widget = None
        self.style = None
        
        # 사용 가능한 테마들 (동적 import 방지)
        self.themes: Dict[str, Type[BaseTheme]] = {}
        
        # 테마 변경 콜백들
        self.theme_change_callbacks = []
        
        # 기본 테마들 등록
        self._register_default_themes()
    
    def _register_default_themes(self):
        """기본 테마들 등록"""
        try:
            from .default_theme import DefaultTheme
            self.themes['default'] = DefaultTheme
        except ImportError:
            pass
        
        try:
            from .dark_theme import DarkTheme
            self.themes['dark'] = DarkTheme
        except ImportError:
            pass
        
        try:
            from .light_theme import LightTheme
            self.themes['light'] = LightTheme
        except ImportError:
            pass
    
    def initialize(self, root: tk.Tk):
        """테마 시스템 초기화"""
        self.root_widget = root
        self.style = ttk.Style()
        
        # 기본 테마 적용
        self.apply_theme('default')
    
    def register_theme(self, name: str, theme_class: Type[BaseTheme]):
        """새 테마 등록"""
        self.themes[name] = theme_class
    
    def get_available_themes(self) -> list:
        """사용 가능한 테마 목록 반환"""
        return list(self.themes.keys())
    
    def get_current_theme_name(self) -> str:
        """현재 테마 이름 반환"""
        return self.current_theme.name if self.current_theme else 'default'
    
    def apply_theme(self, theme_name: str):
        """테마 적용"""
        if theme_name not in self.themes:
            print(f"⚠️ 알 수 없는 테마: {theme_name}")
            theme_name = 'default'
        
        if theme_name not in self.themes:
            # 기본 테마도 없으면 더미 테마 생성
            self.current_theme = self._create_dummy_theme()
        else:
            # 테마 인스턴스 생성
            theme_class = self.themes[theme_name]
            self.current_theme = theme_class()
        
        # 루트 윈도우에 적용
        if self.root_widget:
            self.current_theme.apply_to_root(self.root_widget)
        
        # TTK 스타일 적용
        if self.style:
            self._apply_ttk_styles()
        
        # 콜백 호출
        self._notify_theme_change()
        
        print(f"✅ 테마 적용 완료: {self.current_theme.name}")
    
    def _create_dummy_theme(self):
        """더미 테마 생성"""
        class DummyTheme(BaseTheme):
            @property
            def name(self) -> str:
                return "default"
            
            @property
            def colors(self) -> Dict[str, str]:
                return {
                    'background': '#f0f0f0',
                    'text': '#000000',
                    'button_bg': '#e1e1e1',
                    'button_text': '#000000'
                }
            
            @property
            def fonts(self) -> Dict[str, tuple]:
                return {
                    'default': ('Arial', 10),
                    'button': ('Arial', 9),
                    'heading': ('Arial', 10, 'bold')
                }
            
            @property
            def styles(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        return DummyTheme()
    
    def _apply_ttk_styles(self):
        """TTK 위젯에 스타일 적용"""
        if not self.current_theme or not self.style:
            return
        
        # 기본 스타일 설정
        colors = self.current_theme.colors
        fonts = self.current_theme.fonts
        styles = self.current_theme.styles
        
        # 기본 색상 설정
        self.style.configure('TLabel', 
                           background=colors.get('background'),
                           foreground=colors.get('text'),
                           font=fonts.get('default'))
        
        self.style.configure('TButton',
                           background=colors.get('button_bg'),
                           foreground=colors.get('button_text'),
                           font=fonts.get('button'))
        
        self.style.configure('TFrame',
                           background=colors.get('background'))
        
        self.style.configure('TLabelFrame',
                           background=colors.get('background'),
                           foreground=colors.get('text'),
                           font=fonts.get('heading'))
        
        # 특별한 스타일들
        for style_name, style_config in styles.items():
            try:
                self.style.configure(style_name, **style_config)
            except Exception as e:
                print(f"⚠️ 스타일 적용 오류 ({style_name}): {e}")
    
    def get_color(self, color_name: str, default: str = '#000000') -> str:
        """현재 테마의 색상 반환"""
        if self.current_theme:
            return self.current_theme.colors.get(color_name, default)
        return default
    
    def get_font(self, font_name: str, default: tuple = ('Arial', 10)) -> tuple:
        """현재 테마의 폰트 반환"""
        if self.current_theme:
            return self.current_theme.fonts.get(font_name, default)
        return default
    
    def add_theme_change_callback(self, callback):
        """테마 변경 콜백 추가"""
        self.theme_change_callbacks.append(callback)
    
    def _notify_theme_change(self):
        """테마 변경 알림"""
        for callback in self.theme_change_callbacks:
            try:
                callback(self.current_theme)
            except Exception as e:
                print(f"⚠️ 테마 변경 콜백 오류: {e}")


# 전역 테마 매니저 인스턴스
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """전역 테마 매니저 반환"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager

def apply_theme(theme_name: str):
    """전역 테마 적용"""
    manager = get_theme_manager()
    manager.apply_theme(theme_name)

def get_current_color(color_name: str, default: str = '#000000') -> str:
    """현재 테마의 색상 반환"""
    manager = get_theme_manager()
    return manager.get_color(color_name, default)
