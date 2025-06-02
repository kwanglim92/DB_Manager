# LoadingDialog 및 공통 다이얼로그

import tkinter as tk
from tkinter import ttk

class LoadingDialog:
    """
    로딩 중임을 알려주는 대화 상자 클래스
    """
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("로딩 중...")
        window_width = 300
        window_height = 100
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.top.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.top.transient(parent)
        self.top.grab_set()
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            self.top, 
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=200
        )
        self.progress.pack(pady=10)
        self.status_label = ttk.Label(self.top, text="파일 로딩 중...")
        self.status_label.pack(pady=5)
        self.percentage_label = ttk.Label(self.top, text="0%")
        self.percentage_label.pack(pady=5)
        self.top.protocol("WM_DELETE_WINDOW", lambda: None)
    def update_progress(self, value, status_text=None):
        self.progress_var.set(value)
        self.percentage_label.config(text=f"{int(value)}%")
        if status_text:
            self.status_label.config(text=status_text)
        self.top.update()
    def close(self):
        self.top.grab_release()
        self.top.destroy()
