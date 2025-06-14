# 변경 이력 관리 탭 및 기능

import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import pandas as pd
from app.utils import create_treeview_with_scrollbar, create_label_entry_pair
from app.loading import LoadingDialog

def add_change_history_functions_to_class(cls):
    """
    DBManager 클래스에 변경 이력 관리 기능을 추가합니다.
    """
    def create_change_history_tab(self):
        history_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(history_tab, text="변경 이력 관리")
        left_frame = ttk.LabelFrame(history_tab, text="변경 이력 조회", width=300, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        date_frame = ttk.Frame(left_frame)
        date_frame.pack(fill=tk.X, pady=5)
        ttk.Label(date_frame, text="시작 날짜:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.start_date_var = tk.StringVar()
        ttk.Entry(date_frame, textvariable=self.start_date_var, width=12).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(date_frame, text="(YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Label(date_frame, text="종료 날짜:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.end_date_var = tk.StringVar()
        ttk.Entry(date_frame, textvariable=self.end_date_var, width=12).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(date_frame, text="(YYYY-MM-DD)").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        type_frame = ttk.Frame(left_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="항목 유형:").pack(side=tk.LEFT, padx=5)
        self.item_type_var = tk.StringVar(value="all")
        ttk.Radiobutton(type_frame, text="전체", variable=self.item_type_var, value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="장비 유형", variable=self.item_type_var, value="equipment_type").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="파라미터", variable=self.item_type_var, value="parameter").pack(side=tk.LEFT, padx=5)
        change_frame = ttk.Frame(left_frame)
        change_frame.pack(fill=tk.X, pady=5)
        ttk.Label(change_frame, text="변경 유형:").pack(side=tk.LEFT, padx=5)
        self.change_type_var = tk.StringVar(value="all")
        ttk.Radiobutton(change_frame, text="전체", variable=self.change_type_var, value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(change_frame, text="추가", variable=self.change_type_var, value="add").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(change_frame, text="수정", variable=self.change_type_var, value="update").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(change_frame, text="삭제", variable=self.change_type_var, value="delete").pack(side=tk.LEFT, padx=5)
        page_frame = ttk.Frame(left_frame)
        page_frame.pack(fill=tk.X, pady=5)
        ttk.Label(page_frame, text="페이지:").pack(side=tk.LEFT, padx=5)
        self.current_page_var = tk.IntVar(value=1)
        self.current_page_entry = ttk.Entry(page_frame, textvariable=self.current_page_var, width=5)
        self.current_page_entry.pack(side=tk.LEFT, padx=2)
        self.total_pages_label = ttk.Label(page_frame, text="/ 1")
        self.total_pages_label.pack(side=tk.LEFT, padx=2)
        ttk.Button(page_frame, text="◀", width=3, command=lambda: self.change_page(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(page_frame, text="▶", width=3, command=lambda: self.change_page(1)).pack(side=tk.LEFT, padx=2)
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="조회", command=self.query_change_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="엑셀로 내보내기", command=self.export_history_to_excel).pack(side=tk.LEFT, padx=5)
        columns = ("changed_at", "username", "change_type", "item_type", "item_name", "old_value", "new_value")
        headings = {
            "changed_at": "변경일시", "username": "사용자", "change_type": "변경유형", "item_type": "항목유형",
            "item_name": "항목명", "old_value": "이전값", "new_value": "변경값"
        }
        column_widths = {
            "changed_at": 140, "username": 80, "change_type": 80, "item_type": 100,
            "item_name": 140, "old_value": 120, "new_value": 120
        }
        right_frame = ttk.Frame(history_tab)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree_frame, self.history_tree = create_treeview_with_scrollbar(
            right_frame, columns, headings, column_widths, height=30)
        tree_frame.pack(fill=tk.BOTH, expand=True)
    cls.create_change_history_tab = create_change_history_tab
    # 이하 query_change_history, export_history_to_excel 등 함수들 이관 (생략)
