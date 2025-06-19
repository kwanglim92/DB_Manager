"""
메인 애플리케이션 Controller
기존 DBManager 클래스의 UI 로직을 분리하여 MVVM 패턴 구현
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any

from .base_controller import BaseController
from ..viewmodels.main_viewmodel import MainViewModel


class MainController(BaseController):
    """
    메인 애플리케이션의 Controller
    MainViewModel과 메인 UI 간의 상호작용을 조정
    """
    
    def __init__(self, main_window: tk.Tk, viewmodel: MainViewModel = None):
        """
        MainController 초기화
        
        Args:
            main_window: 메인 윈도우
            viewmodel: MainViewModel (None이면 새로 생성)
        """
        self.main_window = main_window
        
        if viewmodel is None:
            viewmodel = MainViewModel()
        
        # UI 컴포넌트들
        self.menubar = None
        self.status_bar = None
        self.main_notebook = None
        self.comparison_notebook = None
        self.log_text = None
        
        # 탭 컨트롤러들
        self.tab_controllers = {}
        
        super().__init__(main_window, viewmodel)
        
        # UI 구성
        self._create_ui()
        
        # 초기 로그 메시지
        self.viewmodel.add_log_message("DB Manager 초기화 완료")
        if self.viewmodel.db_connected:
            self.viewmodel.add_log_message("Default DB 관리 기능 준비 완료")
    
    def _setup_bindings(self):
        """ViewModel 속성 바인딩 설정"""
        # 윈도우 제목 바인딩
        self.bind_property_to_view('app_title', self._update_window_title)
        
        # 상태 메시지 바인딩
        self.bind_property_to_view('status_message', self._update_status_bar)
        
        # 로그 메시지 바인딩
        log_messages = self.viewmodel.log_messages
        log_messages.bind_changed(self._update_log_display)
        
        # 유지보수 모드 바인딩
        self.bind_property_to_view('maint_mode', self._update_maintenance_mode_ui)
        
        # 오류 메시지 바인딩
        self.bind_property_to_view('error_message', self._handle_error_message)
        
        # 파일 목록 바인딩
        file_names = self.viewmodel.file_names
        file_names.bind_changed(self._update_file_display)
    
    def _setup_view_events(self):
        """View 이벤트 처리 설정"""
        # 윈도우 닫기 이벤트
        self.main_window.protocol("WM_DELETE_WINDOW", self._on_window_closing)
        
        # 키보드 단축키
        self.main_window.bind('<Control-o>', lambda e: self._handle_load_folder())
        self.main_window.bind('<Control-O>', lambda e: self._handle_load_folder())
        self.main_window.bind('<F1>', lambda e: self._handle_show_user_guide())
    
    def _create_ui(self):
        """UI 구성 요소 생성"""
        # 윈도우 기본 설정
        self.main_window.title(self.viewmodel.app_title)
        self.main_window.geometry(self.viewmodel.window_geometry)
        
        # 아이콘 설정 (기존 방식 유지)
        self._setup_window_icon()
        
        # 메뉴바 생성
        self._create_menubar()
        
        # 상태바 생성
        self._create_status_bar()
        
        # 메인 노트북 생성
        self._create_main_notebook()
        
        # 로그 영역 생성
        self._create_log_area()
        
        # 기본 탭들 생성
        self._create_default_tabs()
    
    def _setup_window_icon(self):
        """윈도우 아이콘 설정"""
        try:
            # 기존 방식 유지 (새로운 config 시스템이 있으면 사용)
            try:
                from app.core.config import AppConfig
                config = AppConfig()
                icon_path = config.icon_path
                if icon_path.exists():
                    self.main_window.iconbitmap(str(icon_path))
                    return
            except ImportError:
                pass
            
            # fallback: 기존 방식
            import sys
            import os
            
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__)))))
            
            icon_path = os.path.join(application_path, "resources", "icons", "db_compare.ico")
            if os.path.exists(icon_path):
                self.main_window.iconbitmap(icon_path)
                
        except Exception as e:
            print(f"아이콘 로드 실패: {str(e)}")
    
    def _create_menubar(self):
        """메뉴바 생성"""
        self.menubar = tk.Menu(self.main_window)
        
        # 파일 메뉴
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="폴더 열기 (Ctrl+O)", command=self._handle_load_folder)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.main_window.quit)
        self.menubar.add_cascade(label="파일", menu=file_menu)
        
        # 도구 메뉴
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        tools_menu.add_command(label="Maintenance Mode", command=self._handle_toggle_maintenance)
        self.menubar.add_cascade(label="도구", menu=tools_menu)
        
        # 도움말 메뉴
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="사용 설명서 (F1)", command=self._handle_show_user_guide)
        help_menu.add_separator()
        help_menu.add_command(label="프로그램 정보", command=self._handle_show_about)
        self.menubar.add_cascade(label="도움말", menu=help_menu)
        
        self.main_window.config(menu=self.menubar)
    
    def _create_status_bar(self):
        """상태바 생성"""
        self.status_bar = ttk.Label(self.main_window, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_main_notebook(self):
        """메인 노트북 생성"""
        self.main_notebook = ttk.Notebook(self.main_window)
        self.main_notebook.pack(expand=True, fill=tk.BOTH)
        
        # 비교 노트북 생성
        self.comparison_notebook = ttk.Notebook(self.main_notebook)
        self.main_notebook.add(self.comparison_notebook, text="DB 비교")
    
    def _create_log_area(self):
        """로그 영역 생성"""
        # 로그 프레임
        log_frame = ttk.Frame(self.main_window)
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # 로그 텍스트
        self.log_text = tk.Text(log_frame, height=5, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # 로그 클리어 버튼
        clear_button = ttk.Button(log_frame, text="로그 클리어")
        self.bind_button_command(clear_button, "clear_log")
        clear_button.pack(side=tk.RIGHT, padx=(5, 0))
    
    def _create_default_tabs(self):
        """기본 탭들 생성"""
        # 실제 탭 생성은 기존 방식 유지하되, 컨트롤러 패턴으로 관리
        # 여기서는 기본 구조만 설정하고, 실제 탭은 필요시 생성
        pass
    
    # 이벤트 핸들러들
    def _handle_load_folder(self):
        """폴더 로드 처리"""
        folder_path = self.create_folder_dialog("폴더 선택")
        if folder_path:
            self.viewmodel.execute_command('load_folder', folder_path)
    
    def _handle_toggle_maintenance(self):
        """유지보수 모드 토글 처리"""
        if not self.viewmodel.maint_mode:
            password = self.create_input_dialog(
                "유지보수 모드", "비밀번호를 입력하세요:", show_char="*"
            )
            if password:
                self.viewmodel.execute_command('toggle_maintenance_mode', password)
        else:
            self.viewmodel.execute_command('toggle_maintenance_mode')
    
    def _handle_show_user_guide(self):
        """사용자 가이드 표시 처리"""
        result = self.viewmodel.execute_command('show_user_guide')
        if result:
            self.show_info(result['title'], result['message'])
    
    def _handle_show_about(self):
        """프로그램 정보 표시 처리"""
        result = self.viewmodel.execute_command('show_about')
        if result:
            self.show_info(result['title'], result['message'])
    
    def _on_window_closing(self):
        """윈도우 닫기 이벤트 처리"""
        try:
            # 리소스 정리
            self.cleanup()
            self.main_window.destroy()
        except Exception as e:
            print(f"윈도우 닫기 중 오류: {e}")
            self.main_window.destroy()
    
    # View 업데이트 함수들
    def _update_window_title(self, title: str):
        """윈도우 제목 업데이트"""
        self.main_window.title(title)
    
    def _update_status_bar(self, message: str):
        """상태바 업데이트"""
        if self.status_bar:
            self.status_bar.config(text=message)
    
    def _update_log_display(self):
        """로그 표시 업데이트"""
        if not self.log_text:
            return
        
        try:
            # 최근 로그 메시지들 가져오기
            recent_logs = self.viewmodel.get_recent_log_messages(50)
            
            # 로그 텍스트 업데이트
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            
            for log_message in recent_logs:
                self.log_text.insert(tk.END, log_message + "\n")
            
            # 맨 아래로 스크롤
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
            
        except Exception as e:
            print(f"로그 표시 업데이트 오류: {e}")
    
    def _update_maintenance_mode_ui(self, is_maintenance_mode: bool):
        """유지보수 모드 UI 업데이트"""
        try:
            if is_maintenance_mode:
                # 유지보수 모드 활성화 - 유지보수 탭들 표시
                self._show_maintenance_tabs()
            else:
                # 유지보수 모드 비활성화 - 유지보수 탭들 숨기기
                self._hide_maintenance_tabs()
                
        except Exception as e:
            print(f"유지보수 모드 UI 업데이트 오류: {e}")
    
    def _handle_error_message(self, error_message: str):
        """오류 메시지 처리"""
        if error_message:
            self.show_error("오류", error_message)
            # 오류 표시 후 클리어
            self.viewmodel.clear_error()
    
    def _update_file_display(self):
        """파일 표시 업데이트"""
        # 파일 목록이 변경되면 관련 탭들 업데이트
        try:
            # 각 탭 컨트롤러에 업데이트 알림
            for tab_controller in self.tab_controllers.values():
                if hasattr(tab_controller, 'refresh_view'):
                    tab_controller.refresh_view()
                    
        except Exception as e:
            print(f"파일 표시 업데이트 오류: {e}")
    
    # 유지보수 모드 탭 관리
    def _show_maintenance_tabs(self):
        """유지보수 모드 탭들 표시"""
        try:
            # QC 체크 탭
            if 'qc_check' not in self.tab_controllers:
                self._create_qc_check_tab()
            
            # Default DB 탭
            if 'default_db' not in self.tab_controllers:
                self._create_default_db_tab()
            
            # 변경 이력 탭
            if 'change_history' not in self.tab_controllers:
                self._create_change_history_tab()
                
        except Exception as e:
            print(f"유지보수 탭 표시 오류: {e}")
    
    def _hide_maintenance_tabs(self):
        """유지보수 모드 탭들 숨기기"""
        try:
            # 유지보수 관련 탭들을 메인 노트북에서 제거
            for i in range(self.main_notebook.index("end")):
                tab_text = self.main_notebook.tab(i, "text")
                if tab_text in ["QC 검수", "Default DB 관리", "변경 이력"]:
                    self.main_notebook.forget(i)
                    break
                    
        except Exception as e:
            print(f"유지보수 탭 숨기기 오류: {e}")
    
    def _create_qc_check_tab(self):
        """QC 체크 탭 생성 (기존 방식 유지)"""
        # 임시로 기본 프레임만 생성
        qc_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(qc_frame, text="QC 검수")
        
        # 추후 별도 QC 컨트롤러로 분리 예정
        label = ttk.Label(qc_frame, text="QC 검수 기능 (개발 중)")
        label.pack(expand=True)
    
    def _create_default_db_tab(self):
        """Default DB 탭 생성 (기존 방식 유지)"""
        # 임시로 기본 프레임만 생성
        db_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(db_frame, text="Default DB 관리")
        
        # 추후 별도 DB 컨트롤러로 분리 예정
        label = ttk.Label(db_frame, text="Default DB 관리 기능 (개발 중)")
        label.pack(expand=True)
    
    def _create_change_history_tab(self):
        """변경 이력 탭 생성 (기존 방식 유지)"""
        # 임시로 기본 프레임만 생성
        history_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(history_frame, text="변경 이력")
        
        # 추후 별도 히스토리 컨트롤러로 분리 예정
        label = ttk.Label(history_frame, text="변경 이력 기능 (개발 중)")
        label.pack(expand=True)
    
    # 기존 manager.py 기능과의 호환성 메서드들
    def update_log(self, message: str):
        """로그 업데이트 (기존 호환성)"""
        self.viewmodel.add_log_message(message)
    
    def get_main_window(self) -> tk.Tk:
        """메인 윈도우 반환"""
        return self.main_window
    
    def get_viewmodel(self) -> MainViewModel:
        """ViewModel 반환"""
        return self.viewmodel
    
    def add_tab_controller(self, name: str, controller):
        """탭 컨트롤러 추가"""
        self.tab_controllers[name] = controller
    
    def get_tab_controller(self, name: str):
        """탭 컨트롤러 가져오기"""
        return self.tab_controllers.get(name)
    
    def remove_tab_controller(self, name: str):
        """탭 컨트롤러 제거"""
        if name in self.tab_controllers:
            controller = self.tab_controllers[name]
            if hasattr(controller, 'cleanup'):
                controller.cleanup()
            del self.tab_controllers[name] 