# Default DB 관리 탭 및 기능

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
from app.utils import create_treeview_with_scrollbar, create_label_entry_pair, format_num_value

def add_default_db_functions_to_class(cls):
    """
    DBManager 클래스에 Default DB 관리 기능을 추가합니다.
    """
    def create_default_db_tab(self):
        default_db_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(default_db_tab, text="Default DB 관리")
        # 이하 기존 create_default_db_tab 코드 이관 (생략)
    cls.create_default_db_tab = create_default_db_tab
    # 기타 함수들도 모두 이관 (생략)
