"""
UI 탭 생성 및 관리를 담당하는 모듈
"""

import tkinter as tk
from tkinter import ttk
import sys
import os


class TabManager:
    """UI 탭 생성 및 관리를 담당하는 클래스"""
    
    def __init__(self, manager):
        """
        Args:
            manager: DBManager 인스턴스 참조
        """
        self.manager = manager
    
    def setup_window_with_new_config(self):
        """새로운 설정 시스템을 사용한 윈도우 설정"""
        self.manager.window = tk.Tk()
        self.manager.window.title(self.manager.config.app_name)
        self.manager.window.geometry(self.manager.config.window_geometry)
        
        try:
            icon_path = self.manager.config.icon_path
            if icon_path and icon_path.exists():
                self.manager.window.iconbitmap(str(icon_path))
        except Exception as e:
            print(f"아이콘 로드 실패: {str(e)}")
        
        self.setup_common_ui()
    
    def setup_window_legacy(self):
        """기존 방식의 윈도우 설정 (fallback)"""
        self.manager.window = tk.Tk()
        self.manager.window.title("DB Manager")
        self.manager.window.geometry("1300x800")
        
        try:
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                # src/app/manager.py에서 프로젝트 루트로 2번 상위 디렉토리로 이동
                application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            icon_path = os.path.join(application_path, "resources", "icons", "db_compare.ico")
            self.manager.window.iconbitmap(icon_path)
        except Exception as e:
            print(f"아이콘 로드 실패: {str(e)}")
        
        self.setup_common_ui()
    
    def setup_common_ui(self):
        """공통 UI 요소들을 설정합니다."""
        from app.ui.managers.menu_manager import MenuManager
        menu_manager = MenuManager(self.manager)
        menu_manager.create_menu()
        
        self.manager.status_bar = ttk.Label(self.manager.window, relief=tk.SUNKEN, anchor=tk.W)
        self.manager.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.manager.main_notebook = ttk.Notebook(self.manager.window)
        self.manager.main_notebook.pack(expand=True, fill=tk.BOTH)
        
        self.manager.comparison_notebook = ttk.Notebook(self.manager.main_notebook)
        self.manager.main_notebook.add(self.manager.comparison_notebook, text="DB 비교")
        
        self.manager.log_text = tk.Text(self.manager.window, height=5, state=tk.DISABLED)
        self.manager.log_text.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        log_scrollbar = ttk.Scrollbar(self.manager.log_text, orient="vertical", command=self.manager.log_text.yview)
        self.manager.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_comparison_tabs(self):
        """비교 탭들을 생성합니다."""
        # 기본 비교 관련 탭들 생성
        self.create_grid_view_tab()
        self.create_comparison_tab()
        self.create_diff_only_tab()
        self.create_report_tab()
    
    def create_grid_view_tab(self):
        """그리드 뷰 탭을 생성합니다."""
        # 격자 보기 탭
        grid_tab = ttk.Frame(self.manager.comparison_notebook)
        self.manager.comparison_notebook.add(grid_tab, text="격자 보기")
        
        # 실제 격자 뷰 구현은 기존 manager.py의 로직을 유지
        # 이 부분은 추후 단계에서 상세 구현
        
        # 탭 변수 저장
        self.manager.grid_tab = grid_tab
    
    def create_comparison_tab(self):
        """비교 탭을 생성합니다."""
        # 값 차이 탭
        comparison_tab = ttk.Frame(self.manager.comparison_notebook)
        self.manager.comparison_notebook.add(comparison_tab, text="값 차이")
        
        # 탭 변수 저장
        self.manager.comparison_tab = comparison_tab
    
    def create_diff_only_tab(self):
        """차이점만 보기 탭을 생성합니다."""
        # 차이점만 보기 탭
        diff_tab = ttk.Frame(self.manager.comparison_notebook)
        self.manager.comparison_notebook.add(diff_tab, text="차이점만 보기")
        
        # 탭 변수 저장
        self.manager.diff_tab = diff_tab
    
    def create_report_tab(self):
        """보고서 탭을 생성합니다."""
        # 보고서 탭
        report_tab = ttk.Frame(self.manager.comparison_notebook)
        self.manager.comparison_notebook.add(report_tab, text="보고서")
        
        # 탭 변수 저장
        self.manager.report_tab = report_tab
    
    def create_qc_tabs_with_advanced_features(self):
        """QC 관련 고급 탭들을 생성합니다."""
        if self.manager.maint_mode:
            self.create_qc_check_tab()
            self.create_default_db_tab()
    
    def create_qc_check_tab(self):
        """QC 검수 탭을 생성합니다."""
        if hasattr(self.manager, 'qc_check_frame') and self.manager.qc_check_frame:
            return
        
        qc_tab = ttk.Frame(self.manager.main_notebook)
        self.manager.main_notebook.add(qc_tab, text="QC 검수")
        self.manager.qc_check_frame = qc_tab
    
    def create_default_db_tab(self):
        """Default DB 관리 탭을 생성합니다."""
        if hasattr(self.manager, 'default_db_frame') and self.manager.default_db_frame:
            return
        
        default_db_tab = ttk.Frame(self.manager.main_notebook)
        self.manager.main_notebook.add(default_db_tab, text="Default DB 관리")
        self.manager.default_db_frame = default_db_tab
    
