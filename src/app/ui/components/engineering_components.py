"""
Professional Engineering Workbench UI 컴포넌트
일관된 스타일과 동작을 위한 표준화된 UI 요소들
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable, Any, Tuple
from ..themes.theme_manager import get_theme_manager


class EngineeringButton:
    """전문적인 엔지니어링 스타일 버튼"""
    
    @staticmethod
    def create_primary_button(parent, text: str, command: Callable = None, **kwargs) -> ttk.Button:
        """주요 액션 버튼 (액센트 색상)"""
        return ttk.Button(
            parent, 
            text=text, 
            command=command,
            style='Accent.TButton',
            **kwargs
        )
    
    @staticmethod
    def create_secondary_button(parent, text: str, command: Callable = None, **kwargs) -> ttk.Button:
        """보조 액션 버튼 (기본 스타일)"""
        return ttk.Button(
            parent, 
            text=text, 
            command=command,
            style='TButton',
            **kwargs
        )
    
    @staticmethod
    def create_tool_button(parent, text: str, command: Callable = None, **kwargs) -> ttk.Button:
        """도구 버튼 (작은 크기)"""
        return ttk.Button(
            parent, 
            text=text, 
            command=command,
            style='Tool.TButton',
            **kwargs
        )
    
    @staticmethod
    def create_status_button(parent, text: str, status: str, command: Callable = None, **kwargs) -> ttk.Button:
        """상태별 버튼 (성공/경고/위험)"""
        style_map = {
            'success': 'Success.TButton',
            'warning': 'Warning.TButton',
            'danger': 'Danger.TButton',
            'error': 'Danger.TButton'
        }
        return ttk.Button(
            parent, 
            text=text, 
            command=command,
            style=style_map.get(status, 'TButton'),
            **kwargs
        )


class EngineeringLabel:
    """전문적인 엔지니어링 스타일 라벨"""
    
    @staticmethod
    def create_title(parent, text: str, **kwargs) -> ttk.Label:
        """제목 라벨"""
        return ttk.Label(
            parent, 
            text=text,
            style='Title.TLabel',
            **kwargs
        )
    
    @staticmethod
    def create_heading(parent, text: str, **kwargs) -> ttk.Label:
        """헤딩 라벨"""
        return ttk.Label(
            parent, 
            text=text,
            style='Heading.TLabel',
            **kwargs
        )
    
    @staticmethod
    def create_subtitle(parent, text: str, **kwargs) -> ttk.Label:
        """부제목 라벨"""
        return ttk.Label(
            parent, 
            text=text,
            style='Subtitle.TLabel',
            **kwargs
        )
    
    @staticmethod
    def create_status_label(parent, text: str, status: str, **kwargs) -> ttk.Label:
        """상태 라벨"""
        style_map = {
            'success': 'Success.TLabel',
            'warning': 'Warning.TLabel',
            'error': 'Error.TLabel',
            'info': 'Info.TLabel',
            'status': 'Status.TLabel'
        }
        return ttk.Label(
            parent, 
            text=text,
            style=style_map.get(status, 'TLabel'),
            **kwargs
        )
    
    @staticmethod
    def create_qc_severity_label(parent, text: str, severity: str, **kwargs) -> ttk.Label:
        """QC 심각도 라벨"""
        style_map = {
            '높음': 'QC.High.TLabel',
            '중간': 'QC.Medium.TLabel', 
            '낮음': 'QC.Low.TLabel',
            '통과': 'QC.Pass.TLabel'
        }
        return ttk.Label(
            parent, 
            text=text,
            style=style_map.get(severity, 'TLabel'),
            **kwargs
        )


class EngineeringFrame:
    """전문적인 엔지니어링 스타일 프레임"""
    
    @staticmethod
    def create_control_frame(parent, title: str = "", **kwargs) -> ttk.LabelFrame:
        """컨트롤 패널 프레임"""
        theme_manager = get_theme_manager()
        spacing = theme_manager.current_theme.get_spacing() if hasattr(theme_manager.current_theme, 'get_spacing') else {'frame_padding': 10}
        
        frame = ttk.LabelFrame(
            parent,
            text=title,
            style='TLabelFrame',
            padding=spacing.get('frame_padding', 10),
            **kwargs
        )
        return frame
    
    @staticmethod
    def create_content_frame(parent, **kwargs) -> ttk.Frame:
        """콘텐츠 프레임"""
        return ttk.Frame(
            parent,
            style='TFrame',
            **kwargs
        )
    
    @staticmethod
    def create_toolbar_frame(parent, **kwargs) -> ttk.Frame:
        """툴바 프레임"""
        frame = ttk.Frame(
            parent,
            style='TFrame',
            **kwargs
        )
        frame.pack(fill=tk.X, padx=5, pady=5)
        return frame


class EngineeringTreeview:
    """전문적인 엔지니어링 스타일 트리뷰"""
    
    @staticmethod
    def create_with_scrollbar(parent, columns: List[str], headings: Dict[str, str], 
                             column_widths: Dict[str, int], height: int = 15,
                             **kwargs) -> Tuple[ttk.Frame, ttk.Treeview]:
        """스크롤바가 있는 트리뷰 생성"""
        # 컨테이너 프레임
        frame = ttk.Frame(parent, style='TFrame')
        
        # 트리뷰 생성
        tree = ttk.Treeview(
            frame,
            columns=columns,
            show='tree headings',
            height=height,
            style='Treeview',
            **kwargs
        )
        
        # 헤딩 설정
        tree.heading('#0', text='', anchor='w')
        tree.column('#0', width=0, stretch=False)  # 트리 컬럼 숨김
        
        for col in columns:
            tree.heading(col, text=headings.get(col, col), anchor='w')
            tree.column(col, width=column_widths.get(col, 100), anchor='w')
        
        # 스크롤바 생성
        v_scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        h_scrollbar = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 배치
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # 그리드 가중치 설정
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # 행 색상 태그 설정
        EngineeringTreeview._setup_row_tags(tree)
        
        return frame, tree
    
    @staticmethod
    def _setup_row_tags(tree: ttk.Treeview):
        """행 색상 태그 설정"""
        theme_manager = get_theme_manager()
        if not theme_manager.current_theme:
            return
            
        colors = theme_manager.current_theme.colors
        
        # 기본 행 태그
        tree.tag_configure('odd', background=colors.get('tree_bg', '#ffffff'))
        tree.tag_configure('even', background=colors.get('tree_alternate_bg', '#f9f9f9'))
        
        # 상태별 태그
        tree.tag_configure('success', foreground=colors.get('success', '#107c10'))
        tree.tag_configure('warning', foreground=colors.get('warning', '#ff8c00'))
        tree.tag_configure('error', foreground=colors.get('error', '#d13438'))
        tree.tag_configure('info', foreground=colors.get('info', '#0078d4'))
        
        # QC 심각도 태그
        tree.tag_configure('severity_높음', foreground=colors.get('qc_high_severity', '#d13438'))
        tree.tag_configure('severity_중간', foreground=colors.get('qc_medium_severity', '#ff8c00'))
        tree.tag_configure('severity_낮음', foreground=colors.get('qc_low_severity', '#ffb900'))
        
    @staticmethod
    def apply_alternating_colors(tree: ttk.Treeview):
        """교대로 행 색상 적용"""
        for i, item in enumerate(tree.get_children()):
            tag = 'even' if i % 2 == 0 else 'odd'
            tree.set(item, '#0', tree.item(item, 'text'))
            tree.item(item, tags=(tag,))


class EngineeringInput:
    """전문적인 엔지니어링 스타일 입력 요소"""
    
    @staticmethod
    def create_label_entry_pair(parent, label_text: str, row: int, column: int = 0, 
                               initial_value: str = "", width: int = 20) -> Tuple[tk.StringVar, ttk.Entry]:
        """라벨과 입력 필드 쌍 생성"""
        # 라벨
        ttk.Label(parent, text=label_text, style='TLabel').grid(
            row=row, column=column, sticky='w', padx=5, pady=2
        )
        
        # 변수와 입력 필드
        var = tk.StringVar(value=initial_value)
        entry = ttk.Entry(
            parent, 
            textvariable=var, 
            width=width,
            style='TEntry'
        )
        entry.grid(row=row, column=column+1, sticky='ew', padx=5, pady=2)
        
        return var, entry
    
    @staticmethod
    def create_label_combobox_pair(parent, label_text: str, values: List[str], 
                                  row: int, column: int = 0, 
                                  initial_value: str = "", width: int = 20) -> Tuple[tk.StringVar, ttk.Combobox]:
        """라벨과 콤보박스 쌍 생성"""
        # 라벨
        ttk.Label(parent, text=label_text, style='TLabel').grid(
            row=row, column=column, sticky='w', padx=5, pady=2
        )
        
        # 변수와 콤보박스
        var = tk.StringVar(value=initial_value)
        combo = ttk.Combobox(
            parent, 
            textvariable=var, 
            values=values,
            state='readonly',
            width=width,
            style='TCombobox'
        )
        combo.grid(row=row, column=column+1, sticky='ew', padx=5, pady=2)
        
        return var, combo


class EngineeringDialog:
    """전문적인 엔지니어링 스타일 다이얼로그"""
    
    @staticmethod
    def create_message_dialog(parent, title: str, message: str, dialog_type: str = 'info') -> tk.Toplevel:
        """메시지 다이얼로그 생성"""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        
        theme_manager = get_theme_manager()
        if theme_manager.current_theme:
            dialog.configure(bg=theme_manager.current_theme.colors.get('background'))
        
        # 아이콘과 메시지
        main_frame = ttk.Frame(dialog, style='TFrame', padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # 아이콘
        icon_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅',
            'question': '❓'
        }
        
        icon_label = ttk.Label(
            main_frame, 
            text=icon_map.get(dialog_type, 'ℹ️'),
            font=('맑은 고딕', 16)
        )
        icon_label.grid(row=0, column=0, padx=(0, 10), sticky='n')
        
        # 메시지
        message_label = ttk.Label(
            main_frame, 
            text=message,
            style='TLabel',
            wraplength=300
        )
        message_label.grid(row=0, column=1, sticky='ew')
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.grid(row=1, column=0, columnspan=2, pady=(15, 0), sticky='ew')
        
        # 확인 버튼
        ok_button = EngineeringButton.create_primary_button(
            button_frame, 
            "확인", 
            command=dialog.destroy
        )
        ok_button.pack(side='right')
        
        # 다이얼로그 크기 조정 및 중앙 배치
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        return dialog


class EngineeringLayout:
    """전문적인 엔지니어링 스타일 레이아웃"""
    
    @staticmethod
    def create_two_column_layout(parent) -> Tuple[ttk.Frame, ttk.Frame]:
        """2열 레이아웃 생성"""
        left_frame = ttk.Frame(parent, style='TFrame')
        right_frame = ttk.Frame(parent, style='TFrame')
        
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        return left_frame, right_frame
    
    @staticmethod
    def create_header_content_layout(parent) -> Tuple[ttk.Frame, ttk.Frame]:
        """헤더-콘텐츠 레이아웃 생성"""
        header_frame = ttk.Frame(parent, style='TFrame')
        content_frame = ttk.Frame(parent, style='TFrame')
        
        header_frame.pack(fill='x', padx=10, pady=(10, 0))
        content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        return header_frame, content_frame
    
    @staticmethod
    def create_tab_layout(parent, tab_names: List[str]) -> Tuple[ttk.Notebook, Dict[str, ttk.Frame]]:
        """탭 레이아웃 생성"""
        notebook = ttk.Notebook(parent, style='TNotebook')
        tabs = {}
        
        for name in tab_names:
            frame = ttk.Frame(notebook, style='TFrame')
            notebook.add(frame, text=name)
            tabs[name] = frame
        
        notebook.pack(fill='both', expand=True)
        return notebook, tabs


class EngineeringUtils:
    """엔지니어링 UI 유틸리티"""
    
    @staticmethod
    def set_window_icon(window: tk.Tk, icon_text: str = "🔧"):
        """윈도우 아이콘 설정"""
        try:
            # 텍스트 아이콘 설정 (이모지)
            window.iconname(icon_text)
            window.title(window.title() + f" {icon_text}")
        except:
            pass
    
    @staticmethod
    def center_window(window: tk.Tk, width: int = None, height: int = None):
        """윈도우를 화면 중앙에 배치"""
        window.update_idletasks()
        
        if width is None:
            width = window.winfo_width()
        if height is None:
            height = window.winfo_height()
        
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    @staticmethod
    def apply_professional_styling(widget):
        """전문적인 스타일링 적용"""
        # 폰트 및 색상 적용
        theme_manager = get_theme_manager()
        if theme_manager.current_theme:
            try:
                if hasattr(widget, 'configure'):
                    if isinstance(widget, (ttk.Label, ttk.Button)):
                        widget.configure(style='TLabel' if isinstance(widget, ttk.Label) else 'TButton')
            except:
                pass


# 편의를 위한 단축 함수들
def create_engineering_treeview_with_scrollbar(parent, columns: List[str], headings: Dict[str, str], 
                                             column_widths: Dict[str, int], height: int = 15) -> Tuple[ttk.Frame, ttk.Treeview]:
    """스크롤바가 있는 엔지니어링 스타일 트리뷰 생성 (기존 utils.py 함수 대체)"""
    return EngineeringTreeview.create_with_scrollbar(parent, columns, headings, column_widths, height)

def create_engineering_label_entry_pair(parent, label_text: str, row: int, column: int = 0, 
                                       initial_value: str = "", width: int = 20) -> Tuple[tk.StringVar, ttk.Entry]:
    """라벨과 입력 필드 쌍 생성 (기존 utils.py 함수 대체)"""
    return EngineeringInput.create_label_entry_pair(parent, label_text, row, column, initial_value, width)