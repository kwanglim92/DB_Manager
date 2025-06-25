# 공통 유틸리티 함수 (리팩토링된 헬퍼 모듈들로 통합)
# 기존 코드 호환성을 위한 래퍼 함수들

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

# 새로운 헬퍼 모듈들 임포트 (호환성 체크)
try:
    from .utils.helpers.ui_helpers import UIHelpers
    from .utils.helpers.data_helpers import DataHelpers
    from .utils.helpers.file_helpers import FileHelpers
    from .utils.helpers.validation_helpers import ValidationHelpers
    USE_NEW_HELPERS = True
except ImportError:
    USE_NEW_HELPERS = False
    # 조용한 fallback - 헬퍼 모듈이 없을 때는 기존 구현 사용
    pass

# ===== 기존 코드 호환성을 위한 래퍼 함수들 =====

def create_treeview_with_scrollbar(parent, columns, headings, column_widths=None, height=20):
    """
    스크롤바가 있는 트리뷰를 생성하여 반환합니다.
    """
    if USE_NEW_HELPERS:
        return UIHelpers.create_treeview_with_scrollbar(
            parent, columns, headings, column_widths, height
        )
    else:
        # 기존 구현
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
            if column_widths and col in column_widths:
                treeview.column(col, width=column_widths[col], stretch=True)
            else:
                treeview.column(col, width=100, stretch=True)
        
        return frame, treeview

def create_label_entry_pair(parent, label_text, row=0, column=0, initial_value=""):
    """
    레이블과 입력 필드 쌍을 생성합니다.
    """
    ttk.Label(parent, text=label_text).grid(row=row, column=column, padx=5, pady=5, sticky="w")
    var = tk.StringVar(value=initial_value)
    entry = ttk.Entry(parent, textvariable=var, width=30)
    entry.grid(row=row, column=column+1, padx=5, pady=5, sticky="ew")
    return var, entry

def format_num_value(value, decimal_places=4):
    """
    숫자 값을 적절한 형식으로 포맷팅합니다.
    """
    if USE_NEW_HELPERS:
        return DataHelpers.format_num_value(value, decimal_places)
    else:
        # 기존 구현
        if value is None:
            return ""
        
        try:
            # 정수인 경우
            if float(value).is_integer():
                return str(int(value))
            
            # 실수인 경우
            formatted = f"{float(value):.{decimal_places}f}"
            return formatted.rstrip('0').rstrip('.') if '.' in formatted else f"{float(value):.0f}"
        except (ValueError, TypeError):
            return str(value)

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
    """
    if USE_NEW_HELPERS:
        return ValidationHelpers.verify_password(password)
    else:
        # 기존 구현
        import hashlib
        if not password:
            return False
        
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config", "settings.json"
            )
            
            if os.path.exists(config_path):
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                password_hash = settings.get('maint_password_hash', '')
            else:
                return False
            
            input_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            return input_hash == password_hash
        except Exception:
            return False

def change_maintenance_password(current_password, new_password):
    """
    유지보수 모드 비밀번호를 변경합니다.
    """
    if USE_NEW_HELPERS:
        return ValidationHelpers.change_maintenance_password(current_password, new_password)
    else:
        # 기존 구현
        import hashlib
        if not verify_password(current_password):
            return False
        
        try:
            import json
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config", "settings.json"
            )
            
            settings = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            new_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
            settings['maint_password_hash'] = new_hash
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception:
            return False

def load_settings():
    """
    설정 파일을 로드합니다.
    """
    if USE_NEW_HELPERS:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "settings.json"
        )
        return FileHelpers.read_json_file(config_path) or {}
    else:
        # 기존 구현
        import json
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "settings.json"
        )
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

def save_settings(settings):
    """
    설정 파일을 저장합니다.
    """
    if USE_NEW_HELPERS:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "settings.json"
        )
        return FileHelpers.write_json_file(config_path, settings)
    else:
        # 기존 구현
        import json
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config", "settings.json"
        )
        
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

def create_safe_filename(filename):
    """
    안전한 파일명을 생성합니다.
    """
    if USE_NEW_HELPERS:
        return FileHelpers.get_safe_filename(filename)
    else:
        # 기존 구현
        import re
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe_filename = re.sub(r'_+', '_', safe_filename)
        safe_filename = safe_filename.strip('. ')
        return safe_filename if safe_filename else "untitled"

def parse_numeric_value(value):
    """
    문자열에서 숫자 값을 추출합니다.
    """
    if USE_NEW_HELPERS:
        return DataHelpers.parse_numeric_value(value)
    else:
        # 기존 구현
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

def calculate_similarity(str1, str2):
    """
    두 문자열의 유사도를 계산합니다.
    """
    if USE_NEW_HELPERS:
        return DataHelpers.calculate_similarity(str1, str2)
    else:
        # 기본 구현
        if str1 == str2:
            return 1.0
        return 0.0

def export_dataframe_to_excel(df, filename, sheet_name='Sheet1'):
    """
    DataFrame을 Excel 파일로 내보냅니다.
    """
    if USE_NEW_HELPERS:
        return FileHelpers.write_excel_file(df, filename, sheet_name)
    else:
        # 기존 구현
        try:
            df.to_excel(filename, sheet_name=sheet_name, index=False)
            return True
        except Exception:
            return False

def read_text_file_to_dataframe(file_path):
    """
    텍스트 파일을 DataFrame으로 읽습니다.
    """
    if USE_NEW_HELPERS:
        return FileHelpers.parse_custom_text_file(file_path)
    else:
        # 기본 구현 - 간단한 CSV 형태로 읽기
        try:
            import pandas as pd
            return pd.read_csv(file_path, sep='\\t', encoding='utf-8')
        except Exception:
            try:
                return pd.read_csv(file_path, encoding='utf-8')
            except Exception:
                return None

# ===== 새로운 헬퍼 모듈들 직접 노출 =====
# 더 고급 기능이 필요한 경우 직접 사용 가능

if USE_NEW_HELPERS:
    # UI 헬퍼
    UIHelper = UIHelpers
    
    # 데이터 헬퍼  
    DataHelper = DataHelpers
    
    # 파일 헬퍼
    FileHelper = FileHelpers
    
    # 검증 헬퍼
    ValidationHelper = ValidationHelpers
else:
    # 기존 구현 사용 시 더미 클래스 제공
    class DummyHelper:
        pass
    
    UIHelper = DummyHelper
    DataHelper = DummyHelper
    FileHelper = DummyHelper
    ValidationHelper = DummyHelper

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