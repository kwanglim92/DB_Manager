# DBManager 클래스 및 메인 GUI 관리

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sys, os
from datetime import datetime
from app.schema import DBSchema
from app.loading import LoadingDialog
from app.qc import add_qc_check_functions_to_class
from app.enhanced_qc import add_enhanced_qc_functions_to_class
from app.defaultdb import add_default_db_functions_to_class
from app.history import add_change_history_functions_to_class
from app.utils import create_treeview_with_scrollbar, create_label_entry_pair, format_num_value

# 🆕 새로운 설정 시스템 (선택적 사용)
try:
    from app.core.config import AppConfig
    from app.utils.path_utils import PathManager
    from app.utils.validation import ValidationUtils
    USE_NEW_CONFIG = True
except ImportError:
    USE_NEW_CONFIG = False

# 🆕 새로운 서비스 시스템 (점진적 전환)
try:
    from app.services import ServiceFactory, LegacyAdapter, SERVICES_AVAILABLE
    import json
    USE_NEW_SERVICES = True
except ImportError:
    USE_NEW_SERVICES = False
    SERVICES_AVAILABLE = False

class DBManager:
    def __init__(self):
        # 🆕 새로운 설정 시스템 사용 (기존 코드 유지)
        if USE_NEW_CONFIG:
            self.config = AppConfig()
            self.path_manager = PathManager()
            self.validator = ValidationUtils()
        
        self.maint_mode = False
        self.selected_equipment_type_id = None
        self.file_names = []
        self.folder_path = ""
        self.merged_df = None
        self.context_menu = None
        
        # QC 엔지니어용 탭 프레임들을 저장할 변수들
        self.qc_check_frame = None
        self.default_db_frame = None  
        self.change_history_frame = None
        
        try:
            self.db_schema = DBSchema()
        except Exception as e:
            print(f"DB 스키마 초기화 실패: {str(e)}")
            self.db_schema = None
        
        add_qc_check_functions_to_class(DBManager)
        add_enhanced_qc_functions_to_class(DBManager)
        add_default_db_functions_to_class(DBManager)
        add_change_history_functions_to_class(DBManager)
        
        # 🆕 아이콘 로드 개선 (기존 코드와 호환)
        if USE_NEW_CONFIG:
            self._setup_window_with_new_config()
        else:
            self._setup_window_legacy()
        
        # 바인딩 설정
        for key in ('<Control-o>', '<Control-O>'):
            self.window.bind(key, self.load_folder)
        self.window.bind('<F1>', self.show_user_guide)
        
        self.status_bar.config(text="Ready")
        self.update_log("DB Manager 초기화 완료 - 장비 생산 엔지니어 모드")
        if self.db_schema:
            self.update_log("로컬 데이터베이스 초기화 완료")
        else:
            self.update_log("DB 스키마 초기화 실패")
        
        # 🆕 새로운 서비스 시스템 초기화 (UI 설정 후)
        self._setup_service_layer()
        
        # 기본적으로는 장비 생산 엔지니어용 탭만 생성
        self.create_comparison_tabs()

    def _setup_window_with_new_config(self):
        """새로운 설정 시스템을 사용한 윈도우 설정"""
        self.window = tk.Tk()
        self.window.title(self.config.app_name)
        self.window.geometry(self.config.window_geometry)
        
        try:
            icon_path = self.config.icon_path
            if icon_path.exists():
                self.window.iconbitmap(str(icon_path))
        except Exception as e:
            print(f"아이콘 로드 실패: {str(e)}")
        
        self._setup_common_ui()
    
    def _setup_window_legacy(self):
        """기존 방식의 윈도우 설정 (fallback)"""
        self.window = tk.Tk()
        self.window.title("DB Manager")
        self.window.geometry("1300x800")
        try:
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                # src/app/manager.py에서 프로젝트 루트로 2번 상위 디렉토리로 이동
                application_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(application_path, "resources", "icons", "db_compare.ico")
            self.window.iconbitmap(icon_path)
        except Exception as e:
            print(f"아이콘 로드 실패: {str(e)}")
        
        self._setup_common_ui()
    
    def _setup_common_ui(self):
        """공통 UI 요소들을 설정합니다."""
        self.create_menu()
        self.status_bar = ttk.Label(self.window, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.main_notebook = ttk.Notebook(self.window)
        self.main_notebook.pack(expand=True, fill=tk.BOTH)
        self.comparison_notebook = ttk.Notebook(self.main_notebook)
        self.main_notebook.add(self.comparison_notebook, text="DB 비교")
        self.log_text = tk.Text(self.window, height=5, state=tk.DISABLED)
        self.log_text.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        log_scrollbar = ttk.Scrollbar(self.log_text, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_service_layer(self):
        """🆕 새로운 서비스 레이어 초기화"""
        self.service_factory = None
        self.legacy_adapter = None
        self.use_new_services = {}
        
        if not USE_NEW_SERVICES or not SERVICES_AVAILABLE:
            self.update_log("서비스 레이어를 사용할 수 없습니다 (fallback mode)")
            return
        
        try:
            # 설정 파일에서 서비스 사용 설정 로드
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "settings.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.use_new_services = settings.get('use_new_services', {})
                    service_config = settings.get('service_config', {})
            else:
                self.use_new_services = {'equipment_service': False}
                service_config = {}
            
            # 서비스 팩토리 초기화
            if self.db_schema:
                self.service_factory = ServiceFactory(self.db_schema, service_config)
                self.legacy_adapter = LegacyAdapter(self.service_factory)
                
                # 서비스 상태 로깅
                status = self.service_factory.get_service_status()
                self.update_log(f"서비스 레이어 초기화 완료: {len(status)}개 서비스 등록")
                
                # 활성 서비스들 확인
                active_services = [k for k, v in self.use_new_services.items() if v]
                if active_services:
                    self.update_log(f"활성 서비스: {', '.join(active_services)}")
                
            else:
                self.update_log("DB 스키마가 없어 서비스 팩토리를 초기화할 수 없습니다")
                
        except Exception as e:
            self.update_log(f"서비스 레이어 초기화 실패: {str(e)}")
            print(f"Service layer initialization failed: {str(e)}")
    
    def _should_use_service(self, service_name: str) -> bool:
        """특정 서비스 사용 여부 확인"""
        return (USE_NEW_SERVICES and 
                SERVICES_AVAILABLE and 
                self.service_factory is not None and
                self.use_new_services.get(service_name, False))

    def get_db_connection(self):
        """
        데이터베이스 연결을 반환합니다.
        다른 모듈들(qc.py, defaultdb.py, file_handler.py)에서 사용됩니다.
        
        Returns:
            sqlite3.Connection: 데이터베이스 연결 객체
        """
        if self.db_schema:
            import sqlite3
            return sqlite3.connect(self.db_schema.db_path)
        else:
            raise Exception("DBSchema가 초기화되지 않았습니다.")

    def show_about(self):
        """프로그램 정보 다이얼로그 표시"""
        messagebox.showinfo(
            "프로그램 정보",
            "DB Manager\n버전: 1.0.1\n제작자: kwanglim92\n\n이 프로그램은 DB 파일 비교, 관리, 보고서 생성 등 다양한 기능을 제공합니다."
        )

    def show_user_guide(self, event=None):
        """사용자 가이드 다이얼로그 표시"""
        guide_text = (
            "[DB Manager 사용자 가이드]\n\n"
            "• 폴더 열기: 파일 > 폴더 열기 (Ctrl+O)\n"
            "• DB 비교: 여러 DB 파일을 불러와 값 차이, 격자 뷰, 보고서 등 다양한 탭에서 확인\n"
            "• 유지보수 모드: 도구 > Maintenance Mode (비밀번호 필요)\n"
            "• Default DB 관리, QC 검수, 변경 이력 등은 유지보수 모드에서만 사용 가능\n"
            "• 각 탭에서 우클릭 및 버튼으로 항목 추가/삭제/내보내기 등 다양한 작업 지원\n"
            "• 문의: github.com/kwanglim92/DB_Manager\n\n"
            "= 사용자 역할 =\n"
            "• 장비 생산 엔지니어: DB 비교 기능 사용\n"
            "• QC 엔지니어: Maintenance Mode로 모든 기능 사용"
        )
        messagebox.showinfo("사용 설명서", guide_text)

    def create_menu(self):
        """메뉴바를 생성합니다."""
        menubar = tk.Menu(self.window)
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="폴더 열기 (Ctrl+O)", command=self.load_folder)
        file_menu.add_separator()
        file_menu.add_command(label="보고서 내보내기", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.window.quit)
        menubar.add_cascade(label="파일", menu=file_menu)
        # 도구 메뉴
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="👤 사용자 모드 전환", command=self.toggle_maint_mode)
        tools_menu.add_separator()
        tools_menu.add_command(label="🔐 비밀번호 변경", command=self.show_change_password_dialog)
        tools_menu.add_command(label="⚙️ 설정", command=self.show_settings_dialog)
        menubar.add_cascade(label="도구", menu=tools_menu)
        # 도움말 메뉴
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="사용 설명서 (F1)", command=self.show_user_guide)
        help_menu.add_separator()
        help_menu.add_command(label="프로그램 정보", command=self.show_about)
        menubar.add_cascade(label="도움말", menu=help_menu)
        self.window.config(menu=menubar)

    def update_log(self, message):
        """로그 표시 영역에 메시지를 추가합니다."""
        self.log_text.configure(state=tk.NORMAL)
        from datetime import datetime
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def toggle_maint_mode(self):
        """유지보수 모드 토글"""
        if self.maint_mode:
            self.update_log("유지보수 모드가 비활성화되었습니다. (장비 생산 엔지니어 모드)")
            self.maint_mode = False
            self.status_bar.config(text="장비 생산 엔지니어 모드")
            self.disable_maint_features()
        else:
            password = simpledialog.askstring("유지보수 모드", "QC 엔지니어 비밀번호를 입력하세요:", show="*")
            if password is None:
                return
            from app.utils import verify_password
            if verify_password(password):
                self.enable_maint_features()
            else:
                messagebox.showerror("오류", "비밀번호가 일치하지 않습니다.")
        
        self.update_default_db_ui_state()

    def show_change_password_dialog(self):
        """유지보수 모드 비밀번호 변경 다이얼로그를 표시합니다."""
        current_password = simpledialog.askstring("비밀번호 변경", "현재 비밀번호를 입력하세요:", show="*")
        if current_password is None:
            return
        from app.utils import verify_password, change_maintenance_password
        if not verify_password(current_password):
            messagebox.showerror("오류", "현재 비밀번호가 일치하지 않습니다.")
            return
        new_password = simpledialog.askstring("비밀번호 변경", "새 비밀번호를 입력하세요:", show="*")
        if new_password is None:
            return
        confirm_password = simpledialog.askstring("비밀번호 변경", "새 비밀번호를 다시 입력하세요:", show="*")
        if confirm_password is None:
            return
        if new_password != confirm_password:
            messagebox.showerror("오류", "새 비밀번호가 일치하지 않습니다.")
            return
        if change_maintenance_password(current_password, new_password):
            messagebox.showinfo("성공", "비밀번호가 성공적으로 변경되었습니다.")
            self.update_log("유지보수 모드 비밀번호가 변경되었습니다.")
        else:
            messagebox.showerror("오류", "비밀번호 변경에 실패했습니다.")

    def show_settings_dialog(self):
        """설정 다이얼로그를 표시합니다."""
        from app.ui.dialogs.enhanced_dialogs import show_settings_dialog
        
        # 현재 설정 로드
        current_settings = {}
        if hasattr(self, 'config') and self.config:
            ui_settings = self.config.get_setting('ui', {})
            current_settings = {
                'theme': ui_settings.get('theme', 'default') if isinstance(ui_settings, dict) else 'default'
            }
        
        # 설정 다이얼로그 표시
        result = show_settings_dialog(self.window, current_settings)
        
        if result:
            # 설정 적용
            self.apply_settings(result)
            self.update_log("설정이 업데이트되었습니다.")
    
    def apply_settings(self, settings):
        """설정 적용"""
        if not hasattr(self, 'config') or not self.config:
            return
            
        # 테마 설정 적용
        if 'theme' in settings:
            ui_settings = self.config.get_setting('ui', {})
            if not isinstance(ui_settings, dict):
                ui_settings = {}
            ui_settings['theme'] = settings['theme']
            self.config.set_setting('ui', ui_settings)
            
            # 설정 파일 저장
            try:
                if self.config.save_settings():
                    self.update_log(f"테마가 '{settings['theme']}'로 변경되었습니다.")
                else:
                    self.update_log("설정 저장에 실패했습니다.")
            except Exception as e:
                self.update_log(f"설정 저장 중 오류: {e}")

    def update_default_db_ui_state(self):
        """유지보수 모드에 따라 Default DB 관련 UI 요소들의 상태를 업데이트합니다."""
        if hasattr(self, 'show_default_candidates_cb'):
            if self.maint_mode:
                self.show_default_candidates_cb.configure(state="normal")
            else:
                if hasattr(self, 'show_default_candidates_var'):
                    self.show_default_candidates_var.set(False)
                self.show_default_candidates_cb.configure(state="disabled")
                self.update_comparison_view()
        
        self.update_comparison_context_menu_state()
        
        # 모든 탭 업데이트
        if hasattr(self, 'update_all_tabs'):
            # 탭 업데이트는 파일이 로드된 경우에만
            if self.merged_df is not None:
                self.update_all_tabs()

    def enable_maint_features(self):
        """유지보수 모드 활성화 - QC 엔지니어용 탭들을 추가합니다."""
        import threading
        loading_dialog = LoadingDialog(self.window)
        
        def worker():
            try:
                self.maint_mode = True
                
                loading_dialog.update_progress(20, "QC 검수 탭 생성 중...")
                self.window.after(0, self.create_qc_check_tab)
                
                loading_dialog.update_progress(50, "Default DB 관리 탭 생성 중...")
                self.window.after(0, self.create_default_db_tab)
                
                loading_dialog.update_progress(80, "변경 이력 관리 탭 생성 중...")
                self.window.after(0, self.create_change_history_tab)
                
                loading_dialog.update_progress(100, "완료")
                self.window.after(100, loading_dialog.close)
                
                self.window.after(200, lambda: self.update_log("QC 엔지니어 모드가 활성화되었습니다."))
                self.window.after(200, lambda: self.status_bar.config(text="QC 엔지니어 모드"))
                
            except Exception as e:
                self.window.after(0, loading_dialog.close)
                self.window.after(0, lambda: messagebox.showerror("오류", f"유지보수 모드 활성화 중 오류 발생: {str(e)}"))
        
        threading.Thread(target=worker, daemon=True).start()

    def create_comparison_tabs(self):
        """비교 관련 탭 생성 - 기본 기능만"""
        self.create_grid_view_tab()
        self.create_comparison_tab()
        self.create_diff_only_tab()
        # 보고서, 간단 비교, 고급 분석은 QC 탭으로 이동

    def create_qc_tabs_with_advanced_features(self):
        """QC 탭에 고급 기능들 추가"""
        if not hasattr(self, 'qc_notebook'):
            return
            
        # 보고서 탭을 QC 노트북에 추가
        self.create_report_tab_in_qc()
        
        # 간단한 비교 기능을 QC 노트북에 추가
        try:
            from app.simple_comparison import add_simple_comparison_to_class
            add_simple_comparison_to_class(DBManager)
            if hasattr(self, 'create_simple_comparison_features_in_qc'):
                self.create_simple_comparison_features_in_qc()
        except ImportError as e:
            self.update_log(f"[경고] 간단한 비교 기능을 불러올 수 없습니다: {e}")
        
        # 고급 비교 기능을 QC 노트북에 추가 (선택적)
        try:
            from app.advanced_comparison import add_advanced_comparison_to_class
            add_advanced_comparison_to_class(DBManager)
            if hasattr(self, 'create_advanced_comparison_features_in_qc'):
                self.create_advanced_comparison_features_in_qc()
        except ImportError as e:
            self.update_log(f"[경고] 고급 비교 기능을 불러올 수 없습니다: {e}")

    def create_report_tab_in_qc(self):
        """QC 노트북에 보고서 탭 생성"""
        if not hasattr(self, 'qc_notebook'):
            return
            
        report_tab = ttk.Frame(self.qc_notebook)
        self.qc_notebook.add(report_tab, text="보고서")
        
        control_frame = ttk.Frame(report_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        export_btn = ttk.Button(control_frame, text="보고서 내보내기", command=self.export_report)
        export_btn.pack(side=tk.RIGHT, padx=10)
        
        columns = ["Module", "Part", "ItemName"] + (self.file_names if self.file_names else [])
        self.qc_report_tree = ttk.Treeview(report_tab, columns=columns, show="headings", selectmode="browse")
        
        for col in columns:
            self.qc_report_tree.heading(col, text=col)
            self.qc_report_tree.column(col, width=120)
        
        v_scroll = ttk.Scrollbar(report_tab, orient="vertical", command=self.qc_report_tree.yview)
        h_scroll = ttk.Scrollbar(report_tab, orient="horizontal", command=self.qc_report_tree.xview)
        self.qc_report_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.qc_report_tree.pack(expand=True, fill=tk.BOTH)
        
        self.update_qc_report_view()

    def update_qc_report_view(self):
        """QC 보고서 뷰 업데이트"""
        if not hasattr(self, 'qc_report_tree'):
            return
            
        for item in self.qc_report_tree.get_children():
            self.qc_report_tree.delete(item)
            
        if self.merged_df is not None:
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            for (module, part, item_name), group in grouped:
                values = [module, part, item_name]
                for fname in self.file_names:
                    model_data = group[group["Model"] == fname]
                    if not model_data.empty:
                        values.append(str(model_data["ItemValue"].iloc[0]))
                    else:
                        values.append("-")
                self.qc_report_tree.insert("", "end", values=values)

    def create_diff_only_tab(self):
        """차이만 보기 탭 생성"""
        diff_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(diff_tab, text="🔍 차이점 분석")
        
        # 상단 정보 패널
        control_frame = ttk.Frame(diff_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.diff_only_count_label = ttk.Label(control_frame, text="값이 다른 항목: 0개")
        self.diff_only_count_label.pack(side=tk.RIGHT, padx=10)
        
        # 트리뷰 생성
        if self.file_names:
            columns = ["Module", "Part", "ItemName"] + self.file_names
        else:
            columns = ["Module", "Part", "ItemName"]
            
        self.diff_only_tree = ttk.Treeview(diff_tab, columns=columns, show="headings", selectmode="extended")
        
        # 헤딩 설정
        for col in columns:
            self.diff_only_tree.heading(col, text=col)
            if col in ["Module", "Part", "ItemName"]:
                self.diff_only_tree.column(col, width=120)
            else:
                self.diff_only_tree.column(col, width=150)
        
        # 스크롤바 추가
        v_scroll = ttk.Scrollbar(diff_tab, orient="vertical", command=self.diff_only_tree.yview)
        h_scroll = ttk.Scrollbar(diff_tab, orient="horizontal", command=self.diff_only_tree.xview)
        self.diff_only_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        
        # 위젯 배치
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.diff_only_tree.pack(expand=True, fill=tk.BOTH)
        
        # 차이점 데이터 업데이트
        self.update_diff_only_view()

    def update_diff_only_view(self):
        """차이점만 보기 탭 업데이트 - 하이라이트 제거"""
        if not hasattr(self, 'diff_only_tree'):
            return
            
        for item in self.diff_only_tree.get_children():
            self.diff_only_tree.delete(item)
        
        diff_count = 0
        if self.merged_df is not None:
            # 컬럼 업데이트
            columns = ["Module", "Part", "ItemName"] + self.file_names
            self.diff_only_tree["columns"] = columns
            
            for col in columns:
                self.diff_only_tree.heading(col, text=col)
                if col in ["Module", "Part", "ItemName"]:
                    self.diff_only_tree.column(col, width=120)
                else:
                    self.diff_only_tree.column(col, width=150)
            
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            
            for (module, part, item_name), group in grouped:
                # 각 파일별 값 추출
                file_values = {}
                for model in self.file_names:
                    model_data = group[group["Model"] == model]
                    if not model_data.empty:
                        file_values[model] = str(model_data["ItemValue"].iloc[0])
                    else:
                        file_values[model] = "-"
                
                # 차이점이 있는지 확인
                unique_values = set(v for v in file_values.values() if v != "-")
                if len(unique_values) > 1:
                    # 차이점이 있는 항목만 추가 (하이라이트 없이)
                    row_values = [module, part, item_name]
                    row_values.extend([file_values.get(model, "-") for model in self.file_names])
                    
                    self.diff_only_tree.insert("", "end", values=row_values)
                    diff_count += 1
        
        # 차이점 카운트 업데이트
        if hasattr(self, 'diff_only_count_label'):
            self.diff_only_count_label.config(text=f"값이 다른 항목: {diff_count}개")

    def create_report_tab(self):
        report_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(report_tab, text="보고서")
        control_frame = ttk.Frame(report_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        export_btn = ttk.Button(control_frame, text="보고서 내보내기", command=self.export_report)
        export_btn.pack(side=tk.RIGHT, padx=10)
        columns = ["Module", "Part", "ItemName"] + self.file_names
        self.report_tree = ttk.Treeview(report_tab, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=120)
        v_scroll = ttk.Scrollbar(report_tab, orient="vertical", command=self.report_tree.yview)
        h_scroll = ttk.Scrollbar(report_tab, orient="horizontal", command=self.report_tree.xview)
        self.report_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.report_tree.pack(expand=True, fill=tk.BOTH)
        self.update_report_view()

    def update_report_view(self):
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        if self.merged_df is not None:
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            for (module, part, item_name), group in grouped:
                values = [module, part, item_name]
                for fname in self.file_names:
                    values.append(group[fname].iloc[0] if fname in group else "")
                self.report_tree.insert("", "end", values=values)

    def export_report(self):
        # 보고서 내보내기 기능 (실제 구현은 utils.py 등에서 분리 가능)
        try:
            from tkinter import filedialog
            import pandas as pd
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel 파일", "*.xlsx"), ("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
                title="보고서 내보내기"
            )
            if not file_path:
                return
            data = []
            for item in self.report_tree.get_children():
                data.append(self.report_tree.item(item)["values"])
            df = pd.DataFrame(data, columns=["Module", "Part", "ItemName"] + self.file_names)
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
            else:
                df.to_excel(file_path, index=False)
            messagebox.showinfo("완료", "보고서가 성공적으로 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"보고서 내보내기 중 오류 발생: {str(e)}")


    def load_folder(self, event=None):
        # 파일 확장자 필터 설정
        filetypes = [
            ("DB 파일", "*.txt;*.db;*.csv"),
            ("텍스트 파일", "*.txt"),
            ("CSV 파일", "*.csv"),
            ("DB 파일", "*.db"),
            ("모든 파일", "*.*")
        ]
        files = filedialog.askopenfilenames(
            title="📂 DB 파일을 선택하세요",
            filetypes=filetypes,
            initialdir=self.folder_path if self.folder_path else None
        )
        if not files:
            self.status_bar.config(text="파일 선택이 취소되었습니다.")
            return
        loading_dialog = LoadingDialog(self.window)
        try:
            import pandas as pd
            import os
            import sqlite3
            df_list = []
            self.file_names = []
            total_files = len(files)
            loading_dialog.update_progress(0, "파일 로딩 준비 중...")
            for idx, file in enumerate(files, 1):
                try:
                    progress = (idx / total_files) * 70
                    loading_dialog.update_progress(
                        progress,
                        f"파일 로딩 중... ({idx}/{total_files})"
                    )
                    file_name = os.path.basename(file)
                    base_name = os.path.splitext(file_name)[0]
                    ext = os.path.splitext(file_name)[1].lower()
                    if ext == '.txt':
                        df = pd.read_csv(file, delimiter="\t", dtype=str)
                    elif ext == '.csv':
                        df = pd.read_csv(file, dtype=str)
                    elif ext == '.db':
                        conn = sqlite3.connect(file)
                        df = pd.read_sql("SELECT * FROM main_table", conn)
                        conn.close()
                    df["Model"] = base_name
                    df_list.append(df)
                    self.file_names.append(base_name)
                except Exception as e:
                    messagebox.showwarning(
                        "경고", 
                        f"'{file_name}' 파일 로드 중 오류 발생:\n{str(e)}"
                    )
            if df_list:
                self.folder_path = os.path.dirname(files[0])
                loading_dialog.update_progress(75, "데이터 병합 중...")
                self.merged_df = pd.concat(df_list, ignore_index=True)
                loading_dialog.update_progress(85, "화면 업데이트 중...")
                self.update_all_tabs()
                loading_dialog.update_progress(100, "완료!")
                loading_dialog.close()
                messagebox.showinfo(
                    "로드 완료",
                    f"총 {len(df_list)}개의 DB 파일을 성공적으로 로드했습니다.\n"
                    f"• 폴더: {self.folder_path}\n"
                    f"• 파일: {', '.join(self.file_names)}"
                )
                self.status_bar.config(
                    text=f"총 {len(df_list)}개의 DB 파일이 로드되었습니다. "
                         f"(폴더: {os.path.basename(self.folder_path)})"
                )
            else:
                loading_dialog.close()
                messagebox.showerror("오류", "파일을 로드할 수 없습니다.")
                self.status_bar.config(text="파일 로드 실패")
        except Exception as e:
            loading_dialog.close()
            messagebox.showerror("오류", f"예기치 않은 오류가 발생했습니다:\n{str(e)}")

    def update_all_tabs(self):
        # 기존 탭 제거
        for tab in self.comparison_notebook.winfo_children():
            tab.destroy()
        # 탭 다시 생성
        self.create_comparison_tabs()
        
        # 격자뷰와 차이점뷰 업데이트
        if hasattr(self, 'update_grid_view'):
            self.update_grid_view()
        if hasattr(self, 'update_diff_only_view'):
            self.update_diff_only_view()
        
        # QC 보고서 뷰도 업데이트 (유지보수 모드인 경우)
        if self.maint_mode and hasattr(self, 'update_qc_report_view'):
            self.update_qc_report_view()

    def create_grid_view_tab(self):
        """격자뷰 탭 생성 - 트리뷰 구조"""
        grid_frame = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(grid_frame, text="📊 메인 비교")
        
        # 상단 정보 패널
        info_frame = ttk.Frame(grid_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 통계 정보 라벨들
        self.grid_total_label = ttk.Label(info_frame, text="총 파라미터: 0")
        self.grid_total_label.pack(side=tk.LEFT, padx=10)
        
        self.grid_modules_label = ttk.Label(info_frame, text="모듈 수: 0")
        self.grid_modules_label.pack(side=tk.LEFT, padx=10)
        
        self.grid_parts_label = ttk.Label(info_frame, text="파트 수: 0")
        self.grid_parts_label.pack(side=tk.LEFT, padx=10)
        
        # 차이점 개수 라벨 추가
        self.grid_diff_label = ttk.Label(info_frame, text="값이 다른 항목: 0", foreground="red")
        self.grid_diff_label.pack(side=tk.RIGHT, padx=10)
        

        
        # 메인 트리뷰 생성 (계층 구조)
        self.grid_tree = ttk.Treeview(grid_frame, selectmode="extended")
        
        # 동적 컬럼 설정
        if self.file_names:
            columns = tuple(self.file_names)
        else:
            columns = ("값",)
            
        self.grid_tree["columns"] = columns
        
        # 첫 번째 컬럼 (트리 구조용)
        self.grid_tree.heading("#0", text="구조", anchor="w")
        self.grid_tree.column("#0", width=250, anchor="w")
        
        # 파일별 값 컬럼들
        for col in columns:
            self.grid_tree.heading(col, text=col, anchor="center")
            self.grid_tree.column(col, width=150, anchor="center")
        
        # 스크롤바 추가
        v_scroll = ttk.Scrollbar(grid_frame, orient="vertical", command=self.grid_tree.yview)
        h_scroll = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.grid_tree.xview)
        self.grid_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        
        # 위젯 배치
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.grid_tree.pack(expand=True, fill=tk.BOTH)
        
        # 격자뷰 데이터 업데이트
        self.update_grid_view()

    def update_grid_view(self):
        """격자뷰 데이터 업데이트 - 트리뷰 구조"""
        if not hasattr(self, 'grid_tree'):
            return
            
        # 기존 데이터 삭제
        for item in self.grid_tree.get_children():
            self.grid_tree.delete(item)
        
        if self.merged_df is None or self.merged_df.empty:
            # 통계 정보 초기화
            if hasattr(self, 'grid_total_label'):
                self.grid_total_label.config(text="총 파라미터: 0개")
                self.grid_modules_label.config(text="모듈 수: 0개") 
                self.grid_parts_label.config(text="파트 수: 0개")
            return
        
        # 동적 컬럼 업데이트
        columns = tuple(self.file_names) if self.file_names else ("값",)
        self.grid_tree["columns"] = columns
        
        # 컬럼 헤딩 업데이트
        for col in columns:
            self.grid_tree.heading(col, text=col, anchor="center")
            self.grid_tree.column(col, width=150, anchor="center")
        
        # 계층별 스타일 태그 설정
        # 모듈 레벨 - 가장 크고 굵게 (기본 파란색)
        self.grid_tree.tag_configure("module", 
                                    font=("Arial", 11, "bold"), 
                                    background="#F5F5F5", 
                                    foreground="#1565C0")
        
        # 모듈 레벨 - 차이 있음 (빨간색 강조)
        self.grid_tree.tag_configure("module_diff", 
                                    font=("Arial", 11, "bold"), 
                                    background="#F5F5F5", 
                                    foreground="#D32F2F")
        
        # 파트 레벨 - 중간 크기, 볼드
        self.grid_tree.tag_configure("part", 
                                    font=("Arial", 10, "bold"), 
                                    background="#FAFAFA", 
                                    foreground="#424242")
        
        # 파트 레벨 - 모든 값 동일 (초록색)
        self.grid_tree.tag_configure("part_clean", 
                                    font=("Arial", 10, "bold"), 
                                    background="#FAFAFA", 
                                    foreground="#2E7D32")
        
        # 파트 레벨 - 차이 있음 (빨간색 강조)
        self.grid_tree.tag_configure("part_diff", 
                                    font=("Arial", 10, "bold"), 
                                    background="#FAFAFA", 
                                    foreground="#D32F2F")
        

        
        # 파라미터 레벨 - 기본 크기
        self.grid_tree.tag_configure("parameter_same", 
                                    font=("Arial", 9), 
                                    background="white", 
                                    foreground="black")
        
        # 차이점이 있는 파라미터 - 전체 목록 탭과 동일한 색상
        self.grid_tree.tag_configure("parameter_different", 
                                    font=("Arial", 9), 
                                    background="#FFECB3", 
                                    foreground="#E65100")
        
        # 계층 구조 데이터 구성
        modules_data = {}
        total_params = 0
        diff_count = 0
        
        grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
        
        for (module, part, item_name), group in grouped:
            if module not in modules_data:
                modules_data[module] = {}
            if part not in modules_data[module]:
                modules_data[module][part] = {}
            
            # 각 파일별 값 수집
            values = []
            for model in self.file_names:
                model_data = group[group["Model"] == model]
                if not model_data.empty:
                    values.append(str(model_data["ItemValue"].iloc[0]))
                else:
                    values.append("-")
            
            # 값 차이 확인 (빈 값 제외)
            non_empty_values = [v for v in values if v != "-"]
            has_difference = len(set(non_empty_values)) > 1 if len(non_empty_values) > 1 else False
            
            modules_data[module][part][item_name] = {
                "values": values,
                "has_difference": has_difference
            }
            total_params += 1
            if has_difference:
                diff_count += 1
        
        # 트리뷰에 계층 구조로 데이터 추가
        for module_name in sorted(modules_data.keys()):
            # 모듈 레벨 통계 계산
            module_total = sum(len(modules_data[module_name][part]) for part in modules_data[module_name])
            module_diff = sum(1 for part in modules_data[module_name] 
                            for item in modules_data[module_name][part] 
                            if modules_data[module_name][part][item]["has_difference"])
            
            # 모듈 표시 - 파란색 통일
            if module_diff == 0:
                module_text = f"📁 {module_name} ({module_total})"
            else:
                module_text = f"📁 {module_name} ({module_total}) Diff: {module_diff}"
            module_tag = "module"
            
            # 모듈 노드 추가
            module_node = self.grid_tree.insert("", "end", 
                                               text=module_text, 
                                               values=[""] * len(columns), 
                                               open=True,
                                               tags=(module_tag,))
            
            for part_name in sorted(modules_data[module_name].keys()):
                # 파트 레벨 통계 계산
                part_total = len(modules_data[module_name][part_name])
                part_diff = sum(1 for item in modules_data[module_name][part_name] 
                              if modules_data[module_name][part_name][item]["has_difference"])
                
                # 파트 표시 - 차이가 없으면 초록색, 있으면 회색
                if part_diff == 0:
                    part_text = f"📂 {part_name} ({part_total})"
                    part_tag = "part_clean"
                else:
                    part_text = f"📂 {part_name} ({part_total}) Diff: {part_diff}"
                    part_tag = "part_diff"
                
                # 파트 노드 추가
                part_node = self.grid_tree.insert(module_node, "end", 
                                                 text=part_text, 
                                                 values=[""] * len(columns), 
                                                 open=True,
                                                 tags=(part_tag,))
                
                for item_name in sorted(modules_data[module_name][part_name].keys()):
                    # 파라미터 노드 추가 - 기본 크기, 차이점에 따라 색상 구분
                    item_data = modules_data[module_name][part_name][item_name]
                    values = item_data["values"]
                    has_difference = item_data["has_difference"]
                    
                    # 태그 선택
                    tag = "parameter_different" if has_difference else "parameter_same"
                    
                    self.grid_tree.insert(part_node, "end", 
                                        text=item_name, 
                                        values=values, 
                                        tags=(tag,))
        
        # 통계 정보 업데이트
        if hasattr(self, 'grid_total_label'):
            self.grid_total_label.config(text=f"총 파라미터: {total_params}")
            self.grid_modules_label.config(text=f"모듈 수: {len(modules_data)}")
            
            total_parts = sum(len(parts) for parts in modules_data.values())
            self.grid_parts_label.config(text=f"파트 수: {total_parts}")
            
            # 차이점 개수도 표시
            if hasattr(self, 'grid_diff_label'):
                self.grid_diff_label.config(text=f"값이 다른 항목: {diff_count}")

    def create_comparison_tab(self):
        comparison_frame = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(comparison_frame, text="📋 전체 목록")
        style = ttk.Style()
        style.configure("Custom.Treeview", rowheight=22)
        
        # 상단 검색 및 제어 패널
        top_frame = ttk.Frame(comparison_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 검색 기능 추가 (좌측)
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(search_frame, text="ItemName 검색:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        self.search_clear_btn = ttk.Button(search_frame, text="지우기", command=self.clear_search, width=8)
        self.search_clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 검색 결과 정보
        self.search_result_label = ttk.Label(search_frame, text="", foreground="blue")
        self.search_result_label.pack(side=tk.LEFT, padx=(5, 0))
        
        control_frame = ttk.Frame(comparison_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        if self.maint_mode:
            self.select_all_var = tk.BooleanVar(value=False)
            self.select_all_cb = ttk.Checkbutton(
                control_frame,
                text="모두 선택",
                variable=self.select_all_var,
                command=self.toggle_select_all_checkboxes
            )
            self.select_all_cb.pack(side=tk.LEFT, padx=5)
        if self.maint_mode:
            self.selected_count_label = ttk.Label(control_frame, text="선택된 항목: 0개")
            self.selected_count_label.pack(side=tk.RIGHT, padx=10)
            self.send_to_default_btn = ttk.Button(
                control_frame,
                text="Default DB로 전송",
                command=self.add_to_default_db
            )
            self.send_to_default_btn.pack(side=tk.RIGHT, padx=10)
        else:
            self.diff_count_label = ttk.Label(control_frame, text="값이 다른 항목: 0개")
            self.diff_count_label.pack(side=tk.RIGHT, padx=10)
        self.item_checkboxes = {}
        if self.maint_mode:
            columns = ["Checkbox", "Module", "Part", "ItemName"] + self.file_names
        else:
            columns = ["Module", "Part", "ItemName"] + self.file_names
        self.comparison_tree = ttk.Treeview(comparison_frame, selectmode="extended", style="Custom.Treeview")
        self.comparison_tree["columns"] = columns
        self.comparison_tree.heading("#0", text="", anchor="w")
        self.comparison_tree.column("#0", width=0, stretch=False)
        col_offset = 0
        if self.maint_mode:
            self.comparison_tree.heading("Checkbox", text="선택")
            self.comparison_tree.column("Checkbox", width=50, anchor="center")
            col_offset = 1
        for idx, col in enumerate(["Module", "Part", "ItemName"]):
            self.comparison_tree.heading(col, text=col, anchor="w")
            self.comparison_tree.column(col, width=100)
        for model in self.file_names:
            self.comparison_tree.heading(model, text=model, anchor="w")
            self.comparison_tree.column(model, width=150)
        v_scroll = ttk.Scrollbar(comparison_frame, orient="vertical", 
                                command=self.comparison_tree.yview)
        h_scroll = ttk.Scrollbar(comparison_frame, orient="horizontal", 
                                command=self.comparison_tree.xview)
        self.comparison_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.comparison_tree.pack(expand=True, fill=tk.BOTH)
        self.comparison_tree.bind("<<TreeviewSelect>>", self.update_selected_count)
        self.create_comparison_context_menu()
        if not self.maint_mode:
            self.update_comparison_context_menu_state()
        self.update_comparison_view()

    def add_to_default_db(self):
        """체크된 항목들을 Default DB로 전송 - 중복도 기반 통계 분석"""
        if not self.maint_mode:
            messagebox.showwarning("권한 없음", "유지보수 모드에서만 Default DB에 항목을 추가할 수 있습니다.")
            return

        # 체크된 항목들 수집
        selected_items = []
        if any(self.item_checkboxes.values()):
            # 체크박스가 하나라도 선택된 경우
            for item_key, is_checked in self.item_checkboxes.items():
                if is_checked:
                    # item_key에서 module, part, item_name 분리
                    parts = item_key.split('_')
                    if len(parts) >= 3:
                        module, part, item_name = parts[0], parts[1], '_'.join(parts[2:])
                        
                        # 트리뷰에서 해당 항목 찾기
                        for child_id in self.comparison_tree.get_children():
                            values = self.comparison_tree.item(child_id, 'values')
                            if len(values) >= 4 and values[1] == module and values[2] == part and values[3] == item_name:
                                selected_items.append(child_id)
                                break
        else:
            # 체크박스가 선택되지 않은 경우, 트리뷰에서 직접 선택된 항목 사용
            selected_items = self.comparison_tree.selection()

        if not selected_items:
            messagebox.showwarning("선택 필요", "Default DB에 추가할 항목을 먼저 선택해주세요.")
            return

        # 장비 유형 선택 또는 새로 생성
        equipment_types = self.db_schema.get_equipment_types()
        type_names = [f"{name} (ID: {type_id})" for type_id, name, _ in equipment_types]
        
        # 고급 선택 다이얼로그
        dlg = tk.Toplevel(self.window)
        dlg.title("Default DB 추가 - 통계 기반 기준값 설정")
        dlg.geometry("700x600")
        dlg.transient(self.window)
        dlg.grab_set()
        
        # 부모 창 중앙에 배치
        from app.utils import center_dialog_on_parent
        center_dialog_on_parent(dlg, self.window)
        
        # 장비 유형 선택 프레임
        type_frame = ttk.LabelFrame(dlg, text="🔧 장비 유형 선택", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(type_frame, text="기존 장비 유형:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        selected_type = tk.StringVar()
        combo = ttk.Combobox(type_frame, textvariable=selected_type, values=type_names, state="readonly", width=40)
        combo.grid(row=0, column=1, padx=5, pady=5)
        if type_names:
            combo.set(type_names[0])
        
        ttk.Label(type_frame, text="또는 새 장비 유형:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        new_type_var = tk.StringVar()
        new_type_entry = ttk.Entry(type_frame, textvariable=new_type_var, width=40)
        new_type_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 통계 분석 설정
        stats_frame = ttk.LabelFrame(dlg, text="📊 통계 분석 설정 (중복도 기반 기준값 도출)", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        analyze_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(stats_frame, text="✓ 값의 중복도 분석 수행 (권장)", variable=analyze_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Label(stats_frame, text="신뢰도 임계값:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        confidence_var = tk.DoubleVar(value=50.0)
        confidence_scale = ttk.Scale(stats_frame, from_=0, to=100, variable=confidence_var, orient="horizontal", length=200)
        confidence_scale.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        confidence_label = ttk.Label(stats_frame, text="50.0% (과반수 이상)")
        confidence_label.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        def update_confidence_label(event=None):
            val = confidence_var.get()
            if val >= 80:
                desc = "매우 높음"
            elif val >= 60:
                desc = "높음" 
            elif val >= 40:
                desc = "보통"
            else:
                desc = "낮음"
            confidence_label.config(text=f"{val:.1f}% ({desc})")
        confidence_scale.configure(command=update_confidence_label)
        
        # 미리보기 영역
        preview_frame = ttk.LabelFrame(dlg, text="📋 추가될 항목 미리보기 및 통계", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        preview_text = tk.Text(preview_frame, height=12, wrap=tk.WORD, font=("Consolas", 9))
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_text.yview)
        preview_text.configure(yscrollcommand=preview_scroll.set)
        
        preview_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        preview_text.pack(fill=tk.BOTH, expand=True)
        
        def update_preview():
            """미리보기 업데이트"""
            preview_text.delete(1.0, tk.END)
            
            if not analyze_var.get():
                preview_text.insert(tk.END, f"📋 단순 추가 모드\n")
                preview_text.insert(tk.END, f"총 {len(selected_items)}개 항목을 첫 번째 파일 값으로 추가합니다.\n\n")
                for item_id in selected_items[:10]:  # 처음 10개만 미리보기
                    item_values = self.comparison_tree.item(item_id, "values")
                    col_offset = 1 if self.maint_mode else 0
                    module, part, item_name = item_values[col_offset], item_values[col_offset+1], item_values[col_offset+2]
                    value = item_values[col_offset+3]
                    preview_text.insert(tk.END, f"  • {part}_{item_name}: {value}\n")
                if len(selected_items) > 10:
                    preview_text.insert(tk.END, f"  ... 및 {len(selected_items)-10}개 더\n")
                return
            
            # 통계 분석 수행
            try:
                stats_analysis = self.analyze_parameter_statistics(selected_items)
                
                preview_text.insert(tk.END, f"📊 === 통계 분석 결과 ===\n")
                preview_text.insert(tk.END, f"분석된 파라미터: {len(stats_analysis)}개\n")
                preview_text.insert(tk.END, f"전체 파일 수: {len(self.file_names)}개\n")
                preview_text.insert(tk.END, f"파일 목록: {', '.join(self.file_names)}\n\n")
                
                high_confidence = 0
                medium_confidence = 0
                low_confidence = 0
                threshold = confidence_var.get() / 100.0
                
                for param_name, stats in stats_analysis.items():
                    confidence = stats['confidence_score']
                    if confidence >= threshold:
                        high_confidence += 1
                        status = "✅ 추가됨"
                        color_tag = "high"
                    elif confidence >= 0.3:
                        medium_confidence += 1
                        status = "⚠️ 중간 신뢰도"
                        color_tag = "medium"
                    else:
                        low_confidence += 1
                        status = "❌ 낮은 신뢰도"
                        color_tag = "low"
                    
                    # 값 분포 정보
                    value_info = f"{stats['most_common_value']}"
                    if stats['unique_values'] > 1:
                        value_info += f" (총 {stats['unique_values']}가지 값)"
                    
                    preview_text.insert(tk.END, f"{param_name}:\n")
                    preview_text.insert(tk.END, f"  기준값: {value_info}\n")
                    preview_text.insert(tk.END, f"  신뢰도: {confidence*100:.1f}% ({stats['occurrence_count']}/{stats['total_files']})\n")
                    
                    if stats['is_numeric']:
                        preview_text.insert(tk.END, f"  수치범위: {stats['min']:.3f} ~ {stats['max']:.3f}\n")
                        preview_text.insert(tk.END, f"  평균±표준편차: {stats['mean']:.3f} ± {stats['std']:.3f}\n")
                    
                    preview_text.insert(tk.END, f"  상태: {status}\n\n")
                
                preview_text.insert(tk.END, f"📈 === 요약 ===\n")
                preview_text.insert(tk.END, f"추가될 항목 (신뢰도 ≥{confidence_var.get():.1f}%): {high_confidence}개\n")
                preview_text.insert(tk.END, f"중간 신뢰도 (30-{confidence_var.get():.1f}%): {medium_confidence}개\n") 
                preview_text.insert(tk.END, f"제외될 항목 (<30%): {low_confidence}개\n")
                
            except Exception as e:
                preview_text.insert(tk.END, f"❌ 통계 분석 오류: {str(e)}")
        
        # 버튼 프레임
        button_frame = ttk.Frame(dlg)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="🔄 미리보기 업데이트", command=update_preview).pack(side=tk.LEFT, padx=5)
        
        def show_duplicate_check():
            """중복 검사 다이얼로그 표시"""
            duplicate_analysis = self.get_duplicate_analysis(selected_items)
            self.show_duplicate_analysis_dialog(duplicate_analysis)
        
        ttk.Button(button_frame, text="🔍 중복 검사", command=show_duplicate_check).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ 취소", command=dlg.destroy).pack(side=tk.RIGHT, padx=5)
        
        def on_confirm():
            # 장비 유형 결정
            if new_type_var.get().strip():
                # 새 장비 유형 생성
                type_name = new_type_var.get().strip()
                type_id = self.db_schema.add_equipment_type(type_name, f"다중 모델 비교를 통해 자동 생성된 장비 유형")
                self.update_log(f"새 장비 유형 생성: {type_name} (ID: {type_id})")
                
                # 변경 이력 기록
                self.db_schema.log_change_history(
                    "add", "equipment_type", type_name, "", 
                    f"multi-model comparison based", "admin"
                )
                
            elif selected_type.get():
                # 기존 장비 유형 사용
                type_id_str = selected_type.get().split("ID: ")[1][:-1]
                type_id = int(type_id_str)
                type_name = selected_type.get().split(" (ID:")[0]
            else:
                messagebox.showerror("오류", "장비 유형을 선택하거나 새로 입력해주세요.")
                return
            
            # 실제 DB 추가 로직
            try:
                if analyze_var.get():
                    # 통계 기반 추가
                    stats_analysis = self.analyze_parameter_statistics(selected_items)
                    added_count, updated_count, skipped_count = self.add_parameters_with_statistics(
                        type_id, stats_analysis, confidence_var.get() / 100.0
                    )
                    
                    result_msg = (f"🎯 통계 기반 Default DB 추가 완료:\n\n"
                                 f"📊 분석된 파라미터: {len(stats_analysis)}개\n"
                                 f"✅ 새로 추가: {added_count}개\n"
                                 f"🔄 업데이트: {updated_count}개\n"
                                 f"❌ 낮은 신뢰도로 제외: {skipped_count}개\n\n"
                                 f"💡 신뢰도 기준: {confidence_var.get():.1f}%")
                else:
                    # 단순 추가
                    added_count = self.add_parameters_simple(type_id, selected_items)
                    result_msg = f"📋 단순 추가 완료:\n\n총 {added_count}개의 항목이 Default DB에 추가되었습니다."
                
                # 종합 변경 이력 기록
                total_changes = added_count + (updated_count if analyze_var.get() else 0)
                self.db_schema.log_change_history(
                    "bulk_add", "parameter", f"{type_name}_bulk_operation", 
                    "", f"Added/Updated {total_changes} parameters via multi-model analysis", "admin"
                )
                
                messagebox.showinfo("✅ 작업 완료", result_msg)
                dlg.destroy()
                self.update_comparison_view() # UI 갱신
                
                # Default DB 관리 탭이 있으면 업데이트
                if hasattr(self, 'default_db_tree') and hasattr(self, 'equipment_type_combo'):
                    self.refresh_equipment_types()
                    # 방금 추가한 장비 유형이 선택되도록 설정
                    type_names = self.equipment_type_combo['values']
                    for type_name in type_names:
                        if type_name.startswith(type_name.split(" (ID:")[0]):
                            self.equipment_type_combo.set(type_name)
                            self.on_equipment_type_selected()
                            break
                
            except Exception as e:
                messagebox.showerror("❌ 오류", f"Default DB 추가 중 오류 발생:\n{str(e)}")
                self.update_log(f"Default DB 추가 오류: {str(e)}")

        ttk.Button(button_frame, text="✅ Default DB에 추가", command=on_confirm).pack(side=tk.RIGHT, padx=5)
        
        # 초기 미리보기 업데이트
        self.window.after(100, update_preview)

    def analyze_parameter_statistics(self, selected_items):
        """
        선택된 파라미터들의 통계 분석을 수행합니다.
        중복도 기반으로 가장 적합한 기준값을 결정합니다.
        
        Args:
            selected_items: 선택된 트리뷰 아이템 ID 리스트
            
        Returns:
            dict: 파라미터별 통계 정보
        """
        stats_analysis = {}
        
        for item_id in selected_items:
            item_values = self.comparison_tree.item(item_id, "values")
            
            # 유지보수 모드 여부에 따라 인덱스 조정
            col_offset = 1 if self.maint_mode else 0
            module, part, item_name = item_values[col_offset], item_values[col_offset+1], item_values[col_offset+2]
            
            param_name = f"{part}_{item_name}"
            
            # 모든 파일에서 해당 파라미터의 값 수집
            file_values = []
            for i, model in enumerate(self.file_names):
                if col_offset + 3 + i < len(item_values):
                    value = item_values[col_offset + 3 + i]
                    if value and value != "-":
                        file_values.append(str(value))
            
            if not file_values:
                continue
            
            # 값별 빈도 계산
            from collections import Counter
            value_counts = Counter(file_values)
            total_files = len(file_values)
            
            # 가장 빈번한 값 선택
            most_common_value, occurrence_count = value_counts.most_common(1)[0]
            confidence_score = occurrence_count / total_files
            
            # 수치값인 경우 통계 정보 추가 계산
            numeric_values = []
            for val in file_values:
                try:
                    numeric_values.append(float(val))
                except (ValueError, TypeError):
                    pass
            
            stats_info = {
                'param_name': param_name,
                'module': module,
                'part': part,
                'item_name': item_name,
                'all_values': file_values,
                'value_counts': dict(value_counts),
                'most_common_value': most_common_value,
                'occurrence_count': occurrence_count,
                'total_files': total_files,
                'confidence_score': confidence_score,
                'unique_values': len(value_counts),
                'source_files': ','.join(self.file_names[:len(file_values)])
            }
            
            # 수치 통계 추가
            if numeric_values:
                import numpy as np
                stats_info.update({
                    'is_numeric': True,
                    'mean': np.mean(numeric_values),
                    'std': np.std(numeric_values),
                    'min': np.min(numeric_values),
                    'max': np.max(numeric_values),
                    'cv': np.std(numeric_values) / np.mean(numeric_values) if np.mean(numeric_values) != 0 else 0
                })
            else:
                stats_info['is_numeric'] = False
            
            stats_analysis[param_name] = stats_info
        
        return stats_analysis

    def add_parameters_with_statistics(self, type_id, stats_analysis, confidence_threshold=0.5):
        """
        통계 분석 결과를 바탕으로 파라미터를 Default DB에 추가합니다.
        
        Args:
            type_id: 장비 유형 ID
            stats_analysis: analyze_parameter_statistics 결과
            confidence_threshold: 신뢰도 임계값 (0.0 ~ 1.0)
            
        Returns:
            tuple: (추가된 개수, 업데이트된 개수, 제외된 개수)
        """
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for param_name, stats in stats_analysis.items():
            if stats['confidence_score'] < confidence_threshold:
                skipped_count += 1
                self.update_log(f"'{param_name}' 제외 - 낮은 신뢰도: {stats['confidence_score']*100:.1f}%")
                continue
            
            try:
                # 기존 항목 확인
                existing_stats = self.db_schema.get_parameter_statistics(type_id, param_name)
                
                # 최소/최대 사양 계산 (수치인 경우)
                min_spec = None
                max_spec = None
                if stats['is_numeric']:
                    # 평균 ± 2σ 범위를 사양으로 설정
                    mean = stats['mean']
                    std = stats['std']
                    min_spec = str(round(mean - 2 * std, 3))
                    max_spec = str(round(mean + 2 * std, 3))
                
                record_id = self.db_schema.add_default_value(
                    type_id, 
                    param_name, 
                    stats['most_common_value'],
                    min_spec,
                    max_spec,
                    stats['occurrence_count'],
                    stats['total_files'],
                    stats['source_files']
                )
                
                if existing_stats:
                    updated_count += 1
                    self.update_log(f"'{param_name}' 업데이트 완료 - 신뢰도: {stats['confidence_score']*100:.1f}%")
                else:
                    added_count += 1
                    self.update_log(f"'{param_name}' 추가 완료 - 신뢰도: {stats['confidence_score']*100:.1f}%")
                
            except Exception as e:
                skipped_count += 1
                self.update_log(f"'{param_name}' 처리 실패: {e}")
        
        return added_count, updated_count, skipped_count

    def add_parameters_simple(self, type_id, selected_items):
        """
        간단한 방식으로 파라미터를 Default DB에 추가합니다.
        첫 번째 파일의 값을 기준값으로 사용합니다.
        
        Args:
            type_id: 장비 유형 ID
            selected_items: 선택된 트리뷰 아이템 ID 리스트
            
        Returns:
            int: 추가된 항목 개수
        """
        count = 0
        for item_id in selected_items:
            item_values = self.comparison_tree.item(item_id, "values")
            
            # 유지보수 모드 여부에 따라 인덱스 조정
            col_offset = 1 if self.maint_mode else 0
            module, part, item_name = item_values[col_offset], item_values[col_offset+1], item_values[col_offset+2]
            
            # 첫 번째 파일의 값을 사용
            value = item_values[col_offset+3] 
            
            param_name = f"{part}_{item_name}"
            
            try:
                record_id = self.db_schema.add_default_value(
                    type_id, param_name, value, None, None, 1, 1, self.file_names[0]
                )
                
                # 변경 이력 기록
                self.db_schema.log_change_history(
                    "add", "parameter", param_name, "", 
                    f"default: {value}, source: {self.file_names[0]}", "admin"
                )
                
                count += 1
                self.update_log(f"'{param_name}' 추가 성공 (ID: {record_id})")
            except Exception as e:
                self.update_log(f"'{param_name}' 추가 실패: {e}")
        
        return count

    def on_search_changed(self, event=None):
        """검색어 변경 시 필터링"""
        search_text = self.search_var.get().lower().strip()
        self.update_comparison_view(search_filter=search_text)
    
    def clear_search(self):
        """검색 입력창 지우기"""
        self.search_var.set("")
        self.update_comparison_view(search_filter="")

    def toggle_select_all_checkboxes(self):
        if not self.maint_mode:
            return
        check = self.select_all_var.get()
        for item in self.comparison_tree.get_children():
            values = list(self.comparison_tree.item(item, "values"))
            if len(values) > 0:
                values[0] = "☑" if check else "☐"
                self.comparison_tree.item(item, values=values)
                module, part, item_name = values[1], values[2], values[3]
                item_key = f"{module}_{part}_{item_name}"
                self.item_checkboxes[item_key] = check
        self.update_checked_count()

    def update_comparison_view(self, search_filter=""):
        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)
        
        saved_checkboxes = self.item_checkboxes.copy()
        self.item_checkboxes.clear()
        
        if self.maint_mode:
            self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
        else:
            self.comparison_tree.unbind("<ButtonRelease-1>")
        
        diff_count = 0
        total_items = 0
        filtered_items = 0
        
        if self.merged_df is not None:
            # 파라미터별로 그룹화하여 비교
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            
            for (module, part, item_name), group in grouped:
                total_items += 1
                
                # 검색 필터링 적용
                if search_filter and search_filter not in item_name.lower():
                    continue
                
                filtered_items += 1
                
                values = []
                
                if self.maint_mode:
                    checkbox_state = "☐"
                    item_key = f"{module}_{part}_{item_name}"
                    if item_key in saved_checkboxes and saved_checkboxes[item_key]:
                        checkbox_state = "☑"
                    self.item_checkboxes[item_key] = (checkbox_state == "☑")
                    values.append(checkbox_state)
                
                values.extend([module, part, item_name])
                
                # 각 파일별 값 추출 및 비교
                file_values = []
                for model in self.file_names:
                    model_data = group[group["Model"] == model]
                    if not model_data.empty:
                        value = model_data["ItemValue"].iloc[0]
                        file_values.append(str(value))
                    else:
                        file_values.append("-")
                
                values.extend(file_values)
                
                # 차이점 검사 - 모든 값이 동일한지 확인
                unique_values = set(v for v in file_values if v != "-")
                has_difference = len(unique_values) > 1
                
                tags = []
                if has_difference:
                    tags.append("different")
                    diff_count += 1
                
                # Default DB에 존재하는지 확인
                is_existing = self.check_if_parameter_exists(module, part, item_name)
                if is_existing:
                    tags.append("existing")
                
                self.comparison_tree.insert("", "end", values=values, tags=tuple(tags))
            
            # 스타일 설정
            self.comparison_tree.tag_configure("different", background="#FFECB3", foreground="#E65100")
            self.comparison_tree.tag_configure("existing", foreground="#1976D2")
            
            if self.maint_mode:
                self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
            
            self.update_selected_count(None)
        
        # 차이점 카운트 업데이트
        if not self.maint_mode and hasattr(self, 'diff_count_label'):
            self.diff_count_label.config(text=f"값이 다른 항목: {diff_count}개")
        
        # 검색 결과 표시 업데이트
        if hasattr(self, 'search_result_label'):
            if search_filter:
                self.search_result_label.config(text=f"검색 결과: {filtered_items}개 (전체: {total_items}개)")
            else:
                self.search_result_label.config(text="")

    def create_comparison_context_menu(self):
        self.comparison_context_menu = tk.Menu(self.window, tearoff=0)
        self.comparison_context_menu.add_command(label="선택한 항목을 Default DB에 추가", command=self.add_to_default_db)
        self.comparison_tree.bind("<Button-3>", self.show_comparison_context_menu)
        self.update_comparison_context_menu_state()

    def show_comparison_context_menu(self, event):
        if not self.maint_mode:
            return
        if not self.comparison_tree.selection():
            return
        try:
            self.comparison_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.comparison_context_menu.grab_release()

    def update_comparison_context_menu_state(self):
        if hasattr(self, 'comparison_context_menu'):
            state = "normal" if self.maint_mode else "disabled"
            try:
                self.comparison_context_menu.entryconfig("선택한 항목을 Default DB에 추가", state=state)
            except Exception as e:
                self.update_log(f"컨텍스트 메뉴 상태 업데이트 중 오류 발생: {str(e)}")

    def toggle_checkbox(self, event):
        if not self.maint_mode:
            return
        region = self.comparison_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.comparison_tree.identify_column(event.x)
        if column != "#1":
            return
        item = self.comparison_tree.identify_row(event.y)
        if not item:
            return
        values = self.comparison_tree.item(item, "values")
        if not values or len(values) < 4:
            return
        current_state = values[0]
        module, part, item_name = values[1], values[2], values[3]
        item_key = f"{module}_{part}_{item_name}"
        new_state = "☑" if current_state == "☐" else "☐"
        self.item_checkboxes[item_key] = (new_state == "☑")
        new_values = list(values)
        new_values[0] = new_state
        self.comparison_tree.item(item, values=new_values)
        self.update_checked_count()

    def update_selected_count(self, event):
        if not self.maint_mode:
            return
        checked_count = sum(1 for checked in self.item_checkboxes.values() if checked)
        if checked_count > 0:
            self.selected_count_label.config(text=f"체크된 항목: {checked_count}개")
        else:
            selected_items = self.comparison_tree.selection()
            count = len(selected_items)
            self.selected_count_label.config(text=f"선택된 항목: {count}개")

    def update_checked_count(self):
        if not self.maint_mode:
            return
        checked_count = sum(1 for checked in self.item_checkboxes.values() if checked)
        self.selected_count_label.config(text=f"체크된 항목: {checked_count}개")

    def check_if_parameter_exists(self, module, part, item_name):
        try:
            equipment_types = self.db_schema.get_equipment_types()
            for type_id, type_name, _ in equipment_types:
                if type_name.lower() == module.lower():
                    default_values = self.db_schema.get_default_values(type_id)
                    for _, param_name, _, _, _, _ in default_values:
                        if param_name == f"{part}_{item_name}" or param_name == item_name:
                            return True
            return False
        except Exception as e:
            self.update_log(f"DB_ItemName 존재 여부 확인 중 오류: {str(e)}")
            return False

    def disable_maint_features(self):
        """유지보수 모드 비활성화 - QC 엔지니어용 탭들을 제거합니다."""
        # QC 엔지니어용 탭들 제거
        if hasattr(self, 'main_notebook'):
            tabs_to_remove = []
            for tab_id in range(self.main_notebook.index('end')):
                tab_text = self.main_notebook.tab(tab_id, 'text')
                if tab_text in ["Default DB 관리", "QC 검수", "변경 이력 관리"]:
                    tabs_to_remove.append(tab_id)
            
            # 역순으로 제거 (인덱스 변경 방지)
            for tab_id in reversed(tabs_to_remove):
                self.main_notebook.forget(tab_id)
        
        # QC 엔지니어용 탭 프레임 참조 제거
        self.qc_check_frame = None
        self.default_db_frame = None
        self.change_history_frame = None
        
        # QC 노트북 참조 제거
        if hasattr(self, 'qc_notebook'):
            del self.qc_notebook

    def create_qc_check_tab(self):
        """QC 검수 탭 생성 - 완전한 기능 구현"""
        if self.qc_check_frame is not None:
            return  # 이미 생성된 경우 중복 생성 방지
            
        self.qc_check_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.qc_check_frame, text="QC 검수")
        
        # 🆕 src/app/qc.py의 완전한 QC 탭 기능 사용
        # 기존 기본 탭 대신 고급 QC 기능이 포함된 탭 생성
        
        # 상단 컨트롤 프레임
        control_frame = ttk.Frame(self.qc_check_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 장비 유형 선택 프레임
        type_frame = ttk.LabelFrame(control_frame, text="장비 유형 선택", padding=10)
        type_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # 장비 유형 콤보박스
        ttk.Label(type_frame, text="장비 유형:").pack(side=tk.LEFT, padx=(0, 5))
        self.qc_type_var = tk.StringVar()
        self.qc_type_combobox = ttk.Combobox(type_frame, textvariable=self.qc_type_var, state="readonly", width=20)
        self.qc_type_combobox.pack(side=tk.LEFT, padx=(0, 10))

        # 🆕 새로고침 버튼 추가
        refresh_btn = ttk.Button(type_frame, text="🔄 목록 새로고침", command=self.refresh_qc_equipment_types)
        refresh_btn.pack(side=tk.LEFT, padx=(5, 10))

        # QC 실행 버튼
        qc_btn = ttk.Button(type_frame, text="QC 검수 실행", command=self.perform_qc_check)
        qc_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 검수 결과 프레임
        middle_frame = ttk.LabelFrame(self.qc_check_frame, text="검수 결과", padding=10)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 검수 결과 트리뷰
        from app.widgets import create_treeview_with_scrollbar
        
        columns = ("parameter", "issue_type", "description", "severity")
        headings = {
            "parameter": "파라미터", 
            "issue_type": "문제 유형", 
            "description": "설명", 
            "severity": "심각도"
        }
        column_widths = {
            "parameter": 200, 
            "issue_type": 150, 
            "description": 300, 
            "severity": 100
        }

        qc_result_frame, self.qc_result_tree = create_treeview_with_scrollbar(
            middle_frame, columns, headings, column_widths, height=15)
        qc_result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 검수 통계 프레임
        bottom_frame = ttk.LabelFrame(self.qc_check_frame, text="검수 통계", padding=10)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.stats_frame = ttk.Frame(bottom_frame)
        self.stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.chart_frame = ttk.Frame(bottom_frame)
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 장비 유형 목록 로드
        self.load_equipment_types_for_qc()
        
        self.update_log("✅ 완전한 기능의 QC 검수 탭 생성 완료")

    def create_default_db_tab(self):
        """Default DB 관리 탭 생성"""
        try:
            self.update_log("🔧 Default DB 관리 탭 생성 시작...")
            
            if self.default_db_frame is not None:
                self.update_log("⚠️ Default DB 탭이 이미 존재함 - 중복 생성 방지")
                return  # 이미 생성된 경우 중복 생성 방지
            
            # DBSchema 확인
            if not self.db_schema:
                self.update_log("❌ DBSchema가 초기화되지 않음 - 탭 생성 취소")
                return
                
            self.default_db_frame = ttk.Frame(self.main_notebook)
            self.main_notebook.add(self.default_db_frame, text="Default DB 관리")
            self.update_log("✅ Default DB 탭 프레임 생성 완료")
            
            # 상단 제어 패널
            control_frame = ttk.Frame(self.default_db_frame)
            control_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # 장비 유형 관리 섹션
            equipment_frame = ttk.LabelFrame(control_frame, text="🔧 장비 유형 관리", padding=10)
            equipment_frame.pack(fill=tk.X, pady=5)
            
            # 장비 유형 선택
            ttk.Label(equipment_frame, text="장비 유형:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            self.equipment_type_var = tk.StringVar()
            self.equipment_type_combo = ttk.Combobox(equipment_frame, textvariable=self.equipment_type_var, 
                                                   state="readonly", width=30)
            self.equipment_type_combo.grid(row=0, column=1, padx=5, pady=5)
            self.equipment_type_combo.bind("<<ComboboxSelected>>", self.on_equipment_type_selected)
            self.update_log("✅ 장비 유형 콤보박스 생성 완료")
            
            # 장비 유형 관리 버튼들
            ttk.Button(equipment_frame, text="새 장비 유형 추가", 
                      command=self.add_equipment_type_dialog).grid(row=0, column=2, padx=5, pady=5)
            ttk.Button(equipment_frame, text="삭제", 
                      command=self.delete_equipment_type).grid(row=0, column=3, padx=5, pady=5)
            ttk.Button(equipment_frame, text="새로고침", 
                      command=self.refresh_equipment_types).grid(row=0, column=4, padx=5, pady=5)
            
            # 파라미터 관리 섹션
            param_frame = ttk.LabelFrame(control_frame, text="📊 파라미터 관리", padding=10)
            param_frame.pack(fill=tk.X, pady=5)
            
            # 파라미터 관리 버튼들
            ttk.Button(param_frame, text="파라미터 추가", 
                      command=self.add_parameter_dialog).pack(side=tk.LEFT, padx=5)
            ttk.Button(param_frame, text="선택 항목 삭제", 
                      command=self.delete_selected_parameters).pack(side=tk.LEFT, padx=5)
            ttk.Button(param_frame, text="Excel로 내보내기", 
                      command=self.export_default_db_to_excel).pack(side=tk.LEFT, padx=5)
            ttk.Button(param_frame, text="Excel에서 가져오기", 
                      command=self.import_default_db_from_excel).pack(side=tk.LEFT, padx=5)
            
            # 파라미터 목록 트리뷰
            tree_frame = ttk.Frame(self.default_db_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 트리뷰 생성 (순차 번호 컬럼으로 변경)
            columns = ("no", "parameter_name", "default_value", "min_spec", "max_spec", 
                      "occurrence_count", "total_files", "confidence_score", "source_files", "description")

            self.default_db_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
            self.update_log("✅ Default DB 트리뷰 생성 완료")

            # 컬럼 헤더 설정
            headers = {
                "no": "No.",  # 순차 번호 컬럼
                "parameter_name": "파라미터명",
                "default_value": "설정값",  # 🔄 "기본값" → "설정값"으로 변경
                "min_spec": "최소값",
                "max_spec": "최대값",
                "occurrence_count": "발생횟수",
                "total_files": "전체파일",
                "confidence_score": "신뢰도(%)",
                "source_files": "소스파일",
                "description": "설명"  # 🆕 description 컬럼 추가
            }

            column_widths = {
                "no": 50,  # 순차 번호 컬럼 너비
                "parameter_name": 220,
                "default_value": 100,
                "min_spec": 80,
                "max_spec": 80,
                "occurrence_count": 80,
                "total_files": 80,
                "confidence_score": 80,
                "source_files": 150,
                "description": 150  # 🆕 description 컬럼 너비 추가
            }
            
            for col in columns:
                self.default_db_tree.heading(col, text=headers[col])
                self.default_db_tree.column(col, width=column_widths[col], minwidth=50)
            
            # 스크롤바 추가
            db_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.default_db_tree.yview)
            self.default_db_tree.configure(yscrollcommand=db_scrollbar.set)
            
            db_h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.default_db_tree.xview)
            self.default_db_tree.configure(xscrollcommand=db_h_scrollbar.set)
            
            # 배치
            self.default_db_tree.grid(row=0, column=0, sticky="nsew")
            db_scrollbar.grid(row=0, column=1, sticky="ns")
            db_h_scrollbar.grid(row=1, column=0, sticky="ew")
            
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # 더블클릭으로 편집
            self.default_db_tree.bind("<Double-1>", self.edit_parameter_dialog)
            
            # 상태 표시줄
            status_frame = ttk.Frame(self.default_db_frame)
            status_frame.pack(fill=tk.X, padx=10, pady=5)
            
            self.default_db_status_label = ttk.Label(status_frame, text="장비 유형을 선택하세요.")
            self.default_db_status_label.pack(side=tk.LEFT)
            self.update_log("✅ Default DB 상태 표시줄 생성 완료")
            
            # 초기 데이터 로드 (UI 초기화 완료 후 실행)
            self.window.after(200, self.refresh_equipment_types)
            
            # 디버깅을 위한 로그 추가
            self.update_log("✅ Default DB 관리 탭이 완전히 생성되었습니다.")
            
        except Exception as e:
            error_msg = f"Default DB 관리 탭 생성 오류: {e}"
            self.update_log(f"❌ {error_msg}")
            print(f"DEBUG - create_default_db_tab error: {e}")
            import traceback
            traceback.print_exc()

    def refresh_equipment_types(self):
        """장비 유형 목록을 새로고침합니다. (전체 탭 동기화)"""
        try:
            self.update_log("🔄 전체 장비 유형 목록 동기화 시작...")
            
            # DBSchema가 초기화되었는지 확인
            if not self.db_schema:
                self.update_log("❌ DBSchema가 초기화되지 않음")
                return
            
            # 최신 장비 유형 목록 조회
            equipment_types = self.db_schema.get_equipment_types()
            self.update_log(f"📊 조회된 장비 유형: {len(equipment_types)}개")
            
            # 1. Default DB 관리 탭 갱신
            self._refresh_default_db_equipment_types(equipment_types)
            
            # 2. QC 검수 탭 갱신  
            self._refresh_qc_equipment_types(equipment_types)
            
            # 3. defaultdb.py의 장비 유형 목록 갱신
            self._refresh_defaultdb_equipment_types(equipment_types)
            
            self.update_log("✅ 전체 장비 유형 목록 동기화 완료")
                
        except Exception as e:
            error_msg = f"장비 유형 동기화 오류: {e}"
            self.update_log(f"❌ {error_msg}")
            print(f"DEBUG - refresh_equipment_types error: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_default_db_equipment_types(self, equipment_types):
        """Default DB 관리 탭의 장비 유형 목록 갱신"""
        try:
            # manager.py의 Default DB 탭 콤보박스 갱신
            if hasattr(self, 'equipment_type_combo'):
                current_selection = self.equipment_type_var.get()
                type_names = [f"{name} (ID: {type_id})" for type_id, name, _ in equipment_types]
                
                self.equipment_type_combo['values'] = type_names
                
                # 현재 선택된 항목이 여전히 존재하는지 확인
                if current_selection and current_selection in type_names:
                    self.equipment_type_combo.set(current_selection)
                elif type_names:
                    self.equipment_type_combo.set(type_names[0])
                    self.on_equipment_type_selected()
                else:
                    self.equipment_type_var.set("")
                    self.update_default_db_display([])
                
                self.update_log(f"📋 Default DB 탭 콤보박스 갱신: {len(type_names)}개")
                
        except Exception as e:
            self.update_log(f"⚠️ Default DB 탭 갱신 실패: {e}")

    def _refresh_qc_equipment_types(self, equipment_types):
        """QC 검수 탭의 장비 유형 목록 갱신"""
        try:
            # QC 검수 탭 콤보박스 갱신
            if hasattr(self, 'qc_type_combobox') and hasattr(self, 'equipment_types_for_qc'):
                current_selection = getattr(self, 'qc_type_var', tk.StringVar()).get()
                
                # 장비 유형 딕셔너리 업데이트
                self.equipment_types_for_qc = {name: type_id for type_id, name, _ in equipment_types}
                type_names = list(self.equipment_types_for_qc.keys())
                
                self.qc_type_combobox['values'] = type_names
                
                # 현재 선택된 항목이 여전히 존재하는지 확인
                if current_selection and current_selection in type_names:
                    self.qc_type_combobox.set(current_selection)
                elif type_names:
                    self.qc_type_combobox.set(type_names[0])
                else:
                    if hasattr(self, 'qc_type_var'):
                        self.qc_type_var.set("")
                
                self.update_log(f"🔍 QC 검수 탭 콤보박스 갱신: {len(type_names)}개")
            
            # 🆕 QC 탭의 기본 장비 유형 로드 함수도 호출
            if hasattr(self, 'load_equipment_types_for_qc'):
                self.load_equipment_types_for_qc()
                self.update_log("🔍 QC 탭 load_equipment_types_for_qc 함수도 호출 완료")
                
        except Exception as e:
            self.update_log(f"⚠️ QC 검수 탭 갱신 실패: {e}")

    def _refresh_defaultdb_equipment_types(self, equipment_types):
        """defaultdb.py 모듈의 장비 유형 목록 갱신"""
        try:
            # defaultdb.py의 load_equipment_types 함수 호출
            if hasattr(self, 'load_equipment_types'):
                self.load_equipment_types()
                self.update_log("🗃️ defaultdb 모듈 장비 유형 갱신 완료")
                
            # defaultdb.py의 load_equipment_type_list도 갱신 (관리 대화상자용)
            # 이는 대화상자가 열려 있을 때만 필요하므로 별도 처리
                
        except Exception as e:
            self.update_log(f"⚠️ defaultdb 모듈 갱신 실패: {e}")

    def refresh_all_equipment_type_lists(self):
        """모든 탭의 장비 유형 목록을 강제로 새로고침 (외부 호출용)"""
        self.refresh_equipment_types()
        
        # 🆕 QC 탭도 강제 갱신
        try:
            if hasattr(self, 'load_equipment_types_for_qc'):
                self.load_equipment_types_for_qc()
                self.update_log("🔍 QC 탭 추가 갱신 완료")
        except Exception as e:
            self.update_log(f"⚠️ QC 탭 추가 갱신 실패: {e}")
        
        # 추가적으로 다른 모듈에서도 갱신이 필요한 경우
        try:
            # default_db_helpers.py의 update_equipment_type_list 호출
            if hasattr(self, 'update_equipment_type_list'):
                self.update_equipment_type_list()
                self.update_log("📋 default_db_helpers 모듈도 갱신 완료")
        except Exception as e:
            self.update_log(f"⚠️ default_db_helpers 갱신 실패: {e}")
        
        # 🆕 동기화 상태 확인
        self.update_log("🎯 전체 장비 유형 동기화 완료!")

    def on_equipment_type_selected(self, event=None):
        """장비 유형이 선택되었을 때 호출됩니다."""
        try:
            selected = self.equipment_type_var.get()
            self.update_log(f"🔄 장비 유형 선택됨: '{selected}'")
            
            if not selected:
                self.update_default_db_display([])
                self.update_log("⚠️ 선택된 장비 유형이 없음 - 빈 목록 표시")
                return
                
            # 장비 유형 ID 추출
            type_id_str = selected.split("ID: ")[1][:-1]
            type_id = int(type_id_str)
            self.update_log(f"🔍 추출된 장비 유형 ID: {type_id}")
            
            # 해당 장비 유형의 파라미터들 조회 (DBSchema 메서드 직접 사용)
            default_values = self.db_schema.get_default_values(type_id)
            self.update_log(f"📊 조회된 파라미터 수: {len(default_values)}개")
            
            if default_values:
                # 첫 번째 파라미터 정보 로그
                first_param = default_values[0]
                self.update_log(f"🔖 첫 번째 파라미터: {first_param[1]} = {first_param[2]}")
            
            self.update_default_db_display(default_values)
            self.update_log("✅ Default DB 화면 업데이트 완료")
            
        except Exception as e:
            error_msg = f"장비 유형 선택 처리 오류: {e}"
            self.update_log(f"❌ {error_msg}")
            print(f"DEBUG - on_equipment_type_selected error: {e}")
            import traceback
            traceback.print_exc()

    def update_default_db_display(self, default_values=None):
        """Default DB 파라미터 목록을 업데이트합니다."""
        try:
            self.update_log(f"🔄 Default DB 화면 업데이트 시작... (항목 수: {len(default_values) if default_values else 0})")
            
            # 기존 항목들 제거
            for item in self.default_db_tree.get_children():
                self.default_db_tree.delete(item)
            
            if default_values is None:
                self.update_log("⚠️ default_values가 None - 빈 화면 표시")
                return
                
            # 새 항목들 추가
            added_count = 0
            for record in default_values:
                # record 구조: (id, parameter_name, default_value, min_spec, max_spec, type_name, 
                #                occurrence_count, total_files, confidence_score, source_files, description)
                
                record_id = record[0]
                parameter_name = record[1]
                default_value = record[2]
                min_spec = record[3] if record[3] else ""
                max_spec = record[4] if record[4] else ""
                
                # 새 컬럼들 처리 (없을 수도 있음)
                try:
                    occurrence_count = record[6] if len(record) > 6 else 1
                    total_files = record[7] if len(record) > 7 else 1
                    confidence_score = record[8] if len(record) > 8 else 1.0
                    source_files = record[9] if len(record) > 9 else ""
                    description = record[10] if len(record) > 10 else ""  # 🆕 description 처리
                except IndexError:
                    occurrence_count = 1
                    total_files = 1
                    confidence_score = 1.0
                    source_files = ""
                    description = ""
                
                # 신뢰도를 퍼센트로 변환
                confidence_percent = f"{confidence_score * 100:.1f}"
                
                values = (record_id, parameter_name, default_value, min_spec, max_spec,
                         occurrence_count, total_files, confidence_percent, source_files, description)  # 🆕 description 추가
                
                self.default_db_tree.insert("", "end", values=values)
                added_count += 1
            
            # 상태 업데이트
            count = len(default_values)
            selected_type = self.equipment_type_var.get().split(" (ID:")[0] if self.equipment_type_var.get() else "선택없음"
            status_text = f"장비유형: {selected_type} | 파라미터: {count}개"
            self.default_db_status_label.config(text=status_text)
            
            self.update_log(f"✅ 트리뷰에 {added_count}개 항목 추가 완료")
            self.update_log(f"📊 상태표시줄 업데이트: {status_text}")
            
        except Exception as e:
            error_msg = f"Default DB 화면 업데이트 오류: {e}"
            self.update_log(f"❌ {error_msg}")
            print(f"DEBUG - update_default_db_display error: {e}")
            import traceback
            traceback.print_exc()

    def add_equipment_type_dialog(self):
        """새 장비 유형 추가 다이얼로그"""
        dlg = tk.Toplevel(self.window)
        dlg.title("새 장비 유형 추가")
        dlg.geometry("400x200")
        dlg.transient(self.window)
        dlg.grab_set()
        
        # 부모 창 중앙에 배치
        from app.loading import center_dialog_on_parent
        center_dialog_on_parent(dlg, self.window)
        
        ttk.Label(dlg, text="장비 유형 이름:").pack(pady=10)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dlg, textvariable=name_var, width=30)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        ttk.Label(dlg, text="설명 (선택사항):").pack(pady=10)
        desc_var = tk.StringVar()
        desc_entry = ttk.Entry(dlg, textvariable=desc_var, width=50)
        desc_entry.pack(pady=5)
        
        def on_add():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("오류", "장비 유형 이름을 입력해주세요.")
                return
            
            try:
                type_id = self.db_schema.add_equipment_type(name, desc_var.get().strip())
                self.update_log(f"새 장비 유형 추가: {name} (ID: {type_id})")
                
                # 변경 이력 기록
                self.db_schema.log_change_history("add", "equipment_type", name, "", desc_var.get(), "admin")
                
                # 목록 새로고침
                self.refresh_equipment_types()
                
                # 새로 추가된 항목 선택
                type_names = self.equipment_type_combo['values']
                for type_name in type_names:
                    if f"ID: {type_id}" in type_name:
                        self.equipment_type_combo.set(type_name)
                        self.on_equipment_type_selected()
                        break
                
                dlg.destroy()
                messagebox.showinfo("성공", f"장비 유형 '{name}'이 추가되었습니다.")
                
            except Exception as e:
                messagebox.showerror("오류", f"장비 유형 추가 실패:\n{str(e)}")
        
        button_frame = ttk.Frame(dlg)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="추가", command=on_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=dlg.destroy).pack(side=tk.LEFT, padx=5)

    def delete_equipment_type(self):
        """선택된 장비 유형을 삭제합니다."""
        selected = self.equipment_type_var.get()
        if not selected:
            messagebox.showwarning("경고", "삭제할 장비 유형을 선택해주세요.")
            return
        
        type_name = selected.split(" (ID:")[0]
        type_id_str = selected.split("ID: ")[1][:-1]
        type_id = int(type_id_str)
        
        # 확인 다이얼로그
        result = messagebox.askyesno("확인", 
                                   f"장비 유형 '{type_name}'과 관련된 모든 파라미터를 삭제하시겠습니까?\n"
                                   f"이 작업은 되돌릴 수 없습니다.")
        
        if result:
            try:
                # 관련 파라미터 수 확인
                default_values = self.db_schema.get_default_values(type_id)
                param_count = len(default_values)
                
                # 삭제 실행
                success = self.db_schema.delete_equipment_type(type_id)
                
                if success:
                    self.update_log(f"장비 유형 삭제: {type_name} (파라미터 {param_count}개 포함)")
                    
                    # 변경 이력 기록
                    self.db_schema.log_change_history("delete", "equipment_type", type_name, 
                                                    f"{param_count} parameters", "", "admin")
                    
                    # 🆕 전체 탭 동기화 - 모든 장비 유형 목록 새로고침
                    self.refresh_all_equipment_type_lists()
                    messagebox.showinfo("성공", f"장비 유형 '{type_name}'과 관련 파라미터 {param_count}개가 삭제되었습니다.")
                else:
                    messagebox.showerror("오류", "장비 유형 삭제에 실패했습니다.")
                    
            except Exception as e:
                messagebox.showerror("오류", f"장비 유형 삭제 중 오류:\n{str(e)}")

    def add_parameter_dialog(self):
        """새 파라미터 추가 다이얼로그"""
        if not self.equipment_type_var.get():
            messagebox.showwarning("경고", "먼저 장비 유형을 선택해주세요.")
            return
        
        # 구현 예정
        messagebox.showinfo("개발 중", "파라미터 수동 추가 기능은 개발 중입니다.\n"
                                      "현재는 DB 비교 탭에서 'Default DB로 전송' 기능을 사용해주세요.")

    def delete_selected_parameters(self):
        """선택된 파라미터들을 삭제합니다."""
        selected_items = self.default_db_tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "삭제할 파라미터를 선택해주세요.")
            return
        
        # 구현 예정
        messagebox.showinfo("개발 중", "파라미터 삭제 기능은 개발 중입니다.")

    def edit_parameter_dialog(self, event):
        """파라미터 편집 다이얼로그"""
        selected_item = self.default_db_tree.selection()
        if not selected_item:
            return
        
        # 구현 예정
        messagebox.showinfo("개발 중", "파라미터 편집 기능은 개발 중입니다.")

    def export_default_db_to_excel(self):
        """Default DB를 Excel로 내보내기"""
        # 구현 예정
        messagebox.showinfo("개발 중", "Excel 내보내기 기능은 개발 중입니다.")

    def import_default_db_from_excel(self):
        """Excel에서 Default DB 가져오기"""
        # 구현 예정
        messagebox.showinfo("개발 중", "Excel 가져오기 기능은 개발 중입니다.")

    def create_change_history_tab(self):
        """변경 이력 관리 탭 생성"""
        if self.change_history_frame is not None:
            return  # 이미 생성된 경우 중복 생성 방지
            
        self.change_history_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.change_history_frame, text="변경 이력 관리")
        
        info_label = ttk.Label(self.change_history_frame, 
                              text="변경 이력 관리 기능\n\n파라미터 변경 이력을 추적할 수 있습니다.\nQC 엔지니어 전용 기능입니다.",
                              justify="center")
        info_label.pack(expand=True)

    def get_duplicate_analysis(self, selected_items):
        """
        선택된 항목들의 중복 상태를 분석합니다.
        강화된 중복 검사 기능으로 잠재적 중복까지 감지합니다.
        
        Args:
            selected_items: 선택된 트리뷰 아이템 ID 리스트
            
        Returns:
            dict: 중복 분석 결과
        """
        duplicate_analysis = {
            'existing_in_db': [],      # 이미 DB에 존재하는 항목
            'potential_duplicates': [], # 비슷한 이름의 잠재적 중복
            'new_parameters': [],       # 완전히 새로운 파라미터
            'conflict_analysis': {},    # 값 충돌 분석
            'summary': {}              # 요약 정보
        }
        
        # 기존 Default DB의 모든 파라미터 목록 가져오기
        existing_params = {}
        try:
            default_values = self.db_schema.get_default_values()
            for record in default_values:
                param_name = record[1]  # parameter_name
                default_value = record[2]  # default_value
                equipment_type = record[5]  # type_name
                existing_params[param_name] = {
                    'value': default_value,
                    'equipment_type': equipment_type,
                    'record': record
                }
        except Exception as e:
            self.update_log(f"기존 파라미터 조회 오류: {e}")
            return duplicate_analysis
        
        for item_id in selected_items:
            item_values = self.comparison_tree.item(item_id, "values")
            
            # 유지보수 모드 여부에 따라 인덱스 조정
            col_offset = 1 if self.maint_mode else 0
            module, part, item_name = item_values[col_offset], item_values[col_offset+1], item_values[col_offset+2]
            
            param_name = f"{part}_{item_name}"
            current_value = item_values[col_offset+3] if len(item_values) > col_offset+3 else ""
            
            # 1. 정확한 이름 매칭 검사
            if param_name in existing_params:
                existing_record = existing_params[param_name]
                duplicate_analysis['existing_in_db'].append({
                    'param_name': param_name,
                    'current_value': current_value,
                    'existing_value': existing_record['value'],
                    'equipment_type': existing_record['equipment_type'],
                    'value_match': str(current_value).strip() == str(existing_record['value']).strip()
                })
                
                # 값 충돌 분석
                if str(current_value).strip() != str(existing_record['value']).strip():
                    duplicate_analysis['conflict_analysis'][param_name] = {
                        'current_value': current_value,
                        'existing_value': existing_record['value'],
                        'equipment_type': existing_record['equipment_type']
                    }
            else:
                # 2. 유사한 이름 검사 (잠재적 중복)
                similar_params = []
                for existing_param in existing_params.keys():
                    # 레벤슈타인 거리 계산
                    similarity = self.calculate_string_similarity(param_name, existing_param)
                    if similarity > 0.8:  # 80% 이상 유사
                        similar_params.append({
                            'existing_param': existing_param,
                            'similarity': similarity,
                            'existing_value': existing_params[existing_param]['value'],
                            'equipment_type': existing_params[existing_param]['equipment_type']
                        })
                
                if similar_params:
                    duplicate_analysis['potential_duplicates'].append({
                        'param_name': param_name,
                        'current_value': current_value,
                        'similar_params': sorted(similar_params, key=lambda x: x['similarity'], reverse=True)
                    })
                else:
                    # 3. 완전히 새로운 파라미터
                    duplicate_analysis['new_parameters'].append({
                        'param_name': param_name,
                        'current_value': current_value,
                        'module': module,
                        'part': part,
                        'item_name': item_name
                    })
        
        # 요약 정보 생성
        duplicate_analysis['summary'] = {
            'total_selected': len(selected_items),
            'exact_duplicates': len(duplicate_analysis['existing_in_db']),
            'potential_duplicates': len(duplicate_analysis['potential_duplicates']),
            'new_parameters': len(duplicate_analysis['new_parameters']),
            'value_conflicts': len(duplicate_analysis['conflict_analysis']),
            'safe_to_add': len(duplicate_analysis['new_parameters'])
        }
        
        return duplicate_analysis

    def calculate_string_similarity(self, str1, str2):
        """
        두 문자열 간의 유사도를 계산합니다 (레벤슈타인 거리 기반).
        
        Args:
            str1, str2: 비교할 문자열
            
        Returns:
            float: 0.0 ~ 1.0 사이의 유사도 (1.0이 완전 동일)
        """
        if str1 == str2:
            return 1.0
        
        len1, len2 = len(str1), len(str2)
        if len1 == 0:
            return 0.0 if len2 > 0 else 1.0
        if len2 == 0:
            return 0.0
        
        # 동적 프로그래밍으로 레벤슈타인 거리 계산
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if str1[i-1] == str2[j-1] else 1
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # 삭제
                    matrix[i][j-1] + 1,      # 삽입
                    matrix[i-1][j-1] + cost  # 대체
                )
        
        # 유사도 계산 (0.0 ~ 1.0)
        max_len = max(len1, len2)
        distance = matrix[len1][len2]
        similarity = 1.0 - (distance / max_len)
        
        return similarity

    def show_duplicate_analysis_dialog(self, duplicate_analysis):
        """
        중복 분석 결과를 보여주는 다이얼로그를 표시합니다.
        
        Args:
            duplicate_analysis: get_duplicate_analysis 결과
        """
        dlg = tk.Toplevel(self.window)
        dlg.title("🔍 중복 검사 결과")
        dlg.geometry("900x700")
        dlg.transient(self.window)
        dlg.grab_set()
        
        # 요약 정보 표시
        summary_frame = ttk.LabelFrame(dlg, text="📊 요약", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        summary = duplicate_analysis['summary']
        summary_text = (f"선택된 항목: {summary['total_selected']}개 | "
                       f"정확 중복: {summary['exact_duplicates']}개 | "
                       f"잠재 중복: {summary['potential_duplicates']}개 | "
                       f"새 파라미터: {summary['new_parameters']}개 | "
                       f"값 충돌: {summary['value_conflicts']}개")
        
        ttk.Label(summary_frame, text=summary_text, font=("", 10, "bold")).pack()
        
        # 탭 구성
        notebook = ttk.Notebook(dlg)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. 기존 DB 중복 탭
        existing_frame = ttk.Frame(notebook)
        notebook.add(existing_frame, text=f"🔴 기존 DB 중복 ({len(duplicate_analysis['existing_in_db'])}개)")
        
        if duplicate_analysis['existing_in_db']:
            existing_text = tk.Text(existing_frame, wrap=tk.WORD, font=("Consolas", 9))
            existing_scroll = ttk.Scrollbar(existing_frame, orient="vertical", command=existing_text.yview)
            existing_text.configure(yscrollcommand=existing_scroll.set)
            
            existing_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            existing_text.pack(fill=tk.BOTH, expand=True)
            
            existing_text.insert(tk.END, "⚠️ 다음 파라미터들이 이미 Default DB에 존재합니다:\n\n")
            
            for item in duplicate_analysis['existing_in_db']:
                status = "✅ 값 일치" if item['value_match'] else "❌ 값 불일치"
                status_color = "✅" if item['value_match'] else "🔥"
                
                existing_text.insert(tk.END, f"{status_color} {item['param_name']}\n")
                existing_text.insert(tk.END, f"   현재 값: {item['current_value']}\n")
                existing_text.insert(tk.END, f"   DB 저장값: {item['existing_value']}\n")
                existing_text.insert(tk.END, f"   장비 유형: {item['equipment_type']}\n")
                existing_text.insert(tk.END, f"   상태: {status}\n")
                
                if not item['value_match']:
                    existing_text.insert(tk.END, f"   ⚠️ 주의: 값이 다릅니다! 기존 값을 덮어쓸지 검토 필요\n")
                existing_text.insert(tk.END, "\n")
        else:
            ttk.Label(existing_frame, text="✅ 기존 DB와 정확히 일치하는 중복 항목이 없습니다.", 
                     font=("", 12)).pack(expand=True)
        
        # 2. 잠재적 중복 탭
        potential_frame = ttk.Frame(notebook)
        notebook.add(potential_frame, text=f"🟡 잠재적 중복 ({len(duplicate_analysis['potential_duplicates'])}개)")
        
        if duplicate_analysis['potential_duplicates']:
            potential_text = tk.Text(potential_frame, wrap=tk.WORD, font=("Consolas", 9))
            potential_scroll = ttk.Scrollbar(potential_frame, orient="vertical", command=potential_text.yview)
            potential_text.configure(yscrollcommand=potential_scroll.set)
            
            potential_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            potential_text.pack(fill=tk.BOTH, expand=True)
            
            potential_text.insert(tk.END, "🔍 유사한 이름의 파라미터들이 발견되었습니다:\n")
            potential_text.insert(tk.END, "이들은 실제로는 같은 파라미터일 가능성이 있습니다.\n\n")
            
            for item in duplicate_analysis['potential_duplicates']:
                potential_text.insert(tk.END, f"🟡 새 파라미터: {item['param_name']}\n")
                potential_text.insert(tk.END, f"   값: {item['current_value']}\n")
                potential_text.insert(tk.END, f"   유사한 기존 파라미터들:\n")
                
                for similar in item['similar_params']:
                    similarity_bar = "█" * int(similar['similarity'] * 10)
                    potential_text.insert(tk.END, f"      • {similar['existing_param']}\n")
                    potential_text.insert(tk.END, f"        유사도: {similar['similarity']*100:.1f}% {similarity_bar}\n")
                    potential_text.insert(tk.END, f"        기존 값: {similar['existing_value']}\n")
                    potential_text.insert(tk.END, f"        장비 유형: {similar['equipment_type']}\n")
                potential_text.insert(tk.END, "\n")
        else:
            ttk.Label(potential_frame, text="✅ 유사한 이름의 잠재적 중복 항목이 없습니다.", 
                     font=("", 12)).pack(expand=True)
        
        # 3. 새로운 파라미터 탭
        new_frame = ttk.Frame(notebook)
        notebook.add(new_frame, text=f"🟢 새 파라미터 ({len(duplicate_analysis['new_parameters'])}개)")
        
        if duplicate_analysis['new_parameters']:
            new_text = tk.Text(new_frame, wrap=tk.WORD, font=("Consolas", 9))
            new_scroll = ttk.Scrollbar(new_frame, orient="vertical", command=new_text.yview)
            new_text.configure(yscrollcommand=new_scroll.set)
            
            new_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            new_text.pack(fill=tk.BOTH, expand=True)
            
            new_text.insert(tk.END, "✨ 완전히 새로운 파라미터들입니다:\n")
            new_text.insert(tk.END, "이들은 안전하게 Default DB에 추가할 수 있습니다.\n\n")
            
            for item in duplicate_analysis['new_parameters']:
                new_text.insert(tk.END, f"✅ {item['param_name']}\n")
                new_text.insert(tk.END, f"   값: {item['current_value']}\n")
                new_text.insert(tk.END, f"   모듈: {item['module']}\n")
                new_text.insert(tk.END, f"   파트: {item['part']}\n")
                new_text.insert(tk.END, f"   항목명: {item['item_name']}\n\n")
        else:
            ttk.Label(new_frame, text="ℹ️ 새로운 파라미터가 없습니다.", 
                     font=("", 12)).pack(expand=True)
        
        # 4. 권장사항 탭 (새로 추가)
        recommend_frame = ttk.Frame(notebook)
        notebook.add(recommend_frame, text="💡 권장사항")
        
        recommend_text = tk.Text(recommend_frame, wrap=tk.WORD, font=("", 10))
        recommend_scroll = ttk.Scrollbar(recommend_frame, orient="vertical", command=recommend_text.yview)
        recommend_text.configure(yscrollcommand=recommend_scroll.set)
        
        recommend_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        recommend_text.pack(fill=tk.BOTH, expand=True)
        
        # 권장사항 생성
        recommend_text.insert(tk.END, "📋 중복 검사 기반 권장사항\n\n")
        
        if summary['exact_duplicates'] > 0:
            recommend_text.insert(tk.END, f"🔴 정확한 중복 항목 ({summary['exact_duplicates']}개):\n")
            if summary['value_conflicts'] > 0:
                recommend_text.insert(tk.END, f"   • {summary['value_conflicts']}개 항목에서 값 충돌 발견\n")
                recommend_text.insert(tk.END, f"   • 기존 값을 덮어쓸지 신중히 검토하세요\n")
                recommend_text.insert(tk.END, f"   • 통계 기반 분석을 활용하여 신뢰도가 높은 값을 선택하세요\n")
            else:
                recommend_text.insert(tk.END, f"   • 모든 값이 일치하므로 안전하게 진행 가능합니다\n")
            recommend_text.insert(tk.END, "\n")
        
        if summary['potential_duplicates'] > 0:
            recommend_text.insert(tk.END, f"🟡 잠재적 중복 항목 ({summary['potential_duplicates']}개):\n")
            recommend_text.insert(tk.END, f"   • 파라미터 이름을 검토하여 실제 중복인지 확인하세요\n")
            recommend_text.insert(tk.END, f"   • 동일한 파라미터라면 기존 이름으로 통일을 권장합니다\n")
            recommend_text.insert(tk.END, f"   • 다른 파라미터라면 그대로 추가해도 됩니다\n\n")
        
        if summary['new_parameters'] > 0:
            recommend_text.insert(tk.END, f"🟢 새로운 파라미터 ({summary['new_parameters']}개):\n")
            recommend_text.insert(tk.END, f"   • 안전하게 Default DB에 추가할 수 있습니다\n")
            recommend_text.insert(tk.END, f"   • 통계 기반 분석으로 신뢰도 높은 기준값을 설정하세요\n\n")
        
        # 전체 권장사항
        recommend_text.insert(tk.END, "💡 전체 권장사항:\n")
        recommend_text.insert(tk.END, "1. 통계 기반 분석을 활용하여 중복도가 높은 값을 기준값으로 선택\n")
        recommend_text.insert(tk.END, "2. 신뢰도 임계값을 적절히 설정 (50% 이상 권장)\n")
        recommend_text.insert(tk.END, "3. 값 충돌이 있는 경우 수동으로 검토 후 결정\n")
        recommend_text.insert(tk.END, "4. 잠재적 중복은 파라미터 명명 규칙을 통일하여 해결\n")
        
        # 버튼 프레임
        button_frame = ttk.Frame(dlg)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="닫기", command=dlg.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 중복 해결 버튼 (추후 기능 확장용)
        if summary['potential_duplicates'] > 0 or summary['value_conflicts'] > 0:
            ttk.Button(button_frame, text="중복 해결 마법사", 
                      command=lambda: self.show_duplicate_resolution_wizard(duplicate_analysis)).pack(side=tk.LEFT, padx=5)

    def show_duplicate_resolution_wizard(self, duplicate_analysis):
        """
        중복 해결을 도와주는 마법사 다이얼로그 (추후 확장 기능)
        
        Args:
            duplicate_analysis: 중복 분석 결과
        """
        messagebox.showinfo("개발 중", "중복 해결 마법사는 추후 버전에서 제공될 예정입니다.\n\n"
                                      "현재는 수동으로 중복을 검토하고 해결해주세요.")

    # 🎯 2단계-C: 개선된 메뉴 시스템 메서드들
    def create_enhanced_menu(self):
        """개선된 사용자 역할별 메뉴 생성"""
        menubar = tk.Menu(self.window)
        
        # 🎯 파일 메뉴 - 모든 사용자 공통
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="📁 폴더 열기 (Ctrl+O)", command=self.load_folder)
        file_menu.add_separator()
        file_menu.add_command(label="📊 보고서 내보내기", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 종료", command=self.window.quit)
        menubar.add_cascade(label="파일", menu=file_menu)
        
        # 🎯 분석 메뉴 - 장비 생산 엔지니어 기본 기능
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="🔍 DB 비교 분석", command=lambda: self.main_notebook.select(0))
        analysis_menu.add_separator()
        analysis_menu.add_command(label="📈 통계 분석", command=self.show_statistics_summary)
        analysis_menu.add_command(label="🔄 데이터 새로고침", command=self.refresh_all_data)
        menubar.add_cascade(label="분석", menu=analysis_menu)
        
        # 🎯 QC 관리 메뉴 - QC 엔지니어 전용 (동적 활성화)
        self.qc_menu = tk.Menu(menubar, tearoff=0)
        self.qc_menu.add_command(label="🔍 QC 검수", command=self.goto_qc_check_tab, state="disabled")
        self.qc_menu.add_command(label="🗄️ Default DB 관리", command=self.goto_default_db_tab, state="disabled")
        self.qc_menu.add_command(label="📝 변경 이력", command=self.goto_change_history_tab, state="disabled")
        self.qc_menu.add_separator()
        self.qc_menu.add_command(label="📤 데이터 내보내기", command=self.export_qc_data, state="disabled")
        self.qc_menu.add_command(label="📥 데이터 가져오기", command=self.import_qc_data, state="disabled")
        
        # 🎯 도구 메뉴 - 시스템 설정
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="👤 사용자 모드 전환", command=self.toggle_maint_mode)
        tools_menu.add_separator()
        tools_menu.add_command(label="🔐 비밀번호 변경", command=self.show_change_password_dialog)
        tools_menu.add_command(label="⚙️ 설정", command=self.show_settings_dialog)
        menubar.add_cascade(label="도구", menu=tools_menu)
        
        # 🎯 도움말 메뉴
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="📖 사용 설명서 (F1)", command=self.show_user_guide)
        help_menu.add_command(label="🆘 문제 해결", command=self.show_troubleshooting_guide)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ 프로그램 정보", command=self.show_about)
        menubar.add_cascade(label="도움말", menu=help_menu)
        
        self.window.config(menu=menubar)
        return menubar

    def update_enhanced_menu_state(self):
        """개선된 메뉴 상태 업데이트"""
        if hasattr(self, 'qc_menu'):
            if self.maint_mode:
                self._enable_qc_menu()
            else:
                self._disable_qc_menu()

    def _enable_qc_menu(self):
        """QC 메뉴 활성화"""
        try:
            # QC 메뉴를 메뉴바에 추가 (도구 메뉴 앞에)
            current_menubar = self.window['menu']
            if current_menubar:
                # QC 관리 메뉴가 이미 있는지 확인
                menu_found = False
                try:
                    for i in range(20):  # 충분한 범위로 검색
                        try:
                            label = current_menubar.entrycget(i, 'label')
                            if label == "QC 관리":
                                menu_found = True
                                break
                        except:
                            break
                except:
                    pass
                
                if not menu_found:
                    # 도구 메뉴 앞에 QC 관리 메뉴 삽입
                    try:
                        current_menubar.insert_cascade(2, label="QC 관리", menu=self.qc_menu)
                    except:
                        current_menubar.add_cascade(label="QC 관리", menu=self.qc_menu)
            
            # QC 메뉴 항목들 활성화
            for i in range(self.qc_menu.index('end') + 1):
                try:
                    self.qc_menu.entryconfig(i, state="normal")
                except:
                    pass
                    
        except Exception as e:
            self.update_log(f"QC 메뉴 활성화 중 오류: {e}")

    def _disable_qc_menu(self):
        """QC 메뉴 비활성화"""
        try:
            # QC 메뉴 항목들 비활성화
            if hasattr(self, 'qc_menu'):
                for i in range(self.qc_menu.index('end') + 1):
                    try:
                        self.qc_menu.entryconfig(i, state="disabled")
                    except:
                        pass
            
            # QC 메뉴를 메뉴바에서 제거
            current_menubar = self.window['menu']
            if current_menubar:
                try:
                    for i in range(20):  # 충분한 범위로 검색
                        try:
                            label = current_menubar.entrycget(i, 'label')
                            if label == "QC 관리":
                                current_menubar.delete(i)
                                break
                        except:
                            break
                except:
                    pass
                    
        except Exception as e:
            self.update_log(f"QC 메뉴 비활성화 중 오류: {e}")

    def get_current_mode_display(self) -> str:
        """현재 모드 표시 문자열 반환"""
        if self.maint_mode:
            return "👤 QC 엔지니어 모드"
        else:
            return "👤 장비 생산 엔지니어 모드"

    def force_refresh_all_equipment_types(self):
        """모든 탭의 장비 유형 목록을 강제로 새로고침 (추가/삭제 후 호출용)"""
        try:
            self.update_log("🔄 강제 새로고침: 모든 탭 동기화 시작...")
            
            # 1. 기본 새로고침 실행
            self.refresh_equipment_types()
            
            # 2. QC 탭 강제 갱신
            if hasattr(self, 'load_equipment_types_for_qc'):
                try:
                    self.load_equipment_types_for_qc()
                    self.update_log("✅ QC 탭 강제 갱신 완료")
                except Exception as e:
                    self.update_log(f"⚠️ QC 탭 강제 갱신 실패: {e}")
            
            # 3. defaultdb.py 모듈 강제 갱신
            if hasattr(self, 'load_equipment_types'):
                try:
                    self.load_equipment_types()
                    self.update_log("✅ defaultdb 모듈 강제 갱신 완료")
                except Exception as e:
                    self.update_log(f"⚠️ defaultdb 모듈 강제 갱신 실패: {e}")
            
            # 4. 모든 콤보박스 상태 로그
            self._log_all_combobox_states()
            
            self.update_log("🎉 강제 새로고침 완료: 모든 탭 동기화됨")
            
        except Exception as e:
            self.update_log(f"❌ 강제 새로고침 실패: {e}")
            import traceback
            traceback.print_exc()

    def _log_all_combobox_states(self):
        """모든 콤보박스의 현재 상태를 로그에 출력"""
        try:
            # Default DB 탭 콤보박스
            if hasattr(self, 'equipment_type_combo'):
                values = self.equipment_type_combo['values']
                current = self.equipment_type_var.get() if hasattr(self, 'equipment_type_var') else "없음"
                self.update_log(f"📋 Default DB 콤보박스: {len(values)}개 항목, 현재 선택: {current}")
            
            # QC 탭 콤보박스
            if hasattr(self, 'qc_type_combobox'):
                values = self.qc_type_combobox['values']
                current = self.qc_type_var.get() if hasattr(self, 'qc_type_var') else "없음"
                self.update_log(f"🔍 QC 검수 콤보박스: {len(values)}개 항목, 현재 선택: {current}")
            
            # defaultdb.py 모듈 콤보박스
            if hasattr(self, 'equipment_type_combobox'):
                values = self.equipment_type_combobox['values']
                current = self.equipment_type_var.get() if hasattr(self, 'equipment_type_var') else "없음" 
                self.update_log(f"🗃️ defaultdb 콤보박스: {len(values)}개 항목, 현재 선택: {current}")
                
        except Exception as e:
            self.update_log(f"⚠️ 콤보박스 상태 로그 실패: {e}")

    def refresh_qc_equipment_types(self):
        """QC 탭의 장비 유형 목록 수동 새로고침"""
        try:
            self.update_log("🔄 QC 탭 장비 유형 목록 수동 새로고침 시작...")
            
            # 현재 선택된 장비 유형 저장
            current_selection = self.qc_type_var.get() if hasattr(self, 'qc_type_var') else ""
            
            # 장비 유형 목록 다시 로드
            self.load_equipment_types_for_qc()
            
            # 이전 선택이 여전히 존재하면 복원
            if (current_selection and hasattr(self, 'qc_type_combobox') and 
                current_selection in self.qc_type_combobox['values']):
                self.qc_type_combobox.set(current_selection)
                self.update_log(f"✅ QC 탭 새로고침 완료 - 이전 선택 '{current_selection}' 복원")
            else:
                self.update_log("✅ QC 탭 새로고침 완료 - 새 목록으로 업데이트")
            
            # 성공 메시지
            messagebox.showinfo("새로고침 완료", "QC 탭의 장비 유형 목록이 최신 상태로 업데이트되었습니다.")
            
        except Exception as e:
            error_msg = f"QC 탭 새로고침 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("새로고침 오류", error_msg)

    def load_equipment_types_for_qc(self):
        """QC 검수를 위한 장비 유형 목록 로드"""
        if not hasattr(self, 'qc_type_combobox'):
            self.update_log("⚠️ QC 콤보박스가 아직 생성되지 않음")
            return
            
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 장비 유형 정보 조회
            cursor.execute("SELECT id, type_name FROM Equipment_Types ORDER BY type_name")
            equipment_types = cursor.fetchall()

            # 콤보박스 업데이트
            if equipment_types:
                self.equipment_types_for_qc = {name: id for id, name in equipment_types}
                self.qc_type_combobox['values'] = list(self.equipment_types_for_qc.keys())
                if self.qc_type_combobox['values']:
                    self.qc_type_combobox.current(0)  # 첫 번째 항목 선택
                self.update_log(f"✅ QC 탭 장비 유형 로드 완료: {len(equipment_types)}개")
            else:
                self.equipment_types_for_qc = {}
                self.qc_type_combobox['values'] = []
                self.update_log("⚠️ 등록된 장비 유형이 없습니다")

        except Exception as e:
            error_msg = f"QC 장비 유형 로드 중 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)
        finally:
            if conn:
                conn.close()

    def perform_qc_check(self):
        """QC 검수 실행 - Performance 모드 지원"""
        if not hasattr(self, 'qc_type_var') or not hasattr(self, 'equipment_types_for_qc'):
            self.update_log("❌ QC 검수 기능이 초기화되지 않았습니다")
            return
        
        selected_type = self.qc_type_var.get()
        if not selected_type:
            messagebox.showwarning("경고", "장비 유형을 선택해주세요.")
            return
        
        if self.merged_df is None:
            messagebox.showwarning("경고", "비교할 파일을 먼저 로드해주세요.")
            return
        
        try:
            self.update_log(f"🔍 QC 검수 시작: {selected_type}")
            
            # QC 결과 초기화
            for item in self.qc_result_tree.get_children():
                self.qc_result_tree.delete(item)
            
            # 기본 QC 검수 수행
            issues_found = 0
            
            # 선택된 장비 유형 ID 가져오기
            type_id = self.equipment_types_for_qc.get(selected_type)
            if not type_id:
                messagebox.showerror("오류", "선택된 장비 유형의 정보를 찾을 수 없습니다.")
                return
            
            # Default DB에서 기준값 가져오기
            default_values = self.db_schema.get_default_values(type_id)
            
            # 각 파라미터별로 검수 수행
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            
            for (module, part, item_name), group in grouped:
                param_name = f"{part}_{item_name}"
                
                # Default DB에서 해당 파라미터 찾기
                default_info = None
                for default_record in default_values:
                    if len(default_record) >= 6 and default_record[1] == param_name:
                        default_info = default_record
                        break
                
                # 값 일관성 검사
                file_values = []
                for model in self.file_names:
                    model_data = group[group["Model"] == model]
                    if not model_data.empty:
                        value = str(model_data["ItemValue"].iloc[0])
                        file_values.append(value)
                
                # 값이 다른 경우 이슈로 등록
                unique_values = set(v for v in file_values if v != "-")
                if len(unique_values) > 1:
                    issue_desc = f"파일 간 값 불일치: {', '.join(unique_values)}"
                    self.qc_result_tree.insert("", "end", values=[
                        param_name, "값 불일치", issue_desc, "중간"
                    ])
                    issues_found += 1
                
                # Default DB와 비교 (있는 경우)
                if default_info and len(file_values) > 0:
                    default_value = str(default_info[2])  # default_value 컬럼
                    current_value = file_values[0]  # 첫 번째 파일 값
                    
                    if current_value != "-" and current_value != default_value:
                        issue_desc = f"기준값({default_value})과 다름: {current_value}"
                        self.qc_result_tree.insert("", "end", values=[
                            param_name, "기준값 불일치", issue_desc, "높음"
                        ])
                        issues_found += 1
            
            # 검수 완료 메시지
            if issues_found == 0:
                messagebox.showinfo("QC 검수 완료", "문제가 발견되지 않았습니다.")
                self.update_log("✅ QC 검수 완료 - 문제 없음")
            else:
                messagebox.showinfo("QC 검수 완료", f"{issues_found}개의 문제가 발견되었습니다.")
                self.update_log(f"⚠️ QC 검수 완료 - {issues_found}개 문제 발견")
            
        except Exception as e:
            error_msg = f"QC 검수 중 오류: {str(e)}"
            self.update_log(f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)
            import traceback
            traceback.print_exc()
