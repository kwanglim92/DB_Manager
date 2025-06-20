# 공통 유틸리티 함수
# 유틸리티 함수 - 공통으로 사용되는 유틸리티 함수 모음

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

def create_treeview_with_scrollbar(parent, columns, headings, column_widths, height=None):
    """
    스크롤바가 있는 트리뷰를 생성하여 반환합니다.

    Args:
        parent: 부모 위젯
        columns: 열 ID 튜플
        headings: 열 제목 매핑 딕셔너리 {열ID: 표시명}
        column_widths: 열 너비 매핑 딕셔너리 {열ID: 너비}
        height: 트리뷰 높이 (행 수)

    Returns:
        (frame, treeview): 프레임과 트리뷰 객체
    """
    # 프레임 생성
    frame = ttk.Frame(parent)

    # 스크롤바 생성
    y_scrollbar = ttk.Scrollbar(frame)
    y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    x_scrollbar = ttk.Scrollbar(frame, orient="horizontal")
    x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # 트리뷰 생성
    kwargs = {'yscrollcommand': y_scrollbar.set, 'xscrollcommand': x_scrollbar.set}
    if height:
        kwargs['height'] = height

    treeview = ttk.Treeview(frame, columns=columns, show="headings", **kwargs)
    treeview.pack(fill=tk.BOTH, expand=True)

    # 스크롤바 연결
    y_scrollbar.config(command=treeview.yview)
    x_scrollbar.config(command=treeview.xview)

    # 열 설정
    for col in columns:
        treeview.heading(col, text=headings.get(col, col))
        treeview.column(col, width=column_widths.get(col, 100), stretch=True)

    return frame, treeview

def create_label_entry_pair(parent, label_text, row=0, column=0, initial_value=""):
    """
    레이블과 입력 필드 쌍을 생성합니다.

    Args:
        parent: 부모 위젯
        label_text: 레이블 텍스트
        row: 그리드 행 위치
        column: 그리드 열 위치
        initial_value: 초기값

    Returns:
        (var, entry): 변수와 입력 필드 객체
    """
    ttk.Label(parent, text=label_text).grid(row=row, column=column, padx=5, pady=5, sticky="w")
    var = tk.StringVar(value=initial_value)
    entry = ttk.Entry(parent, textvariable=var, width=30)
    entry.grid(row=row, column=column+1, padx=5, pady=5, sticky="ew")
    return var, entry

def format_num_value(value):
    """
    숫자 값을 적절한 형식으로 포맷팅합니다.

    Args:
        value: 포맷팅할 숫자 값

    Returns:
        포맷팅된 문자열
    """
    if value is None:
        return ""

    try:
        # 정수인 경우
        if float(value).is_integer():
            return str(int(value))

        # 실수인 경우
        return f"{float(value):.4f}".rstrip('0').rstrip('.') if '.' in f"{float(value):.4f}" else f"{float(value):.0f}"
    except (ValueError, TypeError):
        return str(value)

def generate_unique_filename(prefix, extension):
    """
    타임스탬프를 이용하여 고유한 파일명을 생성합니다.

    Args:
        prefix: 파일명 접두사
        extension: 파일 확장자 (점 포함)

    Returns:
        고유한 파일명
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}{extension}"

def open_folder_dialog(initial_dir=None):
    """
    폴더 선택 대화상자를 표시합니다.

    Args:
        initial_dir: 초기 디렉토리 경로

    Returns:
        선택한 폴더 경로 또는 취소 시 None
    """
    folder_path = filedialog.askdirectory(initialdir=initial_dir, title="폴더 선택")
    return folder_path if folder_path else None

def open_file_dialog(file_types=None, initial_dir=None, title="파일 선택"):
    """
    파일 선택 대화상자를 표시합니다.

    Args:
        file_types: 파일 형식 목록 [("설명", "*.확장자"), ...]
        initial_dir: 초기 디렉토리 경로
        title: 대화상자 제목

    Returns:
        선택한 파일 경로 또는 취소 시 None
    """
    if file_types is None:
        file_types = [("모든 파일", "*.*")]

    file_path = filedialog.askopenfilename(
        filetypes=file_types,
        initialdir=initial_dir,
        title=title
    )
    return file_path if file_path else None

def save_file_dialog(default_extension, file_types=None, initial_dir=None, 
                     title="파일 저장", initial_file=None):
    """
    파일 저장 대화상자를 표시합니다.

    Args:
        default_extension: 기본 확장자 (점 포함)
        file_types: 파일 형식 목록 [("설명", "*.확장자"), ...]
        initial_dir: 초기 디렉토리 경로
        title: 대화상자 제목
        initial_file: 초기 파일명

    Returns:
        저장할 파일 경로 또는 취소 시 None
    """
    if file_types is None:
        file_types = [("모든 파일", "*.*")]

    kwargs = {
        'defaultextension': default_extension,
        'filetypes': file_types,
        'initialdir': initial_dir,
        'title': title
    }

    if initial_file:
        kwargs['initialfile'] = initial_file

    file_path = filedialog.asksaveasfilename(**kwargs)
    return file_path if file_path else None

def create_sqlite_connection(db_path):
    """
    SQLite 데이터베이스 연결을 생성합니다.

    Args:
        db_path: 데이터베이스 파일 경로

    Returns:
        연결 객체
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # 외래 키 제약 활성화
        return conn
    except sqlite3.Error as e:
        messagebox.showerror("데이터베이스 연결 오류", str(e))
        return None

def execute_query(conn, query, params=None):
    """
    SQL 쿼리를 실행합니다.

    Args:
        conn: 데이터베이스 연결 객체
        query: SQL 쿼리 문자열
        params: 쿼리 파라미터 (튜플 또는 딕셔너리)

    Returns:
        커서 객체
    """
    try:
        if params:
            return conn.execute(query, params)
        else:
            return conn.execute(query)
    except sqlite3.Error as e:
        messagebox.showerror("쿼리 실행 오류", str(e))
        raise

def excel_to_dataframe(file_path, sheet_name=0):
    """
    Excel 파일을 DataFrame으로 로드합니다.

    Args:
        file_path: Excel 파일 경로
        sheet_name: 시트 이름 또는 인덱스

    Returns:
        pandas DataFrame
    """
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        messagebox.showerror("Excel 파일 로드 오류", str(e))
        return None

def dataframe_to_excel(df, file_path, sheet_name="Sheet1"):
    """
    DataFrame을 Excel 파일로 저장합니다.

    Args:
        df: pandas DataFrame
        file_path: 저장할 파일 경로
        sheet_name: 시트 이름

    Returns:
        성공 여부 (True/False)
    """
    try:
        df.to_excel(file_path, sheet_name=sheet_name, index=False)
        return True
    except Exception as e:
        messagebox.showerror("Excel 파일 저장 오류", str(e))
        return False

def create_backup(file_path, backup_dir=None):
    """
    파일의 백업을 생성합니다.

    Args:
        file_path: 백업할 파일 경로
        backup_dir: 백업 디렉토리 (설정값: 파일과 같은 디렉토리)

    Returns:
        백업 파일 경로
    """
    import shutil
    from datetime import datetime

    if not os.path.exists(file_path):
        return None

    # 백업 디렉토리 설정
    if backup_dir is None:
        backup_dir = os.path.dirname(file_path)

    # 백업 디렉토리가 없으면 생성
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # 파일명과 확장자 분리
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)

    # 타임스탬프를 이용한 백업 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{name}_backup_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_filename)

    # 파일 복사
    shutil.copy2(file_path, backup_path)
    return backup_path

def compare_values(val1, val2, tolerance=0.0001):
    """
    두 값을 비교합니다. 숫자인 경우 허용 오차를 적용합니다.

    Args:
        val1: 첫 번째 값
        val2: 두 번째 값
        tolerance: 숫자 비교 시 허용 오차

    Returns:
        같으면 True, 다르면 False
    """
    # 둘 다 None이거나 빈 문자열이면 같음
    if (val1 is None or val1 == "") and (val2 is None or val2 == ""):
        return True

    # 한쪽만 None이거나 빈 문자열이면 다름
    if (val1 is None or val1 == "") or (val2 is None or val2 == ""):
        return False

    # 문자열로 변환하여 정확히 같으면 같음
    if str(val1) == str(val2):
        return True

    # 숫자로 변환 시도
    try:
        num1 = float(val1)
        num2 = float(val2)
        # 허용 오차 내에 있으면 같음
        return abs(num1 - num2) <= tolerance
    except (ValueError, TypeError):
        # 숫자로 변환할 수 없으면 다름
        return False

def verify_password(password):
    """유지보수 모드 비밀번호 확인"""
    # 간단한 비밀번호 확인 (실제 환경에서는 해시 사용 권장)
    return password == "1"

def change_maintenance_password(current_password, new_password):
    """유지보수 모드 비밀번호 변경"""
    if verify_password(current_password):
        # 실제 환경에서는 설정 파일이나 데이터베이스에 저장
        # 지금은 간단하게 구현
        return True
    return False

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

def create_centered_dialog(parent, title="다이얼로그", geometry="400x300"):
    """
    부모 창 중앙에 위치한 다이얼로그를 생성합니다.
    
    Args:
        parent: 부모 윈도우
        title: 다이얼로그 제목
        geometry: 다이얼로그 크기 ("widthxheight" 형식)
        
    Returns:
        tk.Toplevel: 생성된 다이얼로그
    """
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry(geometry)
    dialog.transient(parent)
    dialog.grab_set()
    
    # 부모 창 중앙에 배치
    center_dialog_on_parent(dialog, parent)
    
    return dialog
