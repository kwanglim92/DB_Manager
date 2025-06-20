# 파일 처리 모듈 - 파일 로드 및 저장 관련 기능

import os
import pandas as pd
import numpy as np
import sqlite3
import tkinter as tk
from tkinter import messagebox
from app.loading import LoadingDialog
from app.utils import format_num_value, create_sqlite_connection, execute_query

def add_file_handler_functions_to_class(cls):
    """
    DBManager 클래스에 파일 처리 기능을 추가합니다.
    """
    def load_folder(self):
        """폴더에서 파일 로드"""
        # 폴더 선택 대화상자
        from tkinter import filedialog
        folder_path = filedialog.askdirectory(title="데이터 폴더 선택")

        if not folder_path:
            return

        self.folder_path = folder_path

        # 로딩 대화상자 표시
        loading_dialog = LoadingDialog(self.window)
        self.window.update_idletasks()

        try:
            # 폴더 내 엑셀 파일 목록 수집
            loading_dialog.update_progress(5, "파일 목록 수집 중...")
            excel_files = []
            for file in os.listdir(folder_path):
                if file.lower().endswith(('.xlsx', '.xls')) and not file.startswith('~$'):
                    excel_files.append(os.path.join(folder_path, file))

            if not excel_files:
                loading_dialog.close()
                messagebox.showinfo("알림", "선택한 폴더에 Excel 파일이 없습니다.")
                return

            # Default DB 파라미터 로드
            loading_dialog.update_progress(10, "Default DB 파라미터 로드 중...")
            default_params = self.load_default_parameters()

            if not default_params:
                loading_dialog.close()
                messagebox.showinfo("알림", "Default DB에서 파라미터를 로드할 수 없습니다.")
                return

            # 파일별 데이터 로드
            file_dfs = []
            self.file_names = []

            total_files = len(excel_files)
            for i, file_path in enumerate(excel_files):
                file_name = os.path.basename(file_path)
                progress = 10 + int(70 * (i / total_files))
                loading_dialog.update_progress(progress, f"파일 로드 중... ({i+1}/{total_files})")

                try:
                    # 파일 로드
                    file_df = pd.read_excel(file_path)

                    # 필요한 열 확인
                    if 'parameter' not in file_df.columns or 'value' not in file_df.columns:
                        messagebox.showwarning("경고", f"파일 '{file_name}'에 필요한 열(parameter, value)이 없습니다. 건너뜁니다.")
                        continue

                    # 파라미터-값 매핑 (파라미터를 인덱스로 설정)
                    file_df = file_df[['parameter', 'value']].copy()
                    file_df.columns = ['parameter', f'file_{i}']
                    file_dfs.append(file_df)
                    self.file_names.append(file_path)

                except Exception as e:
                    messagebox.showwarning("경고", f"파일 '{file_name}' 로드 중 오류 발생: {str(e)}. 건너뜁니다.")

            if not file_dfs:
                loading_dialog.close()
                messagebox.showinfo("알림", "처리할 수 있는 파일이 없습니다.")
                return

            # 파일 데이터와 Default DB 데이터 병합
            loading_dialog.update_progress(80, "데이터 병합 중...")

            # 모든 파일 데이터 병합
            merged_df = default_params
            for file_df in file_dfs:
                merged_df = pd.merge(merged_df, file_df, on='parameter', how='outer')

            # 결측값 처리
            merged_df.fillna('', inplace=True)

            # 병합된 데이터 저장
            self.merged_df = merged_df

            # UI 업데이트
            loading_dialog.update_progress(90, "UI 업데이트 중...")
            self.update_all_tabs()

            # 완료
            loading_dialog.update_progress(100, "완료")
            loading_dialog.close()

            # 로그 업데이트
            self.update_log(f"[파일 로드] 폴더 '{folder_path}'에서 {len(self.file_names)}개 파일이 로드되었습니다.")

        except Exception as e:
            loading_dialog.close()
            messagebox.showerror("오류", f"파일 로드 중 오류 발생: {str(e)}")

    def load_default_parameters(self):
        """Default DB에서 파라미터 로드"""
        try:
            # 선택된 장비 유형 확인
            if not hasattr(self, 'selected_equipment_type_id'):
                # 장비 유형 선택 대화상자 표시
                equipment_type_id = self.select_equipment_type_dialog()
                if not equipment_type_id:
                    return None
                self.selected_equipment_type_id = equipment_type_id

            # 데이터베이스 연결
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 장비 유형의 파라미터 조회
            query = """
            SELECT p.name as parameter, p.min_value, p.max_value, p.default_value 
            FROM parameters p 
            WHERE p.equipment_type_id = ? 
            ORDER BY p.name
            """
            cursor.execute(query, (self.selected_equipment_type_id,))
            params = cursor.fetchall()

            # DataFrame 생성
            df = pd.DataFrame(params, columns=['parameter', 'min_value', 'max_value', 'default_value'])

            # 수치형 값 포맷팅
            for col in ['min_value', 'max_value', 'default_value']:
                df[col] = df[col].apply(lambda x: format_num_value(x) if pd.notna(x) else "")

            conn.close()
            return df

        except Exception as e:
            messagebox.showerror("오류", f"Default 파라미터 로드 중 오류 발생: {str(e)}")
            return None

    def select_equipment_type_dialog(self):
        """장비 유형 선택 대화상자"""
        try:
            # 데이터베이스 연결
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # 장비 유형 목록 조회
            cursor.execute("SELECT id, type_name FROM Equipment_Types ORDER BY type_name")
            equipment_types = cursor.fetchall()

            if not equipment_types:
                messagebox.showinfo("알림", "등록된 장비 유형이 없습니다.")
                conn.close()
                return None

            # 장비 유형 선택 대화상자
            dialog = tk.Toplevel(self.window)
            dialog.title("장비 유형 선택")
            dialog.geometry("400x300")
            dialog.transient(self.window)
            dialog.grab_set()

            # 중앙 배치
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() - width) // 2
            y = (dialog.winfo_screenheight() - height) // 2
            dialog.geometry(f"{width}x{height}+{x}+{y}")

            # 안내 레이블
            tk.Label(
                dialog, 
                text="파일을 비교할 장비 유형을 선택하세요:", 
                pady=10
            ).pack(fill=tk.X)

            # 리스트박스
            frame = tk.Frame(dialog)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            scrollbar = tk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
            listbox.pack(fill=tk.BOTH, expand=True)

            scrollbar.config(command=listbox.yview)

            # 장비 유형 목록 추가
            for eq_id, eq_name in equipment_types:
                listbox.insert(tk.END, f"{eq_name} (ID: {eq_id})")

            # 가장 처음 항목 선택
            listbox.selection_set(0)

            # 선택한 ID 저장용 변수
            selected_id = [None]

            # 버튼 영역
            button_frame = tk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            # 확인 버튼 이벤트 핸들러
            def on_ok():
                selection = listbox.curselection()
                if selection:
                    selected_text = listbox.get(selection[0])
                    # ID 부분 추출
                    selected_id[0] = int(selected_text.split("ID: ")[1].strip(")"))
                dialog.destroy()

            # 취소 버튼 이벤트 핸들러
            def on_cancel():
                selected_id[0] = None
                dialog.destroy()

            # 버튼 추가
            tk.Button(button_frame, text="확인", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="취소", command=on_cancel, width=10).pack(side=tk.RIGHT, padx=5)

            # 대화상자 표시 및 대기
            dialog.wait_window(dialog)

            conn.close()
            return selected_id[0]

        except Exception as e:
            messagebox.showerror("오류", f"장비 유형 로드 중 오류 발생: {str(e)}")
            return None

    def update_all_tabs(self):
        """모든 탭 업데이트"""
        if hasattr(self, 'merged_df') and self.merged_df is not None:
            # 비교 탭 업데이트
            self.update_comparison_view()

            # 리포트 탭 업데이트
            self.update_report_view()

    def export_file_data(self, file_type="excel"):
        """병합된 데이터 내보내기"""
        if not hasattr(self, 'merged_df') or self.merged_df is None or self.merged_df.empty:
            messagebox.showinfo("알림", "내보낼 데이터가 없습니다.")
            return

        try:
            from tkinter import filedialog

            if file_type == "excel":
                # Excel 파일로 저장
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")],
                    title="데이터 저장"
                )

                if not file_path:
                    return

                self.merged_df.to_excel(file_path, index=False)
                messagebox.showinfo("알림", f"데이터가 '{file_path}'에 저장되었습니다.")

            elif file_type == "csv":
                # CSV 파일로 저장
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
                    title="데이터 저장"
                )

                if not file_path:
                    return

                self.merged_df.to_csv(file_path, index=False)
                messagebox.showinfo("알림", f"데이터가 '{file_path}'에 저장되었습니다.")

            # 로그 업데이트
            self.update_log(f"[데이터 내보내기] '{file_path}'에 데이터가 저장되었습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"데이터 내보내기 중 오류 발생: {str(e)}")

    # 클래스에 함수 추가
    cls.load_folder = load_folder
    cls.load_default_parameters = load_default_parameters
    cls.select_equipment_type_dialog = select_equipment_type_dialog
    cls.update_all_tabs = update_all_tabs
    cls.export_file_data = export_file_data
