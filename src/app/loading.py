# LoadingDialog 및 공통 다이얼로그

import tkinter as tk
from tkinter import ttk

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

class LoadingDialog:
    """
    로딩 중임을 알려주는 대화 상자 클래스
    """
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("로딩 중...")
        
        # 기본 크기 설정
        window_width = 300
        window_height = 100
        self.top.geometry(f'{window_width}x{window_height}')
        
        # 모달 설정
        self.top.transient(parent)
        self.top.grab_set()
        
        # UI 구성
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
        
        # 창 닫기 버튼 비활성화
        self.top.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # 부모 창 중앙에 배치
        center_dialog_on_parent(self.top, parent)
    def update_progress(self, value, status_text=None):
        self.progress_var.set(value)
        self.percentage_label.config(text=f"{int(value)}%")
        if status_text:
            self.status_label.config(text=status_text)
        self.top.update()
    def close(self):
        self.top.grab_release()
        self.top.destroy()
