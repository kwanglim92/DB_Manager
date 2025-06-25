# 파일 처리 서비스 모듈
# manager.py에서 추출된 파일 I/O 관련 기능들

import os
import pandas as pd
import sqlite3
from tkinter import filedialog, messagebox


def export_dataframe_to_file(df, default_filename="export", title="데이터 내보내기"):
    """
    DataFrame을 파일로 내보내기
    
    Args:
        df: 내보낼 DataFrame
        default_filename: 기본 파일명
        title: 파일 선택 대화상자 제목
        
    Returns:
        str: 저장된 파일 경로 (취소시 None)
    """
    if df is None or df.empty:
        messagebox.showinfo("정보", "내보낼 데이터가 없습니다.")
        return None
    
    try:
        # 파일 저장 대화상자
        filename = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            if filename.endswith('.xlsx'):
                df.to_excel(filename, index=False)
            else:
                df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("완료", f"데이터가 성공적으로 내보내졌습니다:\n{filename}")
            return filename
        
        return None
        
    except Exception as e:
        messagebox.showerror("오류", f"데이터 내보내기 중 오류 발생: {e}")
        return None


def export_tree_data_to_file(tree_widget, columns, file_names=None, title="보고서 내보내기"):
    """
    TreeView 데이터를 파일로 내보내기
    
    Args:
        tree_widget: tkinter TreeView 위젯
        columns: 컬럼 이름 리스트
        file_names: 추가 컬럼 이름들 (옵션)
        title: 파일 선택 대화상자 제목
        
    Returns:
        str: 저장된 파일 경로 (취소시 None)
    """
    try:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx"), ("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
            title=title
        )
        
        if not file_path:
            return None
            
        # TreeView에서 데이터 추출
        data = []
        for item in tree_widget.get_children():
            data.append(tree_widget.item(item)["values"])
        
        # 컬럼 이름 설정
        if file_names:
            all_columns = columns + file_names
        else:
            all_columns = columns
            
        df = pd.DataFrame(data, columns=all_columns)
        
        # 파일 저장
        if file_path.endswith(".csv"):
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
        else:
            df.to_excel(file_path, index=False)
            
        messagebox.showinfo("완료", "보고서가 성공적으로 저장되었습니다.")
        return file_path
        
    except Exception as e:
        messagebox.showerror("오류", f"보고서 내보내기 중 오류 발생: {str(e)}")
        return None


def load_database_files():
    """
    여러 데이터베이스 파일들을 로드하여 병합된 DataFrame 반환
    
    Returns:
        tuple: (merged_df, file_names, uploaded_files) 또는 (None, None, None)
    """
    try:
        # 파일 확장자 필터 설정
        filetypes = [
            ("DB 파일", "*.txt;*.db;*.csv"),
            ("텍스트 파일", "*.txt"),
            ("DB 파일", "*.db"),
            ("CSV 파일", "*.csv"),
            ("모든 파일", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="DB 파일들을 선택하세요 (여러 개 선택 가능)",
            filetypes=filetypes
        )
        
        if not files:
            return None, None, None
        
        return load_and_merge_files(files)
        
    except Exception as e:
        messagebox.showerror("오류", f"파일 로드 중 오류 발생: {str(e)}")
        return None, None, None


def load_and_merge_files(file_paths):
    """
    파일 경로 리스트를 받아서 로드하고 병합
    
    Args:
        file_paths: 로드할 파일 경로들의 리스트
        
    Returns:
        tuple: (merged_df, file_names, uploaded_files)
    """
    from app.loading import LoadingDialog
    import tkinter as tk
    
    # 로딩 다이얼로그 생성 (부모 창이 없는 경우)
    try:
        root = tk._default_root
        if root is None:
            root = tk.Tk()
            root.withdraw()
        loading_dialog = LoadingDialog(root)
    except:
        loading_dialog = None
    
    if loading_dialog:
        loading_dialog.show("파일을 로드하는 중...")
    
    try:
        dataframes = []
        file_names = []
        uploaded_files = {}
        
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            if loading_dialog:
                progress = int((i / total_files) * 100)
                loading_dialog.update_progress(progress, f"파일 로드 중... ({i+1}/{total_files})")
            
            file_name = os.path.basename(file_path)
            file_names.append(file_name)
            
            # 파일 확장자에 따른 로드 방식 결정
            if file_path.endswith('.db'):
                df = load_db_file(file_path, file_name)
            elif file_path.endswith('.csv'):
                df = load_csv_file(file_path, file_name)
            else:  # .txt 파일
                df = load_txt_file(file_path, file_name)
            
            if df is not None:
                dataframes.append(df)
                uploaded_files[file_name] = file_path
        
        if loading_dialog:
            loading_dialog.update_progress(90, "데이터 병합 중...")
        
        # 모든 DataFrame 병합
        if dataframes:
            merged_df = merge_dataframes(dataframes)
            
            if loading_dialog:
                loading_dialog.update_progress(100, "완료!")
                loading_dialog.hide()
            
            return merged_df, file_names, uploaded_files
        else:
            if loading_dialog:
                loading_dialog.hide()
            messagebox.showwarning("경고", "로드할 수 있는 파일이 없습니다.")
            return None, None, None
            
    except Exception as e:
        if loading_dialog:
            loading_dialog.hide()
        raise e


def load_db_file(file_path, file_name):
    """SQLite DB 파일 로드"""
    try:
        conn = sqlite3.connect(file_path)
        
        # 테이블 목록 가져오기
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        
        if not tables:
            conn.close()
            return None
        
        # 첫 번째 테이블의 데이터 로드
        table_name = tables[0][0]
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        # 파일명을 새 컬럼으로 추가
        df[file_name] = df.iloc[:, -1]  # 마지막 컬럼 값을 사용
        
        return df
        
    except Exception as e:
        print(f"DB 파일 로드 실패 ({file_name}): {e}")
        return None


def load_csv_file(file_path, file_name):
    """CSV 파일 로드"""
    try:
        # 여러 인코딩 시도
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                # 파일명을 새 컬럼으로 추가
                df[file_name] = df.iloc[:, -1]  # 마지막 컬럼 값을 사용
                return df
            except UnicodeDecodeError:
                continue
        
        print(f"CSV 파일 로드 실패 ({file_name}): 지원되는 인코딩이 없습니다.")
        return None
        
    except Exception as e:
        print(f"CSV 파일 로드 실패 ({file_name}): {e}")
        return None


def load_txt_file(file_path, file_name):
    """텍스트 파일 로드 (탭 구분)"""
    try:
        # 여러 인코딩 시도
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, sep='\t', encoding=encoding)
                # 파일명을 새 컬럼으로 추가  
                df[file_name] = df.iloc[:, -1]  # 마지막 컬럼 값을 사용
                return df
            except UnicodeDecodeError:
                continue
        
        print(f"텍스트 파일 로드 실패 ({file_name}): 지원되는 인코딩이 없습니다.")
        return None
        
    except Exception as e:
        print(f"텍스트 파일 로드 실패 ({file_name}): {e}")
        return None


def merge_dataframes(dataframes):
    """여러 DataFrame들을 병합"""
    try:
        if not dataframes:
            return None
        
        if len(dataframes) == 1:
            return dataframes[0]
        
        # 공통 컬럼을 기준으로 병합
        merged = dataframes[0]
        
        for df in dataframes[1:]:
            # 공통 컬럼 찾기 (파일명 컬럼 제외)
            common_cols = []
            for col in merged.columns:
                if col in df.columns and not (col.endswith('.txt') or col.endswith('.db') or col.endswith('.csv')):
                    common_cols.append(col)
            
            if common_cols:
                # 공통 컬럼을 기준으로 outer join
                merged = pd.merge(merged, df, on=common_cols, how='outer')
            else:
                # 공통 컬럼이 없으면 단순 concat
                merged = pd.concat([merged, df], ignore_index=True, sort=False)
        
        return merged
        
    except Exception as e:
        print(f"DataFrame 병합 실패: {e}")
        return None


class FileService:
    """파일 서비스 클래스 - 상태 유지가 필요한 경우 사용"""
    
    def __init__(self):
        self.last_export_path = None
        self.last_import_path = None
    
    def export_dataframe(self, df, default_filename="export", title="데이터 내보내기"):
        """DataFrame 내보내기"""
        result = export_dataframe_to_file(df, default_filename, title)
        if result:
            self.last_export_path = os.path.dirname(result)
        return result
    
    def export_tree_data(self, tree_widget, columns, file_names=None, title="보고서 내보내기"):
        """TreeView 데이터 내보내기"""
        result = export_tree_data_to_file(tree_widget, columns, file_names, title)
        if result:
            self.last_export_path = os.path.dirname(result)
        return result
    
    def load_database_files(self):
        """데이터베이스 파일들 로드"""
        result = load_database_files()
        if result[0] is not None:
            # 첫 번째 파일의 디렉토리를 기억
            file_paths = list(result[2].values()) if result[2] else []
            if file_paths:
                self.last_import_path = os.path.dirname(file_paths[0])
        return result