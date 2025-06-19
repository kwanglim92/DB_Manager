"""
UI 컴포넌트 기본 클래스
기존 utils.py의 UI 헬퍼 함수들을 객체지향 방식으로 개선
"""

import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable

class BaseComponent(ABC):
    """
    UI 컴포넌트의 기본 클래스
    재사용 가능하고 일관성 있는 UI 컴포넌트 구축을 위한 기반
    """
    
    def __init__(self, parent: tk.Widget, **kwargs):
        """
        기본 컴포넌트 초기화
        
        Args:
            parent: 부모 위젯
            **kwargs: 추가 설정 옵션
        """
        self.parent = parent
        self.options = kwargs
        self.widget = None
        self.callbacks = {}
        
        # 컴포넌트 구축
        self._setup_widget()
        self._configure_widget()
        self._bind_events()
    
    @abstractmethod
    def _setup_widget(self):
        """위젯 생성 (서브클래스에서 구현)"""
        pass
    
    def _configure_widget(self):
        """위젯 설정 (서브클래스에서 오버라이드 가능)"""
        pass
    
    def _bind_events(self):
        """이벤트 바인딩 (서브클래스에서 오버라이드 가능)"""
        pass
    
    def get_widget(self) -> tk.Widget:
        """메인 위젯 반환"""
        return self.widget
    
    def pack(self, **kwargs):
        """위젯을 pack으로 배치"""
        if self.widget:
            self.widget.pack(**kwargs)
        return self
    
    def grid(self, **kwargs):
        """위젯을 grid로 배치"""
        if self.widget:
            self.widget.grid(**kwargs)
        return self
    
    def place(self, **kwargs):
        """위젯을 place로 배치"""
        if self.widget:
            self.widget.place(**kwargs)
        return self
    
    def configure(self, **kwargs):
        """위젯 설정 변경"""
        if self.widget:
            self.widget.configure(**kwargs)
        return self
    
    def bind_callback(self, event_name: str, callback: Callable):
        """콜백 함수 바인딩"""
        self.callbacks[event_name] = callback
        return self
    
    def trigger_callback(self, event_name: str, *args, **kwargs):
        """콜백 함수 실행"""
        if event_name in self.callbacks:
            try:
                return self.callbacks[event_name](*args, **kwargs)
            except Exception as e:
                print(f"콜백 실행 오류 ({event_name}): {e}")
        return None
    
    def show_error(self, title: str, message: str):
        """에러 메시지 표시"""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str):
        """정보 메시지 표시"""
        messagebox.showinfo(title, message)
    
    def show_warning(self, title: str, message: str):
        """경고 메시지 표시"""
        messagebox.showwarning(title, message)
    
    def ask_yes_no(self, title: str, message: str) -> bool:
        """예/아니오 질문"""
        return messagebox.askyesno(title, message)

class ContainerComponent(BaseComponent):
    """
    컨테이너 컴포넌트 기본 클래스
    다른 컴포넌트들을 포함하는 컨테이너용
    """
    
    def __init__(self, parent: tk.Widget, container_type: str = "frame", **kwargs):
        """
        컨테이너 컴포넌트 초기화
        
        Args:
            parent: 부모 위젯
            container_type: 컨테이너 유형 ("frame", "labelframe", "notebook" 등)
            **kwargs: 추가 설정 옵션
        """
        self.container_type = container_type
        self.child_components = []
        super().__init__(parent, **kwargs)
    
    def _setup_widget(self):
        """컨테이너 위젯 생성"""
        if self.container_type == "frame":
            self.widget = ttk.Frame(self.parent, **self.options)
        elif self.container_type == "labelframe":
            self.widget = ttk.LabelFrame(self.parent, **self.options)
        elif self.container_type == "notebook":
            self.widget = ttk.Notebook(self.parent, **self.options)
        else:
            self.widget = ttk.Frame(self.parent, **self.options)
    
    def add_component(self, component: BaseComponent) -> 'ContainerComponent':
        """자식 컴포넌트 추가"""
        self.child_components.append(component)
        return self
    
    def get_component(self, index: int) -> Optional[BaseComponent]:
        """인덱스로 자식 컴포넌트 가져오기"""
        if 0 <= index < len(self.child_components):
            return self.child_components[index]
        return None
    
    def clear_components(self):
        """모든 자식 컴포넌트 제거"""
        for component in self.child_components:
            widget = component.get_widget()
            if widget:
                widget.destroy()
        self.child_components.clear()

class FormComponent(ContainerComponent):
    """
    폼 입력 컴포넌트 기본 클래스
    라벨과 입력 필드가 조합된 폼을 위한 컨테이너
    """
    
    def __init__(self, parent: tk.Widget, title: Optional[str] = None, **kwargs):
        """
        폼 컴포넌트 초기화
        
        Args:
            parent: 부모 위젯
            title: 폼 제목 (LabelFrame 사용 시)
            **kwargs: 추가 설정 옵션
        """
        self.title = title
        self.fields = {}
        
        # 제목이 있으면 LabelFrame 사용
        container_type = "labelframe" if title else "frame"
        if title:
            kwargs["text"] = title
        
        super().__init__(parent, container_type, **kwargs)
    
    def add_field(self, field_name: str, label_text: str, 
                  field_type: str = "entry", initial_value: str = "",
                  options: Optional[Dict[str, Any]] = None) -> 'FormComponent':
        """
        폼 필드 추가
        
        Args:
            field_name: 필드 이름 (내부 식별용)
            label_text: 라벨 텍스트
            field_type: 필드 유형 ("entry", "combobox", "text", "checkbox" 등)
            initial_value: 초기값
            options: 추가 옵션
            
        Returns:
            self (메서드 체이닝용)
        """
        if options is None:
            options = {}
        
        row = len(self.fields)
        
        # 라벨 생성
        label = ttk.Label(self.widget, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="w")
        
        # 필드 변수 및 위젯 생성
        var = tk.StringVar(value=initial_value)
        
        if field_type == "entry":
            field_widget = ttk.Entry(self.widget, textvariable=var, **options)
        elif field_type == "combobox":
            field_widget = ttk.Combobox(self.widget, textvariable=var, **options)
        elif field_type == "text":
            field_widget = tk.Text(self.widget, **options)
            field_widget.insert('1.0', initial_value)
            var = None  # Text 위젯은 StringVar 사용 안함
        elif field_type == "checkbox":
            var = tk.BooleanVar(value=bool(initial_value))
            field_widget = ttk.Checkbutton(self.widget, variable=var, **options)
        else:
            field_widget = ttk.Entry(self.widget, textvariable=var, **options)
        
        field_widget.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        
        # 컬럼 가중치 설정 (필드가 확장되도록)
        self.widget.columnconfigure(1, weight=1)
        
        # 필드 정보 저장
        self.fields[field_name] = {
            'label': label,
            'widget': field_widget,
            'variable': var,
            'type': field_type
        }
        
        return self
    
    def get_field_value(self, field_name: str) -> Any:
        """필드 값 가져오기"""
        if field_name not in self.fields:
            return None
        
        field_info = self.fields[field_name]
        field_type = field_info['type']
        
        if field_type == "text":
            return field_info['widget'].get('1.0', tk.END).strip()
        elif field_info['variable']:
            return field_info['variable'].get()
        else:
            return None
    
    def set_field_value(self, field_name: str, value: Any):
        """필드 값 설정"""
        if field_name not in self.fields:
            return
        
        field_info = self.fields[field_name]
        field_type = field_info['type']
        
        if field_type == "text":
            field_info['widget'].delete('1.0', tk.END)
            field_info['widget'].insert('1.0', str(value))
        elif field_info['variable']:
            field_info['variable'].set(value)
    
    def get_all_values(self) -> Dict[str, Any]:
        """모든 필드 값을 딕셔너리로 반환"""
        values = {}
        for field_name in self.fields:
            values[field_name] = self.get_field_value(field_name)
        return values
    
    def set_all_values(self, values: Dict[str, Any]):
        """딕셔너리로 모든 필드 값 설정"""
        for field_name, value in values.items():
            self.set_field_value(field_name, value)
    
    def clear_all_fields(self):
        """모든 필드 초기화"""
        for field_name in self.fields:
            field_info = self.fields[field_name]
            field_type = field_info['type']
            
            if field_type == "text":
                field_info['widget'].delete('1.0', tk.END)
            elif field_type == "checkbox":
                field_info['variable'].set(False)
            elif field_info['variable']:
                field_info['variable'].set("")
    
    def validate_fields(self, required_fields: Optional[List[str]] = None) -> List[str]:
        """
        필드 유효성 검사
        
        Args:
            required_fields: 필수 필드 목록
            
        Returns:
            List[str]: 오류 메시지 목록
        """
        errors = []
        
        if required_fields:
            for field_name in required_fields:
                value = self.get_field_value(field_name)
                if not value or (isinstance(value, str) and not value.strip()):
                    field_info = self.fields.get(field_name, {})
                    label_text = field_info.get('label', {}).cget('text') if 'label' in field_info else field_name
                    errors.append(f"{label_text}는 필수 항목입니다.")
        
        return errors 