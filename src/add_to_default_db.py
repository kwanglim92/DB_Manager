def add_to_default_db(self):
    """선택한 항목을 Default DB에 추가합니다.
    유지보수 모드에서만 작동하며, 체크박스를 통한 일괄 적용 기능을 제공합니다.
    """
    # 선택한 항목 확인
    selected_items_tree_ids = self.comparison_tree.selection()
    if not selected_items_tree_ids:
        messagebox.showinfo("알림", "Default DB에 추가할 항목을 선택하세요.")
        return

    # 유지보수 모드 확인
    if not self.maint_mode:
        result = messagebox.askyesno("유지보수 모드 필요", "Default DB를 수정하려면 유지보수 모드가 필요합니다. 지금 활성화하시겠습니까?")
        if result:
            self.toggle_maint_mode()
        else:
            return

    # 유지보수 모드가 활성화되지 않았다면 종료
    if not self.maint_mode:
        return

    equipment_types = self.db_schema.get_equipment_types()
    type_names = [name for _, name, _ in equipment_types]

    select_dialog = tk.Toplevel(self.window)
    select_dialog.title("장비 유형 선택")
    select_dialog.geometry("400x600")  # 크기 조정
    select_dialog.transient(self.window)
    select_dialog.grab_set()
    
    # --- UI Elements for select_dialog ---
    list_frame = ttk.Frame(select_dialog)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(list_frame, text="기존 장비 유형 선택:").pack(anchor=tk.W)
    type_listbox = tk.Listbox(list_frame, height=10, exportselection=False)
    for name_only in type_names:
        type_listbox.insert(tk.END, name_only)
    if type_names:
        type_listbox.selection_set(0)
    type_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
    
    # 일괄 적용 옵션 추가
    options_frame = ttk.LabelFrame(select_dialog, text="옵션")
    options_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # 중복 항목 자동 덮어쓰기 체크박스
    auto_overwrite_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(options_frame, text="중복 항목 자동 덮어쓰기", variable=auto_overwrite_var).pack(anchor=tk.W, padx=5, pady=3)
    
    # 자동 계산 값 사용 체크박스
    use_auto_calc_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(options_frame, text="자동 계산 값 사용 (min/max)", variable=use_auto_calc_var).pack(anchor=tk.W, padx=5, pady=3)

    new_type_frame = ttk.Frame(select_dialog)
    new_type_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(new_type_frame, text="새 장비 유형 추가:").pack(side=tk.LEFT)
    new_type_entry = ttk.Entry(new_type_frame)
    new_type_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    button_frame = ttk.Frame(select_dialog)
    button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
    # --- End UI Elements ---

    def on_confirm():
        nonlocal equipment_types  # To allow modification if a new type is added
        chosen_type_name = ""
        
        # 자동 덮어쓰기 옵션 값 가져오기
        is_auto_overwrite = auto_overwrite_var.get()
        is_use_auto_calc = use_auto_calc_var.get()
        
        # Determine selected or new equipment type
        if type_listbox.curselection():
            chosen_type_name = type_listbox.get(type_listbox.curselection())
        elif new_type_entry.get().strip():
            chosen_type_name = new_type_entry.get().strip()
            try:
                self.db_schema.add_equipment_type(chosen_type_name, "")
                equipment_types = self.db_schema.get_equipment_types()  # Refresh
            except Exception as e:
                messagebox.showerror("오류", f"새 장비 유형 추가 중 오류 발생: {str(e)}", parent=select_dialog)
                return
        else:
            messagebox.showinfo("알림", "장비 유형을 선택하거나 새로 입력하세요.", parent=select_dialog)
            return

        selected_equipment_type_id = None
        for et_id, et_name, _ in equipment_types:
            if et_name == chosen_type_name:
                selected_equipment_type_id = et_id
                break
        
        if selected_equipment_type_id is None:
            messagebox.showerror("오류", f"장비 유형 ID를 찾을 수 없습니다: {chosen_type_name}", parent=select_dialog)
            return

        # Process selected items from the comparison tree
        items_to_potentially_add = []  # List of (param_name, values_tuple)
        param_names_in_selection = []  # For checking duplicates within selection itself

        for item_tree_id in selected_items_tree_ids:
            values = self.comparison_tree.item(item_tree_id, "values")
            module, part, item_name_val = values[0], values[1], values[2]
            param_name = f"{part}_{item_name_val}" if part else item_name_val
            if param_name not in param_names_in_selection:  # Avoid processing duplicates from selection
                items_to_potentially_add.append((param_name, values))
                param_names_in_selection.append(param_name)

        # Check which of these already exist in the DB for the selected equipment type
        db_params_existing_for_type = []  # Names of params already in DB for this type
        db_params_new_for_type = []       # (param_name, values) for params not in DB for this type

        conn = sqlite3.connect(self.db_schema.db_path)
        cursor = conn.cursor()
        for param_name, p_values in items_to_potentially_add:
            cursor.execute(
                "SELECT id FROM Default_DB_Values WHERE equipment_type_id = ? AND parameter_name = ?",
                (selected_equipment_type_id, param_name)
            )
            if cursor.fetchone():
                db_params_existing_for_type.append((param_name, p_values))
            else:
                db_params_new_for_type.append((param_name, p_values))
        conn.close()

        params_for_db_operation = []  # Final list of (param_name, values) to process

        if db_params_existing_for_type:
            if len(db_params_existing_for_type) == len(items_to_potentially_add):
                messagebox.showinfo("알림", f"선택한 모든 항목이 '{chosen_type_name}' 유형으로 이미 Default DB에 존재합니다.", parent=select_dialog)
                select_dialog.destroy()
                return
            
            # 자동 덮어쓰기 옵션이 활성화된 경우 대화상자 없이 진행
            if is_auto_overwrite:
                params_for_db_operation.extend(db_params_new_for_type)
                params_for_db_operation.extend(db_params_existing_for_type)  # Add existing ones to be overwritten
            else:
                # 자동 덮어쓰기 옵션이 비활성화된 경우 대화상자 표시
                dialog_result = messagebox.askyesnocancel(
                    "중복 항목 확인",
                    f"선택한 {len(items_to_potentially_add)}개 항목 중 {len(db_params_existing_for_type)}개는 '{chosen_type_name}' 유형으로 이미 Default DB에 존재합니다.\n\n"
                    f"- 예 (덮어쓰기): 기존 값을 새 값으로 업데이트하고, 새 항목도 추가합니다.\n"
                    f"- 아니오 (건너뛰기): 이미 존재하는 항목은 무시하고 새 항목만 추가합니다.\n"
                    f"- 취소: 작업을 취소합니다.",
                    parent=select_dialog
                )

                if dialog_result is None:  # Cancel
                    select_dialog.destroy()
                    return
                elif dialog_result:  # Yes (Overwrite)
                    params_for_db_operation.extend(db_params_new_for_type)
                    params_for_db_operation.extend(db_params_existing_for_type)  # Add existing ones to be overwritten
                else:  # No (Skip)
                    params_for_db_operation.extend(db_params_new_for_type)
        else:  # No existing params for this type among selected items
            params_for_db_operation.extend(db_params_new_for_type)
        
        if not params_for_db_operation:
            messagebox.showinfo("알림", "Default DB에 추가/업데이트할 새 항목이 없습니다.", parent=select_dialog)
            select_dialog.destroy()
            return

        progress_dialog = LoadingDialog(self.window)
        progress_dialog.update_progress(0, "Default DB에 항목 추가/업데이트 중...")
        
        try:
            num_processed = 0
            for idx, (param_name, p_values) in enumerate(params_for_db_operation):
                # Values from p_values: module, part, item_name_val are p_values[0], p_values[1], p_values[2]
                # Model values start from p_values[3]
                
                model_numeric_values = []
                first_non_numeric_value = None
                all_hyphen = True
                
                # 자동 계산 값 사용 옵션이 활성화된 경우에만 min/max 계산
                calculate_minmax = is_use_auto_calc

                for i in range(len(self.file_names)):
                    val_str = p_values[3 + i]
                    if val_str != "-":
                        all_hyphen = False
                        try:
                            model_numeric_values.append(float(val_str))
                        except ValueError:
                            if first_non_numeric_value is None:
                                first_non_numeric_value = val_str
                
                # 기본값 및 min/max 계산
                default_val = None
                min_spec = None
                max_spec = None
                
                if model_numeric_values:
                    # 숫자 값이 있는 경우 평균값을 기본값으로 사용
                    default_val = sum(model_numeric_values) / len(model_numeric_values)
                    
                    # 자동 계산 값 사용 옵션이 활성화된 경우에만 min/max 계산
                    if calculate_minmax:
                        min_spec = min(model_numeric_values) * 0.9  # 10% 여유
                        max_spec = max(model_numeric_values) * 1.1  # 10% 여유
                elif first_non_numeric_value is not None:
                    # 숫자가 아닌 값이 있는 경우 첫 번째 값을 사용
                    default_val = first_non_numeric_value
                elif all_hyphen:
                    self.update_log(f"Skipping '{param_name}' as all model values are '-' or invalid.")
                    continue  # Skip this parameter entirely
                else:  # Should not happen if logic above is correct, but as a fallback
                    self.update_log(f"Skipping '{param_name}' due to no valid values for default.")
                    continue

                # DB Operation: Add or Update
                conn_op = sqlite3.connect(self.db_schema.db_path)
                cursor_op = conn_op.cursor()
                cursor_op.execute(
                    "SELECT id FROM Default_DB_Values WHERE equipment_type_id = ? AND parameter_name = ?",
                    (selected_equipment_type_id, param_name)
                )
                existing_db_id_tuple = cursor_op.fetchone()
                
                if existing_db_id_tuple:  # Update
                    self.db_schema.update_default_value(
                        existing_db_id_tuple[0], 
                        param_name, 
                        default_val, 
                        min_spec, 
                        max_spec, 
                        conn_override=conn_op
                    )
                else:  # Add
                    self.db_schema.add_default_value(
                        selected_equipment_type_id,
                        param_name,
                        default_val,
                        min_spec,
                        max_spec,
                        conn_override=conn_op
                    )
                conn_op.commit()
                conn_op.close()
                num_processed += 1
                
                progress = (idx + 1) / len(params_for_db_operation) * 100
                progress_dialog.update_progress(progress, f"처리 중... ({idx+1}/{len(params_for_db_operation)})")

            progress_dialog.update_progress(100, "완료!")
            progress_dialog.close()
            
            messagebox.showinfo(
                "완료",
                f"'{chosen_type_name}' 장비 유형의 Default DB에 {num_processed}개 항목이 성공적으로 추가/업데이트되었습니다.",
                parent=select_dialog
            )
            
            if hasattr(self, 'update_equipment_type_list'):  # Check if Default DB tab exists
                self.update_equipment_type_list()  # Refresh Default DB tab
            self.update_comparison_view()  # Refresh comparison view

        except Exception as e:
            if 'progress_dialog' in locals() and progress_dialog.top.winfo_exists():
                progress_dialog.close()
            messagebox.showerror("오류", f"Default DB 항목 처리 중 예외 발생:\n{str(e)}", parent=select_dialog)
        
        select_dialog.destroy()

    def on_cancel():
        select_dialog.destroy()

    ttk.Button(button_frame, text="확인", command=on_confirm).pack(side=tk.RIGHT, padx=5)
    ttk.Button(button_frame, text="취소", command=on_cancel).pack(side=tk.RIGHT, padx=5)
    
    self.window.wait_window(select_dialog)
