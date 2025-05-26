"""
공통 유틸리티 함수 모듈

이 모듈은 DB_Manager 애플리케이션에서 공통으로 사용되는 유틸리티 함수를 제공합니다.
UI 요소 생성, 데이터 처리 등 여러 곳에서 재사용 가능한 함수들을 정의합니다.
"""

import tkinter as tk
from tkinter import ttk

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
