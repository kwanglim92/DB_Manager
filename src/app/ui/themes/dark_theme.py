"""
다크 테마
DB Manager의 다크 모드 테마
"""

from typing import Dict, Any
from .theme_manager import BaseTheme


class DarkTheme(BaseTheme):
    """다크 테마"""
    
    @property
    def name(self) -> str:
        return "Dark"
    
    @property
    def colors(self) -> Dict[str, str]:
        return {
            # 기본 색상
            'background': '#2d2d2d',
            'text': '#ffffff',
            'accent': '#0078d4',
            
            # 버튼 색상
            'button_bg': '#404040',
            'button_text': '#ffffff',
            'button_hover_bg': '#505050',
            'button_pressed_bg': '#606060',
            
            # 입력 필드 색상
            'entry_bg': '#404040',
            'entry_text': '#ffffff',
            'entry_border': '#555555',
            
            # 트리뷰 색상
            'tree_bg': '#404040',
            'tree_text': '#ffffff',
            'tree_header_bg': '#505050',
            'tree_header_text': '#ffffff',
            'tree_selected_bg': '#0078d4',
            'tree_selected_text': '#ffffff',
            'tree_alternate_bg': '#353535',
            
            # 상태 색상
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'info': '#17a2b8',
            
            # 메뉴 색상
            'menu_bg': '#2d2d2d',
            'menu_text': '#ffffff',
            'menu_hover_bg': '#404040',
            
            # 프레임 색상
            'frame_bg': '#2d2d2d',
            'labelframe_bg': '#2d2d2d',
            'labelframe_text': '#ffffff',
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