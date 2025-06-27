"""
Professional Engineering Workbench 테마
DB Manager의 전문적인 엔지니어링 도구 테마
"""

from typing import Dict, Any
from .theme_manager import BaseTheme


class EngineeringTheme(BaseTheme):
    """Professional Engineering Workbench 테마"""
    
    @property
    def name(self) -> str:
        return "Engineering"
    
    @property
    def colors(self) -> Dict[str, str]:
        return {
            # 기본 색상 - 중성적이고 전문적
            'background': '#f5f5f5',  # 약간 더 밝은 회색 (눈의 피로 줄임)
            'surface': '#ffffff',     # 깨끗한 흰색 표면
            'text': '#2c2c2c',        # 부드러운 검은색 (순수 검정보다 읽기 편함)
            'text_secondary': '#666666',  # 보조 텍스트
            'accent': '#0078d4',      # Microsoft 블루 (신뢰성)
            'accent_dark': '#106ebe', # 어두운 액센트
            
            # 버튼 색상 - 전문적이고 명확한 계층
            'button_bg': '#e8e8e8',
            'button_text': '#2c2c2c',
            'button_hover_bg': '#d1d1d1',
            'button_pressed_bg': '#bfbfbf',
            'button_border': '#cccccc',
            
            # 입력 필드 색상 - 깔끔하고 현대적
            'entry_bg': '#ffffff',
            'entry_text': '#2c2c2c',
            'entry_border': '#d1d1d1',
            'entry_border_focus': '#0078d4',
            'entry_placeholder': '#888888',
            
            # 트리뷰 색상 - 데이터 중심의 디자인
            'tree_bg': '#ffffff',
            'tree_text': '#2c2c2c',
            'tree_header_bg': '#f0f0f0',
            'tree_header_text': '#2c2c2c',
            'tree_selected_bg': '#0078d4',
            'tree_selected_text': '#ffffff',
            'tree_alternate_bg': '#f9f9f9',
            'tree_border': '#e1e1e1',
            
            # 상태 색상 - 엔지니어링 표준 색상
            'success': '#107c10',     # 안전한 녹색
            'warning': '#ff8c00',     # 주의 오렌지
            'error': '#d13438',       # 위험 빨강
            'info': '#0078d4',        # 정보 파랑
            'pending': '#605e5c',     # 대기 회색
            
            # QC 관련 색상
            'qc_high_severity': '#d13438',    # 높음 - 빨강
            'qc_medium_severity': '#ff8c00',  # 중간 - 오렌지
            'qc_low_severity': '#ffb900',     # 낮음 - 노랑
            'qc_pass': '#107c10',             # 통과 - 녹색
            
            # 메뉴 색상 - 통합된 디자인
            'menu_bg': '#f5f5f5',
            'menu_text': '#2c2c2c',
            'menu_hover_bg': '#e8e8e8',
            'menu_separator': '#d1d1d1',
            
            # 프레임 색상 - 계층적 구조
            'frame_bg': '#f5f5f5',
            'labelframe_bg': '#f5f5f5',
            'labelframe_text': '#2c2c2c',
            'labelframe_border': '#d1d1d1',
            
            # 스크롤바 색상 - 미니멀하고 기능적
            'scrollbar_bg': '#f5f5f5',
            'scrollbar_thumb': '#c1c1c1',
            'scrollbar_thumb_hover': '#a6a6a6',
            
            # 특수 색상
            'border': '#d1d1d1',
            'border_light': '#e8e8e8',
            'shadow': '#00000020',
            'disabled_bg': '#f0f0f0',
            'disabled_text': '#a6a6a6',
            'selection_bg': '#cce8ff',
            'selection_text': '#2c2c2c',
            
            # 탭 색상
            'tab_bg': '#e8e8e8',
            'tab_text': '#2c2c2c',
            'tab_active_bg': '#ffffff',
            'tab_active_text': '#2c2c2c',
            'tab_hover_bg': '#d1d1d1',
            
            # 툴팁 색상
            'tooltip_bg': '#ffffcc',
            'tooltip_text': '#2c2c2c',
            'tooltip_border': '#cccccc',
        }
    
    @property
    def fonts(self) -> Dict[str, tuple]:
        return {
            # 기본 폰트 - 맑은 고딕 (한국어 최적화)
            'default': ('맑은 고딕', 9),
            'small': ('맑은 고딕', 8),
            'large': ('맑은 고딕', 10),
            'xlarge': ('맑은 고딕', 11),
            
            # 헤딩 폰트 - 계층적 구조
            'heading': ('맑은 고딕', 10, 'bold'),
            'title': ('맑은 고딕', 12, 'bold'),
            'subtitle': ('맑은 고딕', 10, 'bold'),
            
            # 인터페이스 폰트
            'button': ('맑은 고딕', 9),
            'menu': ('맑은 고딕', 9),
            'entry': ('맑은 고딕', 9),
            'label': ('맑은 고딕', 9),
            
            # 데이터 표시 폰트
            'tree': ('맑은 고딕', 9),
            'tree_header': ('맑은 고딕', 9, 'bold'),
            'data': ('맑은 고딕', 9),
            'number': ('Consolas', 9),  # 숫자는 고정폭 폰트
            
            # 특수 용도 폰트
            'monospace': ('Consolas', 9),
            'code': ('Consolas', 9),
            'status': ('맑은 고딕', 8),
            'tooltip': ('맑은 고딕', 8),
            
            # QC 관련 폰트
            'qc_result': ('맑은 고딕', 9),
            'qc_severity': ('맑은 고딕', 9, 'bold'),
        }
    
    @property
    def styles(self) -> Dict[str, Dict[str, Any]]:
        colors = self.colors
        fonts = self.fonts
        
        return {
            # === 기본 위젯 스타일 ===
            'TLabel': {
                'background': colors['background'],
                'foreground': colors['text'],
                'font': fonts['default']
            },
            
            'TButton': {
                'background': colors['button_bg'],
                'foreground': colors['button_text'],
                'font': fonts['button'],
                'borderwidth': 1,
                'relief': 'solid',
                'padding': [8, 4]
            },
            
            'TFrame': {
                'background': colors['frame_bg'],
                'borderwidth': 0
            },
            
            'TLabelFrame': {
                'background': colors['labelframe_bg'],
                'foreground': colors['labelframe_text'],
                'font': fonts['heading'],
                'borderwidth': 1,
                'relief': 'solid'
            },
            
            'TEntry': {
                'fieldbackground': colors['entry_bg'],
                'foreground': colors['entry_text'],
                'font': fonts['entry'],
                'borderwidth': 1,
                'relief': 'solid'
            },
            
            # === 특별한 버튼 스타일 ===
            'Accent.TButton': {
                'background': colors['accent'],
                'foreground': '#ffffff',
                'font': fonts['button'],
                'borderwidth': 0,
                'padding': [12, 6]
            },
            
            'Success.TButton': {
                'background': colors['success'],
                'foreground': '#ffffff',
                'font': fonts['button'],
                'borderwidth': 0,
                'padding': [8, 4]
            },
            
            'Warning.TButton': {
                'background': colors['warning'],
                'foreground': '#ffffff',
                'font': fonts['button'],
                'borderwidth': 0,
                'padding': [8, 4]
            },
            
            'Danger.TButton': {
                'background': colors['error'],
                'foreground': '#ffffff',
                'font': fonts['button'],
                'borderwidth': 0,
                'padding': [8, 4]
            },
            
            'Tool.TButton': {
                'background': colors['surface'],
                'foreground': colors['text'],
                'font': fonts['button'],
                'borderwidth': 1,
                'relief': 'solid',
                'padding': [6, 3]
            },
            
            # === 헤딩 라벨 스타일 ===
            'Title.TLabel': {
                'background': colors['background'],
                'foreground': colors['text'],
                'font': fonts['title']
            },
            
            'Heading.TLabel': {
                'background': colors['background'],
                'foreground': colors['text'],
                'font': fonts['heading']
            },
            
            'Subtitle.TLabel': {
                'background': colors['background'],
                'foreground': colors['text_secondary'],
                'font': fonts['subtitle']
            },
            
            # === 상태 라벨 스타일 ===
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
            
            'Status.TLabel': {
                'background': colors['background'],
                'foreground': colors['text_secondary'],
                'font': fonts['status']
            },
            
            # === QC 관련 스타일 ===
            'QC.High.TLabel': {
                'background': colors['background'],
                'foreground': colors['qc_high_severity'],
                'font': fonts['qc_severity']
            },
            
            'QC.Medium.TLabel': {
                'background': colors['background'],
                'foreground': colors['qc_medium_severity'],
                'font': fonts['qc_severity']
            },
            
            'QC.Low.TLabel': {
                'background': colors['background'],
                'foreground': colors['qc_low_severity'],
                'font': fonts['qc_severity']
            },
            
            'QC.Pass.TLabel': {
                'background': colors['background'],
                'foreground': colors['qc_pass'],
                'font': fonts['qc_severity']
            },
            
            # === 트리뷰 스타일 ===
            'Treeview': {
                'background': colors['tree_bg'],
                'foreground': colors['tree_text'],
                'font': fonts['tree'],
                'fieldbackground': colors['tree_bg'],
                'borderwidth': 1,
                'relief': 'solid'
            },
            
            'Treeview.Heading': {
                'background': colors['tree_header_bg'],
                'foreground': colors['tree_header_text'],
                'font': fonts['tree_header'],
                'relief': 'solid',
                'borderwidth': 1,
                'padding': [4, 4]
            },
            
            # === 노트북 탭 스타일 ===
            'TNotebook': {
                'background': colors['background'],
                'borderwidth': 0
            },
            
            'TNotebook.Tab': {
                'background': colors['tab_bg'],
                'foreground': colors['tab_text'],
                'font': fonts['default'],
                'padding': [12, 8],
                'borderwidth': 1,
                'relief': 'solid'
            },
            
            # === 프로그레스바 스타일 ===
            'TProgressbar': {
                'background': colors['accent'],
                'troughcolor': colors['entry_bg'],
                'borderwidth': 1,
                'relief': 'solid',
                'lightcolor': colors['accent'],
                'darkcolor': colors['accent']
            },
            
            # === 콤보박스 스타일 ===
            'TCombobox': {
                'fieldbackground': colors['entry_bg'],
                'foreground': colors['entry_text'],
                'font': fonts['entry'],
                'borderwidth': 1,
                'relief': 'solid'
            },
            
            # === 체크버튼/라디오버튼 스타일 ===
            'TCheckbutton': {
                'background': colors['background'],
                'foreground': colors['text'],
                'font': fonts['default'],
                'focuscolor': colors['accent']
            },
            
            'TRadiobutton': {
                'background': colors['background'],
                'foreground': colors['text'],
                'font': fonts['default'],
                'focuscolor': colors['accent']
            },
            
            # === 메뉴 스타일 ===
            'TMenubutton': {
                'background': colors['menu_bg'],
                'foreground': colors['menu_text'],
                'font': fonts['menu'],
                'borderwidth': 1,
                'relief': 'solid'
            },
            
            # === 스케일 스타일 ===
            'TScale': {
                'background': colors['background'],
                'troughcolor': colors['entry_bg'],
                'borderwidth': 1,
                'relief': 'solid'
            },
            
            # === 분리자 스타일 ===
            'TSeparator': {
                'background': colors['border']
            },
            
            # === 스핀박스 스타일 ===
            'TSpinbox': {
                'fieldbackground': colors['entry_bg'],
                'foreground': colors['entry_text'],
                'font': fonts['entry'],
                'borderwidth': 1,
                'relief': 'solid'
            }
        }
    
    def get_icon_style(self, icon_type: str) -> Dict[str, str]:
        """아이콘 스타일 반환"""
        icon_styles = {
            'success': {'color': self.colors['success'], 'icon': '✅'},
            'warning': {'color': self.colors['warning'], 'icon': '⚠️'},
            'error': {'color': self.colors['error'], 'icon': '❌'},
            'info': {'color': self.colors['info'], 'icon': 'ℹ️'},
            'qc': {'color': self.colors['accent'], 'icon': '🔍'},
            'tool': {'color': self.colors['text'], 'icon': '🔧'},
            'data': {'color': self.colors['text'], 'icon': '📊'},
            'file': {'color': self.colors['text'], 'icon': '📁'},
            'setting': {'color': self.colors['text'], 'icon': '⚙️'},
        }
        return icon_styles.get(icon_type, {'color': self.colors['text'], 'icon': '•'})
    
    def get_spacing(self) -> Dict[str, int]:
        """간격 설정 반환"""
        return {
            'xs': 2,
            'sm': 4,
            'md': 8,
            'lg': 12,
            'xl': 16,
            'xxl': 24,
            'frame_padding': 10,
            'button_padding': 8,
            'entry_padding': 4,
        }