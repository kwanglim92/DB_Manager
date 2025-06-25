"""
UI 관련 헬퍼 함수들 (기존 중복 함수들 통합)
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Tuple, Any


class UIHelpers:
    """UI 생성 및 관리를 위한 헬퍼 클래스"""
    
    @staticmethod
    def create_treeview_with_scrollbar(parent, columns: List[str], headings: Dict[str, str], 
                                     column_widths: Optional[Dict[str, int]] = None, 
                                     height: int = 20, style: Optional[str] = None, 
                                     show: str = "headings") -> Tuple[tk.Frame, ttk.Treeview]:
        """
        트리뷰와 스크롤바를 포함한 프레임을 생성하고 반환합니다.
        
        Args:
            parent: 부모 위젯
            columns: 컬럼 ID 리스트
            headings: 컬럼 헤더 텍스트 딕셔너리 (key: 컬럼 ID, value: 헤더 텍스트)
            column_widths: 컬럼 너비 딕셔너리 (key: 컬럼 ID, value: 너비)
            height: 트리뷰 높이
            style: 트리뷰 스타일
            show: 트리뷰 표시 옵션 ("headings", "tree", "tree headings" 등)
            
        Returns:
            Tuple[frame, treeview]: 생성된 프레임과 트리뷰
        """
        # 프레임 생성
        frame = ttk.Frame(parent)
        
        # 트리뷰 생성
        if style:
            tree = ttk.Treeview(frame, columns=columns, show=show, height=height, style=style)
        else:
            tree = ttk.Treeview(frame, columns=columns, show=show, height=height)
        
        # 컬럼 설정
        for col in columns:
            # 헤더 설정
            header_text = headings.get(col, col)
            tree.heading(col, text=header_text)
            
            # 너비 설정
            if column_widths and col in column_widths:
                tree.column(col, width=column_widths[col])
            else:
                tree.column(col, width=100)  # 기본 너비
        
        # 스크롤바 생성
        v_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        
        # 트리뷰에 스크롤바 연결
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 위젯 배치
        tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # 그리드 가중치 설정
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        return frame, tree
    
    @staticmethod
    def create_label_entry_pair(parent, label_text: str, entry_var: tk.StringVar = None, 
                               entry_width: int = 20, row: int = 0, 
                               label_column: int = 0, entry_column: int = 1,
                               padx: int = 5, pady: int = 5, sticky: str = "w") -> Tuple[ttk.Label, ttk.Entry]:
        """
        레이블과 엔트리 위젯 쌍을 생성합니다.
        
        Args:
            parent: 부모 위젯
            label_text: 레이블 텍스트
            entry_var: 엔트리와 연결할 StringVar (None이면 새로 생성)
            entry_width: 엔트리 너비
            row: 그리드 행 위치
            label_column: 레이블 컬럼 위치  
            entry_column: 엔트리 컬럼 위치
            padx: 수평 패딩
            pady: 수직 패딩
            sticky: 정렬 방식
            
        Returns:
            Tuple[label, entry]: 생성된 레이블과 엔트리
        """
        # StringVar 생성 (필요한 경우)
        if entry_var is None:
            entry_var = tk.StringVar()
        
        # 레이블 생성
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=label_column, padx=padx, pady=pady, sticky=sticky)
        
        # 엔트리 생성
        entry = ttk.Entry(parent, textvariable=entry_var, width=entry_width)
        entry.grid(row=row, column=entry_column, padx=padx, pady=pady, sticky=sticky)
        
        return label, entry
    
    @staticmethod
    def create_labeled_frame(parent, title: str, padding: int = 10) -> ttk.LabelFrame:
        """
        제목이 있는 프레임을 생성합니다.
        
        Args:
            parent: 부모 위젯
            title: 프레임 제목
            padding: 내부 패딩
            
        Returns:
            ttk.LabelFrame: 생성된 레이블 프레임
        """
        frame = ttk.LabelFrame(parent, text=title, padding=padding)
        return frame
    
    @staticmethod
    def create_button_frame(parent, buttons_config: List[Dict[str, Any]], 
                           orientation: str = "horizontal") -> ttk.Frame:
        """
        버튼들을 포함한 프레임을 생성합니다.
        
        Args:
            parent: 부모 위젯
            buttons_config: 버튼 설정 리스트 
                [{"text": "버튼명", "command": callback, "width": 10}, ...]
            orientation: 배치 방향 ("horizontal" 또는 "vertical")
            
        Returns:
            ttk.Frame: 버튼들이 포함된 프레임
        """
        frame = ttk.Frame(parent)
        
        for i, config in enumerate(buttons_config):
            button = ttk.Button(frame, **config)
            
            if orientation == "horizontal":
                button.pack(side=tk.LEFT, padx=5, pady=5)
            else:
                button.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
        
        return frame
    
    @staticmethod
    def create_search_frame(parent, search_var: tk.StringVar, 
                           placeholder: str = "검색...", 
                           callback: Optional[callable] = None) -> ttk.Frame:
        """
        검색 입력 프레임을 생성합니다.
        
        Args:
            parent: 부모 위젯
            search_var: 검색어를 저장할 StringVar
            placeholder: 플레이스홀더 텍스트
            callback: 검색어 변경 시 호출할 콜백 함수
            
        Returns:
            ttk.Frame: 검색 프레임
        """
        frame = ttk.Frame(parent)
        
        # 검색 레이블
        search_label = ttk.Label(frame, text="🔍")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 검색 엔트리
        search_entry = ttk.Entry(frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 콜백 연결
        if callback:
            search_entry.bind('<KeyRelease>', callback)
        
        # 클리어 버튼
        clear_button = ttk.Button(frame, text="✕", width=3, 
                                 command=lambda: search_var.set(""))
        clear_button.pack(side=tk.LEFT, padx=(5, 0))
        
        return frame
    
    @staticmethod
    def create_filter_frame(parent, filters_config: Dict[str, Dict[str, Any]]) -> ttk.Frame:
        """
        필터 선택 프레임을 생성합니다.
        
        Args:
            parent: 부모 위젯
            filters_config: 필터 설정 딕셔너리
                {
                    "filter_name": {
                        "label": "표시명",
                        "variable": tk.StringVar,
                        "values": ["option1", "option2"],
                        "callback": function
                    }
                }
                
        Returns:
            ttk.Frame: 필터 프레임
        """
        frame = ttk.Frame(parent)
        
        for i, (filter_name, config) in enumerate(filters_config.items()):
            # 필터 레이블
            label = ttk.Label(frame, text=config["label"] + ":")
            label.grid(row=0, column=i*2, padx=5, pady=5, sticky="w")
            
            # 필터 콤보박스
            combo = ttk.Combobox(frame, textvariable=config["variable"], 
                               values=config["values"], width=12, state="readonly")
            combo.grid(row=0, column=i*2+1, padx=5, pady=5)
            
            # 콜백 연결
            if "callback" in config:
                combo.bind('<<ComboboxSelected>>', config["callback"])
        
        return frame
    
    @staticmethod
    def create_progress_frame(parent, progress_var: tk.DoubleVar, 
                             status_var: tk.StringVar) -> ttk.Frame:
        """
        진행률 표시 프레임을 생성합니다.
        
        Args:
            parent: 부모 위젯
            progress_var: 진행률 변수 (0-100)
            status_var: 상태 텍스트 변수
            
        Returns:
            ttk.Frame: 진행률 프레임
        """
        frame = ttk.Frame(parent)
        
        # 진행률 바
        progress_bar = ttk.Progressbar(frame, variable=progress_var, 
                                     maximum=100, length=300)
        progress_bar.pack(side=tk.LEFT, padx=5)
        
        # 상태 레이블
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack(side=tk.LEFT, padx=10)
        
        return frame
    
    @staticmethod
    def create_info_panel(parent, info_config: Dict[str, str]) -> ttk.Frame:
        """
        정보 표시 패널을 생성합니다.
        
        Args:
            parent: 부모 위젯
            info_config: 정보 설정 딕셔너리 {"label": "value"}
            
        Returns:
            ttk.Frame: 정보 패널
        """
        frame = ttk.LabelFrame(parent, text="정보", padding=10)
        
        for i, (label, value) in enumerate(info_config.items()):
            # 레이블
            label_widget = ttk.Label(frame, text=f"{label}:", font=("Arial", 9, "bold"))
            label_widget.grid(row=i, column=0, padx=5, pady=2, sticky="w")
            
            # 값
            value_widget = ttk.Label(frame, text=str(value))
            value_widget.grid(row=i, column=1, padx=5, pady=2, sticky="w")
        
        return frame
    
    @staticmethod
    def setup_context_menu(widget, menu_items: List[Dict[str, Any]]) -> tk.Menu:
        """
        위젯에 컨텍스트 메뉴를 설정합니다.
        
        Args:
            widget: 메뉴를 연결할 위젯
            menu_items: 메뉴 항목 리스트
                [
                    {"label": "항목명", "command": callback},
                    {"separator": True},  # 구분선
                    {"label": "항목명2", "command": callback2, "state": "disabled"}
                ]
                
        Returns:
            tk.Menu: 생성된 컨텍스트 메뉴
        """
        context_menu = tk.Menu(widget, tearoff=0)
        
        for item in menu_items:
            if item.get("separator"):
                context_menu.add_separator()
            else:
                context_menu.add_command(
                    label=item["label"],
                    command=item["command"],
                    state=item.get("state", "normal")
                )
        
        def show_context_menu(event):
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
        
        widget.bind("<Button-3>", show_context_menu)  # 우클릭
        return context_menu
    
    @staticmethod
    def configure_tree_colors(tree: ttk.Treeview, color_config: Dict[str, str]):
        """
        트리뷰의 색상을 설정합니다.
        
        Args:
            tree: 트리뷰 위젯
            color_config: 색상 설정 딕셔너리
                {"tag_name": "background_color"}
        """
        for tag, color in color_config.items():
            tree.tag_configure(tag, background=color)
    
    @staticmethod
    def center_window(window, width: int = None, height: int = None):
        """
        윈도우를 화면 중앙에 배치합니다.
        
        Args:
            window: 중앙 배치할 윈도우
            width: 윈도우 너비 (None이면 현재 크기 사용)
            height: 윈도우 높이 (None이면 현재 크기 사용)
        """
        window.update_idletasks()
        
        # 현재 크기 가져오기 (지정되지 않은 경우)
        if width is None or height is None:
            geometry = window.geometry()
            current_width, current_height = map(int, geometry.split('x')[0]), map(int, geometry.split('x')[1].split('+')[0])
            width = width or current_width
            height = height or current_height
        
        # 화면 크기 가져오기
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # 중앙 위치 계산
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # 윈도우 위치 설정
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    @staticmethod
    def create_tooltip(widget, text: str):
        """
        위젯에 툴팁을 추가합니다.
        
        Args:
            widget: 툴팁을 추가할 위젯
            text: 툴팁 텍스트
        """
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="yellow", 
                           relief="solid", borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            tooltip.after(3000, hide_tooltip)  # 3초 후 자동 숨김
        
        widget.bind("<Enter>", show_tooltip)