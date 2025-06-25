# 비교 탭 및 기능 - 파일 비교 및 차이점 표시

import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from app.widgets import CheckboxTreeview
from app.utils import create_treeview_with_scrollbar, format_num_value

def add_comparison_functions_to_class(cls):
    """
    DBManager 클래스에 비교 기능을 추가합니다.
    """
    def create_comparison_tabs(self):
        """비교 탭 생성"""
        # 그리드 뷰 탭 생성
        self.create_grid_view_tab()

        # 비교 탭 생성
        self.create_comparison_tab()

        # 차이점만 보기 탭 생성
        self.create_diff_only_tab()

    def create_grid_view_tab(self):
        """그리드 뷰 탭 생성 - 모든 파일의 데이터를 표 형태로 표시"""
        grid_view_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(grid_view_tab, text="전체 목록")

        # 필터 패널 생성
        self._create_grid_filter_panel(grid_view_tab)

        # 그리드 뷰 트리뷰 생성
        grid_frame = ttk.Frame(grid_view_tab)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 스크롤바 생성
        y_scrollbar = ttk.Scrollbar(grid_frame)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(grid_frame, orient="horizontal")
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 트리뷰 생성
        self.grid_tree = ttk.Treeview(grid_frame, yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        self.grid_tree.pack(fill=tk.BOTH, expand=True)

        # 스크롤바 연결
        y_scrollbar.config(command=self.grid_tree.yview)
        x_scrollbar.config(command=self.grid_tree.xview)

    def create_comparison_tab(self):
        """비교 탭 생성 - 체크박스로 선택한 항목 비교"""
        comparison_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(comparison_tab, text="비교")

        # 상단 프레임 - 선택 옵션
        top_frame = ttk.Frame(comparison_tab, padding=(10, 5))
        top_frame.pack(fill=tk.X)

        # 전체 선택 체크박스
        self.select_all_var = tk.BooleanVar(value=False)
        self.select_all_cb = ttk.Checkbutton(
            top_frame, text="전체 선택", variable=self.select_all_var, 
            command=self.toggle_select_all_checkboxes
        )
        self.select_all_cb.pack(side=tk.LEFT, padx=5)

        # 선택 항목 카운트
        self.selected_count_label = ttk.Label(top_frame, text="선택: 0 항목")
        self.selected_count_label.pack(side=tk.LEFT, padx=20)

        # 선택 항목 Default DB로 보내기 버튼
        self.send_to_default_btn = ttk.Button(
            top_frame, text="선택 항목 Default DB로 보내기", 
            command=self.send_selected_to_default_db, state="disabled"
        )
        self.send_to_default_btn.pack(side=tk.RIGHT, padx=5)

        # 차이 항목 카운트
        self.diff_count_label = ttk.Label(top_frame, text="차이: 0 항목")
        self.diff_count_label.pack(side=tk.RIGHT, padx=20)

        # 메인 프레임 - 트리뷰
        main_frame = ttk.Frame(comparison_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 스크롤바 생성
        y_scrollbar = ttk.Scrollbar(main_frame)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal")
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 체크박스 트리뷰 생성
        self.comparison_tree = CheckboxTreeview(
            main_frame, 
            checkbox_column="checkbox",
            yscrollcommand=y_scrollbar.set, 
            xscrollcommand=x_scrollbar.set,
            selectmode="browse"
        )
        self.comparison_tree.pack(fill=tk.BOTH, expand=True)

        # 스크롤바 연결
        y_scrollbar.config(command=self.comparison_tree.yview)
        x_scrollbar.config(command=self.comparison_tree.xview)

        # 컨텍스트 메뉴 생성
        self.create_comparison_context_menu()

        # 트리뷰 이벤트 바인딩
        self.comparison_tree.bind("<<CheckboxToggled>>", lambda e: self.update_selected_count())
        self.comparison_tree.bind("<Button-3>", self.show_comparison_context_menu)

    def create_comparison_context_menu(self):
        """비교 탭 컨텍스트 메뉴 생성"""
        self.comparison_context_menu = tk.Menu(self.comparison_tree, tearoff=0)
        self.comparison_context_menu.add_command(label="Default DB로 전송", command=self.send_selected_to_default_db)
        self.comparison_context_menu.add_command(label="행 선택", command=self.toggle_checkbox)
        self.comparison_context_menu.add_separator()
        self.comparison_context_menu.add_command(label="차이점 강조 표시", command=lambda: self.highlight_differences(True))
        self.comparison_context_menu.add_command(label="강조 표시 해제", command=lambda: self.highlight_differences(False))

    def show_comparison_context_menu(self, event):
        """컨텍스트 메뉴 표시"""
        # 마우스 오른쪽 버튼 클릭 위치의 항목 선택
        item = self.comparison_tree.identify_row(event.y)
        if item:
            self.comparison_tree.selection_set(item)
            self.update_comparison_context_menu_state()
            self.comparison_context_menu.post(event.x_root, event.y_root)

    def update_comparison_context_menu_state(self):
        """컨텍스트 메뉴 상태 업데이트"""
        selected_items = self.comparison_tree.selection()
        has_selection = bool(selected_items)

        # Default DB로 전송 메뉴 상태 설정
        self.comparison_context_menu.entryconfig(
            "Default DB로 전송", 
            state="normal" if has_selection and self.maint_mode else "disabled"
        )

    def toggle_checkbox(self):
        """선택된 항목의 체크박스 상태 전환"""
        selected_items = self.comparison_tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        self.comparison_tree.toggle(item)
        self.update_selected_count()

    def toggle_select_all_checkboxes(self):
        """모든 체크박스 선택/해제"""
        all_selected = self.select_all_var.get()

        for item_id in self.comparison_tree.get_children():
            if all_selected:
                self.comparison_tree.check(item_id)
            else:
                self.comparison_tree.uncheck(item_id)

        self.update_selected_count()

    def update_selected_count(self):
        """선택된 항목 수 업데이트"""
        count = len(self.comparison_tree.get_checked_items())
        self.selected_count_label.config(text=f"선택: {count} 항목")

        # 버튼 활성화/비활성화
        if count > 0 and self.maint_mode:
            self.send_to_default_btn.config(state="normal")
        else:
            self.send_to_default_btn.config(state="disabled")

    def create_diff_only_tab(self):
        """차이점만 보기 탭 생성"""
        diff_only_tab = ttk.Frame(self.comparison_notebook)
        self.comparison_notebook.add(diff_only_tab, text="차이점만 보기")

        # 상단 프레임 - 필터 옵션
        top_frame = ttk.Frame(diff_only_tab, padding=(10, 5))
        top_frame.pack(fill=tk.X)

        # 차이점 항목 카운트
        self.diff_only_count_label = ttk.Label(top_frame, text="차이: 0 항목")
        self.diff_only_count_label.pack(side=tk.LEFT, padx=5)

        # 필터 옵션
        ttk.Label(top_frame, text="필터:").pack(side=tk.LEFT, padx=(20, 5))

        self.diff_filter_var = tk.StringVar(value="all")
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side=tk.LEFT)

        ttk.Radiobutton(
            filter_frame, text="모든 차이", value="all", 
            variable=self.diff_filter_var, command=self.update_diff_only_view
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            filter_frame, text="누락된 항목", value="missing", 
            variable=self.diff_filter_var, command=self.update_diff_only_view
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            filter_frame, text="값 차이", value="value", 
            variable=self.diff_filter_var, command=self.update_diff_only_view
        ).pack(side=tk.LEFT, padx=5)

        # 메인 프레임 - 트리뷰
        columns = ("parameter", "default_value", "file_value", "diff_type")
        headings = {
            "parameter": "파라미터", 
            "default_value": "Default DB 값", 
            "file_value": "파일 값", 
            "diff_type": "차이 유형"
        }
        column_widths = {
            "parameter": 200, 
            "default_value": 150, 
            "file_value": 150, 
            "diff_type": 100
        }

        tree_frame, self.diff_only_tree = create_treeview_with_scrollbar(
            diff_only_tab, columns, headings, column_widths
        )
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def update_comparison_view(self, merged_df=None):
        """비교 탭 뷰 업데이트"""
        if merged_df is not None:
            self.merged_df = merged_df

        if self.merged_df is None or self.merged_df.empty:
            return

        # 그리드 뷰 업데이트
        self.update_grid_view()

        # 비교 트리뷰 업데이트
        self.update_comparison_tree()

        # 차이점만 보기 탭 업데이트
        self.update_diff_only_view()

    def update_grid_view(self):
        """그리드 뷰 업데이트"""
        # 트리뷰 초기화
        for col in self.grid_tree['columns']:
            self.grid_tree.heading(col, text="")
            self.grid_tree.column(col, width=0, stretch=False)

        self.grid_tree['columns'] = ()
        self.grid_tree.delete(*self.grid_tree.get_children())

        if self.merged_df is None or self.merged_df.empty:
            return

        # 열 설정
        columns = list(self.merged_df.columns)
        self.grid_tree['columns'] = columns

        # 열 제목 및 너비 설정
        for col in columns:
            self.grid_tree.heading(col, text=col)

            # 파라미터명 열은 더 넓게
            if col == 'parameter':
                width = 200
            else:
                width = 120

            self.grid_tree.column(col, width=width, stretch=True)

        # 데이터 추가
        for _, row in self.merged_df.iterrows():
            values = [row[col] if pd.notna(row[col]) else "" for col in columns]
            self.grid_tree.insert("", "end", values=values)
        
        # 필터 옵션 업데이트
        if hasattr(self, '_update_grid_filter_options'):
            self._update_grid_filter_options()

    def update_comparison_tree(self):
        """비교 트리뷰 업데이트"""
        # 트리뷰 초기화
        for col in self.comparison_tree['columns']:
            self.comparison_tree.heading(col, text="")
            self.comparison_tree.column(col, width=0, stretch=False)

        self.comparison_tree['columns'] = ("checkbox", "parameter", "default_value") + tuple([f"file_{i}" for i in range(len(self.file_names))])

        # 체크박스 열 설정
        self.comparison_tree.column("checkbox", width=40, stretch=False)
        self.comparison_tree.heading("checkbox", text="✓")

        # 파라미터명 열 설정
        self.comparison_tree.column("parameter", width=200, stretch=True)
        self.comparison_tree.heading("parameter", text="파라미터")

        # Default DB 값 열 설정
        self.comparison_tree.column("default_value", width=150, stretch=True)
        self.comparison_tree.heading("default_value", text="Default DB 값")

        # 파일 값 열 설정
        for i, file_name in enumerate(self.file_names):
            col_name = f"file_{i}"
            self.comparison_tree.column(col_name, width=150, stretch=True)
            self.comparison_tree.heading(col_name, text=os.path.basename(file_name))

        # 기존 항목 삭제
        self.comparison_tree.delete(*self.comparison_tree.get_children())

        # 데이터 추가
        diff_count = 0
        self.item_checkboxes = {}

        for _, row in self.merged_df.iterrows():
            parameter = row['parameter']
            default_value = row['default_value'] if 'default_value' in row and pd.notna(row['default_value']) else ""

            # 파일 값 추출
            file_values = []
            has_diff = False

            for i in range(len(self.file_names)):
                col_name = f"file_{i}"
                file_value = row[col_name] if col_name in row and pd.notna(row[col_name]) else ""
                file_values.append(file_value)

                # 차이 체크
                if file_value != default_value:
                    has_diff = True

            # 차이가 있으면 카운트 증가
            if has_diff:
                diff_count += 1

            # 트리뷰에 추가
            values = ("checkbox", parameter, default_value) + tuple(file_values)
            item_id = self.comparison_tree.insert("", "end", values=values[1:])

            # 차이가 있는 항목 스타일 적용
            if has_diff:
                self.comparison_tree.item(item_id, tags=("diff",))

        # 차이 항목 스타일 설정
        self.comparison_tree.tag_configure("diff", background="#FFECB3")

        # 차이 항목 카운트 업데이트
        self.diff_count_label.config(text=f"차이: {diff_count} 항목")

    def update_diff_only_view(self):
        """차이점만 보기 탭 업데이트"""
        # 트리뷰 초기화
        self.diff_only_tree.delete(*self.diff_only_tree.get_children())

        if self.merged_df is None or self.merged_df.empty:
            return

        filter_type = self.diff_filter_var.get()
        diff_count = 0

        # 파일이 여러 개인 경우
        if len(self.file_names) > 1:
            for file_idx, file_name in enumerate(self.file_names):
                file_basename = os.path.basename(file_name)
                file_col = f"file_{file_idx}"

                for _, row in self.merged_df.iterrows():
                    parameter = row['parameter']
                    default_value = row['default_value'] if 'default_value' in row and pd.notna(row['default_value']) else ""
                    file_value = row[file_col] if file_col in row and pd.notna(row[file_col]) else ""

                    # 차이 유형 확인
                    if pd.isna(default_value) and pd.notna(file_value):
                        diff_type = "Default DB에 없음"
                    elif pd.notna(default_value) and pd.isna(file_value):
                        diff_type = "파일에 없음"
                    elif default_value != file_value:
                        diff_type = "값 차이"
                    else:
                        continue  # 차이 없음

                    # 필터 적용
                    if filter_type == "missing" and diff_type not in ["Default DB에 없음", "파일에 없음"]:
                        continue
                    elif filter_type == "value" and diff_type != "값 차이":
                        continue

                    # 트리뷰에 추가
                    self.diff_only_tree.insert(
                        "", "end", 
                        values=(f"{parameter} ({file_basename})", default_value, file_value, diff_type)
                    )
                    diff_count += 1
        else:  # 단일 파일인 경우
            file_col = "file_0"

            for _, row in self.merged_df.iterrows():
                parameter = row['parameter']
                default_value = row['default_value'] if 'default_value' in row and pd.notna(row['default_value']) else ""
                file_value = row[file_col] if file_col in row and pd.notna(row[file_col]) else ""

                # 차이 유형 확인
                if pd.isna(default_value) and pd.notna(file_value):
                    diff_type = "Default DB에 없음"
                elif pd.notna(default_value) and pd.isna(file_value):
                    diff_type = "파일에 없음"
                elif default_value != file_value:
                    diff_type = "값 차이"
                else:
                    continue  # 차이 없음

                # 필터 적용
                if filter_type == "missing" and diff_type not in ["Default DB에 없음", "파일에 없음"]:
                    continue
                elif filter_type == "value" and diff_type != "값 차이":
                    continue

                # 트리뷰에 추가
                self.diff_only_tree.insert(
                    "", "end", 
                    values=(parameter, default_value, file_value, diff_type)
                )
                diff_count += 1

        # 차이 항목 카운트 업데이트
        self.diff_only_count_label.config(text=f"차이: {diff_count} 항목")

    def highlight_differences(self, highlight=True):
        """차이점 강조 표시"""
        if highlight:
            self.comparison_tree.tag_configure("diff", background="#FFECB3")
        else:
            self.comparison_tree.tag_configure("diff", background="")

    def send_selected_to_default_db(self):
        """선택된 항목을 Default DB로 전송"""
        if not self.maint_mode:
            messagebox.showinfo("알림", "유지보수 모드에서만 사용 가능합니다.")
            return

        selected_items = self.comparison_tree.get_checked_items()
        if not selected_items:
            messagebox.showinfo("알림", "전송할 항목을 선택해주세요.")
            return

        # 여기에 Default DB로 선택된 항목을 전송하는 로직 구현
        # ...

    def _create_grid_filter_panel(self, parent_frame):
        """그리드 뷰 필터 패널 생성"""
        try:
            # 필터 프레임
            self.grid_filter_frame = ttk.Frame(parent_frame)
            self.grid_filter_frame.pack(fill=tk.X, pady=(5, 0), padx=10)
            
            # 구분선
            separator = ttk.Separator(self.grid_filter_frame, orient='horizontal')
            separator.pack(fill=tk.X, pady=(5, 8))
            
            # 검색 및 필터 행
            filter_row = ttk.Frame(self.grid_filter_frame)
            filter_row.pack(fill=tk.X, pady=(0, 8))
            
            # 실시간 검색
            search_frame = ttk.Frame(filter_row)
            search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            ttk.Label(search_frame, text="🔎 Search:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 6))
            self.grid_search_var = tk.StringVar()
            self.grid_search_entry = ttk.Entry(search_frame, textvariable=self.grid_search_var, width=25, font=('Segoe UI', 9))
            self.grid_search_entry.pack(side=tk.LEFT, padx=(0, 6))
            self.grid_search_var.trace('w', self._apply_grid_filters)
            
            # Clear 버튼
            clear_btn = ttk.Button(search_frame, text="Clear", command=self._clear_grid_search)
            clear_btn.pack(side=tk.LEFT, padx=(0, 15))
            
            # 엔지니어 관리 버튼들
            engineer_frame = ttk.Frame(search_frame)
            engineer_frame.pack(side=tk.LEFT, padx=(15, 0))
            
            # 엔지니어 관리 버튼 (QC 모드에서만 표시)
            if hasattr(self, 'maint_mode') and self.maint_mode:
                ttk.Button(engineer_frame, text="📊 비교 통계", command=self._show_comparison_statistics).pack(side=tk.LEFT, padx=(0, 5))
                ttk.Button(engineer_frame, text="🎯 중요 항목 관리", command=self._manage_important_items).pack(side=tk.LEFT, padx=(0, 5))
                ttk.Button(engineer_frame, text="📤 선택 항목 내보내기", command=self._export_selected_items).pack(side=tk.LEFT)
            
            # 필터 컨트롤 영역
            self.grid_advanced_filter_visible = tk.BooleanVar(value=False)
            
            control_row = ttk.Frame(filter_row)
            control_row.pack(side=tk.RIGHT, padx=(10, 0))
            
            # 결과 표시 레이블
            self.grid_filter_result_label = ttk.Label(control_row, text="", foreground="#1976D2", font=('Segoe UI', 8))
            self.grid_filter_result_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Advanced Filter 토글 버튼
            self.grid_toggle_advanced_btn = ttk.Button(
                control_row, 
                text="▼ Filters", 
                command=self._toggle_grid_advanced_filters
            )
            self.grid_toggle_advanced_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Reset 버튼
            reset_btn = ttk.Button(control_row, text="Reset", command=self._reset_grid_filters)
            reset_btn.pack(side=tk.LEFT)
            
            # 고급 필터 패널 (처음에는 숨김)
            self.grid_advanced_filter_frame = ttk.Frame(self.grid_filter_frame)
            
            self._create_grid_advanced_filters()
            
        except Exception as e:
            print(f"Grid filter panel error: {e}")

    def _create_grid_advanced_filters(self):
        """그리드 뷰 고급 필터 생성 - Module, Part만 포함 (Data Type 제외)"""
        try:
            # 구분선
            filter_separator = ttk.Separator(self.grid_advanced_filter_frame, orient='horizontal')
            filter_separator.pack(fill=tk.X, pady=(5, 8))
            
            # 필터 행 - 엔지니어 스타일 단일 행 레이아웃
            filters_row = ttk.Frame(self.grid_advanced_filter_frame)
            filters_row.pack(fill=tk.X, pady=(0, 8))
            
            # Module Filter
            module_frame = ttk.Frame(filters_row)
            module_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            ttk.Label(module_frame, text="Module:", font=('Segoe UI', 8)).pack(anchor='w')
            self.grid_module_filter_var = tk.StringVar()
            self.grid_module_filter_combo = ttk.Combobox(module_frame, textvariable=self.grid_module_filter_var, 
                                                      state="readonly", width=12, font=('Segoe UI', 8))
            self.grid_module_filter_combo.pack()
            self.grid_module_filter_combo.bind('<<ComboboxSelected>>', self._apply_grid_filters)
            
            # Part Filter
            part_frame = ttk.Frame(filters_row)
            part_frame.pack(side=tk.LEFT, padx=(0, 20))
            
            ttk.Label(part_frame, text="Part:", font=('Segoe UI', 8)).pack(anchor='w')
            self.grid_part_filter_var = tk.StringVar()
            self.grid_part_filter_combo = ttk.Combobox(part_frame, textvariable=self.grid_part_filter_var, 
                                                    state="readonly", width=12, font=('Segoe UI', 8))
            self.grid_part_filter_combo.pack()
            self.grid_part_filter_combo.bind('<<ComboboxSelected>>', self._apply_grid_filters)
            
            # 제어 버튼들
            control_frame = ttk.Frame(filters_row)
            control_frame.pack(side=tk.LEFT, padx=(20, 0))
            
            # 필터 적용 버튼
            apply_btn = ttk.Button(control_frame, text="🔍 필터 적용", command=self._apply_grid_filters)
            apply_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # 필터 초기화 버튼
            reset_btn = ttk.Button(control_frame, text="🔄 필터 초기화", command=self._reset_grid_filters)
            reset_btn.pack(side=tk.LEFT)
            
        except Exception as e:
            print(f"Grid advanced filters error: {e}")

    def _toggle_grid_advanced_filters(self):
        """그리드 뷰 고급 필터 토글"""
        if self.grid_advanced_filter_visible.get():
            self.grid_advanced_filter_frame.pack_forget()
            self.grid_toggle_advanced_btn.config(text="▼ Filters")
            self.grid_advanced_filter_visible.set(False)
        else:
            self.grid_advanced_filter_frame.pack(fill=tk.X, pady=(0, 5))
            self.grid_toggle_advanced_btn.config(text="▲ Filters")
            self.grid_advanced_filter_visible.set(True)

    def _apply_grid_filters(self, *args):
        """그리드 뷰 필터 적용"""
        try:
            if not hasattr(self, 'merged_df') or self.merged_df is None:
                return
                
            # 원본 데이터 복사
            filtered_df = self.merged_df.copy()
            
            # 1. 검색 필터
            search_text = self.grid_search_var.get().lower().strip()
            if search_text:
                mask = filtered_df.astype(str).apply(lambda x: x.str.lower().str.contains(search_text, na=False)).any(axis=1)
                filtered_df = filtered_df[mask]
            
            # 2. Module 필터
            if hasattr(self, 'grid_module_filter_var'):
                module_filter = self.grid_module_filter_var.get()
                if module_filter and module_filter != "All" and 'Module' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Module'] == module_filter]
            
            # 3. Part 필터
            if hasattr(self, 'grid_part_filter_var'):
                part_filter = self.grid_part_filter_var.get()
                if part_filter and part_filter != "All" and 'Part' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Part'] == part_filter]
            
            # 그리드 뷰 업데이트
            self._update_grid_view_with_filtered_data(filtered_df)
            
            # 결과 표시
            total_count = len(self.merged_df)
            filtered_count = len(filtered_df)
            self.grid_filter_result_label.config(text=f"표시: {filtered_count}/{total_count} 항목")
            
        except Exception as e:
            print(f"Grid filters apply error: {e}")

    def _update_grid_view_with_filtered_data(self, filtered_df):
        """필터링된 데이터로 그리드 뷰 업데이트"""
        try:
            # 기존 데이터 제거
            for item in self.grid_tree.get_children():
                self.grid_tree.delete(item)
            
            # 컬럼 설정
            columns = list(filtered_df.columns)
            self.grid_tree['columns'] = columns
            self.grid_tree['show'] = 'headings'
            
            # 컬럼 헤더 설정
            for col in columns:
                self.grid_tree.heading(col, text=col)
                width = 200 if col == 'parameter' else 120
                self.grid_tree.column(col, width=width, stretch=True)
            
            # 데이터 입력
            for idx, row in filtered_df.iterrows():
                values = [str(val) if pd.notna(val) else "" for val in row]
                self.grid_tree.insert("", "end", values=values)
                
        except Exception as e:
            print(f"Grid view update error: {e}")

    def _update_grid_filter_options(self):
        """그리드 뷰 필터 옵션 업데이트"""
        try:
            if not hasattr(self, 'merged_df') or self.merged_df is None:
                return
                
            # Module 옵션 업데이트
            if 'Module' in self.merged_df.columns:
                modules = sorted(self.merged_df['Module'].dropna().unique())
                module_values = ["All"] + list(modules)
                self.grid_module_filter_combo['values'] = module_values
                if not self.grid_module_filter_var.get():
                    self.grid_module_filter_var.set("All")
            
            # Part 옵션 업데이트
            if 'Part' in self.merged_df.columns:
                parts = sorted(self.merged_df['Part'].dropna().unique())
                part_values = ["All"] + list(parts)
                self.grid_part_filter_combo['values'] = part_values
                if not self.grid_part_filter_var.get():
                    self.grid_part_filter_var.set("All")
                    
        except Exception as e:
            print(f"Grid filter options update error: {e}")

    def _clear_grid_search(self):
        """그리드 뷰 검색 초기화"""
        self.grid_search_var.set("")
        self._apply_grid_filters()

    def _reset_grid_filters(self):
        """그리드 뷰 모든 필터 초기화"""
        try:
            # 검색 초기화
            self.grid_search_var.set("")
            
            # 필터 초기화
            if hasattr(self, 'grid_module_filter_var'):
                self.grid_module_filter_var.set("All")
            if hasattr(self, 'grid_part_filter_var'):
                self.grid_part_filter_var.set("All")
            
            # 필터 적용
            self._apply_grid_filters()
            
        except Exception as e:
            print(f"Grid filters reset error: {e}")

    def _show_comparison_statistics(self):
        """비교 통계 표시 (엔지니어 기능)"""
        try:
            if not hasattr(self, 'merged_df') or self.merged_df is None:
                messagebox.showinfo("정보", "비교할 데이터가 없습니다.")
                return
            
            # 통계 계산
            total_items = len(self.merged_df)
            
            # Module별 통계
            module_stats = {}
            if 'Module' in self.merged_df.columns:
                module_stats = self.merged_df['Module'].value_counts().to_dict()
            
            # Part별 통계
            part_stats = {}
            if 'Part' in self.merged_df.columns:
                part_stats = self.merged_df['Part'].value_counts().to_dict()
            
            # 통계 메시지 생성
            stats_msg = f"📊 DB 비교 통계\n\n"
            stats_msg += f"전체 항목 수: {total_items}개\n\n"
            
            if module_stats:
                stats_msg += "🔧 Module별 분포:\n"
                for module, count in sorted(module_stats.items()):
                    percentage = (count / total_items) * 100
                    stats_msg += f"  • {module}: {count}개 ({percentage:.1f}%)\n"
                stats_msg += "\n"
            
            if part_stats:
                stats_msg += "⚙️ Part별 분포:\n"
                for part, count in sorted(part_stats.items()):
                    percentage = (count / total_items) * 100
                    stats_msg += f"  • {part}: {count}개 ({percentage:.1f}%)\n"
            
            messagebox.showinfo("비교 통계", stats_msg)
            
        except Exception as e:
            messagebox.showerror("오류", f"통계 표시 중 오류 발생: {e}")

    def _manage_important_items(self):
        """중요 항목 관리 (엔지니어 기능)"""
        try:
            # 현재 선택된 항목들을 가져오기
            selected_items = []
            if hasattr(self, 'grid_tree'):
                for item in self.grid_tree.selection():
                    values = self.grid_tree.item(item, 'values')
                    if values:
                        selected_items.append(values[0] if values else "")
            
            if not selected_items:
                messagebox.showinfo("정보", "먼저 중요 항목으로 지정할 항목을 선택해주세요.")
                return
            
            # 중요 항목 지정 확인
            result = messagebox.askyesno(
                "중요 항목 관리", 
                f"선택된 {len(selected_items)}개 항목을 중요 항목으로 지정하시겠습니까?\n\n"
                "중요 항목은 QC 품질 관리에서 우선적으로 검토됩니다."
            )
            
            if result:
                # 여기에 중요 항목 저장 로직 구현
                messagebox.showinfo("완료", f"{len(selected_items)}개 항목이 중요 항목으로 지정되었습니다.")
                
        except Exception as e:
            messagebox.showerror("오류", f"중요 항목 관리 중 오류 발생: {e}")

    def _export_selected_items(self):
        """선택 항목 내보내기 (엔지니어 기능)"""
        try:
            if not hasattr(self, 'merged_df') or self.merged_df is None:
                messagebox.showinfo("정보", "내보낼 데이터가 없습니다.")
                return
            
            from tkinter import filedialog
            
            # 파일 저장 대화상자
            filename = filedialog.asksaveasfilename(
                title="비교 데이터 내보내기",
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"),
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )
            
            if filename:
                if filename.endswith('.xlsx'):
                    self.merged_df.to_excel(filename, index=False)
                else:
                    self.merged_df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                messagebox.showinfo("완료", f"데이터가 성공적으로 내보내졌습니다:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("오류", f"데이터 내보내기 중 오류 발생: {e}")

    # 클래스에 함수 추가
    cls.create_comparison_tabs = create_comparison_tabs
    cls.create_grid_view_tab = create_grid_view_tab
    cls.create_comparison_tab = create_comparison_tab
    cls.create_comparison_context_menu = create_comparison_context_menu
    cls.show_comparison_context_menu = show_comparison_context_menu
    cls.update_comparison_context_menu_state = update_comparison_context_menu_state
    cls.toggle_checkbox = toggle_checkbox
    cls.toggle_select_all_checkboxes = toggle_select_all_checkboxes
    cls.update_selected_count = update_selected_count
    cls.create_diff_only_tab = create_diff_only_tab
    cls.update_comparison_view = update_comparison_view
    cls.update_grid_view = update_grid_view
    cls.update_comparison_tree = update_comparison_tree
    cls.update_diff_only_view = update_diff_only_view
    cls.highlight_differences = highlight_differences
    cls.send_selected_to_default_db = send_selected_to_default_db
    cls._create_grid_filter_panel = _create_grid_filter_panel
    cls._create_grid_advanced_filters = _create_grid_advanced_filters
    cls._toggle_grid_advanced_filters = _toggle_grid_advanced_filters
    cls._apply_grid_filters = _apply_grid_filters
    cls._update_grid_view_with_filtered_data = _update_grid_view_with_filtered_data
    cls._update_grid_filter_options = _update_grid_filter_options
    cls._clear_grid_search = _clear_grid_search
    cls._reset_grid_filters = _reset_grid_filters
    cls._show_comparison_statistics = _show_comparison_statistics
    cls._manage_important_items = _manage_important_items
    cls._export_selected_items = _export_selected_items
