# 공통 유틸리티 함수 (리팩토링된 헬퍼 모듈들로 통합)
# 기존 코드 호환성을 위한 래퍼 함수들

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

# 새로운 헬퍼 모듈들 임포트
from .utils.helpers.ui_helpers import UIHelpers
from .utils.helpers.data_helpers import DataHelpers
from .utils.helpers.file_helpers import FileHelpers
from .utils.helpers.validation_helpers import ValidationHelpers

# ===== 기존 코드 호환성을 위한 래퍼 함수들 =====

def create_treeview_with_scrollbar(parent, columns, headings, column_widths=None, height=20):
    """
    스크롤바가 있는 트리뷰를 생성하여 반환합니다.
    (UIHelpers.create_treeview_with_scrollbar의 래퍼 함수)
    """
    return UIHelpers.create_treeview_with_scrollbar(
        parent, columns, headings, column_widths, height
    )

def create_label_entry_pair(parent, label_text, row=0, column=0, initial_value=""):
    """
    레이블과 입력 필드 쌍을 생성합니다.
    (UIHelpers.create_label_entry_pair의 래퍼 함수)
    """
    var = tk.StringVar(value=initial_value)
    UIHelpers.create_label_entry_pair(
        parent, label_text, var, row=row, 
        label_column=column, entry_column=column+1
    )
    return var, None  # 기존 인터페이스 유지

def format_num_value(value, decimal_places=4):
    """
    숫자 값을 적절한 형식으로 포맷팅합니다.
    (DataHelpers.format_num_value의 래퍼 함수)
    """
    return DataHelpers.format_num_value(value, decimal_places)

def generate_unique_filename(prefix, extension):
    """
    타임스탬프를 이용하여 고유한 파일명을 생성합니다.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = FileHelpers.get_safe_filename(f"{prefix}_{timestamp}{extension}")
    return safe_filename

def open_folder_dialog(initial_dir=None):
    """
    폴더 선택 대화상자를 표시합니다.
    """
    folder_path = filedialog.askdirectory(initialdir=initial_dir, title="폴더 선택")
    return folder_path if folder_path else None

def open_file_dialog(file_types=None, initial_dir=None, title="파일 선택"):
    """
    파일 선택 대화상자를 표시합니다.
    """
    if file_types is None:
        file_types = [("모든 파일", "*.*")]

    file_path = filedialog.askopenfilename(
        filetypes=file_types,
        initialdir=initial_dir,
        title=title
    )
    return file_path if file_path else None

def save_file_dialog(default_extension, file_types=None, initial_dir=None, title="파일 저장"):
    """
    파일 저장 대화상자를 표시합니다.
    """
    if file_types is None:
        file_types = [("모든 파일", "*.*")]

    file_path = filedialog.asksaveasfilename(
        defaultextension=default_extension,
        filetypes=file_types,
        initialdir=initial_dir,
        title=title
    )
    return file_path if file_path else None

def verify_password(password):
    """
    비밀번호를 검증합니다.
    (ValidationHelpers.verify_password의 래퍼 함수)
    """
    return ValidationHelpers.verify_password(password)

def change_maintenance_password(current_password, new_password):
    """
    유지보수 모드 비밀번호를 변경합니다.
    (ValidationHelpers.change_maintenance_password의 래퍼 함수)
    """
    return ValidationHelpers.change_maintenance_password(current_password, new_password)

def load_settings():
    """
    설정 파일을 로드합니다.
    """
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config", "settings.json"
    )
    return FileHelpers.read_json_file(config_path) or {}

def save_settings(settings):
    """
    설정 파일을 저장합니다.
    """
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config", "settings.json"
    )
    return FileHelpers.write_json_file(config_path, settings)

def create_safe_filename(filename):
    """
    안전한 파일명을 생성합니다.
    (FileHelpers.get_safe_filename의 래퍼 함수)
    """
    return FileHelpers.get_safe_filename(filename)

def parse_numeric_value(value):
    """
    문자열에서 숫자 값을 추출합니다.
    (DataHelpers.parse_numeric_value의 래퍼 함수)
    """
    return DataHelpers.parse_numeric_value(value)

def calculate_similarity(str1, str2):
    """
    두 문자열의 유사도를 계산합니다.
    (DataHelpers.calculate_similarity의 래퍼 함수)
    """
    return DataHelpers.calculate_similarity(str1, str2)

def export_dataframe_to_excel(df, filename, sheet_name='Sheet1'):
    """
    DataFrame을 Excel 파일로 내보냅니다.
    (FileHelpers.write_excel_file의 래퍼 함수)
    """
    return FileHelpers.write_excel_file(df, filename, sheet_name)

def read_text_file_to_dataframe(file_path):
    """
    텍스트 파일을 DataFrame으로 읽습니다.
    (FileHelpers.parse_custom_text_file의 래퍼 함수)
    """
    return FileHelpers.parse_custom_text_file(file_path)

# ===== 새로운 헬퍼 모듈들 직접 노출 =====
# 더 고급 기능이 필요한 경우 직접 사용 가능

# UI 헬퍼
UIHelper = UIHelpers

# 데이터 헬퍼  
DataHelper = DataHelpers

# 파일 헬퍼
FileHelper = FileHelpers

# 검증 헬퍼
ValidationHelper = ValidationHelpers

# 이전 버전과 호환성을 위한 별칭들
create_treeview = create_treeview_with_scrollbar
format_number = format_num_value
get_unique_filename = generate_unique_filename
ask_folder = open_folder_dialog
ask_file = open_file_dialog
ask_save_file = save_file_dialog
safe_filename = create_safe_filename

# 로그 함수 (기본 구현)
def log_message(message, level="INFO"):
    """
    로그 메시지를 출력합니다.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def show_info(title, message):
    """정보 메시지박스를 표시합니다."""
    messagebox.showinfo(title, message)

def show_warning(title, message):
    """경고 메시지박스를 표시합니다."""
    messagebox.showwarning(title, message)

def show_error(title, message):
    """오류 메시지박스를 표시합니다."""
    messagebox.showerror(title, message)

def ask_yes_no(title, message):
    """예/아니오 선택 대화상자를 표시합니다."""
    return messagebox.askyesno(title, message)

def ask_ok_cancel(title, message):
    """확인/취소 선택 대화상자를 표시합니다."""
    return messagebox.askokcancel(title, message)