"""
메인 윈도우 관리 클래스
UI 초기화와 기본 윈도우 설정을 담당
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
from typing import Optional

class MainWindow:
    """메인 윈도우 관리 클래스"""
    
    def __init__(self, config=None):
        """
        메인 윈도우 초기화
        
        Args:
            config: 애플리케이션 설정 객체
        """
        self.config = config
        self.window = None
        self.main_notebook = None
        self.comparison_notebook = None
        self.status_bar = None
        self.log_text = None
        self.menubar = None
        
        # 윈도우 설정
        self.title = "DB Manager - Mother DB 관리 시스템"
        self.geometry = "1300x800"
        self.icon_path = self._get_icon_path()
        
    def _get_icon_path(self) -> Optional[str]:
        """아이콘 경로 반환"""
        try:
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                # 프로젝트 루트 경로
                application_path = os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.abspath(__file__)
                            )
                        )
                    )
                )
            icon_path = os.path.join(application_path, "resources", "icons", "db_compare.ico")
            return icon_path if os.path.exists(icon_path) else None
        except Exception:
            return None
    
    def initialize(self) -> tk.Tk:
        """윈도우 초기화 및 반환"""
        self.window = tk.Tk()
        self.window.title(self.title)
        self.window.geometry(self.geometry)
        
        # 아이콘 설정
        if self.icon_path:
            try:
                self.window.iconbitmap(self.icon_path)
            except Exception as e:
                print(f"아이콘 로드 실패: {e}")
        
        # UI 컴포넌트 생성
        self._create_menu()
        self._create_status_bar()
        self._create_main_notebook()
        self._create_log_area()
        
        # 키 바인딩
        self._setup_key_bindings()
        
        return self.window
    
    def _create_menu(self):
        """메뉴바 생성"""
        self.menubar = tk.Menu(self.window)
        
        # 파일 메뉴
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="폴더 열기 (Ctrl+O)")
        file_menu.add_separator()
        file_menu.add_command(label="보고서 내보내기")
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.window.quit)
        self.menubar.add_cascade(label="파일", menu=file_menu)
        
        # 도구 메뉴
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        tools_menu.add_command(label="👤 사용자 모드 전환")
        tools_menu.add_separator()
        tools_menu.add_command(label="⚙️ 설정")
        self.menubar.add_cascade(label="도구", menu=tools_menu)
        
        # Mother DB 메뉴 (QC 엔지니어 모드에서만 활성화)
        mother_db_menu = tk.Menu(self.menubar, tearoff=0)
        mother_db_menu.add_command(label="🎯 Mother DB 빠른 설정")
        mother_db_menu.add_command(label="📊 Mother DB 분석")
        mother_db_menu.add_command(label="🔄 Mother DB 동기화")
        mother_db_menu.add_separator()
        mother_db_menu.add_command(label="📥 Mother DB 가져오기")
        mother_db_menu.add_command(label="📤 Mother DB 내보내기")
        self.menubar.add_cascade(label="Mother DB", menu=mother_db_menu, state="disabled")
        
        # 도움말 메뉴
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="사용 설명서 (F1)")
        help_menu.add_separator()
        help_menu.add_command(label="프로그램 정보")
        self.menubar.add_cascade(label="도움말", menu=help_menu)
        
        self.window.config(menu=self.menubar)
    
    def _create_status_bar(self):
        """상태바 생성"""
        self.status_bar = ttk.Label(
            self.window, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            text="Ready - 장비 생산 엔지니어 모드"
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_main_notebook(self):
        """메인 노트북 (탭 컨테이너) 생성"""
        # 메인 노트북
        self.main_notebook = ttk.Notebook(self.window)
        self.main_notebook.pack(expand=True, fill=tk.BOTH)
        
        # DB 비교 탭 (기본)
        self.comparison_notebook = ttk.Notebook(self.main_notebook)
        self.main_notebook.add(self.comparison_notebook, text="📊 DB 비교")
    
    def _create_log_area(self):
        """로그 영역 생성"""
        # 로그 프레임
        log_frame = ttk.LabelFrame(self.window, text="📝 로그", padding="5")
        log_frame.pack(fill=tk.X, padx=5, pady=5, before=self.status_bar)
        
        # 로그 텍스트 위젯
        self.log_text = tk.Text(
            log_frame, 
            height=5, 
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='#f0f0f0'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 스크롤바
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text['yscrollcommand'] = log_scrollbar.set
    
    def _setup_key_bindings(self):
        """키 바인딩 설정"""
        bindings = {
            '<Control-o>': None,  # 컨트롤러에서 설정
            '<Control-O>': None,
            '<F1>': None,
            '<Control-q>': lambda e: self.window.quit(),
            '<Control-Q>': lambda e: self.window.quit()
        }
        
        for key, handler in bindings.items():
            if handler:
                self.window.bind(key, handler)
    
    def update_log(self, message: str):
        """로그 메시지 추가"""
        if self.log_text:
            self.log_text.configure(state=tk.NORMAL)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
    
    def update_status(self, message: str):
        """상태바 업데이트"""
        if self.status_bar:
            self.status_bar.config(text=message)
    
    def enable_mother_db_menu(self, enabled: bool = True):
        """Mother DB 메뉴 활성화/비활성화"""
        state = "normal" if enabled else "disabled"
        try:
            # Mother DB 메뉴 인덱스 찾기
            menu_index = self.menubar.index("Mother DB")
            self.menubar.entryconfig(menu_index, state=state)
        except:
            pass
    
    def add_tab(self, parent_notebook, widget, title: str):
        """노트북에 탭 추가"""
        parent_notebook.add(widget, text=title)
    
    def remove_tab(self, parent_notebook, title: str):
        """노트북에서 탭 제거"""
        for i in range(parent_notebook.index("end")):
            if parent_notebook.tab(i, "text") == title:
                parent_notebook.forget(i)
                break
    
    def get_window(self) -> tk.Tk:
        """윈도우 객체 반환"""
        return self.window
    
    def get_main_notebook(self) -> ttk.Notebook:
        """메인 노트북 반환"""
        return self.main_notebook
    
    def get_comparison_notebook(self) -> ttk.Notebook:
        """비교 노트북 반환"""
        return self.comparison_notebook