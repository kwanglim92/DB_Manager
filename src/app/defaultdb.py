# Default DB 관리 탭 및 기능

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pandas as pd
import numpy as np
from app.utils import create_treeview_with_scrollbar, create_label_entry_pair, format_num_value
from app.loading import LoadingDialog
from app.text_file_handler import TextFileHandler

def center_dialog_on_parent(dialog, parent):
    """
    다이얼로그를 부모 창 중앙에 위치시킵니다.
    
    Args:
        dialog: 위치를 조정할 다이얼로그 윈도우
        parent: 부모 윈도우
    """
    # 다이얼로그와 부모 창의 크기 정보 업데이트
    dialog.update_idletasks()
    parent.update_idletasks()
    
    # 부모 창의 위치와 크기
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    
    # 다이얼로그의 크기
    dialog_width = dialog.winfo_reqwidth()
    dialog_height = dialog.winfo_reqheight()
    
    # 중앙 위치 계산
    x = parent_x + (parent_width - dialog_width) // 2
    y = parent_y + (parent_height - dialog_height) // 2
    
    # 화면 경계 확인 및 조정
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    
    # 화면 밖으로 나가지 않도록 조정
    if x < 0:
        x = 0
    elif x + dialog_width > screen_width:
        x = screen_width - dialog_width
        
    if y < 0:
        y = 0
    elif y + dialog_height > screen_height:
        y = screen_height - dialog_height
    
    # 다이얼로그 위치 설정
    dialog.geometry(f"+{x}+{y}")

def add_default_db_functions_to_class(cls):
    """
    DBManager 클래스에 Default DB 관리 기능을 추가합니다.
    """
    def create_default_db_tab(self):
        """Default DB 관리 탭 생성"""
        default_db_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(default_db_tab, text="Default DB 관리")

        # 상단 프레임: 장비 유형 선택 및 기능 버튼
        top_frame = ttk.LabelFrame(default_db_tab, text="장비 유형 선택", padding=10)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        # 장비 유형 선택
        type_frame = ttk.Frame(top_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="장비 유형:").pack(side=tk.LEFT, padx=5)
        self.equipment_type_var = tk.StringVar()
        self.equipment_type_combobox = ttk.Combobox(
            type_frame, 
            textvariable=self.equipment_type_var, 
            state="readonly", 
            width=30
        )
        self.equipment_type_combobox.pack(side=tk.LEFT, padx=5)
        self.equipment_type_combobox.bind("<<ComboboxSelected>>", self.on_equipment_type_selected)

        # 장비 유형 관리 버튼
        ttk.Button(type_frame, text="장비 유형 관리", command=self.manage_equipment_types).pack(side=tk.LEFT, padx=5)

        # 기능 버튼 프레임
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # 파라미터 관리 버튼
        ttk.Button(
            button_frame, 
            text="파라미터 추가", 
            command=self.add_parameter
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="파라미터 수정", 
            command=self.edit_parameter
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="파라미터 삭제", 
            command=self.delete_parameter
        ).pack(side=tk.LEFT, padx=5)

        # 임포트/익스포트 버튼 (텍스트 파일 우선)
        ttk.Button(
            button_frame, 
            text="텍스트 파일에서 가져오기", 
            command=self.import_from_text_file
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="텍스트 파일로 내보내기", 
            command=self.export_to_text_file
        ).pack(side=tk.LEFT, padx=5)

        # Excel 기능은 두 번째 줄에 배치
        excel_button_frame = ttk.Frame(top_frame)
        excel_button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            excel_button_frame, 
            text="Excel에서 가져오기", 
            command=self.import_from_excel
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            excel_button_frame, 
            text="Excel로 내보내기", 
            command=self.export_to_excel
        ).pack(side=tk.LEFT, padx=5)

        # 중간 프레임: 파라미터 목록
        middle_frame = ttk.LabelFrame(default_db_tab, text="파라미터 목록", padding=10)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 트리뷰 생성 (Module, Part 컬럼 추가)
        columns = ("parameter_name", "module_name", "part_name", "min_spec", "max_spec", "default_value", "description")
        headings = {
            "parameter_name": "파라미터명", 
            "module_name": "Module",
            "part_name": "Part",
            "min_spec": "최소값", 
            "max_spec": "최대값", 
            "default_value": "설정값",
            "description": "설명"
        }
        column_widths = {
            "parameter_name": 200, 
            "module_name": 80,
            "part_name": 100,
            "min_spec": 80, 
            "max_spec": 80, 
            "default_value": 100,
            "description": 200
        }

        param_tree_frame, self.param_tree = create_treeview_with_scrollbar(
            middle_frame, 
            columns, 
            headings, 
            column_widths, 
            height=15
        )
        param_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 트리뷰 이벤트 바인딩
        self.param_tree.bind("<Double-1>", lambda e: self.edit_parameter())
        self.param_tree.bind("<<TreeviewSelect>>", self.on_parameter_selected)

        # 하단 프레임: 파라미터 상세 정보
        bottom_frame = ttk.LabelFrame(default_db_tab, text="파라미터 상세 정보", padding=10)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 상세 정보 프레임
        detail_frame = ttk.Frame(bottom_frame)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 선택한 파라미터 정보 표시 라벨
        self.param_detail_labels = {}
        detail_fields = [
            ("parameter_name", "파라미터명"), 
            ("module_name", "Module"),
            ("part_name", "Part"),
            ("min_spec", "최소값"), 
            ("max_spec", "최대값"), 
            ("default_value", "설정값"),
            ("description", "설명"),
            ("item_type", "데이터 타입"),
            ("created_at", "생성일시"),
            ("updated_at", "수정일시")
        ]

        for i, (field, label) in enumerate(detail_fields):
            ttk.Label(detail_frame, text=f"{label}:", width=12, anchor="e").grid(
                row=i//3, column=(i%3)*2, padx=5, pady=5, sticky="e"
            )
            detail_label = ttk.Label(detail_frame, text="", width=20, anchor="w")
            detail_label.grid(row=i//3, column=(i%3)*2+1, padx=5, pady=5, sticky="w")
            self.param_detail_labels[field] = detail_label

        # 텍스트 파일 핸들러 초기화
        self.text_file_handler = None

        # 장비 유형 목록 로드
        self.load_equipment_types()

    def initialize_text_file_handler(self):
        """텍스트 파일 핸들러를 초기화합니다."""
        if self.text_file_handler is None:
            self.text_file_handler = TextFileHandler(self.db_schema)

    def load_equipment_types(self):
        """장비 유형 목록 로드"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 장비 유형 정보 조회
            cursor.execute("SELECT id, type_name FROM Equipment_Types ORDER BY type_name")
            equipment_types = cursor.fetchall()

            # 콤보박스 업데이트
            if equipment_types:
                self.equipment_types = {name: id for id, name in equipment_types}
                self.equipment_type_combobox['values'] = list(self.equipment_types.keys())
                self.equipment_type_combobox.current(0)  # 첫 번째 항목 선택

                # 선택된 장비 유형의 파라미터 로드
                self.on_equipment_type_selected(None)
            else:
                self.equipment_types = {}
                self.equipment_type_combobox['values'] = []
                messagebox.showinfo("알림", "등록된 장비 유형이 없습니다. 먼저 장비 유형을 추가해주세요.")

            conn.close()
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 로드 중 오류 발생: {str(e)}")

    def on_equipment_type_selected(self, event):
        """장비 유형 선택 시 이벤트 처리"""
        selected_type = self.equipment_type_var.get()
        if not selected_type:
            return

        try:
            # 선택된 장비 유형 ID 저장
            self.selected_equipment_type_id = self.equipment_types[selected_type]

            # 트리뷰 초기화
            for item in self.param_tree.get_children():
                self.param_tree.delete(item)

            # 파라미터 상세 정보 초기화
            for label in self.param_detail_labels.values():
                label.config(text="")

            # 선택된 장비 유형의 파라미터 로드 (Module, Part 정보 포함)
            conn = self.get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT id, parameter_name, min_spec, max_spec, default_value, description, 
                   created_at, updated_at, module_name, part_name, item_type
            FROM Default_DB_Values 
            WHERE equipment_type_id = ? 
            ORDER BY parameter_name
            """
            cursor.execute(query, (self.selected_equipment_type_id,))
            parameters = cursor.fetchall()

            # 파라미터 목록 표시 (Module, Part 컬럼 포함)
            for param in parameters:
                (param_id, name, min_value, max_value, default_value, description, 
                 created_at, updated_at, module_name, part_name, item_type) = param
                
                # 숫자 값 포맷팅
                min_val_fmt = format_num_value(min_value) if min_value is not None else ""
                max_val_fmt = format_num_value(max_value) if max_value is not None else ""
                default_val_fmt = format_num_value(default_value) if default_value is not None else ""

                self.param_tree.insert(
                    "", "end", 
                    iid=param_id,
                    values=(
                        name, 
                        module_name or "", 
                        part_name or "", 
                        min_val_fmt, 
                        max_val_fmt, 
                        default_val_fmt, 
                        description or ""
                    )
                )

            conn.close()
            self.update_log(f"[Default DB] 장비 유형 '{selected_type}'의 파라미터 목록이 로드되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"파라미터 로드 중 오류 발생: {str(e)}")

    def on_parameter_selected(self, event):
        """파라미터 선택 시 상세 정보 표시"""
        selected_items = self.param_tree.selection()
        if not selected_items:
            # 선택 해제 시 상세 정보 초기화
            for label in self.param_detail_labels.values():
                label.config(text="")
            return

        try:
            param_id = selected_items[0]
            
            # DB에서 상세 정보 조회
            conn = self.get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT parameter_name, min_spec, max_spec, default_value, description, 
                   created_at, updated_at, module_name, part_name, item_type
            FROM Default_DB_Values 
            WHERE id = ?
            """
            cursor.execute(query, (param_id,))
            param_detail = cursor.fetchone()

            if param_detail:
                (name, min_spec, max_spec, default_value, description, 
                 created_at, updated_at, module_name, part_name, item_type) = param_detail

                # 상세 정보 업데이트
                self.param_detail_labels["parameter_name"].config(text=name or "")
                self.param_detail_labels["module_name"].config(text=module_name or "")
                self.param_detail_labels["part_name"].config(text=part_name or "")
                self.param_detail_labels["min_spec"].config(text=format_num_value(min_spec) if min_spec else "")
                self.param_detail_labels["max_spec"].config(text=format_num_value(max_spec) if max_spec else "")
                self.param_detail_labels["default_value"].config(text=format_num_value(default_value) if default_value else "")
                self.param_detail_labels["description"].config(text=description or "")
                self.param_detail_labels["item_type"].config(text=item_type or "")
                self.param_detail_labels["created_at"].config(text=created_at or "")
                self.param_detail_labels["updated_at"].config(text=updated_at or "")

            conn.close()

        except Exception as e:
            messagebox.showerror("오류", f"파라미터 상세 정보 로드 중 오류 발생: {str(e)}")

    def manage_equipment_types(self):
        """장비 유형 관리 대화상자"""
        equipment_type_dialog = tk.Toplevel(self.window)
        equipment_type_dialog.title("장비 유형 관리")
        equipment_type_dialog.geometry("600x400")
        equipment_type_dialog.transient(self.window)
        equipment_type_dialog.grab_set()

        # 부모 창 중앙에 배치
        center_dialog_on_parent(equipment_type_dialog, self.window)

        # 리스트박스 프레임
        list_frame = ttk.LabelFrame(equipment_type_dialog, text="장비 유형 목록")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 리스트박스와 스크롤바
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        equipment_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        equipment_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar.config(command=equipment_listbox.yview)

        # 버튼 프레임
        button_frame = ttk.Frame(equipment_type_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # 버튼 추가
        ttk.Button(
            button_frame, 
            text="추가", 
            command=lambda: self.add_equipment_type(equipment_listbox, equipment_type_dialog)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="수정", 
            command=lambda: self.edit_equipment_type(equipment_listbox, equipment_type_dialog)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="삭제", 
            command=lambda: self.delete_equipment_type(equipment_listbox, equipment_type_dialog)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="닫기", 
            command=equipment_type_dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # 장비 유형 목록 로드
        self.load_equipment_type_list(equipment_listbox)

    def load_equipment_type_list(self, listbox):
        """장비 유형 목록을 리스트박스에 로드"""
        # 리스트박스 초기화
        listbox.delete(0, tk.END)

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 장비 유형 조회
            cursor.execute("SELECT id, type_name FROM Equipment_Types ORDER BY type_name")
            equipment_types = cursor.fetchall()

            # 리스트박스에 추가
            for id, name in equipment_types:
                listbox.insert(tk.END, f"{name} (ID: {id})")

            conn.close()
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 로드 중 오류 발생: {str(e)}")

    def add_equipment_type(self, listbox, dialog):
        """장비 유형 추가"""
        # 장비 유형명 입력 대화상자
        type_name = simpledialog.askstring("장비 유형 추가", "새 장비 유형명을 입력하세요:")

        if not type_name:
            return

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 중복 체크
            cursor.execute("SELECT COUNT(*) FROM Equipment_Types WHERE type_name = ?", (type_name,))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("오류", "이미 존재하는 장비 유형명입니다.")
                conn.close()
                return

            # 장비 유형 추가
            cursor.execute(
                "INSERT INTO Equipment_Types (type_name) VALUES (?)", 
                (type_name,)
            )
            conn.commit()

            # 리스트박스 갱신
            self.load_equipment_type_list(listbox)

            # 🆕 전체 탭 동기화 - 중앙화된 새로고침 함수 호출
            if hasattr(self, 'refresh_all_equipment_type_lists'):
                self.refresh_all_equipment_type_lists()
            else:
                # 콤보박스도 갱신 (fallback)
                self.load_equipment_types()

            # 로그 업데이트
            self.update_log(f"[Default DB] 새 장비 유형 '{type_name}'이(가) 추가되었습니다.")

            conn.close()
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 추가 중 오류 발생: {str(e)}")

    def edit_equipment_type(self, listbox, dialog):
        """장비 유형 수정"""
        # 선택된 항목 확인
        selected_index = listbox.curselection()
        if not selected_index:
            messagebox.showinfo("알림", "수정할 장비 유형을 선택하세요.")
            return

        # 선택된 항목의 ID 추출
        selected_item = listbox.get(selected_index[0])
        type_id = int(selected_item.split("ID: ")[1].strip(")"))
        old_name = selected_item.split(" (ID:")[0]

        # 새 이름 입력
        new_name = simpledialog.askstring("장비 유형 수정", "새 장비 유형명을 입력하세요:")

        if not new_name or new_name == old_name:
            return

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 중복 체크
            cursor.execute("SELECT COUNT(*) FROM Equipment_Types WHERE type_name = ? AND id != ?", (new_name, type_id))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("오류", "이미 존재하는 장비 유형명입니다.")
                conn.close()
                return

            # 장비 유형 수정
            cursor.execute(
                "UPDATE Equipment_Types SET type_name = ? WHERE id = ?", 
                (new_name, type_id)
            )
            conn.commit()

            # 리스트박스 갱신
            self.load_equipment_type_list(listbox)

            # 🆕 전체 탭 동기화 - 중앙화된 새로고침 함수 호출
            if hasattr(self, 'refresh_all_equipment_type_lists'):
                self.refresh_all_equipment_type_lists()
            else:
                # 콤보박스도 갱신 (fallback)
                self.load_equipment_types()

            # 로그 업데이트
            self.update_log(f"[Default DB] 장비 유형이 '{old_name}'에서 '{new_name}'으로 수정되었습니다.")

            conn.close()
        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 수정 중 오류 발생: {str(e)}")

    def delete_equipment_type(self, listbox, dialog):
        """장비 유형 삭제"""
        # 선택된 항목 확인
        selected_index = listbox.curselection()
        if not selected_index:
            messagebox.showinfo("알림", "삭제할 장비 유형을 선택하세요.")
            return

        # 선택된 항목의 ID와 이름 추출
        selected_item = listbox.get(selected_index[0])
        type_id = int(selected_item.split("ID: ")[1].strip(")"))
        type_name = selected_item.split(" (ID:")[0]

        # 삭제 확인
        confirm = messagebox.askyesno(
            "삭제 확인", 
            f"장비 유형 '{type_name}'을(를) 삭제하시겠습니까?\n\n주의: 관련된 모든 파라미터가 함께 삭제됩니다!"
        )

        if not confirm:
            return

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 트랜잭션 시작
            conn.execute("BEGIN TRANSACTION")

            # 관련 파라미터 삭제 (Default_DB_Values 테이블에서)
            cursor.execute("DELETE FROM Default_DB_Values WHERE equipment_type_id = ?", (type_id,))

            # 장비 유형 삭제
            cursor.execute("DELETE FROM Equipment_Types WHERE id = ?", (type_id,))

            # 트랜잭션 커밋
            conn.commit()

            # 리스트박스 갱신
            self.load_equipment_type_list(listbox)

            # 🆕 전체 탭 동기화 - 중앙화된 새로고침 함수 호출
            if hasattr(self, 'refresh_all_equipment_type_lists'):
                self.refresh_all_equipment_type_lists()
            else:
                # 콤보박스도 갱신 (fallback)
                self.load_equipment_types()

            # 로그 업데이트
            self.update_log(f"[Default DB] 장비 유형 '{type_name}'이(가) 삭제되었습니다.")

            conn.close()
        except Exception as e:
            conn.rollback()  # 오류 발생 시 롤백
            messagebox.showerror("오류", f"장비 유형 삭제 중 오류 발생: {str(e)}")

    def add_parameter(self):
        """파라미터 추가"""
        # 장비 유형 선택 여부 확인
        if not hasattr(self, 'selected_equipment_type_id'):
            messagebox.showinfo("알림", "먼저 장비 유형을 선택해주세요.")
            return

        # 파라미터 추가 대화상자
        param_dialog = tk.Toplevel(self.window)
        param_dialog.title("파라미터 추가")
        param_dialog.geometry("450x420")
        param_dialog.transient(self.window)
        param_dialog.grab_set()

        param_frame = ttk.Frame(param_dialog, padding=10)
        param_frame.pack(fill=tk.BOTH, expand=True)

        # 파라미터 입력 필드 (Module, Part, ItemType 추가)
        name_var, name_entry = create_label_entry_pair(param_frame, "파라미터명:", row=0)
        module_var, module_entry = create_label_entry_pair(param_frame, "Module:", row=1)
        part_var, part_entry = create_label_entry_pair(param_frame, "Part:", row=2)
        
        # ItemType 콤보박스
        ttk.Label(param_frame, text="데이터 타입:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        item_type_var = tk.StringVar()
        item_type_combo = ttk.Combobox(
            param_frame, 
            textvariable=item_type_var, 
            values=["double", "int", "string"], 
            state="readonly"
        )
        item_type_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        item_type_combo.set("double")  # 기본값
        
        min_var, min_entry = create_label_entry_pair(param_frame, "최소값:", row=4)
        max_var, max_entry = create_label_entry_pair(param_frame, "최대값:", row=5)
        default_var, default_entry = create_label_entry_pair(param_frame, "설정값:", row=6)

        # 설명 필드 (여러 줄)
        ttk.Label(param_frame, text="설명:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        desc_text = tk.Text(param_frame, height=4, width=30)
        desc_text.grid(row=7, column=1, padx=5, pady=5, sticky="ew")

        # 열 너비 조정
        param_frame.columnconfigure(1, weight=1)

        # 버튼 프레임
        button_frame = ttk.Frame(param_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # 부모 창 중앙에 배치
        center_dialog_on_parent(param_dialog, self.window)

        # 저장 함수
        def save_parameter():
            # 입력값 검증
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("오류", "파라미터명은 필수 입력 항목입니다.")
                return

            module_name = module_var.get().strip()
            part_name = part_var.get().strip()
            item_type = item_type_var.get()

            # 숫자 입력값 변환
            try:
                min_value = float(min_var.get()) if min_var.get().strip() else None
                max_value = float(max_var.get()) if max_var.get().strip() else None
            except ValueError:
                messagebox.showerror("오류", "최소값과 최대값은 숫자여야 합니다.")
                return

            # 최소값/최대값 검증
            if min_value is not None and max_value is not None and min_value > max_value:
                messagebox.showerror("오류", "최소값이 최대값보다 클 수 없습니다.")
                return

            default_value = default_var.get().strip()
            description = desc_text.get("1.0", tk.END).strip()

            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()

                # 중복 체크
                cursor.execute(
                    "SELECT COUNT(*) FROM Default_DB_Values WHERE parameter_name = ? AND equipment_type_id = ?", 
                    (name, self.selected_equipment_type_id)
                )
                if cursor.fetchone()[0] > 0:
                    messagebox.showerror("오류", "이미 존재하는 파라미터명입니다.")
                    conn.close()
                    return

                # 파라미터 추가 (Module, Part, ItemType 포함)
                cursor.execute(
                    """INSERT INTO Default_DB_Values 
                       (equipment_type_id, parameter_name, min_spec, max_spec, default_value, description,
                        module_name, part_name, item_type) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                    (self.selected_equipment_type_id, name, min_value, max_value, default_value, description,
                     module_name, part_name, item_type)
                )
                conn.commit()

                # 대화상자 닫기
                param_dialog.destroy()

                # 파라미터 목록 갱신
                self.on_equipment_type_selected(None)

                # 로그 업데이트
                equipment_type = self.equipment_type_var.get()
                self.update_log(f"[Default DB] 장비 유형 '{equipment_type}'에 새 파라미터 '{name}'이(가) 추가되었습니다.")

                conn.close()
            except Exception as e:
                messagebox.showerror("오류", f"파라미터 추가 중 오류 발생: {str(e)}")

        # 버튼 추가
        ttk.Button(button_frame, text="저장", command=save_parameter).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=param_dialog.destroy).pack(side=tk.RIGHT, padx=5)

        # 첫 번째 필드에 포커스
        name_entry.focus_set()

    def edit_parameter(self):
        """파라미터 수정"""
        # 선택된 파라미터 확인
        selected_items = self.param_tree.selection()
        if not selected_items:
            messagebox.showinfo("알림", "수정할 파라미터를 선택하세요.")
            return

        param_id = selected_items[0]

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 파라미터 정보 조회 (Module, Part, ItemType 포함)
            cursor.execute(
                """SELECT parameter_name, min_spec, max_spec, default_value, description,
                          module_name, part_name, item_type
                   FROM Default_DB_Values WHERE id = ?""", 
                (param_id,)
            )
            param_data = cursor.fetchone()

            if not param_data:
                messagebox.showerror("오류", "파라미터 정보를 찾을 수 없습니다.")
                conn.close()
                return

            (name, min_value, max_value, default_value, description, 
             module_name, part_name, item_type) = param_data

            # 파라미터 수정 대화상자
            param_dialog = tk.Toplevel(self.window)
            param_dialog.title("파라미터 수정")
            param_dialog.geometry("450x420")
            param_dialog.transient(self.window)
            param_dialog.grab_set()

            param_frame = ttk.Frame(param_dialog, padding=10)
            param_frame.pack(fill=tk.BOTH, expand=True)

            # 파라미터 입력 필드 (Module, Part, ItemType 포함)
            name_var, name_entry = create_label_entry_pair(param_frame, "파라미터명:", row=0, initial_value=name)
            module_var, module_entry = create_label_entry_pair(param_frame, "Module:", row=1, initial_value=module_name or "")
            part_var, part_entry = create_label_entry_pair(param_frame, "Part:", row=2, initial_value=part_name or "")
            
            # ItemType 콤보박스
            ttk.Label(param_frame, text="데이터 타입:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
            item_type_var = tk.StringVar()
            item_type_combo = ttk.Combobox(
                param_frame, 
                textvariable=item_type_var, 
                values=["double", "int", "string"], 
                state="readonly"
            )
            item_type_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
            item_type_combo.set(item_type or "double")  # 기존값 또는 기본값
            
            min_var, min_entry = create_label_entry_pair(
                param_frame, "최소값:", row=4, 
                initial_value=str(min_value) if min_value is not None else ""
            )
            max_var, max_entry = create_label_entry_pair(
                param_frame, "최대값:", row=5, 
                initial_value=str(max_value) if max_value is not None else ""
            )
            default_var, default_entry = create_label_entry_pair(param_frame, "설정값:", row=6, initial_value=default_value or "")

            # 설명 필드 (여러 줄)
            ttk.Label(param_frame, text="설명:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
            desc_text = tk.Text(param_frame, height=4, width=30)
            desc_text.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
            desc_text.insert("1.0", description or "")

            # 열 너비 조정
            param_frame.columnconfigure(1, weight=1)

            # 버튼 프레임
            button_frame = ttk.Frame(param_dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            # 부모 창 중앙에 배치
            center_dialog_on_parent(param_dialog, self.window)

            # 저장 함수
            def save_parameter():
                # 입력값 검증
                new_name = name_var.get().strip()
                if not new_name:
                    messagebox.showerror("오류", "파라미터명은 필수 입력 항목입니다.")
                    return

                new_module_name = module_var.get().strip()
                new_part_name = part_var.get().strip()
                new_item_type = item_type_var.get()

                # 숫자 입력값 변환
                try:
                    new_min_value = float(min_var.get()) if min_var.get().strip() else None
                    new_max_value = float(max_var.get()) if max_var.get().strip() else None
                except ValueError:
                    messagebox.showerror("오류", "최소값과 최대값은 숫자여야 합니다.")
                    return

                # 최소값/최대값 검증
                if new_min_value is not None and new_max_value is not None and new_min_value > new_max_value:
                    messagebox.showerror("오류", "최소값이 최대값보다 클 수 없습니다.")
                    return

                new_default_value = default_var.get().strip()
                new_description = desc_text.get("1.0", tk.END).strip()

                try:
                    conn = self.get_db_connection()
                    cursor = conn.cursor()

                    # 중복 체크 (이름이 변경된 경우)
                    if new_name != name:
                        cursor.execute(
                            """SELECT COUNT(*) FROM Default_DB_Values 
                               WHERE parameter_name = ? AND equipment_type_id = ? AND id != ?""", 
                            (new_name, self.selected_equipment_type_id, param_id)
                        )
                        if cursor.fetchone()[0] > 0:
                            messagebox.showerror("오류", "이미 존재하는 파라미터명입니다.")
                            conn.close()
                            return

                    # 파라미터 수정 (Module, Part, ItemType 포함)
                    cursor.execute(
                        """UPDATE Default_DB_Values 
                           SET parameter_name = ?, min_spec = ?, max_spec = ?, default_value = ?, 
                               description = ?, module_name = ?, part_name = ?, item_type = ?,
                               updated_at = CURRENT_TIMESTAMP 
                           WHERE id = ?""", 
                        (new_name, new_min_value, new_max_value, new_default_value, new_description,
                         new_module_name, new_part_name, new_item_type, param_id)
                    )
                    conn.commit()

                    # 대화상자 닫기
                    param_dialog.destroy()

                    # 파라미터 목록 갱신
                    self.on_equipment_type_selected(None)

                    # 로그 업데이트
                    equipment_type = self.equipment_type_var.get()
                    self.update_log(f"[Default DB] 장비 유형 '{equipment_type}'의 파라미터 '{name}'이(가) 수정되었습니다.")

                    conn.close()
                except Exception as e:
                    messagebox.showerror("오류", f"파라미터 수정 중 오류 발생: {str(e)}")

            # 버튼 추가
            ttk.Button(button_frame, text="저장", command=save_parameter).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="취소", command=param_dialog.destroy).pack(side=tk.RIGHT, padx=5)

            # 첫 번째 필드에 포커스
            name_entry.focus_set()

            conn.close()
        except Exception as e:
            messagebox.showerror("오류", f"파라미터 정보 로드 중 오류 발생: {str(e)}")

    def delete_parameter(self):
        """파라미터 삭제"""
        # 선택된 파라미터 확인
        selected_items = self.param_tree.selection()
        if not selected_items:
            messagebox.showinfo("알림", "삭제할 파라미터를 선택하세요.")
            return

        param_id = selected_items[0]
        param_name = self.param_tree.item(param_id, 'values')[0]

        # 삭제 확인
        confirm = messagebox.askyesno(
            "삭제 확인", 
            f"파라미터 '{param_name}'을(를) 삭제하시겠습니까?\n\n주의: 관련된 모든 데이터가 함께 삭제됩니다!"
        )

        if not confirm:
            return

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 트랜잭션 시작
            conn.execute("BEGIN TRANSACTION")

            # 파라미터 삭제 (Default_DB_Values 테이블에서)
            cursor.execute("DELETE FROM Default_DB_Values WHERE id = ?", (param_id,))

            # 트랜잭션 커밋
            conn.commit()

            # 파라미터 목록 갱신
            self.on_equipment_type_selected(None)

            # 로그 업데이트
            equipment_type = self.equipment_type_var.get()
            self.update_log(f"[Default DB] 장비 유형 '{equipment_type}'의 파라미터 '{param_name}'이(가) 삭제되었습니다.")

            conn.close()
        except Exception as e:
            conn.rollback()  # 오류 발생 시 롤백
            messagebox.showerror("오류", f"파라미터 삭제 중 오류 발생: {str(e)}")

    def import_from_excel(self):
        """Excel 파일에서 파라미터 임포트"""
        # 장비 유형 선택 여부 확인
        if not hasattr(self, 'selected_equipment_type_id'):
            messagebox.showinfo("알림", "먼저 장비 유형을 선택해주세요.")
            return

        # 파일 선택 대화상자
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel 파일", "*.xlsx *.xls"), ("모든 파일", "*.*")],
            title="파라미터 목록 Excel 파일 선택"
        )

        if not file_path:
            return

        try:
            # 로딩 대화상자 표시
            loading_dialog = LoadingDialog(self.window)
            loading_dialog.update_progress(10, "Excel 파일을 Import하는 중...")
            
            try:
                # Excel 파일 로드
                df = pd.read_excel(file_path)

                # 필수 열 확인
                required_columns = ["파라미터명", "최소값", "최대값"]
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    loading_dialog.close()
                    messagebox.showerror("오류", f"필수 열이 누락되었습니다: {', '.join(missing_columns)}")
                    return

                # 데이터 변환 및 검증
                loading_dialog.update_progress(30, "데이터 검증 중...")

                # 열 이름 매핑
                column_mapping = {
                    "파라미터명": "name",
                    "최소값": "min_value",
                    "최대값": "max_value",
                    "설정값": "default_value",
                    "설명": "description"
                }

                # 열 이름 변경
                df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

                # 누락된 열 추가
                for col in ["default_value", "description"]:
                    if col not in df.columns:
                        df[col] = None

                # 데이터 정리
                df['name'] = df['name'].astype(str).str.strip()

                # 숫자 데이터 변환 (NaN 처리)
                for col in ["min_value", "max_value"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                # 빈 파라미터명 행 제거
                df = df[df['name'].notna() & (df['name'] != "")].reset_index(drop=True)

                if len(df) == 0:
                    loading_dialog.close()
                    messagebox.showinfo("알림", "임포트할 유효한 파라미터가 없습니다.")
                    return

                # DB 연결
                conn = self.get_db_connection()
                cursor = conn.cursor()

                # 기존 파라미터 조회
                loading_dialog.update_progress(50, "기존 파라미터 확인 중...")
                cursor.execute(
                    "SELECT parameter_name FROM Default_DB_Values WHERE equipment_type_id = ?", 
                    (self.selected_equipment_type_id,)
                )
                existing_params = [row[0] for row in cursor.fetchall()]

                # 중복 파라미터 확인
                duplicates = df[df['name'].isin(existing_params)]['name'].unique().tolist()

                # 중복 처리 여부 확인
                if duplicates:
                    loading_dialog.close()
                    confirm = messagebox.askyesno(
                        "중복 확인", 
                        f"{len(duplicates)}개의 파라미터가 이미 존재합니다. 덮어쓰시겠습니까?\n\n{', '.join(duplicates[:5])}{' 외 더 있음' if len(duplicates) > 5 else ''}"
                    )

                    if not confirm:
                        return

                    loading_dialog = LoadingDialog(self.window)
                    self.window.update_idletasks()
                    loading_dialog.update_progress(60, "데이터 준비 중...")

                # 트랜잭션 시작
                conn.execute("BEGIN TRANSACTION")

                # 파라미터 추가/업데이트
                loading_dialog.update_progress(70, "파라미터 임포트 중...")

                total_count = len(df)
                added_count = 0
                updated_count = 0

                for idx, (i, row) in enumerate(df.iterrows()):
                    # 진행률 업데이트
                    progress = 70 + int(25 * (idx / total_count))
                    loading_dialog.update_progress(progress, f"파라미터 임포트 중... ({idx+1}/{total_count})")

                    name = row['name']
                    min_value = row['min_value'] if not pd.isna(row['min_value']) else None
                    max_value = row['max_value'] if not pd.isna(row['max_value']) else None
                    default_value = row['default_value'] if 'default_value' in row and not pd.isna(row['default_value']) else None
                    description = row['description'] if 'description' in row and not pd.isna(row['description']) else None

                    # 기존 파라미터인지 확인
                    if name in existing_params:
                        # 업데이트
                        cursor.execute(
                            """UPDATE Default_DB_Values 
                               SET min_spec = ?, max_spec = ?, default_value = ?, 
                                   description = ?, updated_at = CURRENT_TIMESTAMP 
                               WHERE parameter_name = ? AND equipment_type_id = ?""", 
                            (min_value, max_value, default_value, description, name, self.selected_equipment_type_id)
                        )
                        updated_count += 1
                    else:
                        # 추가
                        cursor.execute(
                            """INSERT INTO Default_DB_Values 
                               (equipment_type_id, parameter_name, min_spec, max_spec, default_value, description) 
                               VALUES (?, ?, ?, ?, ?, ?)""", 
                            (self.selected_equipment_type_id, name, min_value, max_value, default_value, description)
                        )
                        added_count += 1

                # 트랜잭션 커밋
                conn.commit()

                # 파라미터 목록 갱신
                loading_dialog.update_progress(95, "화면 갱신 중...")
                self.on_equipment_type_selected(None)

                # 완료
                loading_dialog.update_progress(100, "완료")
                conn.close()
                loading_dialog.close()

                # 결과 메시지
                equipment_type = self.equipment_type_var.get()
                self.update_log(f"[Default DB] 장비 유형 '{equipment_type}'에 파라미터 {added_count}개 추가, {updated_count}개 업데이트 완료.")

                messagebox.showinfo(
                    "임포트 완료", 
                    f"파라미터 임포트가 완료되었습니다.\n\n- 추가: {added_count}개\n- 업데이트: {updated_count}개\n- 총 처리: {total_count}개"
                )

            except Exception as e:
                # 오류 처리
                if 'conn' in locals() and conn:
                    conn.rollback()  # 오류 발생 시 롤백
                    conn.close()

                if 'loading_dialog' in locals() and loading_dialog:
                    loading_dialog.close()

                messagebox.showerror("오류", f"파라미터 임포트 중 오류 발생: {str(e)}")

        except Exception as e:
            messagebox.showerror("오류", f"파일 로드 중 오류 발생: {str(e)}")

    def export_to_excel(self):
        """파라미터 목록을 Excel 파일로 내보내기"""
        # 장비 유형 선택 여부 확인
        if not hasattr(self, 'selected_equipment_type_id'):
            messagebox.showinfo("알림", "먼저 장비 유형을 선택해주세요.")
            return

        # 파라미터 있는지 확인
        if not self.param_tree.get_children():
            messagebox.showinfo("알림", "내보낼 파라미터가 없습니다.")
            return

        # 파일 저장 대화상자
        equipment_type = self.equipment_type_var.get()
        default_filename = f"{equipment_type}_파라미터목록.xlsx"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")],
            title="파라미터 목록 저장",
            initialfile=default_filename
        )

        if not file_path:
            return

        try:
            # 로딩 대화상자 표시
            loading_dialog = LoadingDialog(self.window)
            self.window.update_idletasks()
            loading_dialog.update_progress(10, "데이터 변환 중...")

            # DB에서 파라미터 데이터 조회
            conn = self.get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT id, parameter_name, min_spec, max_spec, default_value, description, created_at, updated_at 
            FROM Default_DB_Values 
            WHERE equipment_type_id = ? 
            ORDER BY parameter_name
            """
            cursor.execute(query, (self.selected_equipment_type_id,))
            parameters = cursor.fetchall()

            # 데이터프레임 생성
            loading_dialog.update_progress(40, "데이터 변환 중...")
            df = pd.DataFrame(parameters, columns=[
                "파라미터명", "최소값", "최대값", "설정값", "설명", "생성일시", "수정일시"
            ])

            # 추가 정보 시트 준비
            loading_dialog.update_progress(70, "메타데이터 준비 중...")

            # 장비 유형 정보 조회
            cursor.execute("SELECT * FROM Equipment_Types WHERE id = ?", (self.selected_equipment_type_id,))
            equipment_info = cursor.fetchone()

            info_data = {
                "정보": ["장비 유형명", "장비 유형 ID", "파라미터 개수", "내보내기 일시"],
                "값": [
                    equipment_info[1],  # name
                    equipment_info[0],  # id
                    len(parameters),
                    pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            info_df = pd.DataFrame(info_data)

            # Excel 저장
            loading_dialog.update_progress(90, "파일 저장 중...")
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="파라미터 목록", index=False)
                info_df.to_excel(writer, sheet_name="메타데이터", index=False)

            # 완료
            loading_dialog.update_progress(100, "완료")
            conn.close()
            loading_dialog.close()

            # 로그 업데이트
            self.update_log(f"[Default DB] 장비 유형 '{equipment_type}'의 파라미터 목록을 '{file_path}'에 저장했습니다.")

            messagebox.showinfo(
                "내보내기 완료", 
                f"파라미터 목록이 성공적으로 저장되었습니다.\n\n- 파일: {file_path}\n- 총 {len(parameters)}개의 파라미터 저장됨"
            )

        except Exception as e:
            if 'loading_dialog' in locals():
                loading_dialog.close()

            if 'conn' in locals():
                conn.close()

            messagebox.showerror("오류", f"파일 저장 중 오류 발생: {str(e)}")

    def import_from_text_file(self):
        """텍스트 파일에서 파라미터 Import"""
        try:
            self.initialize_text_file_handler()
            
            # 파일 선택 대화상자
            file_path = filedialog.askopenfilename(
                title="텍스트 파일 선택",
                filetypes=[
                    ("텍스트 파일", "*.txt"),
                    ("모든 파일", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # 파일 형식 먼저 검증
            is_valid, error_msg = self.text_file_handler.validate_text_file_format(file_path)
            if not is_valid:
                messagebox.showerror("오류", error_msg)
                return
            
            # 장비 유형명 입력받기 (로딩 다이얼로그 전에)
            equipment_type_name = simpledialog.askstring(
                "장비 유형", 
                f"장비 유형명을 입력하세요:\n(파일: {os.path.basename(file_path)})"
            )
            
            if not equipment_type_name:
                messagebox.showinfo("알림", "Import가 취소되었습니다.")
                return
            
            # 로딩 다이얼로그 표시
            loading_dialog = LoadingDialog(self.window)
            loading_dialog.update_progress(10, "텍스트 파일을 Import하는 중...")
            
            try:
                # Import 실행
                success, message = self.text_file_handler.import_from_text_file(file_path, equipment_type_name)
                loading_dialog.update_progress(100, "완료")
                loading_dialog.close()
                
                if success:
                    messagebox.showinfo("성공", message)
                    # 장비 유형 목록과 파라미터 목록 새로고침
                    self.load_equipment_types()
                    self.update_log("[Default DB] 텍스트 파일 Import가 완료되었습니다.")
                else:
                    messagebox.showerror("오류", message)
                    
            except Exception as e:
                loading_dialog.close()
                messagebox.showerror("오류", f"Import 중 오류 발생: {str(e)}")

        except Exception as e:
            messagebox.showerror("오류", f"텍스트 파일 Import 중 오류 발생: {str(e)}")

    def export_to_text_file(self):
        """텍스트 파일로 파라미터 Export"""
        try:
            # 장비 유형이 선택되었는지 확인
            if not hasattr(self, 'selected_equipment_type_id') or not self.selected_equipment_type_id:
                messagebox.showwarning("경고", "먼저 장비 유형을 선택해주세요.")
                return
            
            self.initialize_text_file_handler()
            
            # Export 데이터 검증
            is_valid, message, data_count = self.text_file_handler.validate_export_data(self.selected_equipment_type_id)
            if not is_valid:
                messagebox.showerror("오류", message)
                return
            
            # 확인 대화상자
            selected_type = self.equipment_type_var.get()
            if not messagebox.askyesno("확인", f"장비 유형 '{selected_type}'의 {data_count}개 파라미터를 텍스트 파일로 Export하시겠습니까?"):
                return
            
            # 파일 저장 대화상자
            file_path = filedialog.asksaveasfilename(
                title="텍스트 파일로 저장",
                defaultextension=".txt",
                filetypes=[
                    ("텍스트 파일", "*.txt"),
                    ("모든 파일", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # 로딩 다이얼로그 표시
            loading_dialog = LoadingDialog(self.window)
            loading_dialog.update_progress(10, "텍스트 파일로 Export하는 중...")
            
            try:
                success, message = self.text_file_handler.export_to_text_file(self.selected_equipment_type_id, file_path)
                loading_dialog.update_progress(100, "완료")
                loading_dialog.close()
                
                if success:
                    messagebox.showinfo("성공", message)
                    self.update_log("[Default DB] 텍스트 파일 Export가 완료되었습니다.")
                else:
                    messagebox.showerror("오류", message)
                    
            except Exception as e:
                loading_dialog.close()
                messagebox.showerror("오류", f"Export 중 오류 발생: {str(e)}")

        except Exception as e:
            messagebox.showerror("오류", f"텍스트 파일 Export 중 오류 발생: {str(e)}")

    # 클래스에 함수 추가
    cls.create_default_db_tab = create_default_db_tab
    cls.initialize_text_file_handler = initialize_text_file_handler
    cls.load_equipment_types = load_equipment_types
    cls.on_equipment_type_selected = on_equipment_type_selected
    cls.on_parameter_selected = on_parameter_selected
    cls.manage_equipment_types = manage_equipment_types
    cls.load_equipment_type_list = load_equipment_type_list
    cls.add_equipment_type = add_equipment_type
    cls.edit_equipment_type = edit_equipment_type
    cls.delete_equipment_type = delete_equipment_type
    cls.add_parameter = add_parameter
    cls.edit_parameter = edit_parameter
    cls.delete_parameter = delete_parameter
    cls.import_from_excel = import_from_excel
    cls.export_to_excel = export_to_excel
    cls.import_from_text_file = import_from_text_file
    cls.export_to_text_file = export_to_text_file
