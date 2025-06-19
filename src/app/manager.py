# DBManager 클래스 및 메인 GUI 관리

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sys, os
from datetime import datetime
from app.schema import DBSchema
from app.loading import LoadingDialog
from app.qc import add_qc_check_functions_to_class
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
        tools_menu.add_command(label="Maintenance Mode", command=self.toggle_maint_mode)
        tools_menu.add_command(label="비밀번호 변경", command=self.show_change_password_dialog)
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
        """선택된 항목을 Default DB에 추가합니다."""
        if not self.maint_mode:
            messagebox.showwarning("권한 없음", "이 기능은 유지보수 모드에서만 사용 가능합니다.")
            return

        # self.item_checkboxes 또는 self.comparison_tree.selection()에서 항목 가져오기
        selected_items = []
        if any(self.item_checkboxes.values()):
            # 체크박스가 하나라도 선택된 경우
            for item_key, is_checked in self.item_checkboxes.items():
                if is_checked:
                    # item_key에서 module, part, item_name 분리
                    parts = item_key.split('_')
                    module, part, item_name = parts[0], parts[1], '_'.join(parts[2:])
                    
                    # 트리뷰에서 해당 항목 찾기
                    for child_id in self.comparison_tree.get_children():
                        values = self.comparison_tree.item(child_id, 'values')
                        if values[1] == module and values[2] == part and values[3] == item_name:
                            selected_items.append(child_id)
                            break
        else:
            # 체크박스가 선택되지 않은 경우, 트리뷰에서 직접 선택된 항목 사용
            selected_items = self.comparison_tree.selection()

        if not selected_items:
            messagebox.showwarning("선택 필요", "Default DB에 추가할 항목을 먼저 선택해주세요.")
            return

        # 장비 유형 선택
        equipment_types = self.db_schema.get_equipment_types()
        if not equipment_types:
            messagebox.showerror("오류", "등록된 장비 유형이 없습니다. 먼저 Default DB 관리 탭에서 장비 유형을 추가하세요.")
            return
        
        type_names = [f"{name} (ID: {type_id})" for type_id, name, _ in equipment_types]
        
        # 선택 다이얼로그
        dlg = tk.Toplevel(self.window)
        dlg.title("장비 유형 선택")
        dlg.geometry("300x200")
        
        ttk.Label(dlg, text="아래 목록에서 장비 유형을 선택하세요:").pack(pady=10)
        
        selected_type = tk.StringVar()
        combo = ttk.Combobox(dlg, textvariable=selected_type, values=type_names, state="readonly")
        combo.pack(pady=5)
        combo.set(type_names[0])

        def on_confirm():
            type_id_str = selected_type.get().split("ID: ")[1][:-1]
            type_id = int(type_id_str)
            
            # 실제 DB 추가 로직
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
                    self.db_schema.add_default_value(type_id, param_name, value, None, None, f"Added from {self.file_names[0]}")
                    count += 1
                except Exception as e:
                    self.update_log(f"'{param_name}' 추가 실패: {e}")

            messagebox.showinfo("완료", f"총 {count}개의 항목이 Default DB에 추가되었습니다.")
            dlg.destroy()
            self.update_comparison_view() # UI 갱신

        ttk.Button(dlg, text="확인", command=on_confirm).pack(pady=10)

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
        """QC 검수 탭 생성"""
        if self.qc_check_frame is not None:
            return  # 이미 생성된 경우 중복 생성 방지
            
        self.qc_check_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.qc_check_frame, text="QC 검수")
        
        # QC 탭 내부에 노트북 생성
        self.qc_notebook = ttk.Notebook(self.qc_check_frame)
        self.qc_notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # 기본 QC 검수 탭
        basic_qc_tab = ttk.Frame(self.qc_notebook)
        self.qc_notebook.add(basic_qc_tab, text="기본 검수")
        
        # 기본 QC 검수 내용
        info_label = ttk.Label(basic_qc_tab, 
                              text="QC 검수 기능\n\n파라미터 값들의 품질을 검수할 수 있습니다.\nQC 엔지니어 전용 기능입니다.",
                              justify="center")
        info_label.pack(expand=True)
        
        # QC 검수 트리뷰 (기본)
        qc_tree_frame, self.qc_tree = create_treeview_with_scrollbar(
            basic_qc_tab,
            columns=("parameter", "value", "status", "note"),
            headings={"parameter": "파라미터", "value": "값", "status": "상태", "note": "비고"},
            column_widths={"parameter": 200, "value": 150, "status": 80, "note": 200},
            height=15
        )
        qc_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # QC 탭에 고급 기능들 추가
        self.create_qc_tabs_with_advanced_features()

    def create_default_db_tab(self):
        """Default DB 관리 탭 생성"""
        if self.default_db_frame is not None:
            return  # 이미 생성된 경우 중복 생성 방지
            
        self.default_db_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.default_db_frame, text="Default DB 관리")
        
        info_label = ttk.Label(self.default_db_frame, 
                              text="Default DB 관리 기능\n\n기본 파라미터 값들을 관리할 수 있습니다.\nQC 엔지니어 전용 기능입니다.",
                              justify="center")
        info_label.pack(expand=True)

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
