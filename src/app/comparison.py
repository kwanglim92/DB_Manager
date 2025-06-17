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
        self.comparison_notebook.add(grid_view_tab, text="그리드 뷰")

        # 그리드 뷰 트리뷰 생성
        grid_frame = ttk.Frame(grid_view_tab)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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
