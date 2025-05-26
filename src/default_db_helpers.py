"""
Default DB 관리 기능을 위한 헬퍼 모듈

이 모듈은 DBManager 클래스에 Default DB 관리 기능을 추가하는 함수들을 제공합니다.
런타임에 DBManager 클래스에 기능을 추가하는 방식으로 동작합니다.
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
from common_utils import create_treeview_with_scrollbar, create_label_entry_pair, format_num_value

def add_default_db_functions_to_class(cls):
    """
    DBManager 클래스에 Default DB 관리 기능을 추가합니다.
    
    Args:
        cls: 기능을 추가할 클래스 (DBManager)
    """
    
    def log_change_history(self, change_type, item_type, item_name, old_value="", new_value=""):
        """
        변경 이력을 기록합니다.
        
        Args:
            change_type: 변경 유형 ('add', 'update', 'delete')
            item_type: 항목 유형 ('equipment_type', 'parameter')
            item_name: 항목 이름
            old_value: 변경 전 값 (삭제 또는 수정 시)
            new_value: 변경 후 값 (추가 또는 수정 시)
        """
        try:
            # 현재 사용자 정보 (실제 시스템에서는 로그인한 사용자 정보를 가져와야 함)
            username = "admin"
            
            # DB 스키마를 통해 변경 이력 기록
            self.db_schema.log_change_history(change_type, item_type, item_name, old_value, new_value, username)
            
            # 로그에도 기록
            log_message = f"변경 이력: [{change_type}] {item_type} - {item_name}"
            self.update_log(log_message)
            
        except Exception as e:
            print(f"변경 이력 기록 오류: {str(e)}")

    
    def create_default_db_tab(self):
        """
        Default DB 관리 탭을 생성합니다.
        장비 유형별 파라미터 관리 및 최소/최대값 설정 기능을 제공합니다.
        """
        default_db_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(default_db_tab, text="Default DB 관리")
        
        # 상단 프레임 - 전체 파라미터 목록 표시
        top_frame = ttk.LabelFrame(default_db_tab, text="전체 파라미터 목록", padding=10)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 전체 파라미터 트리뷰 생성
        columns = ("module", "part", "itemname", "default", "min", "max")
        headings = {
            "module": "Module", 
            "part": "Part", 
            "itemname": "ItemName", 
            "default": "기본값", 
            "min": "최소값", 
            "max": "최대값"
        }
        column_widths = {
            "module": 150, 
            "part": 150, 
            "parameter": 200, 
            "default": 100, 
            "min": 100, 
            "max": 100
        }
        
        all_params_frame, self.all_params_tree = create_treeview_with_scrollbar(
            top_frame, columns, headings, column_widths, height=10)
        all_params_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 검색 및 필터링 프레임
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="검색:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.filter_parameters)
        
        ttk.Button(filter_frame, text="전체 새로고침", command=self.load_all_parameters).pack(side=tk.RIGHT, padx=5)
        
        # 하단 프레임 - 좌측: 장비 유형 목록, 우측: 파라미터 편집
        bottom_frame = ttk.Frame(default_db_tab)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 좌측 프레임 (장비 유형 목록)
        left_frame = ttk.LabelFrame(bottom_frame, text="장비 유형 관리", width=250, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 장비 유형 목록 프레임 및 리스트박스
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 장비 유형 목록 리스트박스
        self.equipment_type_listbox = tk.Listbox(list_frame, height=15, exportselection=False)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.equipment_type_listbox.yview)
        self.equipment_type_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.equipment_type_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 장비 유형 선택 시 이벤트 연결
        self.equipment_type_listbox.bind('<<ListboxSelect>>', self.on_equipment_type_selected)
        
        # 버튼 프레임
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="추가", command=self.add_equipment_type).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="삭제", command=self.delete_equipment_type).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="새로고침", command=self.update_equipment_type_list).pack(side=tk.LEFT, padx=5)
        
        # 우측 프레임 (파라미터 목록 및 편집)
        right_frame = ttk.LabelFrame(bottom_frame, text="파라미터 관리", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 선택된 장비 유형 표시
        self.selected_type_var = tk.StringVar(value="선택된 장비 유형: 없음")
        ttk.Label(right_frame, textvariable=self.selected_type_var, font=("Helvetica", 10, "bold")).pack(pady=5)
        
        # 파라미터 목록 트리뷰
        param_list_frame = ttk.Frame(right_frame)
        param_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 파라미터 트리뷰 생성
        columns = ("parameter", "default", "min", "max")
        headings = {
            "parameter": "파라미터", 
            "default": "기본값", 
            "min": "최소값", 
            "max": "최대값"
        }
        column_widths = {
            "parameter": 250, 
            "default": 100, 
            "min": 100, 
            "max": 100
        }
        
        param_tree_frame, self.parameter_tree = create_treeview_with_scrollbar(
            param_list_frame, columns, headings, column_widths, height=8)
        param_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.parameter_tree.bind("<<TreeviewSelect>>", self.on_parameter_selected)
        
        # 파라미터 편집 프레임
        param_form_frame = ttk.LabelFrame(right_frame, text="파라미터 편집", padding=10)
        param_form_frame.pack(fill=tk.X, expand=False, pady=5)
        
        form_frame = ttk.Frame(param_form_frame)
        form_frame.pack(fill=tk.X, expand=True)
        
        # 파라미터 입력 폼
        row = 0
        ttk.Label(form_frame, text="파라미터 이름:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.param_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.param_name_var, width=25).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        
        row += 1
        ttk.Label(form_frame, text="기본값:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.default_value_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.default_value_var, width=25).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        
        row += 1
        ttk.Label(form_frame, text="최소값:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.min_value_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.min_value_var, width=25).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        
        row += 1
        ttk.Label(form_frame, text="최대값:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_value_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.max_value_var, width=25).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 편집 버튼 프레임
        edit_button_frame = ttk.Frame(param_form_frame)
        edit_button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(edit_button_frame, text="추가", command=self.add_parameter).pack(side=tk.LEFT, padx=5)
        ttk.Button(edit_button_frame, text="수정", command=self.update_parameter).pack(side=tk.LEFT, padx=5)
        ttk.Button(edit_button_frame, text="삭제", command=self.delete_parameter).pack(side=tk.LEFT, padx=5)
        ttk.Button(edit_button_frame, text="초기화", command=self.clear_parameter_form).pack(side=tk.LEFT, padx=5)
        
        # 파라미터 트리뷰 선택 이벤트 연결
        self.parameter_tree.bind('<<TreeviewSelect>>', self.on_parameter_selected)
        
        # 장비 유형 목록 로드
        self.update_equipment_type_list()
    
    def update_equipment_type_list(self):
        """장비 유형 목록을 업데이트합니다."""
        self.equipment_type_listbox.delete(0, tk.END)
        try:
            # 장비 유형 목록 가져오기 및 저장 (ID 참조를 위해)
            equipment_types = self.db_schema.get_equipment_types()
            self.equipment_type_ids = [type_id for type_id, _, _ in equipment_types]
            
            for _, type_name, _ in equipment_types:
                self.equipment_type_listbox.insert(tk.END, type_name)
            
            # 파라미터 목록 초기화
            for item in self.parameter_tree.get_children():
                self.parameter_tree.delete(item)
            
            self.clear_parameter_form()
            self.parameter_label.config(text="ItemName 목록")
            
            # 전체 파라미터 목록 업데이트
            self.load_all_parameters()
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 목록 로드 중 오류 발생: {str(e)}")
            self.update_log(f"장비 유형 목록 로드 오류: {str(e)}")
            
    def load_all_parameters(self):
        """전체 파라미터 목록을 로드합니다."""
        try:
            # 트리뷰 초기화
            for item in self.all_params_tree.get_children():
                self.all_params_tree.delete(item)
            
            # 모든 장비 유형에 대한 파라미터 가져오기
            equipment_types = self.db_schema.get_equipment_types()
            
            for type_id, type_name, _ in equipment_types:
                # 해당 장비 유형의 파라미터 가져오기
                parameters = self.db_schema.get_default_values(type_id)
                
                for param in parameters:
                    # 파라미터 형식이 변경되었을 수 있으므로 안전하게 처리
                    if len(param) >= 8:
                        param_id, eq_type_id, param_name, default_val, min_val, max_val = param[0], param[1], param[2], param[3], param[4], param[5]
                    else:
                        # 파라미터 형식이 다른 경우 처리
                        self.update_log(f"경고: 파라미터 형식이 예상과 다릅니다: {param}")
                        continue
                    
                    # 파라미터 이름 분리 (Module_Part_ItemName 형식)
                    parts = param_name.split('_')
                    if len(parts) >= 3:
                        module = parts[0]
                        part = parts[1]
                        itemname = '_'.join(parts[2:])  # 나머지 부분을 ItemName으로 처리
                    else:
                        module = ""
                        part = ""
                        itemname = param_name
                    
                    # 전체 파라미터 트리에 추가
                    self.all_params_tree.insert(
                        "", tk.END, 
                        values=(module, part, itemname, default_val, min_val, max_val, type_name),
                        tags=(str(param_id),)
                    )
            
            # 정렬
            self.sort_all_parameters()
            self.update_log("전체 파라미터 목록 불러오기 성공")
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 로드 중 오류 발생: {str(e)}")
            self.update_log(f"파라미터 로드 오류: {str(e)}")
            
    def sort_all_parameters(self):
        """전체 파라미터 목록을 정렬합니다."""
        items = [(self.all_params_tree.item(item, "values"), item) for item in self.all_params_tree.get_children()]
        items.sort(key=lambda x: (x[0][0], x[0][1], x[0][2]))  # 모듈, 파트, 파라미터 순으로 정렬
        
        # 정렬된 순서로 다시 배치
        for i, (_, item) in enumerate(items):
            self.all_params_tree.move(item, "", i)
            
    def filter_parameters(self, event=None):
        """검색어에 따라 파라미터 목록을 필터링합니다."""
        search_text = self.search_var.get().lower()
        
        # 검색어가 없으면 모든 항목 표시
        if not search_text:
            self.load_all_parameters()
            return
        
        # 기존 항목 삭제
        for item in self.all_params_tree.get_children():
            self.all_params_tree.delete(item)
        
        try:
            # 모든 장비 유형 가져오기
            equipment_types = self.db_schema.get_equipment_types()
            
            # 각 장비 유형별 파라미터 로드 및 검색어에 맞는 항목만 표시
            for type_id, type_name, _ in equipment_types:
                if search_text in type_name.lower():
                    # 장비 유형 이름에 검색어가 포함된 경우 모든 파라미터 표시
                    self.add_equipment_parameters_to_tree(type_id, type_name)
                else:
                    # 장비 유형 이름에 검색어가 없는 경우 파라미터별로 검색
                    default_values = self.db_schema.get_default_values(type_id)
                    
                    # 파트와 모듈 구분 (type_name에서 파싱)
                    if '_' in type_name:
                        module, part = type_name.split('_', 1)
                    else:
                        module, part = type_name, ""
                    
                    # 파라미터 이름, 값 등에 검색어가 포함된 항목만 추가
                    for value_id, param_name, default_val, min_val, max_val, _ in default_values:
                        if (search_text in param_name.lower() or 
                            search_text in str(default_val).lower() or
                            search_text in str(min_val).lower() or
                            search_text in str(max_val).lower()):
                            
                            self.all_params_tree.insert(
                                "", tk.END, 
                                values=(module, part, param_name, default_val, min_val, max_val),
                                tags=(str(value_id),)
                            )
            
            # 정렬
            self.sort_all_parameters()
            
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 필터링 중 오류 발생: {str(e)}")
            self.update_log(f"파라미터 필터링 오류: {str(e)}")
    
    def add_equipment_parameters_to_tree(self, type_id, type_name):
        """특정 장비 유형의 모든 파라미터를 트리에 추가합니다."""
        default_values = self.db_schema.get_default_values(type_id)
        
        # 파트와 모듈 구분 (type_name에서 파싱)
        if '_' in type_name:
            module, part = type_name.split('_', 1)
        else:
            module, part = type_name, ""
        
        # 각 파라미터 추가
        for value_id, param_name, default_val, min_val, max_val, _ in default_values:
            self.all_params_tree.insert(
                "", tk.END, 
                values=(module, part, param_name, default_val, min_val, max_val),
                tags=(str(value_id),)
            )
    def on_equipment_type_selected(self, event):
        """장비 유형 선택시 해당 파라미터 목록 표시"""
        selection = self.equipment_type_listbox.curselection()
        
        # 트리뷰 초기화
        for item in self.parameter_tree.get_children():
            self.parameter_tree.delete(item)
        
        if not selection:
            self.selected_type_var.set("선택된 장비 유형: 없음")
            self.clear_parameter_form()
            return
        
        type_index = selection[0]
        type_name = self.equipment_type_listbox.get(type_index)
        self.selected_type_var.set(f"선택된 장비 유형: {type_name}")
        
        try:
            # 장비 유형 ID 가져오기
            equipment_types = self.db_schema.get_equipment_types()
            equipment_type_id = None
            for id, name, _ in equipment_types:
                if name == type_name:
                    equipment_type_id = id
                    break
            
            if equipment_type_id is None:
                return
            
            # 해당 장비 유형의 파라미터 가져오기
            parameters = self.db_schema.get_default_values(equipment_type_id)
            
            for param in parameters:
                # 파라미터 형식이 변경되었을 수 있으므로 안전하게 처리
                if len(param) >= 8:
                    param_id, eq_type_id, param_name, default_val, min_val, max_val = param[0], param[1], param[2], param[3], param[4], param[5]
                else:
                    # 파라미터 형식이 다른 경우 처리
                    self.update_log(f"경고: 파라미터 형식이 예상과 다릅니다: {param}")
                    continue
                
                # 트리뷰에 추가
                self.parameter_tree.insert(
                    "", tk.END, values=(param_name, default_val, min_val, max_val),
                    tags=(str(param_id),))
            
            self.clear_parameter_form()
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 로드 중 오류 발생: {str(e)}")
            self.update_log(f"파라미터 로드 오류: {str(e)}")
            
    def on_parameter_selected(self, event):
        """파라미터 선택시 편집 폼에 데이터 표시"""
        selection = self.parameter_tree.selection()
        if not selection:
            return
        
        try:
            # 트리뷰에서 선택한 파라미터 값 가져오기
            values = self.parameter_tree.item(selection[0], "values")
            
            # 폼에 값 설정
            self.param_name_var.set(values[0])
            self.default_value_var.set(values[1])
            self.min_value_var.set(values[2])
            self.max_value_var.set(values[3])
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 선택 중 오류 발생: {str(e)}")
            self.update_log(f"파라미터 선택 오류: {str(e)}")
    
    def clear_parameter_form(self):
        """파라미터 편집 폼을 초기화합니다."""
        self.param_name_var.set("")
        self.default_value_var.set("")
        self.min_value_var.set("")
        self.max_value_var.set("")
        if self.parameter_tree.selection():
            self.parameter_tree.selection_remove(self.parameter_tree.selection())
    
    def add_equipment_type(self):
        """새 장비 유형을 추가합니다."""
        if not self.maint_mode:
            messagebox.showinfo("알림", "유지보수 모드에서만 장비 유형을 추가할 수 있습니다.")
            return
        
        type_name = simpledialog.askstring("장비 유형 추가", "추가할 장비 유형 이름을 입력하세요:")
        if not type_name:
            return
        
        try:
            # 장비 유형 추가
            self.db_schema.add_equipment_type(type_name, "")
            
            # 변경 이력 기록
            self.log_change_history("add", "equipment_type", type_name, "", "")
            
            self.update_equipment_type_list()
            self.update_log(f"장비 유형 추가: {type_name}")
            
            # 새로 추가된 항목 선택
            for i in range(self.equipment_type_listbox.size()):
                if self.equipment_type_listbox.get(i) == type_name:
                    self.equipment_type_listbox.selection_set(i)
                    self.equipment_type_listbox.see(i)
                    self.on_equipment_type_selected(None)
                    break
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 추가 중 오류 발생: {str(e)}")
            self.update_log(f"장비 유형 추가 오류: {str(e)}")
    
    def delete_equipment_type(self):
        """선택한 장비 유형을 삭제합니다."""
        if not self.maint_mode:
            messagebox.showinfo("알림", "유지보수 모드에서만 장비 유형을 삭제할 수 있습니다.")
            return
        
        selection = self.equipment_type_listbox.curselection()
        if not selection:
            messagebox.showinfo("알림", "삭제할 장비 유형을 선택하세요.")
            return
        
        type_name = self.equipment_type_listbox.get(selection[0])
        confirm = messagebox.askyesno("확인", f"'{type_name}' 장비 유형과 관련된 모든 파라미터를 삭제하시겠습니까?")
        if not confirm:
            return
            
        # 비밀번호 확인 대화상자 생성
        password_dialog = tk.Toplevel(self.window)
        password_dialog.title("비밀번호 확인")
        password_dialog.geometry("300x150")
        password_dialog.resizable(False, False)
        password_dialog.transient(self.window)
        password_dialog.grab_set()
        
        # 대화상자 가운데 배치
        password_dialog.grid_columnconfigure(0, weight=1)
        password_dialog.grid_rowconfigure(0, weight=1)
        password_dialog.grid_rowconfigure(1, weight=1)
        password_dialog.grid_rowconfigure(2, weight=1)
        
        # 안내 메시지
        ttk.Label(password_dialog, text=f"'{type_name}' 장비 유형을 삭제하려면\n비밀번호를 입력하세요.", 
                 justify="center").grid(row=0, column=0, padx=10, pady=(10, 5))
        
        # 비밀번호 입력 필드
        password_var = tk.StringVar()
        password_entry = ttk.Entry(password_dialog, textvariable=password_var, show="*", width=20)
        password_entry.grid(row=1, column=0, padx=10, pady=5)
        password_entry.focus_set()
        
        # 버튼 프레임
        button_frame = ttk.Frame(password_dialog)
        button_frame.grid(row=2, column=0, padx=10, pady=(5, 10))
        
        # 비밀번호 확인 함수
        def validate_password():
            entered_password = password_var.get()
            # 실제 서비스에서는 더 복잡한 비밀번호 검사 로직 구현 필요
            # 예시: 비밀번호 "admin1234"
            if entered_password == "admin1234":
                password_dialog.destroy()
                delete_confirmed()
            else:
                messagebox.showerror("오류", "비밀번호가 올바르지 않습니다.")
        
        # 삭제 작업 함수
        def delete_confirmed():
        
            # 선택된 장비 유형의 ID 가져오기
            equipment_types = self.db_schema.get_equipment_types()
            selected_type_id = None
            for type_id, name, _ in equipment_types:
                if name == type_name:
                    selected_type_id = type_id
                    break
            
            if selected_type_id is None:
                return
            
            try:
                # 삭제 전 파라미터 목록 가져오기(변경 이력에 기록하기 위해)
                default_values = self.db_schema.get_default_values(selected_type_id)
                
                # 삭제 전 장비 유형 변경 내역 기록
                self.log_change_history("delete", "equipment_type", type_name, "", "")
                
                # 각 파라미터도 삭제로 기록
                for value_id, param_name, default_val, min_val, max_val, _ in default_values:
                    param_values = f"default: {default_val}, min: {min_val}, max: {max_val}"
                    self.log_change_history("delete", "parameter", param_name, param_values, "")
                
                self.db_schema.delete_equipment_type(selected_type_id)
                self.update_equipment_type_list()
                self.update_log(f"장비 유형 삭제: {type_name}")
            except Exception as e:
                messagebox.showerror("오류", f"장비 유형 삭제 중 오류 발생: {str(e)}")
                self.update_log(f"장비 유형 삭제 오류: {str(e)}")
        
        # 확인/취소 버튼
        ttk.Button(button_frame, text="확인", command=validate_password).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=password_dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Enter 키 바인딩
        password_entry.bind("<Return>", lambda event: validate_password())
        
        # 대화상자가 닫힐 때까지 대기
        self.window.wait_window(password_dialog)
    
    def add_parameter(self):
        """새 파라미터를 추가합니다."""
        if not self.maint_mode:
            messagebox.showinfo("알림", "유지보수 모드에서만 파라미터를 추가할 수 있습니다.")
            return
        
        # 장비 유형이 선택되었는지 확인
        selection = self.equipment_type_listbox.curselection()
        if not selection:
            messagebox.showinfo("알림", "파라미터를 추가할 장비 유형을 선택하세요.")
            return
        
        # 선택된 장비 유형 정보 가져오기
        type_index = selection[0]
        type_name = self.equipment_type_listbox.get(type_index)
        
        # 파라미터 정보 가져오기
        param_name = self.param_name_var.get().strip()
        if not param_name:
            messagebox.showinfo("알림", "파라미터 이름을 입력하세요.")
            return
        
        # 입력값 가져오기
        default_val = self.default_value_var.get().strip()
        min_val = self.min_value_var.get().strip()
        max_val = self.max_value_var.get().strip()
        
        if not default_val:
            messagebox.showinfo("알림", "기본값을 입력하세요.")
            return
        
        # 숫자로 변환 가능한지 확인
        try:
            if default_val:
                float(default_val)
            if min_val:
                float(min_val)
            if max_val:
                float(max_val)
        except ValueError:
            messagebox.showerror("오류", "기본값, 최소값, 최대값은 숫자로 입력해야 합니다.")
            return
        
        # 장비 유형 ID 가져오기
        equipment_types = self.db_schema.get_equipment_types()
        equipment_type_id = None
        for id, name, _ in equipment_types:
            if name == type_name:
                equipment_type_id = id
                break
        
        if not equipment_type_id:
            messagebox.showerror("오류", "장비 유형 ID를 찾을 수 없습니다.")
            return
        
        try:
            # 동일한 파라미터가 있는지 확인
            default_values = self.db_schema.get_default_values(equipment_type_id)
            for _, _, existing_param, _, _, _, _, _ in default_values:
                if existing_param == param_name:
                    messagebox.showinfo("알림", f"'{param_name}' 파라미터가 이미 존재합니다.")
                    return
            
            # 공통 유틸리티를 사용하여 값 형식 변환
            default_val = format_num_value(default_val)
            
            # 최소값 처리
            if min_val:
                min_val = format_num_value(min_val)
            else:
                min_val = default_val
            
            # 최대값 처리
            if max_val:
                max_val = format_num_value(max_val)
            else:
                max_val = default_val
            
            # 파라미터 추가
            new_param_id = self.db_schema.add_default_value(
                equipment_type_id, param_name, default_val, min_val, max_val)
            
            # 변경 이력 기록
            new_param_values = f"default: {default_val}, min: {min_val}, max: {max_val}"
            self.log_change_history("add", "parameter", f"{type_name}_{param_name}", "", new_param_values)
            
            # 파라미터 목록 갱신
            self.on_equipment_type_selected(None)
            self.clear_parameter_form()
            self.update_log(f"파라미터 추가: {param_name}")
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 추가 중 오류 발생: {str(e)}")
            self.update_log(f"파라미터 추가 오류: {str(e)}")


    
    def update_parameter(self):
        """선택한 파라미터를 수정합니다."""
        if not self.maint_mode:
            messagebox.showinfo("알림", "유지보수 모드에서만 파라미터를 수정할 수 있습니다.")
            return
        
        selection = self.parameter_tree.selection()
        if not selection:
            messagebox.showinfo("알림", "수정할 파라미터를 선택하세요.")
            return
        
        # 파라미터 정보 가져오기
        param_name = self.param_name_var.get().strip()
        if not param_name:
            messagebox.showinfo("알림", "파라미터 이름을 입력하세요.")
            return
        
        # 입력값 가져오기
        default_val = self.default_value_var.get().strip()
        min_val = self.min_value_var.get().strip()
        max_val = self.max_value_var.get().strip()
        
        if not default_val:
            messagebox.showinfo("알림", "기본값을 입력하세요.")
            return
        
        # 숫자로 변환 가능한지 확인
        try:
            if default_val:
                float(default_val)
            if min_val:
                float(min_val)
            if max_val:
                float(max_val)
        except ValueError:
            messagebox.showerror("오류", "기본값, 최소값, 최대값은 숫자로 입력해야 합니다.")
            return
        
        # 파라미터 ID 가져오기
        value_id = int(self.parameter_tree.item(selection[0], "tags")[0])
        
        try:
            # 수정 전 값 가져오기
            old_values = self.parameter_tree.item(selection[0], "values")
            old_param_name = old_values[0]  # parameter name
            old_default_val = old_values[1]  # default value
            old_min_val = old_values[2]  # min value
            old_max_val = old_values[3]  # max value
            old_param_values = f"default: {old_default_val}, min: {old_min_val}, max: {old_max_val}"
            
            # 공통 유틸리티를 사용하여 값 형식 변환
            default_val = format_num_value(default_val)
            
            # 최소값 처리
            if min_val:
                min_val = format_num_value(min_val)
            else:
                min_val = default_val
            
            # 최대값 처리
            if max_val:
                max_val = format_num_value(max_val)
            else:
                max_val = default_val
            
            # 파라미터 수정
            self.db_schema.update_default_value(value_id, param_name, default_val, min_val, max_val)
            
            # 변경 이력 기록
            type_name = self.equipment_type_listbox.get(self.equipment_type_listbox.curselection()[0])
            new_param_values = f"default: {default_val}, min: {min_val}, max: {max_val}"
            self.log_change_history("update", "parameter", f"{type_name}_{param_name}", old_param_values, new_param_values)
            
            self.on_equipment_type_selected(None)  # 파라미터 목록 갱신
            self.clear_parameter_form()
            self.update_log(f"파라미터 수정: {param_name}")
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 수정 중 오류 발생: {str(e)}")
            self.update_log(f"파라미터 수정 오류: {str(e)}")

    
    def delete_parameter(self):
        """선택한 파라미터를 삭제합니다."""
        if not self.maint_mode:
            messagebox.showinfo("알림", "유지보수 모드에서만 파라미터를 삭제할 수 있습니다.")
            return
        
        selection = self.parameter_tree.selection()
        if not selection:
            messagebox.showinfo("알림", "삭제할 파라미터를 선택하세요.")
            return
        
        # 파라미터 값 가져오기
        values = self.parameter_tree.item(selection[0], "values")
        param_name = values[0]  # parameter name
        
        confirm = messagebox.askyesno("확인", f"'{param_name}' 파라미터를 삭제하시겠습니까?")
        if not confirm:
            return
        
        # 파라미터 ID 가져오기
        value_id = int(self.parameter_tree.item(selection[0], "tags")[0])
        
        try:
            # 삭제 전 값 가져오기
            old_default_val = values[1]  # default value
            old_min_val = values[2]  # min value
            old_max_val = values[3]  # max value
            old_param_values = f"default: {old_default_val}, min: {old_min_val}, max: {old_max_val}"
            
            # 파라미터 삭제
            self.db_schema.delete_default_value(value_id)
            
            # 변경 이력 기록
            type_name = self.equipment_type_listbox.get(self.equipment_type_listbox.curselection()[0])
            self.log_change_history("delete", "parameter", f"{type_name}_{param_name}", old_param_values, "")
            
            self.on_equipment_type_selected(None)  # 파라미터 목록 갱신
            self.clear_parameter_form()
            self.update_log(f"파라미터 삭제: {param_name}")
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 삭제 중 오류 발생: {str(e)}")
            self.update_log(f"파라미터 삭제 오류: {str(e)}")
    
    # 클래스에 메서드 추가
    cls.log_change_history = log_change_history
    cls.create_default_db_tab = create_default_db_tab
    cls.update_equipment_type_list = update_equipment_type_list
    cls.load_all_parameters = load_all_parameters
    cls.sort_all_parameters = sort_all_parameters
    cls.filter_parameters = filter_parameters
    cls.add_equipment_parameters_to_tree = add_equipment_parameters_to_tree
    cls.on_equipment_type_selected = on_equipment_type_selected
    cls.on_parameter_selected = on_parameter_selected
    cls.clear_parameter_form = clear_parameter_form
    cls.add_equipment_type = add_equipment_type
    cls.delete_equipment_type = delete_equipment_type
    cls.add_parameter = add_parameter
    cls.update_parameter = update_parameter
    cls.delete_parameter = delete_parameter
    
    return cls
