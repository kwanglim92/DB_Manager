"""
기본 테마
DB Manager의 기본 색상 및 스타일 테마
"""

from typing import Dict, Any
from .theme_manager import BaseTheme


class DefaultTheme(BaseTheme):
    """기본 테마"""
    
    @property
    def name(self) -> str:
        return "Default"
    
    @property
    def colors(self) -> Dict[str, str]:
        return {
            # 기본 색상
            'background': '#f0f0f0',
            'text': '#000000',
            'accent': '#0078d4',
            
            # 버튼 색상
            'button_bg': '#e1e1e1',
            'button_text': '#000000',
            'button_hover_bg': '#d4d4d4',
            'button_pressed_bg': '#c1c1c1',
            
            # 입력 필드 색상
            'entry_bg': '#ffffff',
            'entry_text': '#000000',
            'entry_border': '#cccccc',
            
            # 트리뷰 색상
            'tree_bg': '#ffffff',
            'tree_text': '#000000',
            'tree_header_bg': '#e9e9e9',
            'tree_header_text': '#000000',
            'tree_selected_bg': '#0078d4',
            'tree_selected_text': '#ffffff',
            'tree_alternate_bg': '#f8f8f8',
            
            # 상태 색상
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'info': '#17a2b8',
            
            # 메뉴 색상
            'menu_bg': '#f0f0f0',
            'menu_text': '#000000',
            'menu_hover_bg': '#e1e1e1',
            
            # 프레임 색상
            'frame_bg': '#f0f0f0',
            'labelframe_bg': '#f0f0f0',
            'labelframe_text': '#000000',
            
            # 스크롤바 색상
            'scrollbar_bg': '#e1e1e1',
            'scrollbar_thumb': '#c1c1c1',
            
            # 특수 색상
            'border': '#cccccc',
            'disabled_bg': '#f5f5f5',
            'disabled_text': '#888888',
        }
    
    @property
    def fonts(self) -> Dict[str, tuple]:
        return {
            'default': ('맑은 고딕', 9),
            'small': ('맑은 고딕', 8),
            'large': ('맑은 고딕', 10),
            'heading': ('맑은 고딕', 10, 'bold'),
            'title': ('맑은 고딕', 12, 'bold'),
            'button': ('맑은 고딕', 9),
            'menu': ('맑은 고딕', 9),
            'entry': ('맑은 고딕', 9),
            'tree': ('맑은 고딕', 9),
            'tree_header': ('맑은 고딕', 9, 'bold'),
            'monospace': ('Consolas', 9),
        }
    
    @property
    def styles(self) -> Dict[str, Dict[str, Any]]:
        colors = self.colors
        fonts = self.fonts
        
        return {
            # 특별한 버튼 스타일들
            'Accent.TButton': {
                'background': colors['accent'],
                'foreground': '#ffffff',
                'font': fonts['button']
            },
            
            'Success.TButton': {
                'background': colors['success'],
                'foreground': '#ffffff',
                'font': fonts['button']
            },
            
            'Warning.TButton': {
                'background': colors['warning'],
                'foreground': '#000000',
                'font': fonts['button']
            },
            
            'Danger.TButton': {
                'background': colors['error'],
                'foreground': '#ffffff',
                'font': fonts['button']
            },
            
            # 헤딩 스타일
            'Heading.TLabel': {
                'background': colors['background'],
                'foreground': colors['text'],
                'font': fonts['heading']
            },
            
            'Title.TLabel': {
                'background': colors['background'],
                'foreground': colors['text'],
                'font': fonts['title']
            },
            
            # 상태 라벨 스타일
            'Success.TLabel': {
                'background': colors['background'],
                'foreground': colors['success'],
                'font': fonts['default']
            },
            
            'Warning.TLabel': {
                'background': colors['background'],
                'foreground': colors['warning'],
                'font': fonts['default']
            },
            
            'Error.TLabel': {
                'background': colors['background'],
                'foreground': colors['error'],
                'font': fonts['default']
            },
            
            'Info.TLabel': {
                'background': colors['background'],
                'foreground': colors['info'],
                'font': fonts['default']
            },
            
            # 트리뷰 스타일
            'Treeview': {
                'background': colors['tree_bg'],
                'foreground': colors['tree_text'],
                'font': fonts['tree'],
                'fieldbackground': colors['tree_bg']
            },
            
            'Treeview.Heading': {
                'background': colors['tree_header_bg'],
                'foreground': colors['tree_header_text'],
                'font': fonts['tree_header'],
                'relief': 'raised',
                'borderwidth': 1
            },
            
            # 프로그레스바 스타일
            'TProgressbar': {
                'background': colors['accent'],
                'troughcolor': colors['entry_bg'],
                'borderwidth': 1,
                'lightcolor': colors['accent'],
                'darkcolor': colors['accent']
            },
            
            # 메뉴 스타일
            'TMenubutton': {
                'background': colors['menu_bg'],
                'foreground': colors['menu_text'],
                'font': fonts['menu']
            },
            
            # 노트북 탭 스타일
            'TNotebook.Tab': {
                'background': colors['button_bg'],
                'foreground': colors['text'],
                'font': fonts['default'],
                'padding': [8, 4]
            }
        } 