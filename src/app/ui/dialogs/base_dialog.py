"""
다이얼로그 기본 클래스
기존 manager.py의 다양한 다이얼로그들을 객체지향 방식으로 개선
"""

import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, Tuple, List

class BaseDialog(ABC):
    """
    다이얼로그의 기본 클래스
    모달 다이얼로그의 공통 패턴을 제공
    """
    
    def __init__(self, parent: tk.Tk, title: str = "다이얼로그", 
                 size: Tuple[int, int] = (400, 300), resizable: bool = False):
        """
        다이얼로그 초기화
        
        Args:
            parent: 부모 윈도우
            title: 다이얼로그 제목
            size: 다이얼로그 크기 (너비, 높이)
            resizable: 크기 조절 가능 여부
        """
        self.parent = parent
        self.result = None
        self.dialog = None
        
        # 다이얼로그 윈도우 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{size[0]}x{size[1]}")
        self.dialog.resizable(resizable, resizable)
        
        # 모달 설정
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 창 중앙 배치
        self._center_window()
        
        # 다이얼로그 구성
        self._setup_dialog()
        self._bind_events()
        
        # 포커스 설정
        self.dialog.focus_set()
    
    def _center_window(self):
        """다이얼로그를 부모 창 중앙에 배치"""
        self.dialog.update_idletasks()
        
        # 부모 창 위치와 크기
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # 다이얼로그 크기
        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()
        
        # 중앙 위치 계산
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    @abstractmethod
    def _setup_dialog(self):
        """다이얼로그 UI 구성 (서브클래스에서 구현)"""
        pass
    
    def _bind_events(self):
        """이벤트 바인딩"""
        # ESC 키로 취소
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        
        # 창 닫기 버튼 처리
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def show(self) -> Any:
        """
        다이얼로그 표시 및 결과 반환
        
        Returns:
            다이얼로그 결과 (OK시 실제 값, Cancel시 None)
        """
        # 다이얼로그가 닫힐 때까지 대기
        self.parent.wait_window(self.dialog)
        return self.result
    
    def ok(self):
        """OK 버튼 처리"""
        if self._validate_input():
            self.result = self._get_result()
            self.dialog.destroy()
    
    def cancel(self):
        """Cancel 버튼 처리"""
        self.result = None
        self.dialog.destroy()
    
    def _validate_input(self) -> bool:
        """입력 유효성 검사 (서브클래스에서 오버라이드)"""
        return True
    
    def _get_result(self) -> Any:
        """결과 값 반환 (서브클래스에서 오버라이드)"""
        return True
    
    def show_error(self, message: str):
        """에러 메시지 표시"""
        messagebox.showerror("오류", message, parent=self.dialog)
    
    def show_warning(self, message: str):
        """경고 메시지 표시"""
        messagebox.showwarning("경고", message, parent=self.dialog)
    
    def ask_confirmation(self, message: str) -> bool:
        """확인 메시지 표시"""
        return messagebox.askyesno("확인", message, parent=self.dialog)

class FormDialog(BaseDialog):
    """
    폼 입력 다이얼로그
    여러 필드를 가진 입력 폼을 위한 다이얼로그
    """
    
    def __init__(self, parent: tk.Tk, title: str = "입력", 
                 fields: Optional[Dict[str, Dict[str, Any]]] = None,
                 size: Tuple[int, int] = (400, 300)):
        """
        폼 다이얼로그 초기화
        
        Args:
            parent: 부모 윈도우
            title: 다이얼로그 제목
            fields: 필드 정의 딕셔너리
            size: 다이얼로그 크기
        """
        self.fields_config = fields or {}
        self.field_widgets = {}
        self.field_variables = {}
        
        super().__init__(parent, title, size)
    
    def _setup_dialog(self):
        """폼 다이얼로그 UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 필드 프레임
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 필드 생성
        self._create_fields(fields_frame)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 버튼 생성
        ttk.Button(button_frame, text="확인", command=self.ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="취소", command=self.cancel).pack(side=tk.RIGHT)
    
    def _create_fields(self, parent: ttk.Frame):
        """필드 생성"""
        row = 0
        for field_name, field_config in self.fields_config.items():
            # 필드 설정 파싱
            label_text = field_config.get('label', field_name)
            field_type = field_config.get('type', 'entry')
            initial_value = field_config.get('initial_value', '')
            width = field_config.get('width', 30)
            options = field_config.get('options', {})
            
            # 라벨 생성
            ttk.Label(parent, text=label_text + ":").grid(
                row=row, column=0, padx=5, pady=5, sticky="w"
            )
            
            # 변수 생성
            if field_type == 'checkbox':
                var = tk.BooleanVar(value=bool(initial_value))
            else:
                var = tk.StringVar(value=str(initial_value))
            
            self.field_variables[field_name] = var
            
            # 위젯 생성
            if field_type == 'entry':
                widget = ttk.Entry(parent, textvariable=var, width=width, **options)
            elif field_type == 'combobox':
                widget = ttk.Combobox(parent, textvariable=var, width=width, **options)
            elif field_type == 'checkbox':
                widget = ttk.Checkbutton(parent, variable=var, **options)
            elif field_type == 'text':
                widget = tk.Text(parent, width=width, height=options.get('height', 4), **options)
                widget.insert('1.0', str(initial_value))
                var = None  # Text 위젯은 StringVar 사용 안함
            else:
                widget = ttk.Entry(parent, textvariable=var, width=width, **options)
            
            widget.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            self.field_widgets[field_name] = widget
            
            # 컬럼 가중치 설정
            parent.columnconfigure(1, weight=1)
            
            row += 1
    
    def get_field_value(self, field_name: str) -> Any:
        """필드 값 가져오기"""
        if field_name not in self.field_widgets:
            return None
        
        field_config = self.fields_config.get(field_name, {})
        field_type = field_config.get('type', 'entry')
        
        if field_type == 'text':
            widget = self.field_widgets[field_name]
            return widget.get('1.0', tk.END).strip()
        elif field_name in self.field_variables:
            return self.field_variables[field_name].get()
        else:
            return None
    
    def set_field_value(self, field_name: str, value: Any):
        """필드 값 설정"""
        if field_name not in self.field_widgets:
            return
        
        field_config = self.fields_config.get(field_name, {})
        field_type = field_config.get('type', 'entry')
        
        if field_type == 'text':
            widget = self.field_widgets[field_name]
            widget.delete('1.0', tk.END)
            widget.insert('1.0', str(value))
        elif field_name in self.field_variables:
            self.field_variables[field_name].set(value)
    
    def _validate_input(self) -> bool:
        """필드 유효성 검사"""
        required_fields = []
        
        # 필수 필드 확인
        for field_name, field_config in self.fields_config.items():
            if field_config.get('required', False):
                required_fields.append(field_name)
        
        # 필수 필드 검증
        for field_name in required_fields:
            value = self.get_field_value(field_name)
            if not value or (isinstance(value, str) and not value.strip()):
                field_config = self.fields_config.get(field_name, {})
                label_text = field_config.get('label', field_name)
                self.show_error(f"{label_text}는 필수 항목입니다.")
                return False
        
        return True
    
    def _get_result(self) -> Dict[str, Any]:
        """모든 필드 값을 딕셔너리로 반환"""
        result = {}
        for field_name in self.fields_config:
            result[field_name] = self.get_field_value(field_name)
        return result

class ConfirmDialog(BaseDialog):
    """
    확인 다이얼로그
    사용자에게 확인을 요청하는 다이얼로그
    """
    
    def __init__(self, parent: tk.Tk, title: str = "확인", 
                 message: str = "", icon: str = "question"):
        """
        확인 다이얼로그 초기화
        
        Args:
            parent: 부모 윈도우
            title: 다이얼로그 제목
            message: 확인 메시지
            icon: 아이콘 유형 ("question", "warning", "info", "error")
        """
        self.message = message
        self.icon = icon
        
        super().__init__(parent, title, (350, 150))
    
    def _setup_dialog(self):
        """확인 다이얼로그 UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 메시지 프레임
        message_frame = ttk.Frame(main_frame)
        message_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 아이콘 (간단한 텍스트로 대체)
        icon_text = {
            "question": "❓",
            "warning": "⚠️", 
            "info": "ℹ️",
            "error": "❌"
        }.get(self.icon, "❓")
        
        ttk.Label(message_frame, text=icon_text, font=("Arial", 16)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(message_frame, text=self.message, wraplength=250).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 버튼 생성
        ttk.Button(button_frame, text="예", command=self.ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="아니오", command=self.cancel).pack(side=tk.RIGHT)

class ListSelectionDialog(BaseDialog):
    """
    목록 선택 다이얼로그
    목록에서 항목을 선택하는 다이얼로그
    """
    
    def __init__(self, parent: tk.Tk, title: str = "선택", 
                 items: List[str] = None, message: str = "",
                 multi_select: bool = False):
        """
        목록 선택 다이얼로그 초기화
        
        Args:
            parent: 부모 윈도우
            title: 다이얼로그 제목
            items: 선택 가능한 항목들
            message: 안내 메시지
            multi_select: 다중 선택 허용 여부
        """
        self.items = items or []
        self.message = message
        self.multi_select = multi_select
        self.listbox = None
        
        super().__init__(parent, title, (350, 400))
    
    def _setup_dialog(self):
        """목록 선택 다이얼로그 UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 메시지 라벨 (있는 경우)
        if self.message:
            ttk.Label(main_frame, text=self.message).pack(fill=tk.X, pady=(0, 10))
        
        # 리스트박스 프레임
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 리스트박스
        selectmode = tk.EXTENDED if self.multi_select else tk.SINGLE
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=selectmode)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바 연결
        scrollbar.config(command=self.listbox.yview)
        
        # 항목 추가
        for item in self.items:
            self.listbox.insert(tk.END, item)
        
        # 첫 번째 항목 선택
        if self.items and not self.multi_select:
            self.listbox.selection_set(0)
        
        # 더블클릭으로 확인
        self.listbox.bind('<Double-1>', lambda e: self.ok())
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 버튼 생성
        ttk.Button(button_frame, text="확인", command=self.ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="취소", command=self.cancel).pack(side=tk.RIGHT)
    
    def _validate_input(self) -> bool:
        """선택 유효성 검사"""
        if not self.listbox.curselection():
            self.show_error("항목을 선택해주세요.")
            return False
        return True
    
    def _get_result(self) -> Any:
        """선택된 항목 반환"""
        selections = self.listbox.curselection()
        
        if self.multi_select:
            return [self.items[i] for i in selections]
        else:
            return self.items[selections[0]] if selections else None

# 편의 함수들 (기존 코드와의 호환성)
def show_form_dialog(parent: tk.Tk, title: str, fields: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """폼 다이얼로그 표시"""
    dialog = FormDialog(parent, title, fields)
    return dialog.show()

def show_confirm_dialog(parent: tk.Tk, title: str, message: str, icon: str = "question") -> bool:
    """확인 다이얼로그 표시"""
    dialog = ConfirmDialog(parent, title, message, icon)
    result = dialog.show()
    return result is not None

def show_list_selection_dialog(parent: tk.Tk, title: str, items: List[str], 
                              message: str = "", multi_select: bool = False) -> Any:
    """목록 선택 다이얼로그 표시"""
    dialog = ListSelectionDialog(parent, title, items, message, multi_select)
    return dialog.show() 