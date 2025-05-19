"""
DB_Manager.py 파일의 개선된 함수들
"""

def create_comparison_tab(self):
    """비교 탭을 생성합니다. 공통 항목 기준 기능과 Default DB 후보 표시 기능이 제거되었습니다."""
    comparison_frame = ttk.Frame(self.comparison_notebook)
    self.comparison_notebook.add(comparison_frame, text="DB 값 비교")
    
    # 상단 컨트롤 프레임 추가
    control_frame = ttk.Frame(comparison_frame)
    control_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 이미 추가된 항목 숨기기 체크박스
    self.hide_existing_var = tk.BooleanVar(value=False)
    self.hide_existing_cb = ttk.Checkbutton(
        control_frame, 
        text="이미 추가된 항목 숨기기", 
        variable=self.hide_existing_var,
        command=self.update_comparison_view
    )
    self.hide_existing_cb.pack(side=tk.LEFT, padx=5)
    
    # Default DB 추가 옵션 프레임
    self.db_options_frame = ttk.LabelFrame(control_frame, text="Default DB 추가 옵션")
    self.db_options_frame.pack(side=tk.LEFT, padx=20, fill=tk.Y)
    
    # 중복 항목 자동 덮어쓰기 체크박스
    self.auto_overwrite_var = tk.BooleanVar(value=False)
    self.auto_overwrite_cb = ttk.Checkbutton(
        self.db_options_frame, 
        text="중복 항목 자동 덮어쓰기", 
        variable=self.auto_overwrite_var
    )
    self.auto_overwrite_cb.pack(anchor=tk.W, padx=5, pady=2)
    
    # 자동 계산 값 사용 체크박스
    self.use_auto_calc_var = tk.BooleanVar(value=True)
    self.use_auto_calc_cb = ttk.Checkbutton(
        self.db_options_frame, 
        text="자동 계산 값 사용 (min/max)", 
        variable=self.use_auto_calc_var
    )
    self.use_auto_calc_cb.pack(anchor=tk.W, padx=5, pady=2)
    
    # 선택된 항목 개수 표시 레이블
    self.selected_count_label = ttk.Label(control_frame, text="체크된 항목: 0개")
    self.selected_count_label.pack(side=tk.RIGHT, padx=10)
    
    # 체크박스 상태를 저장할 딕셔너리
    self.item_checkboxes = {}
    
    # 트리뷰 생성 (다중 선택 모드 활성화)
    self.comparison_tree = ttk.Treeview(comparison_frame, selectmode="extended")
    self.comparison_tree["columns"] = ["Checkbox", "Module", "Part", "ItemName"] + self.file_names
    
    # 컬럼 설정
    self.comparison_tree.heading("#0", text="", anchor="w")
    self.comparison_tree.column("#0", width=0, stretch=False)
    
    # 체크박스 컬럼 추가
    self.comparison_tree.heading("Checkbox", text="선택")
    self.comparison_tree.column("Checkbox", width=50, anchor="center")
    
    for col in ["Module", "Part", "ItemName"]:
        self.comparison_tree.heading(col, text=col, anchor="w")
        self.comparison_tree.column(col, width=100)
    
    for i, name in enumerate(self.file_names):
        self.comparison_tree.heading(name, text=name, anchor="w")
        self.comparison_tree.column(name, width=100)
    
    # 스크롤바 추가
    v_scroll = ttk.Scrollbar(comparison_frame, orient="vertical", 
                            command=self.comparison_tree.yview)
    h_scroll = ttk.Scrollbar(comparison_frame, orient="horizontal", 
                            command=self.comparison_tree.xview)
    self.comparison_tree.configure(yscroll=v_scroll.set, xscroll=h_scroll.set)
    
    # 레이아웃
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    self.comparison_tree.pack(expand=True, fill=tk.BOTH)
    
    # 선택 이벤트 바인딩 (선택된 항목 개수 업데이트)
    self.comparison_tree.bind("<<TreeviewSelect>>", self.update_selected_count)
    
    # 체크박스 클릭 이벤트 추가
    self.comparison_tree.bind("<ButtonRelease-1>", self.toggle_checkbox)
    
    # 컨텍스트 메뉴 생성 및 바인딩
    self.create_comparison_context_menu()
    
    # 유지보수 모드에 따른 UI 상태 설정
    if not self.maint_mode:
        self.update_comparison_context_menu_state()
    
    # 데이터 표시
    self.update_comparison_view()


def update_comparison_view(self):
    """비교 탭의 데이터를 업데이트합니다. 공통 항목 기준 기능과 Default DB 후보 표시 기능이 제거되었습니다."""
    # 기존 항목 삭제
    for item in self.comparison_tree.get_children():
        self.comparison_tree.delete(item)
    
    # 체크박스 상태 저장
    saved_checkboxes = self.item_checkboxes.copy()
    self.item_checkboxes.clear()
    
    if self.merged_df is not None:
        # 데이터 비교 및 표시
        grouped = self.merged_df.groupby(["Module", "Part", "ItemName"])
        
        for (module, part, item_name), group in grouped:
            # 체크박스 상태 (기본값: 체크 안됨)
            checkbox_state = "☐"
            
            # 이전에 체크된 상태가 있으면 복원
            item_key = f"{module}_{part}_{item_name}"
            if item_key in saved_checkboxes and saved_checkboxes[item_key]:
                checkbox_state = "☑"
            
            # 체크박스 상태 저장
            self.item_checkboxes[item_key] = (checkbox_state == "☑")
            
            values = [checkbox_state, module, part, item_name]
            
            # 각 모델의 값 추가
            for model in self.file_names:
                model_value = group[group["Model"] == model]["ItemValue"].values
                value = model_value[0] if len(model_value) > 0 else "-"
                values.append(value)
            
            # 태그 초기화
            tags = []
            
            # 값이 다른 항목은 태그 추가
            model_values = values[4:]
            if len(set(model_values)) > 1:
                tags.append("different")
            
            # 이미 Default DB에 존재하는 항목인지 확인
            is_existing = self.check_if_parameter_exists(module, part, item_name)
            if is_existing:
                tags.append("existing")
            
            # 이미 추가된 항목 숨기기 옵션이 활성화된 경우
            if self.hide_existing_var.get() and is_existing:
                continue  # 이미 존재하는 항목은 표시하지 않음
            
            # 항목 추가
            item_id = self.comparison_tree.insert("", "end", values=values, tags=tuple(tags))
        
        # 태그 스타일 설정
        self.comparison_tree.tag_configure("different", background="light yellow")
        self.comparison_tree.tag_configure("existing", foreground="blue")
        
        # 체크된 항목 개수 업데이트
        self.update_checked_count()


def toggle_checkbox(self, event):
    """체크박스를 토글합니다."""
    # 클릭한 항목과 컬럼 정보 가져오기
    region = self.comparison_tree.identify_region(event.x, event.y)
    if region != "cell":
        return
        
    column = self.comparison_tree.identify_column(event.x)
    if column != "#1":  # 체크박스 컬럼이 아니면 무시
        return
        
    item = self.comparison_tree.identify_row(event.y)
    if not item:
        return
        
    # 현재 항목의 값 가져오기
    values = self.comparison_tree.item(item, "values")
    if not values:
        return
        
    # 체크박스 상태 토글
    current_state = values[0]
    module, part, item_name = values[1], values[2], values[3]
    item_key = f"{module}_{part}_{item_name}"
    
    # 체크박스 상태 변경
    new_state = "☑" if current_state == "☐" else "☐"
    self.item_checkboxes[item_key] = (new_state == "☑")
    
    # 트리뷰 항목 업데이트
    new_values = list(values)
    new_values[0] = new_state
    self.comparison_tree.item(item, values=new_values)
    
    # 체크된 항목 수 업데이트
    self.update_checked_count()


def update_checked_count(self):
    """체크된 항목 개수를 업데이트합니다."""
    checked_count = sum(1 for checked in self.item_checkboxes.values() if checked)
    self.selected_count_label.config(text=f"체크된 항목: {checked_count}개")


def add_to_default_db(self):
    """선택한 항목을 Default DB에 추가합니다."""
    # 유지보수 모드 확인
    if not self.maint_mode:
        result = messagebox.askyesno("유지보수 모드 필요", "Default DB를 수정하려면 유지보수 모드가 필요합니다. 지금 활성화하시겠습니까?")
        if result:
            self.toggle_maint_mode()
        else:
            return

    # 체크된 항목 또는 선택된 항목 확인
    checked_items = []
    for item_id in self.comparison_tree.get_children():
        values = self.comparison_tree.item(item_id, "values")
        if values and values[0] == "☑":  # 체크된 항목
            checked_items.append(item_id)
    
    selected_items_tree_ids = checked_items if checked_items else self.comparison_tree.selection()
    
    if not selected_items_tree_ids:
        messagebox.showinfo("알림", "Default DB에 추가할 항목을 체크하거나 선택하세요.")
        return

    # 장비 유형 선택 대화상자 생성
    equipment_types = self.db_schema.get_equipment_types()
    type_names = [name for _, name, _ in equipment_types]

    select_dialog = tk.Toplevel(self.window)
    select_dialog.title("장비 유형 선택")
    select_dialog.geometry("350x450")
    select_dialog.transient(self.window)
    select_dialog.grab_set()

    # UI 요소 생성
    list_frame = ttk.Frame(select_dialog)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    ttk.Label(list_frame, text="기존 장비 유형 선택:").pack(anchor=tk.W)
    type_listbox = tk.Listbox(list_frame, height=10, exportselection=False)
    for name_only in type_names:
        type_listbox.insert(tk.END, name_only)
    if type_names:
        type_listbox.selection_set(0)
    type_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

    new_type_frame = ttk.Frame(select_dialog)
    new_type_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(new_type_frame, text="새 장비 유형 추가:").pack(side=tk.LEFT)
    new_type_entry = ttk.Entry(new_type_frame)
    new_type_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # 옵션 프레임 추가
    options_frame = ttk.LabelFrame(select_dialog, text="추가 옵션")
    options_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # 중복 항목 자동 덮어쓰기 옵션
    auto_overwrite_var = tk.BooleanVar(value=self.auto_overwrite_var.get())
    auto_overwrite_cb = ttk.Checkbutton(
        options_frame, 
        text="중복 항목 자동 덮어쓰기", 
        variable=auto_overwrite_var
    )
    auto_overwrite_cb.pack(anchor=tk.W, padx=5, pady=2)
    
    # 자동 계산 값 사용 옵션
    use_auto_calc_var = tk.BooleanVar(value=self.use_auto_calc_var.get())
    use_auto_calc_cb = ttk.Checkbutton(
        options_frame, 
        text="자동 계산 값 사용 (min/max)", 
        variable=use_auto_calc_var
    )
    use_auto_calc_cb.pack(anchor=tk.W, padx=5, pady=2)
    
    button_frame = ttk.Frame(select_dialog)
    button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

    def on_confirm():
        chosen_type_name = ""
        
        # 장비 유형 선택 또는 새로 추가
        if type_listbox.curselection():
            chosen_type_name = type_listbox.get(type_listbox.curselection())
        elif new_type_entry.get().strip():
            chosen_type_name = new_type_entry.get().strip()
            try:
                self.db_schema.add_equipment_type(chosen_type_name, "")
                nonlocal equipment_types
                equipment_types = self.db_schema.get_equipment_types()  # 새로고침
            except Exception as e:
                messagebox.showerror("오류", f"새 장비 유형 추가 중 오류 발생: {str(e)}", parent=select_dialog)
                return
        else:
            messagebox.showinfo("알림", "장비 유형을 선택하거나 새로 입력하세요.", parent=select_dialog)
            return

        # 선택한 장비 유형 ID 찾기
        selected_equipment_type_id = None
        for et_id, et_name, _ in equipment_types:
            if et_name == chosen_type_name:
                selected_equipment_type_id = et_id
                break
        
        if selected_equipment_type_id is None:
            messagebox.showerror("오류", f"장비 유형 ID를 찾을 수 없습니다: {chosen_type_name}", parent=select_dialog)
            return

        # 선택한 항목 처리
        items_to_add = []
        
        for item_id in selected_items_tree_ids:
            values = self.comparison_tree.item(item_id, "values")
            if len(values) < 4:  # 체크박스, 모듈, 파트, 아이템 이름 최소 4개 필요
                continue
                
            # 체크박스 값은 무시하고 실제 데이터 값 사용
            module, part, item_name = values[1], values[2], values[3]
            param_name = f"{part}_{item_name}" if part else item_name
            
            # 모델 값 추출 (4번째 인덱스부터)
            model_values = values[4:]
            
            # 항목 추가
            items_to_add.append((param_name, module, part, item_name, model_values))
        
        if not items_to_add:
            messagebox.showinfo("알림", "추가할 유효한 항목이 없습니다.", parent=select_dialog)
            select_dialog.destroy()
            return
            
        # 중복 항목 확인
        conn = sqlite3.connect(self.db_schema.db_path)
        cursor = conn.cursor()
        
        existing_params = []
        new_params = []
        
        for param_info in items_to_add:
            param_name = param_info[0]
            cursor.execute(
                "SELECT id FROM Default_DB_Values WHERE equipment_type_id = ? AND parameter_name = ?",
                (selected_equipment_type_id, param_name)
            )
            if cursor.fetchone():
                existing_params.append(param_info)
            else:
                new_params.append(param_info)
                
        conn.close()
        
        # 중복 항목 처리
        params_to_process = []
        
        if existing_params:
            if auto_overwrite_var.get():
                # 자동 덮어쓰기 활성화 - 모든 항목 처리
                params_to_process = new_params + existing_params
            else:
                # 수동 확인
                if len(existing_params) == len(items_to_add):
                    result = messagebox.askyesno(
                        "중복 항목",
                        f"선택한 모든 항목({len(existing_params)}개)이 이미 존재합니다. 덮어쓰시겠습니까?",
                        parent=select_dialog
                    )
                    if result:
                        params_to_process = existing_params
                else:
                    result = messagebox.askyesnocancel(
                        "중복 항목",
                        f"선택한 {len(items_to_add)}개 항목 중 {len(existing_params)}개가 이미 존재합니다.\n\n"
                        f"- 예: 모든 항목을 덮어씁니다.\n"
                        f"- 아니오: 새 항목만 추가합니다.\n"
                        f"- 취소: 작업을 취소합니다.",
                        parent=select_dialog
                    )
                    if result is None:  # 취소
                        select_dialog.destroy()
                        return
                    elif result:  # 예 (모두 덮어쓰기)
                        params_to_process = new_params + existing_params
                    else:  # 아니오 (새 항목만)
                        params_to_process = new_params
        else:
            # 중복 없음 - 모든 새 항목 처리
            params_to_process = new_params
            
        if not params_to_process:
            messagebox.showinfo("알림", "처리할 항목이 없습니다.", parent=select_dialog)
            select_dialog.destroy()
            return
            
        # 진행 상태 대화상자
        progress_dialog = LoadingDialog(self.window)
        progress_dialog.update_progress(0, "Default DB에 항목 추가/업데이트 중...")
        
        try:
            num_processed = 0
            
            for idx, (param_name, module, part, item_name, model_values) in enumerate(params_to_process):
                # 값 계산
                numeric_values = []
                first_non_numeric = None
                all_hyphen = True
                
                for val_str in model_values:
                    if val_str != "-":
                        all_hyphen = False
                        try:
                            numeric_values.append(float(val_str))
                        except ValueError:
                            if first_non_numeric is None:
                                first_non_numeric = val_str
                
                # 기본값, 최소값, 최대값 설정
                if numeric_values and use_auto_calc_var.get():
                    default_val = sum(numeric_values) / len(numeric_values)
                    min_val = min(numeric_values) * 0.9
                    max_val = max(numeric_values) * 1.1
                elif first_non_numeric is not None:
                    default_val = first_non_numeric
                    min_val = default_val
                    max_val = default_val
                elif all_hyphen:
                    self.update_log(f"'{param_name}' 항목은 모든 값이 '-'이므로 건너뜁니다.")
                    continue
                else:
                    self.update_log(f"'{param_name}' 항목에 유효한 값이 없어 건너뜁니다.")
                    continue
                
                # DB 작업 (추가 또는 업데이트)
                conn = sqlite3.connect(self.db_schema.db_path)
                cursor = conn.cursor()
                
                try:
                    cursor.execute(
                        "SELECT id FROM Default_DB_Values WHERE equipment_type_id = ? AND parameter_name = ?",
                        (selected_equipment_type_id, param_name)
                    )
                    existing_id = cursor.fetchone()
                    
                    if existing_id:  # 업데이트
                        self.db_schema.update_default_value(
                            existing_id[0], param_name, default_val, min_val, max_val, conn_override=conn
                        )
                    else:  # 추가
                        self.db_schema.add_default_value(
                            selected_equipment_type_id, param_name, default_val, min_val, max_val, conn_override=conn
                        )
                        
                    conn.commit()
                    num_processed += 1
                except Exception as e:
                    self.update_log(f"항목 '{param_name}' 처리 중 오류: {str(e)}")
                finally:
                    conn.close()
                
                # 진행 상태 업데이트
                progress = (idx + 1) / len(params_to_process) * 100
                progress_dialog.update_progress(progress, f"처리 중... ({idx+1}/{len(params_to_process)})")
            
            # 완료
            progress_dialog.update_progress(100, "완료!")
            progress_dialog.close()
            
            # 결과 메시지
            messagebox.showinfo(
                "완료",
                f"'{chosen_type_name}' 장비 유형의 Default DB에 {num_processed}개 항목이 성공적으로 추가/업데이트되었습니다.",
                parent=select_dialog
            )
            
            # Default DB 탭 업데이트 (있는 경우)
            if hasattr(self, 'update_equipment_type_list'):
                self.update_equipment_type_list()
                
            # 비교 탭 업데이트
            self.update_comparison_view()
            
        except Exception as e:
            if 'progress_dialog' in locals():
                progress_dialog.close()
            messagebox.showerror("오류", f"항목 처리 중 오류가 발생했습니다: {str(e)}", parent=select_dialog)
            self.update_log(f"Default DB 항목 추가 중 오류: {str(e)}")
        finally:
            select_dialog.destroy()

    def on_cancel():
        select_dialog.destroy()

    ttk.Button(button_frame, text="확인", command=on_confirm).pack(side=tk.RIGHT, padx=5)
    ttk.Button(button_frame, text="취소", command=on_cancel).pack(side=tk.RIGHT, padx=5)
    
    # 대화상자가 닫힐 때까지 대기
    self.window.wait_window(select_dialog)
