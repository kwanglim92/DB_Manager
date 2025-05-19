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
