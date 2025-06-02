"""
# 이 파일은 리팩토링되어 실제 코드는 app/utils.py에서 확인하세요.
# 프로그램 실행은 main.py를 사용하세요.
모듈

이 모듈은 DB_Manager 애플리케이션에서 공통으로 사용되는 유틸리티 함수를 제공합니다.
UI 요소 생성, 데이터 처리, 설정 관리 등 여러 곳에서 재사용 가능한 함수들을 정의합니다.
"""

import os
import json
import hashlib
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def create_treeview_with_scrollbar(parent, columns, headings, column_widths=None, height=20, style=None, show="headings"):
    """
    트리뷰와 스크롤바를 포함한 프레임을 생성하고 반환합니다.
    
    Args:
        parent: 부모 위젯
        columns: 컬럼 ID 리스트
        headings: 컬럼 헤더 텍스트 딕셔너리 (key: 컬럼 ID, value: 헤더 텍스트)
        column_widths: 컬럼 너비 딕셔너리 (key: 컬럼 ID, value: 너비)
        height: 트리뷰 높이
        style: 트리뷰 스타일
        show: 트리뷰 표시 옵션 ("headings", "tree", "tree headings" 등)
        
    Returns:
        tuple: (frame, treeview) - 생성된 프레임과 트리뷰 객체
    """
    frame = ttk.Frame(parent)
    
    # 트리뷰 생성
    tree = ttk.Treeview(frame, columns=columns, show=show, height=height, style=style)
    
    # 스크롤바 생성
    v_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    h_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    
    # 트리뷰와 스크롤바 연결
    tree.configure(yscrollcommand=v_scroll.set, xscroll=h_scroll.set)
    
    # 레이아웃
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # 컬럼 설정
    for col in columns:
        tree.heading(col, text=headings.get(col, col), anchor="w")
        width = 100  # 기본 너비
        if column_widths and col in column_widths:
            width = column_widths[col]
        tree.column(col, width=width)
    
    return frame, tree

def create_label_entry_pair(parent, label_text, variable=None, width=20):
    """
    라벨과 입력 필드를 포함한 프레임을 생성하고 반환합니다.
    
    Args:
        parent: 부모 위젯
        label_text: 라벨 텍스트
        variable: 입력 필드와 연결할 변수 (StringVar 등)
        width: 입력 필드 너비
        
    Returns:
        tuple: (frame, entry) - 생성된 프레임과 입력 필드 객체
    """
    frame = ttk.Frame(parent)
    label = ttk.Label(frame, text=label_text)
    label.pack(side=tk.LEFT, padx=(0, 5))
    
    entry = ttk.Entry(frame, width=width)
    if variable:
        entry.configure(textvariable=variable)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    return frame, entry

def format_num_value(value):
    """
    숫자 또는 문자열 값을 적절한 형식으로 변환합니다.
    
    Args:
        value: 변환할 값
        
    Returns:
        변환된 값 (숫자는 float, 나머지는 문자열)
    """
    try:
        if isinstance(value, str) and value.replace('.', '', 1).isdigit():
            return float(value)
        return value
    except:
        return value

def get_config_path():
    """
    설정 파일 경로를 반환합니다.
    
    Returns:
        str: 설정 파일 경로
    """
    # 애플리케이션 루트 디렉토리 찾기
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(base_dir, 'config')
    
    # 설정 디렉토리가 없으면 생성
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    return os.path.join(config_dir, 'settings.json')

def load_settings():
    """
    설정 파일에서 설정을 로드합니다.
    
    Returns:
        dict: 설정 정보
    """
    config_path = get_config_path()
    default_settings = {
        'maint_password_hash': hashlib.sha256('1234'.encode()).hexdigest(),  # 기본 비밀번호 '1234'의 해시
        'page_size': 100,  # 변경 이력 페이지 크기
        'auto_backup': True,  # 자동 백업 여부
        'backup_interval_days': 7  # 백업 주기 (일)
    }
    
    if not os.path.exists(config_path):
        # 설정 파일이 없으면 기본 설정으로 생성
        save_settings(default_settings)
        return default_settings
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings
    except Exception as e:
        print(f'설정 로드 오류: {str(e)}')
        return default_settings

def save_settings(settings):
    """
    설정을 파일에 저장합니다.
    
    Args:
        settings (dict): 저장할 설정 정보
    
    Returns:
        bool: 저장 성공 여부
    """
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f'설정 저장 오류: {str(e)}')
        return False

def verify_password(input_password, hashed_password=None):
    """
    입력된 비밀번호가 저장된 해시와 일치하는지 확인합니다.
    
    Args:
        input_password (str): 확인할 비밀번호
        hashed_password (str, optional): 비교할 해시 값. 없으면 설정에서 로드
    
    Returns:
        bool: 비밀번호 일치 여부
    """
    if hashed_password is None:
        settings = load_settings()
        hashed_password = settings.get('maint_password_hash')
    
    input_hash = hashlib.sha256(input_password.encode()).hexdigest()
    return input_hash == hashed_password

def change_maintenance_password(old_password, new_password):
    """
    유지보수 모드 비밀번호를 변경합니다.
    
    Args:
        old_password (str): 현재 비밀번호
        new_password (str): 새 비밀번호
    
    Returns:
        bool: 비밀번호 변경 성공 여부
    """
    settings = load_settings()
    
    # 현재 비밀번호 확인
    if not verify_password(old_password, settings.get('maint_password_hash')):
        return False
    
    # 새 비밀번호 해시 생성 및 저장
    settings['maint_password_hash'] = hashlib.sha256(new_password.encode()).hexdigest()
    return save_settings(settings)
