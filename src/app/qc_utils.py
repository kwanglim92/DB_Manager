# QC 검수 공통 유틸리티 함수들

import pandas as pd
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os


class QCDataProcessor:
    """QC 검수 데이터 처리 공통 클래스"""
    
    @staticmethod
    def create_safe_dataframe(data, expected_columns):
        """안전한 데이터프레임 생성"""
        try:
            df = pd.DataFrame(data, columns=expected_columns)
            return df, None
        except Exception as e:
            error_msg = f"데이터프레임 생성 오류: {str(e)}\n데이터 형태: {type(data)}"
            return None, error_msg
    
    @staticmethod
    def validate_checklist_mode_requirements(is_checklist_mode, selected_files):
        """Check list 모드 요구사항 검증"""
        if is_checklist_mode:
            if not selected_files:
                return False, "Check list 중점 모드에서는 검수할 파일을 먼저 선택해야 합니다."
            
            # 파일 데이터 유효성 검증
            valid_files = [name for name, data in selected_files.items() if data is not None]
            if not valid_files:
                return False, "선택된 파일 중 유효한 데이터가 있는 파일이 없습니다."
        
        return True, ""
    
    @staticmethod
    def extract_file_data(selected_files, file_columns=None):
        """파일 데이터 추출 및 처리"""
        if not selected_files:
            return None, "선택된 파일이 없습니다."
        
        try:
            # 첫 번째 파일 사용
            first_file = next(iter(selected_files.keys()))
            file_data = selected_files[first_file]
            
            if isinstance(file_data, pd.DataFrame):
                return file_data, None
            else:
                # 파일 경로인 경우 로드 시도
                try:
                    file_df = pd.read_csv(file_data, sep='\t' if file_data.endswith('.txt') else ',')
                    return file_df, None
                except Exception as load_error:
                    return None, f"파일 로드 실패: {load_error}"
                    
        except Exception as e:
            return None, f"파일 데이터 처리 오류: {e}"


class QCFileSelector:
    """QC 검수용 파일 선택 공통 클래스"""
    
    @staticmethod
    def create_file_selection_dialog(parent_window, uploaded_files, max_files=6):
        """파일 선택 다이얼로그 생성"""
        if not uploaded_files:
            messagebox.showinfo(
                "파일 선택 안내", 
                "QC 검수를 위해서는 먼저 파일을 로드해야 합니다.\n\n"
                "📁 파일 > 폴더 열기를 통해 DB 파일들을 업로드해주세요."
            )
            return None
        
        # 파일 선택 대화상자 생성
        dialog = tk.Toplevel(parent_window)
        dialog.title("🔍 QC 검수 파일 선택")
        dialog.geometry("600x500")
        dialog.transient(parent_window)
        dialog.grab_set()
        dialog.resizable(True, True)
        
        selected_files = {}
        file_vars = {}
        
        # UI 구성
        QCFileSelector._setup_file_dialog_ui(dialog, uploaded_files, file_vars, max_files)
        
        # 결과 반환을 위한 변수
        result = {'selected_files': None}
        
        def apply_selection():
            selected = {name: uploaded_files[name] for name, var in file_vars.items() if var.get()}
            
            if not selected:
                messagebox.showwarning("선택 필요", "최소 1개의 파일을 선택해주세요.")
                return
            
            if len(selected) > max_files:
                messagebox.showwarning("선택 제한", f"최대 {max_files}개의 파일만 선택할 수 있습니다.")
                return
            
            result['selected_files'] = selected
            dialog.destroy()
        
        def cancel_selection():
            dialog.destroy()
        
        # 버튼 프레임
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="취소", command=cancel_selection).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="✅ 선택 완료", command=apply_selection).pack(side=tk.RIGHT, padx=5)
        
        # 대화상자가 닫힐 때까지 대기
        parent_window.wait_window(dialog)
        
        return result['selected_files']
    
    @staticmethod
    def _setup_file_dialog_ui(dialog, uploaded_files, file_vars, max_files):
        """파일 다이얼로그 UI 설정"""
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 정보 레이블
        info_label = ttk.Label(main_frame, text=f"QC 검수에 사용할 파일을 선택하세요 (최대 {max_files}개)")
        info_label.pack(pady=(0, 10))
        
        # 스크롤 가능한 파일 목록
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        for filename, filepath in uploaded_files.items():
            file_vars[filename] = tk.BooleanVar()
            
            file_frame = ttk.Frame(scrollable_frame)
            file_frame.pack(fill=tk.X, pady=2)
            
            checkbox = ttk.Checkbutton(file_frame, text=filename, variable=file_vars[filename])
            checkbox.pack(side=tk.LEFT)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class QCResultExporter:
    """QC 검수 결과 내보내기 공통 클래스"""
    
    @staticmethod
    def export_results_to_file(results, default_filename="qc_results"):
        """QC 검수 결과를 파일로 내보내기"""
        if not results:
            messagebox.showinfo("알림", "내보낼 결과가 없습니다.")
            return False
        
        file_path = filedialog.asksaveasfilename(
            title="QC 검수 결과 저장",
            defaultextension=".xlsx",
            initialvalue=default_filename,
            filetypes=[("Excel 파일", "*.xlsx"), ("CSV 파일", "*.csv")]
        )
        
        if not file_path:
            return False
        
        try:
            # 결과 데이터 정리
            export_data = []
            for result in results:
                export_data.append({
                    '파라미터명': result.get('parameter', ''),
                    'Default Value': result.get('default_value', ''),
                    'File Value': result.get('file_value', ''),
                    'Pass/Fail': result.get('pass_fail', ''),
                    'Issue Type': result.get('issue_type', ''),
                    '설명': result.get('description', ''),
                    '심각도': result.get('severity', ''),
                    '권장사항': result.get('recommendation', '')
                })
            
            # DataFrame 생성 및 저장
            df = pd.DataFrame(export_data)
            
            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False, engine='openpyxl')
            else:
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("성공", f"QC 검수 결과가 저장되었습니다.\n{file_path}")
            return True
            
        except Exception as e:
            messagebox.showerror("오류", f"결과 내보내기 중 오류: {str(e)}")
            return False


class QCErrorHandler:
    """QC 검수 에러 처리 공통 클래스"""
    
    @staticmethod
    def handle_validation_error(error, context="QC 검수"):
        """검증 오류 처리"""
        error_msg = f"{context} 검증 오류: {str(error)}"
        messagebox.showerror("검증 오류", error_msg)
        return error_msg
    
    @staticmethod
    def handle_file_error(error, filename="파일"):
        """파일 처리 오류"""
        error_msg = f"{filename} 처리 중 오류: {str(error)}"
        messagebox.showerror("파일 오류", error_msg)
        return error_msg
    
    @staticmethod
    def handle_database_error(error, operation="데이터베이스 작업"):
        """데이터베이스 오류"""
        error_msg = f"{operation} 중 오류: {str(error)}"
        messagebox.showerror("데이터베이스 오류", error_msg)
        return error_msg
    
    @staticmethod
    def handle_memory_error():
        """메모리 부족 오류"""
        error_msg = "메모리가 부족합니다. 파일 크기를 줄이거나 다른 파일을 선택해주세요."
        messagebox.showerror("메모리 부족", error_msg)
        return error_msg


# 공통 상수 정의
QC_COLUMN_MAPPINGS = {
    'PARAMETER_COLUMNS': ['Parameter', 'parameter', 'Item', 'item', 'Name', 'name', 'ItemName', 'Item Name'],
    'VALUE_COLUMNS': ['Value', 'value', 'Data', 'data', 'Setting', 'setting', 'Val', 'ItemValue'],
    'DEFAULT_DB_COLUMNS': [
        "id", "parameter_name", "default_value", "min_spec", "max_spec", "type_name",
        "occurrence_count", "total_files", "confidence_score", "source_files", "description",
        "module_name", "part_name", "item_type", "is_checklist"
    ]
}

QC_SEVERITY_LEVELS = {
    "높음": 3,
    "중간": 2,
    "낮음": 1
}

QC_ISSUE_TYPES = {
    "data_quality": "데이터 품질",
    "checklist": "Check list 관련",
    "consistency": "일관성",
    "completeness": "완전성",
    "accuracy": "정확성",
    "pass": "통과"
}