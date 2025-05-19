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

def add_default_db_functions_to_class(cls):
    """
    DBManager 클래스에 Default DB 관리 기능을 추가합니다.
    
    Args:
        cls: 기능을 추가할 클래스 (DBManager)
    """
    
    def create_default_db_tab(self):
        """
        Default DB 관리 탭을 생성합니다.
        장비 유형별 파라미터 관리 및 최소/최대값 설정 기능을 제공합니다.
        """
        default_db_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(default_db_tab, text="Default DB 관리")
        
        # 좌측 프레임 (장비 유형 목록)
        left_frame = ttk.Frame(default_db_tab, width=250, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(left_frame, text="장비 유형 관리", font=('Helvetica', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # 장비 유형 목록 프레임
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 장비 유형 목록 리스트박스
        self.equipment_type_listbox = tk.Listbox(list_frame, height=20, exportselection=False)
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
        right_frame = ttk.Frame(default_db_tab, padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 파라미터 목록 라벨
        self.parameter_label = ttk.Label(right_frame, text="파라미터 목록", font=('Helvetica', 12, 'bold'))
        self.parameter_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 파라미터 트리뷰
        columns = ("parameter", "default", "min", "max")
        self.parameter_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
        
        # 컬럼 설정
        self.parameter_tree.heading("parameter", text="파라미터")
        self.parameter_tree.heading("default", text="기본값")
        self.parameter_tree.heading("min", text="최소값")
        self.parameter_tree.heading("max", text="최대값")
        
        self.parameter_tree.column("parameter", width=200)
        self.parameter_tree.column("default", width=100)
        self.parameter_tree.column("min", width=100)
        self.parameter_tree.column("max", width=100)
        
        # 스크롤바 추가
        tree_scroll = ttk.Scrollbar(right_frame, orient="vertical", command=self.parameter_tree.yview)
        self.parameter_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.parameter_tree.pack(fill=tk.BOTH, expand=True)
        
        # 파라미터 편집 프레임
        edit_frame = ttk.LabelFrame(right_frame, text="파라미터 편집", padding=10)
        edit_frame.pack(fill=tk.X, pady=10)
        
        # 파라미터 이름
        param_frame = ttk.Frame(edit_frame)
        param_frame.pack(fill=tk.X, pady=5)
        ttk.Label(param_frame, text="파라미터 이름:").pack(side=tk.LEFT)
        self.param_name_var = tk.StringVar()
        self.param_name_entry = ttk.Entry(param_frame, textvariable=self.param_name_var, width=30)
        self.param_name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 기본값
        default_frame = ttk.Frame(edit_frame)
        default_frame.pack(fill=tk.X, pady=5)
        ttk.Label(default_frame, text="기본값:").pack(side=tk.LEFT)
        self.default_value_var = tk.StringVar()
        self.default_value_entry = ttk.Entry(default_frame, textvariable=self.default_value_var, width=20)
        self.default_value_entry.pack(side=tk.LEFT, padx=5)
        
        # 최소값
        min_frame = ttk.Frame(edit_frame)
        min_frame.pack(fill=tk.X, pady=5)
        ttk.Label(min_frame, text="최소값:").pack(side=tk.LEFT)
        self.min_value_var = tk.StringVar()
        self.min_value_entry = ttk.Entry(min_frame, textvariable=self.min_value_var, width=20)
        self.min_value_entry.pack(side=tk.LEFT, padx=5)
        
        # 최대값
        max_frame = ttk.Frame(edit_frame)
        max_frame.pack(fill=tk.X, pady=5)
        ttk.Label(max_frame, text="최대값:").pack(side=tk.LEFT)
        self.max_value_var = tk.StringVar()
        self.max_value_entry = ttk.Entry(max_frame, textvariable=self.max_value_var, width=20)
        self.max_value_entry.pack(side=tk.LEFT, padx=5)
        
        # 편집 버튼 프레임
        edit_button_frame = ttk.Frame(edit_frame)
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
            equipment_types = self.db_schema.get_equipment_types()
            for _, type_name, _ in equipment_types:
                self.equipment_type_listbox.insert(tk.END, type_name)
            
            # 파라미터 목록 초기화
            for item in self.parameter_tree.get_children():
                self.parameter_tree.delete(item)
            
            self.clear_parameter_form()
            self.parameter_label.config(text="파라미터 목록")
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 목록 로드 중 오류 발생: {str(e)}")
            self.update_log(f"장비 유형 목록 로드 오류: {str(e)}")
    
    def on_equipment_type_selected(self, event):
        """장비 유형 선택 시 파라미터 목록을 업데이트합니다."""
        selection = self.equipment_type_listbox.curselection()
        if not selection:
            return
        
        type_name = self.equipment_type_listbox.get(selection[0])
        self.parameter_label.config(text=f"'{type_name}' 파라미터 목록")
        
        # 파라미터 목록 초기화
        for item in self.parameter_tree.get_children():
            self.parameter_tree.delete(item)
        
        # 선택된 장비 유형의 ID 가져오기
        equipment_types = self.db_schema.get_equipment_types()
        selected_type_id = None
        for type_id, name, _ in equipment_types:
            if name == type_name:
                selected_type_id = type_id
                break
        
        if selected_type_id is None:
            return
        
        # 파라미터 목록 로드
        try:
            default_values = self.db_schema.get_default_values(selected_type_id)
            for value_id, param_name, default_val, min_val, max_val, _ in default_values:
                self.parameter_tree.insert("", tk.END, values=(param_name, default_val, min_val, max_val), tags=(str(value_id),))
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 목록 로드 중 오류 발생: {str(e)}")
            self.update_log(f"파라미터 목록 로드 오류: {str(e)}")
    
    def on_parameter_selected(self, event):
        """파라미터 선택 시 편집 폼을 업데이트합니다."""
        selection = self.parameter_tree.selection()
        if not selection:
            return
        
        values = self.parameter_tree.item(selection[0], "values")
        self.param_name_var.set(values[0])
        self.default_value_var.set(values[1])
        self.min_value_var.set(values[2])
        self.max_value_var.set(values[3])
    
    def clear_parameter_form(self):
        """파라미터 편집 폼을 초기화합니다."""
        self.param_name_var.set("")
        self.default_value_var.set("")
        self.min_value_var.set("")
        self.max_value_var.set("")
    
    def add_equipment_type(self):
        """새 장비 유형을 추가합니다."""
        if not self.maint_mode:
            messagebox.showinfo("알림", "유지보수 모드에서만 장비 유형을 추가할 수 있습니다.")
            return
        
        type_name = simpledialog.askstring("장비 유형 추가", "추가할 장비 유형 이름을 입력하세요:")
        if not type_name:
            return
        
        try:
            self.db_schema.add_equipment_type(type_name, "")
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
            self.db_schema.delete_equipment_type(selected_type_id)
            self.update_equipment_type_list()
            self.update_log(f"장비 유형 삭제: {type_name}")
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 삭제 중 오류 발생: {str(e)}")
            self.update_log(f"장비 유형 삭제 오류: {str(e)}")
    
    def add_parameter(self):
        """새 파라미터를 추가합니다."""
        if not self.maint_mode:
            messagebox.showinfo("알림", "유지보수 모드에서만 파라미터를 추가할 수 있습니다.")
            return
        
        selection = self.equipment_type_listbox.curselection()
        if not selection:
            messagebox.showinfo("알림", "파라미터를 추가할 장비 유형을 선택하세요.")
            return
        
        param_name = self.param_name_var.get().strip()
        default_val = self.default_value_var.get().strip()
        min_val = self.min_value_var.get().strip()
        max_val = self.max_value_var.get().strip()
        
        if not param_name or not default_val:
            messagebox.showinfo("알림", "파라미터 이름과 기본값은 필수 입력 항목입니다.")
            return
        
        type_name = self.equipment_type_listbox.get(selection[0])
        
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
            # 기본값이 숫자인지 확인
            try:
                if default_val.replace('.', '', 1).isdigit():
                    default_val = float(default_val)
            except:
                pass
            
            # 최소값이 숫자인지 확인
            if min_val:
                try:
                    if min_val.replace('.', '', 1).isdigit():
                        min_val = float(min_val)
                except:
                    pass
            else:
                min_val = default_val
            
            # 최대값이 숫자인지 확인
            if max_val:
                try:
                    if max_val.replace('.', '', 1).isdigit():
                        max_val = float(max_val)
                except:
                    pass
            else:
                max_val = default_val
            
            self.db_schema.add_default_value(selected_type_id, param_name, default_val, min_val, max_val)
            self.on_equipment_type_selected(None)  # 파라미터 목록 갱신
            self.clear_parameter_form()
            self.update_log(f"파라미터 추가: {param_name} (장비 유형: {type_name})")
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
        
        param_name = self.param_name_var.get().strip()
        default_val = self.default_value_var.get().strip()
        min_val = self.min_value_var.get().strip()
        max_val = self.max_value_var.get().strip()
        
        if not param_name or not default_val:
            messagebox.showinfo("알림", "파라미터 이름과 기본값은 필수 입력 항목입니다.")
            return
        
        # 파라미터 ID 가져오기
        value_id = int(self.parameter_tree.item(selection[0], "tags")[0])
        
        try:
            # 기본값이 숫자인지 확인
            try:
                if default_val.replace('.', '', 1).isdigit():
                    default_val = float(default_val)
            except:
                pass
            
            # 최소값이 숫자인지 확인
            if min_val:
                try:
                    if min_val.replace('.', '', 1).isdigit():
                        min_val = float(min_val)
                except:
                    pass
            else:
                min_val = default_val
            
            # 최대값이 숫자인지 확인
            if max_val:
                try:
                    if max_val.replace('.', '', 1).isdigit():
                        max_val = float(max_val)
                except:
                    pass
            else:
                max_val = default_val
            
            self.db_schema.update_default_value(value_id, param_name, default_val, min_val, max_val)
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
        
        param_name = self.parameter_tree.item(selection[0], "values")[0]
        confirm = messagebox.askyesno("확인", f"'{param_name}' 파라미터를 삭제하시겠습니까?")
        if not confirm:
            return
        
        # 파라미터 ID 가져오기
        value_id = int(self.parameter_tree.item(selection[0], "tags")[0])
        
        try:
            self.db_schema.delete_default_value(value_id)
            self.on_equipment_type_selected(None)  # 파라미터 목록 갱신
            self.clear_parameter_form()
            self.update_log(f"파라미터 삭제: {param_name}")
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 삭제 중 오류 발생: {str(e)}")
            self.update_log(f"파라미터 삭제 오류: {str(e)}")
    
    # 클래스에 메서드 추가
    cls.create_default_db_tab = create_default_db_tab
    cls.update_equipment_type_list = update_equipment_type_list
    cls.on_equipment_type_selected = on_equipment_type_selected
    cls.on_parameter_selected = on_parameter_selected
    cls.clear_parameter_form = clear_parameter_form
    cls.add_equipment_type = add_equipment_type
    cls.delete_equipment_type = delete_equipment_type
    cls.add_parameter = add_parameter
    cls.update_parameter = update_parameter
    cls.delete_parameter = delete_parameter
    
    return cls
