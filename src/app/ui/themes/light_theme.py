"""
라이트 테마
DB Manager의 밝은 모드 테마
"""

from typing import Dict, Any
from .theme_manager import BaseTheme


class LightTheme(BaseTheme):
    """라이트 테마"""
    
    @property
    def name(self) -> str:
        return "Light"
    
    @property
    def colors(self) -> Dict[str, str]:
        return {
            # 기본 색상
            'background': '#ffffff',
            'text': '#000000',
            'accent': '#0078d4',
            
            # 버튼 색상
            'button_bg': '#f8f8f8',
            'button_text': '#000000',
            'button_hover_bg': '#e8e8e8',
            'button_pressed_bg': '#d8d8d8',
            
            # 입력 필드 색상
            'entry_bg': '#ffffff',
            'entry_text': '#000000',
            'entry_border': '#d0d0d0',
            
            # 트리뷰 색상
            'tree_bg': '#ffffff',
            'tree_text': '#000000',
            'tree_header_bg': '#f0f0f0',
            'tree_header_text': '#000000',
            'tree_selected_bg': '#0078d4',
            'tree_selected_text': '#ffffff',
            'tree_alternate_bg': '#fafafa',
        }
    
    @property
    def fonts(self) -> Dict[str, tuple]:
        return {
            'default': ('맑은 고딕', 9),
            'heading': ('맑은 고딕', 10, 'bold'),
            'button': ('맑은 고딕', 9),
            'tree': ('맑은 고딕', 9),
        }
    
    @property
    def styles(self) -> Dict[str, Dict[str, Any]]:
        return {}
