"""
로딩 다이얼로그 클래스 모듈

이 모듈은 시간이 오래 걸리는 작업에 대한 진행 상황을 표시하는 로딩 다이얼로그를 제공합니다.
"""

import tkinter as tk
from tkinter import ttk

class LoadingDialog:
    """로딩 중임을 알려주는 대화 상자 클래스"""
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("로딩 중...")
        
        # 부모 창 중앙에 위치
        window_width = 300
        window_height = 100
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.top.geometry(f'{window_width}x{window_height}+{x}+{y}')
        
        # 항상 최상위에 표시
        self.top.transient(parent)
        self.top.grab_set()
        
        # 진행 상태 표시
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            self.top, 
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=200
        )
        self.progress.pack(pady=10)
        
        # 현재 작업 설명
        self.status_label = ttk.Label(self.top, text="파일 로딩 중...")
        self.status_label.pack(pady=5)
        
        # 진행률 텍스트
        self.percentage_label = ttk.Label(self.top, text="0%")
        self.percentage_label.pack(pady=5)
        
        # 창 닫기 버튼 비활성화
        self.top.protocol("WM_DELETE_WINDOW", lambda: None)
        
    def update_progress(self, value, status_text=None):
        """진행률 업데이트"""
        self.progress_var.set(value)
        self.percentage_label.config(text=f"{int(value)}%")
        if status_text:
            self.status_label.config(text=status_text)
        self.top.update()
    
    def close(self):
        """다이얼로그 닫기"""
        self.top.grab_release()
        self.top.destroy()
