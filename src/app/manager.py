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

class DBManager:
    def __init__(self):
        self.maint_mode = False
        self.selected_equipment_type_id = None
        self.file_names = []
        self.folder_path = ""
        self.merged_df = None
        self.context_menu = None
        try:
            self.db_schema = DBSchema()
        except Exception as e:
            print(f"DB 스키마 초기화 실패: {str(e)}")
            self.db_schema = None
        add_qc_check_functions_to_class(DBManager)
        add_default_db_functions_to_class(DBManager)
        add_change_history_functions_to_class(DBManager)
        self.window = tk.Tk()
        self.window.title("DB Manager")
        self.window.geometry("1300x800")
        try:
            application_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(application_path, "resources", "icons", "db_compare.ico")
            self.window.iconbitmap(icon_path)
        except Exception as e:
            print(f"아이콘 로드 실패: {str(e)}")
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
        self.window.bind('<F1>', self.show_user_guide)

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
            "• 문의: github.com/kwanglim92/DB_Manager\n"
        )
        messagebox.showinfo("사용 설명서", guide_text)

        for key in ('<Control-o>', '<Control-O>'):
            self.window.bind(key, self.load_folder)
        self.create_comparison_tabs()
        self.status_bar.config(text="Ready")
        self.update_log("DB Manager 초기화 완료")
        if self.db_schema:
            self.update_log("로컬 데이터베이스 초기화 완료")
            self.update_log("Default DB 관리 기능 준비 완료")
        else:
            self.update_log("DB 스키마 초기화 실패")

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
            self.update_log("유지보수 모드가 비활성화되었습니다.")
            self.maint_mode = False
            self.status_bar.config(text="유지보수 모드 비활성화")
            self.disable_maint_features()
        else:
            password = simpledialog.askstring("유지보수 모드", "비밀번호를 입력하세요:", show="*")
            if password is None:
                return
            from app.utils import verify_password
            if verify_password(password):
                loading_dialog = LoadingDialog(self.window)
                loading_dialog.update_progress(10, "유지보수 모드 활성화 중...")
                self.maint_mode = True
                self.status_bar.config(text="유지보수 모드 활성화")
                self.update_log("유지보수 모드가 활성화되었습니다.")
                try:
                    loading_dialog.update_progress(30, "기본 DB 관리 기능 초기화 중...")
                    self.enable_maint_features()
                    loading_dialog.update_progress(100, "완료")
                    loading_dialog.close()
                except Exception as e:
                    loading_dialog.close()
                    messagebox.showerror("오류", f"유지보수 모드 활성화 중 오류 발생: {str(e)}")
            else:
                messagebox.showerror("오류", "비밀번호가 일치하지 않습니다.")
                return
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
                self.show_default_candidates_var.set(False)
                self.show_default_candidates_cb.configure(state="disabled")
                self.update_comparison_view()
        self.update_comparison_context_menu_state()
        self.update_all_tabs()

    def enable_maint_features(self):
        """유지보수 모드 활성화 시 필요한 기능을 활성화합니다. (최적화: 모든 무거운 작업을 스레드로 분리)"""
        import threading
        loading_dialog = LoadingDialog(self.window)
        def worker():
            try:
                if hasattr(self, 'notebook') and self.notebook:
                    for tab_id in range(self.notebook.index('end')):
                        if self.notebook.tab(tab_id, 'text') in ["Default DB 관리", "QC 검수", "변경 이력 관리"]:
                            self.window.after(0, lambda tab_id=tab_id: self.notebook.tab(tab_id, state='normal'))
                for widget_name in ['add_equipment_button', 'add_parameter_button', 'edit_button', 'delete_button']:
                    if hasattr(self, widget_name) and getattr(self, widget_name):
                        self.window.after(0, lambda wn=widget_name: getattr(self, wn).config(state='normal'))
                if hasattr(self, 'equipment_tree'):
                    self.window.after(0, lambda: self.equipment_tree.bind('<Double-1>', self.on_tree_double_click))
                loading_dialog.update_progress(10, "QC 탭 생성 중...")
                if hasattr(self, 'create_qc_check_tab'):
                    self.create_qc_check_tab()
                elif hasattr(self, 'create_qc_tab'):
                    self.create_qc_tab()
                loading_dialog.update_progress(40, "Default DB 관리 탭 생성 중...")
                if hasattr(self, 'create_default_db_tab'):
                    self.create_default_db_tab()
                loading_dialog.update_progress(70, "변경 이력 관리 탭 생성 중...")
                if hasattr(self, 'create_change_history_tab'):
                    self.create_change_history_tab()
                loading_dialog.update_progress(100, "완료")
                self.window.after(0, loading_dialog.close)
            except Exception as e:
                self.window.after(0, loading_dialog.close)
                self.window.after(0, lambda: messagebox.showerror("오류", f"유지보수 모드 활성화 중 오류 발생: {str(e)}"))
        threading.Thread(target=worker, daemon=True).start()

    def create_comparison_tabs(self):
        """비교 관련 탭 생성"""
        self.create_grid_view_tab()
        self.create_comparison_tab()
        self.create_diff_only_tab()
        self.create_report_tab()

    def create_diff_only_tab(self):
        diff_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(diff_tab, text="차이만 보기")
        control_frame = ttk.Frame(diff_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        self.diff_only_count_label = ttk.Label(control_frame, text="값이 다른 항목: 0개")
        self.diff_only_count_label.pack(side=tk.RIGHT, padx=10)
        columns = ["Module", "Part", "ItemName"] + self.file_names
        self.diff_only_tree = ttk.Treeview(diff_tab, columns=columns, show="headings", selectmode="extended")
        for col in columns:
            self.diff_only_tree.heading(col, text=col)
            self.diff_only_tree.column(col, width=120)
        v_scroll = ttk.Scrollbar(diff_tab, orient="vertical", command=self.diff_only_tree.yview)
        h_scroll = ttk.Scrollbar(diff_tab, orient="horizontal", command=self.diff_only_tree.xview)
        self.diff_only_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.diff_only_tree.pack(expand=True, fill=tk.BOTH)
        self.update_diff_only_view()

    def update_diff_only_view(self):
        for item in self.diff_only_tree.get_children():
            self.diff_only_tree.delete(item)
        diff_count = 0
        if self.merged_df is not None:
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            for (module, part, item_name), group in grouped:
                values = [module, part, item_name]
                unique_values = group[self.file_names].nunique().values
                if any(val > 1 for val in unique_values):
                    for fname in self.file_names:
                        values.append(group[fname].iloc[0] if fname in group else "")
                    self.diff_only_tree.insert("", "end", values=values, tags=("different",))
                    diff_count += 1
            self.diff_only_tree.tag_configure("different", background="light yellow")
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

    def create_grid_view_tab(self):
        grid_frame = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(grid_frame, text="📑 격자 뷰")
        grid_frame.rowconfigure([0, 1, 2], weight=1)
        grid_frame.columnconfigure([0, 1], weight=1)
        def count_items(df, module=None, part=None):
            if module is not None and part is not None:
                return df[(df["Module"] == module) & (df["Part"] == part)]["ItemName"].nunique()
            elif module is not None:
                return df[df["Module"] == module]["ItemName"].nunique()
            else:
                return df["ItemName"].nunique()


    def create_comparison_tab(self):
        comparison_frame = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(comparison_frame, text="DB 값 비교")
        style = ttk.Style()
        style.configure("Custom.Treeview", rowheight=22)
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

    def update_comparison_view(self):
        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)
        saved_checkboxes = self.item_checkboxes.copy()
        self.item_checkboxes.clear()
        if self.maint_mode:
            self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
        else:
            self.comparison_tree.unbind("<ButtonRelease-1>")
        diff_count = 0
        if self.merged_df is not None:
            grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
            for (module, part, item_name), group in grouped:
                values = []
                if self.maint_mode:
                    checkbox_state = "☐"
                    item_key = f"{module}_{part}_{item_name}"
                    if item_key in saved_checkboxes and saved_checkboxes[item_key]:
                        checkbox_state = "☑"
                    self.item_checkboxes[item_key] = (checkbox_state == "☑")
                    values.append(checkbox_state)
                values.extend([module, part, item_name])
                for model in self.file_names:
                    model_value = group[group["Model"] == model]["ItemValue"].values
                    value = model_value[0] if len(model_value) > 0 else "-"
                    values.append(value)
                tags = []
                model_values = values[(4 if self.maint_mode else 3):]
                if len(set(model_values)) > 1:
                    tags.append("different")
                    diff_count += 1
                is_existing = self.check_if_parameter_exists(module, part, item_name)
                if is_existing:
                    tags.append("existing")
                self.comparison_tree.insert("", "end", values=values, tags=tuple(tags))
            self.comparison_tree.tag_configure("different", background="light yellow")
            self.comparison_tree.tag_configure("existing", foreground="blue")
            if self.maint_mode:
                self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
            self.update_selected_count(None)
        if not self.maint_mode and hasattr(self, 'diff_count_label'):
            self.diff_count_label.config(text=f"값이 다른 항목: {diff_count}개")

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
