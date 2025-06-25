"""
Comparison 탭을 위한 고급 필터링 기능 모듈
"""

import tkinter as tk
from tkinter import ttk

def add_comparison_filter_functions_to_class(cls):
    """DBManager 클래스에 Comparison 필터링 기능을 추가합니다."""
    
    def _create_comparison_filter_panel(self, parent_frame):
        """Comparison 탭 전용 필터 패널 생성"""
        try:
            # 실시간 검색 및 고급 필터 행
            filter_row = ttk.Frame(parent_frame)
            filter_row.pack(fill=tk.X, pady=(0, 8))
            
            # 실시간 검색 (좌측)
            search_frame = ttk.Frame(filter_row)
            search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            ttk.Label(search_frame, text="🔎 ItemName 검색:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 6))
            self.comp_search_var = tk.StringVar()
            self.comp_search_entry = ttk.Entry(search_frame, textvariable=self.comp_search_var, width=25, font=('Segoe UI', 9))
            self.comp_search_entry.pack(side=tk.LEFT, padx=(0, 6))
            
            # Clear 버튼
            clear_btn = ttk.Button(search_frame, text="지우기", command=self._clear_comparison_search)
            clear_btn.pack(side=tk.LEFT, padx=(0, 15))
            
            # 필터 컨트롤 영역 (우측)
            control_frame = ttk.Frame(filter_row)
            control_frame.pack(side=tk.RIGHT, padx=(10, 0))
            
            # 결과 표시 레이블
            self.comp_filter_result_label = ttk.Label(control_frame, text="", foreground="#1976D2", font=('Segoe UI', 8))
            self.comp_filter_result_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Advanced Filter 토글 버튼
            self.comp_advanced_filter_visible = tk.BooleanVar(value=False)
            self.comp_toggle_advanced_btn = ttk.Button(
                control_frame, 
                text="▼ 고급 필터", 
                command=self._toggle_comparison_advanced_filters
            )
            self.comp_toggle_advanced_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Reset 버튼
            reset_btn = ttk.Button(control_frame, text="초기화", command=self._reset_comparison_filters)
            reset_btn.pack(side=tk.LEFT)
            
            # 고급 필터 패널 (처음에는 숨김)
            self.comp_advanced_filter_frame = ttk.Frame(parent_frame)
            
            self._create_comparison_advanced_filters()
            
            # 이벤트 바인딩
            self.comp_search_var.trace('w', lambda *args: self._apply_comparison_filters())
            
            # 컬럼 헤더 클릭 정렬 설정
            self._setup_comparison_column_sorting()
            
            self.update_log("✅ Comparison filters initialized")
            
        except Exception as e:
            self.update_log(f"❌ Comparison filters error: {e}")

    def _create_comparison_advanced_filters(self):
        """Comparison 고급 필터 생성 - Module/Part 지원"""
        try:
            # 구분선
            filter_separator = ttk.Separator(self.comp_advanced_filter_frame, orient='horizontal')
            filter_separator.pack(fill=tk.X, pady=(5, 8))
            
            # 필터 행
            filters_row = ttk.Frame(self.comp_advanced_filter_frame)
            filters_row.pack(fill=tk.X, pady=(0, 8))
            
            # Module Filter
            module_frame = ttk.Frame(filters_row)
            module_frame.pack(side=tk.LEFT, padx=(0, 30))
            
            ttk.Label(module_frame, text="Module:", font=('Segoe UI', 8)).pack(anchor='w')
            self.comp_module_filter_var = tk.StringVar(value="All")
            self.comp_module_filter_combo = ttk.Combobox(module_frame, textvariable=self.comp_module_filter_var, 
                                                       state="readonly", width=15, font=('Segoe UI', 8))
            self.comp_module_filter_combo.pack()
            self.comp_module_filter_combo.bind('<<ComboboxSelected>>', self._on_comp_module_filter_changed)
            
            # Part Filter
            part_frame = ttk.Frame(filters_row)
            part_frame.pack(side=tk.LEFT, padx=(0, 30))
            
            ttk.Label(part_frame, text="Part:", font=('Segoe UI', 8)).pack(anchor='w')
            self.comp_part_filter_var = tk.StringVar(value="All")
            self.comp_part_filter_combo = ttk.Combobox(part_frame, textvariable=self.comp_part_filter_var, 
                                                     state="readonly", width=15, font=('Segoe UI', 8))
            self.comp_part_filter_combo.pack()
            self.comp_part_filter_combo.bind('<<ComboboxSelected>>', self._on_comp_part_filter_changed)
            
            self.update_log("✅ Comparison advanced filters ready")
            
        except Exception as e:
            self.update_log(f"❌ Comparison advanced filters error: {e}")

    def _setup_comparison_column_sorting(self):
        """Comparison 컬럼 헤더 클릭 정렬 설정"""
        try:
            # 정렬 상태 변수 초기화
            self.comp_current_sort_column = ""
            self.comp_current_sort_reverse = False
            
            self.update_log("✅ Comparison 컬럼 정렬 설정 완료")
            
        except Exception as e:
            self.update_log(f"❌ Comparison 컬럼 정렬 설정 오류: {e}")

    def _sort_comparison_by_column(self, column):
        """Comparison 컬럼별 정렬"""
        try:
            # 같은 컬럼을 다시 클릭하면 역순 정렬
            if hasattr(self, 'comp_current_sort_column') and self.comp_current_sort_column == column:
                self.comp_current_sort_reverse = not getattr(self, 'comp_current_sort_reverse', False)
            else:
                self.comp_current_sort_column = column
                self.comp_current_sort_reverse = False
            
            # 필터 적용 (정렬 포함)
            self._apply_comparison_filters()
            
            # 헤더 표시 업데이트
            self._update_comparison_sort_headers()
            
        except Exception as e:
            self.update_log(f"❌ Comparison 정렬 오류: {e}")

    def _update_comparison_sort_headers(self):
        """Comparison 정렬 헤더 표시 업데이트"""
        try:
            if not hasattr(self, 'comparison_tree'):
                return
                
            # 모든 헤더에서 정렬 표시 제거
            for col in ['Module', 'Part', 'ItemName']:
                header_text = col
                self.comparison_tree.heading(col, text=header_text, 
                                           command=lambda c=col: self._sort_comparison_by_column(c))
            
            # 현재 정렬 컬럼에 화살표 표시
            if hasattr(self, 'comp_current_sort_column') and self.comp_current_sort_column:
                arrow = " ↓" if getattr(self, 'comp_current_sort_reverse', False) else " ↑"
                header_text = f"{self.comp_current_sort_column}{arrow}"
                self.comparison_tree.heading(self.comp_current_sort_column, text=header_text,
                                           command=lambda c=self.comp_current_sort_column: self._sort_comparison_by_column(c))
                
        except Exception as e:
            self.update_log(f"❌ Comparison 헤더 업데이트 오류: {e}")

    def _apply_comparison_filters(self):
        """Comparison 필터 적용"""
        try:
            # 검색어와 필터 설정 가져오기
            search_text = getattr(self, 'comp_search_var', tk.StringVar()).get().lower().strip()
            module_filter = getattr(self, 'comp_module_filter_var', tk.StringVar()).get()
            part_filter = getattr(self, 'comp_part_filter_var', tk.StringVar()).get()
            
            # 필터가 적용된 뷰 업데이트
            self._update_comparison_view_with_filters(search_text, module_filter, part_filter)
            
        except Exception as e:
            self.update_log(f"❌ Comparison 필터 적용 오류: {e}")
            # 에러 시 기본 뷰 업데이트 시도
            try:
                self.update_comparison_view()
            except:
                pass

    def _update_comparison_view_with_filters(self, search_filter="", module_filter="", part_filter=""):
        """필터링이 적용된 Comparison 뷰 업데이트"""
        try:
            # 기존 트리 내용 클리어
            if not hasattr(self, 'comparison_tree'):
                return
                
            for item in self.comparison_tree.get_children():
                self.comparison_tree.delete(item)
            
            saved_checkboxes = getattr(self, 'item_checkboxes', {}).copy()
            self.item_checkboxes = {}
            
            if hasattr(self, 'maint_mode') and self.maint_mode:
                if hasattr(self, 'toggle_checkbox'):
                    self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
            else:
                self.comparison_tree.unbind("<ButtonRelease-1>")
            
            diff_count = 0
            total_items = 0
            filtered_items = 0
            
            if hasattr(self, 'merged_df') and self.merged_df is not None:
                # 파라미터별로 그룹화하여 비교
                grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
                
                comparison_data = []
                for (module, part, item_name), group in grouped:
                    total_items += 1
                    
                    # 필터링 적용
                    # 1. 검색 필터
                    if search_filter and search_filter not in item_name.lower():
                        continue
                    
                    # 2. Module 필터
                    if module_filter and module_filter != "All" and module_filter != module:
                        continue
                    
                    # 3. Part 필터
                    if part_filter and part_filter != "All" and part_filter != part:
                        continue
                    
                    # 각 파일별 값 수집
                    values = []
                    for model in getattr(self, 'file_names', []):
                        model_data = group[group["Model"] == model]
                        if not model_data.empty:
                            values.append(str(model_data["ItemValue"].iloc[0]))
                        else:
                            values.append("-")
                    
                    # 값 차이 확인
                    non_empty_values = [v for v in values if v != "-"]
                    has_difference = len(set(non_empty_values)) > 1 if len(non_empty_values) > 1 else False
                    
                    if has_difference:
                        diff_count += 1
                    
                    comparison_data.append({
                        'module': module,
                        'part': part,
                        'item_name': item_name,
                        'values': values,
                        'has_difference': has_difference
                    })
                    
                    filtered_items += 1
                
                # 정렬 적용
                if hasattr(self, 'comp_current_sort_column') and self.comp_current_sort_column:
                    sort_key = {
                        'Module': lambda x: x['module'],
                        'Part': lambda x: x['part'], 
                        'ItemName': lambda x: x['item_name']
                    }.get(self.comp_current_sort_column, lambda x: x['item_name'])
                    
                    comparison_data.sort(key=sort_key, reverse=getattr(self, 'comp_current_sort_reverse', False))
                
                # 트리뷰에 데이터 추가
                for data in comparison_data:
                    module, part, item_name = data['module'], data['part'], data['item_name']
                    values = data['values']
                    has_difference = data['has_difference']
                    
                    # 트리뷰 항목 생성
                    if hasattr(self, 'maint_mode') and self.maint_mode:
                        display_values = ["☐", module, part, item_name] + values
                    else:
                        display_values = [module, part, item_name] + values
                    
                    item_id = self.comparison_tree.insert("", "end", values=display_values)
                    
                    # 차이가 있는 항목에 태그 적용
                    if has_difference:
                        self.comparison_tree.item(item_id, tags=("diff",))
                    
                    # 체크박스 상태 복원
                    if hasattr(self, 'maint_mode') and self.maint_mode:
                        item_key = f"{module}_{part}_{item_name}"
                        if item_key in saved_checkboxes:
                            self.item_checkboxes[item_key] = saved_checkboxes[item_key]
                        else:
                            self.item_checkboxes[item_key] = False
                
                # 스타일 설정
                self.comparison_tree.tag_configure("diff", background="#FFECB3")
                
                # 결과 표시 업데이트
                if hasattr(self, 'comp_filter_result_label'):
                    if search_filter or (module_filter and module_filter != "All") or (part_filter and part_filter != "All"):
                        self.comp_filter_result_label.config(text=f"필터 결과: {filtered_items}/{total_items}")
                    else:
                        self.comp_filter_result_label.config(text="")
                
                # 차이점 개수 업데이트
                if hasattr(self, 'diff_count_label'):
                    self.diff_count_label.config(text=f"값이 다른 항목: {diff_count}개")
                
                # 필터 옵션 업데이트
                self._update_comparison_filter_options()
                
        except Exception as e:
            self.update_log(f"❌ Comparison 뷰 업데이트 오류: {e}")
            # 에러 시 기본 뷰 업데이트 시도
            try:
                self.update_comparison_view()
            except:
                pass

    def _update_comparison_filter_options(self):
        """Comparison 필터 옵션 업데이트"""
        try:
            if not hasattr(self, 'merged_df') or self.merged_df is None:
                return
            
            # Module 옵션 업데이트
            if hasattr(self, 'comp_module_filter_combo'):
                modules = ["All"] + sorted(self.merged_df["Module"].unique().tolist())
                self.comp_module_filter_combo['values'] = modules
                if not self.comp_module_filter_var.get() or self.comp_module_filter_var.get() not in modules:
                    self.comp_module_filter_var.set("All")
            
            # Part 옵션 업데이트
            if hasattr(self, 'comp_part_filter_combo'):
                parts = ["All"] + sorted(self.merged_df["Part"].unique().tolist())
                self.comp_part_filter_combo['values'] = parts
                if not self.comp_part_filter_var.get() or self.comp_part_filter_var.get() not in parts:
                    self.comp_part_filter_var.set("All")
            
        except Exception as e:
            self.update_log(f"❌ Comparison 필터 옵션 업데이트 오류: {e}")

    def _clear_comparison_search(self):
        """Comparison 검색 지우기"""
        if hasattr(self, 'comp_search_var'):
            self.comp_search_var.set("")
            self._apply_comparison_filters()

    def _toggle_comparison_advanced_filters(self):
        """Comparison 고급 필터 토글"""
        try:
            if hasattr(self, 'comp_advanced_filter_visible') and self.comp_advanced_filter_visible.get():
                # 숨김
                if hasattr(self, 'comp_advanced_filter_frame'):
                    self.comp_advanced_filter_frame.pack_forget()
                if hasattr(self, 'comp_toggle_advanced_btn'):
                    self.comp_toggle_advanced_btn.config(text="▼ 고급 필터")
                self.comp_advanced_filter_visible.set(False)
            else:
                # 표시
                if hasattr(self, 'comp_advanced_filter_frame'):
                    self.comp_advanced_filter_frame.pack(fill=tk.X, pady=(0, 5))
                if hasattr(self, 'comp_toggle_advanced_btn'):
                    self.comp_toggle_advanced_btn.config(text="▲ 고급 필터")
                if hasattr(self, 'comp_advanced_filter_visible'):
                    self.comp_advanced_filter_visible.set(True)
                
        except Exception as e:
            self.update_log(f"❌ Comparison 고급 필터 토글 오류: {e}")

    def _reset_comparison_filters(self):
        """Comparison 필터 초기화"""
        try:
            if hasattr(self, 'comp_search_var'):
                self.comp_search_var.set("")
            if hasattr(self, 'comp_module_filter_var'):
                self.comp_module_filter_var.set("All")
            if hasattr(self, 'comp_part_filter_var'):
                self.comp_part_filter_var.set("All")
            
            self._apply_comparison_filters()
            
        except Exception as e:
            self.update_log(f"❌ Comparison 필터 초기화 오류: {e}")

    def _on_comp_module_filter_changed(self, event=None):
        """Comparison Module 필터 변경"""
        self._apply_comparison_filters()

    def _on_comp_part_filter_changed(self, event=None):
        """Comparison Part 필터 변경"""
        self._apply_comparison_filters()

    # 클래스에 메서드 추가
    cls._create_comparison_filter_panel = _create_comparison_filter_panel
    cls._create_comparison_advanced_filters = _create_comparison_advanced_filters
    cls._setup_comparison_column_sorting = _setup_comparison_column_sorting
    cls._sort_comparison_by_column = _sort_comparison_by_column
    cls._update_comparison_sort_headers = _update_comparison_sort_headers
    cls._apply_comparison_filters = _apply_comparison_filters
    cls._update_comparison_view_with_filters = _update_comparison_view_with_filters
    cls._update_comparison_filter_options = _update_comparison_filter_options
    cls._clear_comparison_search = _clear_comparison_search
    cls._toggle_comparison_advanced_filters = _toggle_comparison_advanced_filters
    cls._reset_comparison_filters = _reset_comparison_filters
    cls._on_comp_module_filter_changed = _on_comp_module_filter_changed
    cls._on_comp_part_filter_changed = _on_comp_part_filter_changed 