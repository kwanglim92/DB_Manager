"""
향상된 다이얼로그 시스템
DB Manager를 위한 전용 다이얼로그 컴포넌트들
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List, Optional, Callable
from .base_dialog import BaseDialog


class ProgressDialog(BaseDialog):
    """진행률 표시 다이얼로그"""
    
    def __init__(self, parent=None, title: str = "진행 중...", 
                 message: str = "작업을 수행하고 있습니다.", cancelable: bool = True):
        """ProgressDialog 초기화"""
        super().__init__(parent, title, modal=True)
        
        self.message = message
        self.cancelable = cancelable
        self.cancelled = False
        self.progress_var = tk.IntVar()
        self.status_var = tk.StringVar(value=message)
        
        # UI 생성
        self._create_dialog_ui()
        
        # 취소 불가능한 경우 닫기 버튼 비활성화
        if not cancelable:
            self.protocol("WM_DELETE_WINDOW", self._do_nothing)
    
    def _create_dialog_ui(self):
        """다이얼로그 UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 메시지 라벨
        self.message_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                      font=("Arial", 10))
        self.message_label.pack(pady=(0, 10))
        
        # 진행률 바
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           length=300, mode='determinate')
        self.progress_bar.pack(pady=(0, 10), fill=tk.X)
        
        # 퍼센트 라벨
        self.percent_label = ttk.Label(main_frame, text="0%", font=("Arial", 9))
        self.percent_label.pack(pady=(0, 10))
        
        # 취소 버튼 (옵션)
        if self.cancelable:
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=(10, 0))
            
            self.cancel_button = ttk.Button(button_frame, text="취소", 
                                          command=self._handle_cancel)
            self.cancel_button.pack()
    
    def update_progress(self, value: int, message: str = None):
        """진행률 업데이트"""
        self.progress_var.set(value)
        self.percent_label.config(text=f"{value}%")
        
        if message:
            self.status_var.set(message)
        
        self.update_idletasks()
    
    def _handle_cancel(self):
        """취소 처리"""
        self.cancelled = True
        self.destroy()
    
    def _do_nothing(self):
        """아무것도 하지 않는 함수 (닫기 방지용)"""
        pass
    
    def is_cancelled(self) -> bool:
        """취소 여부 반환"""
        return self.cancelled


class EquipmentTypeDialog(BaseDialog):
    """장비 유형 관리 다이얼로그"""
    
    def __init__(self, parent=None, equipment_data: Dict = None, mode: str = "add"):
        """EquipmentTypeDialog 초기화"""
        title = "장비 유형 추가" if mode == "add" else "장비 유형 편집"
        super().__init__(parent, title, modal=True)
        
        self.equipment_data = equipment_data or {}
        self.mode = mode
        self.result = None
        
        # 입력 변수들
        self.name_var = tk.StringVar(value=self.equipment_data.get('name', ''))
        
        # UI 생성
        self._create_dialog_ui()
        
        # 창 크기 및 위치 설정
        self.geometry("400x300")
        self.center_window()
    
    def _create_dialog_ui(self):
        """다이얼로그 UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 이름 입력
        ttk.Label(main_frame, text="장비 유형명:").pack(anchor="w", pady=5)
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="저장", command=self._save_equipment).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="취소", command=self._cancel).pack(side=tk.RIGHT)
        
        # 첫 번째 입력 필드에 포커스
        name_entry.focus()
    
    def _save_equipment(self):
        """장비 유형 저장"""
        if not self.name_var.get().strip():
            messagebox.showerror("오류", "장비 유형명을 입력해주세요.")
            return
        
        self.result = {"name": self.name_var.get().strip()}
        self.destroy()
    
    def _cancel(self):
        """취소"""
        self.result = None
        self.destroy()


class ParameterDialog(BaseDialog):
    """파라미터 입력 다이얼로그"""
    
    def __init__(self, parent=None, param_data: Dict = None, mode: str = "add"):
        """ParameterDialog 초기화"""
        title = "파라미터 추가" if mode == "add" else "파라미터 편집"
        super().__init__(parent, title, modal=True)
        
        self.param_data = param_data or {}
        self.mode = mode
        self.result = None
        
        # 입력 변수들
        self.name_var = tk.StringVar(value=self.param_data.get('name', ''))
        
        # UI 생성
        self._create_dialog_ui()
        
        # 창 크기 및 위치 설정
        self.geometry("300x200")
        self.center_window()
    
    def _create_dialog_ui(self):
        """다이얼로그 UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 파라미터명 입력
        ttk.Label(main_frame, text="파라미터명:").pack(anchor="w", pady=5)
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=30)
        name_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="저장", command=self._save_parameter).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="취소", command=self._cancel).pack(side=tk.RIGHT)
        
        name_entry.focus()
    
    def _save_parameter(self):
        """파라미터 저장"""
        if not self.name_var.get().strip():
            messagebox.showerror("오류", "파라미터명을 입력해주세요.")
            return
        
        self.result = {"name": self.name_var.get().strip()}
        self.destroy()
    
    def _cancel(self):
        """취소"""
        self.result = None
        self.destroy()


class ExportDialog(BaseDialog):
    """데이터 내보내기 다이얼로그"""
    
    def __init__(self, parent=None, export_types: List[str] = None):
        """ExportDialog 초기화"""
        super().__init__(parent, "데이터 내보내기", modal=True)
        
        self.export_types = export_types or ["Excel", "CSV", "JSON"]
        self.result = None
        
        # 설정 변수들
        self.format_var = tk.StringVar(value=self.export_types[0])
        self.file_path_var = tk.StringVar()
        
        # UI 생성
        self._create_dialog_ui()
        
        # 창 크기 및 위치 설정
        self.geometry("400x250")
        self.center_window()
    
    def _create_dialog_ui(self):
        """다이얼로그 UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 파일 형식 선택
        format_frame = ttk.LabelFrame(main_frame, text="내보내기 형식", padding="10")
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        for fmt in self.export_types:
            ttk.Radiobutton(format_frame, text=fmt, variable=self.format_var, 
                           value=fmt).pack(anchor="w", pady=2)
        
        # 파일 경로 선택
        path_frame = ttk.LabelFrame(main_frame, text="저장 위치", padding="10")
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill=tk.X)
        
        ttk.Entry(path_entry_frame, textvariable=self.file_path_var, 
                 state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(path_entry_frame, text="찾아보기...", 
                  command=self._browse_file).pack(side=tk.RIGHT)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="내보내기", command=self._export_data).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="취소", command=self._cancel).pack(side=tk.RIGHT)
    
    def _browse_file(self):
        """파일 경로 선택"""
        file_path = filedialog.asksaveasfilename(
            title="파일로 저장",
            filetypes=[("모든 파일", "*.*")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
    
    def _export_data(self):
        """데이터 내보내기"""
        if not self.file_path_var.get():
            messagebox.showerror("오류", "저장할 파일 경로를 선택해주세요.")
            return
        
        self.result = {
            "format": self.format_var.get(),
            "file_path": self.file_path_var.get()
        }
        
        self.destroy()
    
    def _cancel(self):
        """취소"""
        self.result = None
        self.destroy()


class SettingsDialog(BaseDialog):
    """설정 다이얼로그"""
    
    def __init__(self, parent=None, current_settings: Dict = None):
        """SettingsDialog 초기화"""
        super().__init__(parent, "설정", modal=True)
        
        self.current_settings = current_settings or {}
        self.result = None
        
        # 설정 변수들
        self.theme_var = tk.StringVar(value=self.current_settings.get('theme', 'default'))
        
        # UI 생성
        self._create_dialog_ui()
        
        # 창 크기 및 위치 설정
        self.geometry("350x200")
        self.center_window()
    
    def _create_dialog_ui(self):
        """다이얼로그 UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 테마 설정
        theme_frame = ttk.LabelFrame(main_frame, text="테마 설정", padding="10")
        theme_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(theme_frame, text="테마:").pack(side=tk.LEFT, padx=(0, 10))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var,
                                  values=["default", "dark", "light"], state="readonly")
        theme_combo.pack(side=tk.LEFT)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="적용", command=self._apply_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="취소", command=self._cancel).pack(side=tk.RIGHT)
    
    def _apply_settings(self):
        """설정 적용"""
        self.result = {"theme": self.theme_var.get()}
        self.destroy()
    
    def _cancel(self):
        """취소"""
        self.result = None
        self.destroy()


# 편의 함수들
def show_progress_dialog(parent=None, title: str = "진행 중...", 
                        message: str = "작업을 수행하고 있습니다.", 
                        cancelable: bool = True) -> ProgressDialog:
    """진행률 다이얼로그 표시"""
    dialog = ProgressDialog(parent, title, message, cancelable)
    return dialog

def show_equipment_type_dialog(parent=None, equipment_data: Dict = None, 
                              mode: str = "add") -> Optional[Dict]:
    """장비 유형 다이얼로그 표시"""
    dialog = EquipmentTypeDialog(parent, equipment_data, mode)
    dialog.wait_window()
    return dialog.result

def show_export_dialog(parent=None, export_types: List[str] = None) -> Optional[Dict]:
    """내보내기 다이얼로그 표시"""
    dialog = ExportDialog(parent, export_types)
    dialog.wait_window()
    return dialog.result

def show_settings_dialog(parent=None, current_settings: Dict = None) -> Optional[Dict]:
    """설정 다이얼로그 표시"""
    dialog = SettingsDialog(parent, current_settings)
    dialog.wait_window()
    return dialog.result 