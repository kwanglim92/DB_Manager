"""
Controller 기본 클래스
MVVM 패턴의 Controller 계층을 위한 기반 클래스
View와 ViewModel 간의 연결을 담당
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable

from ..viewmodels.base_viewmodel import BaseViewModel, PropertyChangeEvent


class BaseController(ABC):
    """
    Controller 기본 클래스
    View와 ViewModel 간의 상호작용을 조정
    """
    
    def __init__(self, view: tk.Widget, viewmodel: BaseViewModel):
        """
        Controller 초기화
        
        Args:
            view: 연결할 View (Tkinter 위젯)
            viewmodel: 연결할 ViewModel
        """
        self.view = view
        self.viewmodel = viewmodel
        self._bindings = []  # 바인딩 추적용
        
        # 초기 설정
        self._setup_bindings()
        self._setup_view_events()
        self._initial_data_binding()
    
    @abstractmethod
    def _setup_bindings(self):
        """ViewModel 속성 바인딩 설정 (서브클래스에서 구현)"""
        pass
    
    @abstractmethod
    def _setup_view_events(self):
        """View 이벤트 처리 설정 (서브클래스에서 구현)"""
        pass
    
    def _initial_data_binding(self):
        """초기 데이터 바인딩"""
        # 서브클래스에서 오버라이드 가능
        pass
    
    def bind_property_to_view(self, property_name: str, 
                             update_view_func: Callable[[Any], None]):
        """
        ViewModel 속성을 View에 바인딩
        
        Args:
            property_name: ViewModel 속성 이름
            update_view_func: View 업데이트 함수
        """
        def property_changed_handler(event: PropertyChangeEvent):
            if event.property_name == property_name:
                try:
                    update_view_func(event.new_value)
                except Exception as e:
                    print(f"View 업데이트 오류 ({property_name}): {e}")
        
        self.viewmodel.bind_property_changed(property_name, property_changed_handler)
        self._bindings.append((property_name, property_changed_handler))
        
        # 초기 값 설정
        initial_value = self.viewmodel.get_property(property_name)
        if initial_value is not None:
            try:
                update_view_func(initial_value)
            except Exception as e:
                print(f"초기 View 업데이트 오류 ({property_name}): {e}")
    
    def bind_command_to_view(self, command_name: str, view_event_source,
                            event_type: str = '<Button-1>', 
                            get_args_func: Optional[Callable] = None):
        """
        ViewModel 명령을 View 이벤트에 바인딩
        
        Args:
            command_name: ViewModel 명령 이름
            view_event_source: 이벤트 소스 위젯
            event_type: 이벤트 타입
            get_args_func: 명령 인자를 가져오는 함수
        """
        def event_handler(event=None):
            try:
                if get_args_func:
                    args = get_args_func()
                    if isinstance(args, (list, tuple)):
                        self.viewmodel.execute_command(command_name, *args)
                    elif isinstance(args, dict):
                        self.viewmodel.execute_command(command_name, **args)
                    else:
                        self.viewmodel.execute_command(command_name, args)
                else:
                    self.viewmodel.execute_command(command_name)
            except Exception as e:
                self.show_error("명령 실행 오류", str(e))
        
        view_event_source.bind(event_type, event_handler)
    
    def bind_menu_command(self, menu: tk.Menu, label: str, command_name: str,
                         get_args_func: Optional[Callable] = None):
        """
        메뉴 항목을 ViewModel 명령에 바인딩
        
        Args:
            menu: 메뉴 객체
            label: 메뉴 항목 라벨
            command_name: ViewModel 명령 이름
            get_args_func: 명령 인자를 가져오는 함수
        """
        def menu_command():
            try:
                if get_args_func:
                    args = get_args_func()
                    if isinstance(args, (list, tuple)):
                        self.viewmodel.execute_command(command_name, *args)
                    elif isinstance(args, dict):
                        self.viewmodel.execute_command(command_name, **args)
                    else:
                        self.viewmodel.execute_command(command_name, args)
                else:
                    self.viewmodel.execute_command(command_name)
            except Exception as e:
                self.show_error("명령 실행 오류", str(e))
        
        menu.add_command(label=label, command=menu_command)
    
    def bind_button_command(self, button: tk.Button, command_name: str,
                           get_args_func: Optional[Callable] = None):
        """
        버튼을 ViewModel 명령에 바인딩
        
        Args:
            button: 버튼 위젯
            command_name: ViewModel 명령 이름
            get_args_func: 명령 인자를 가져오는 함수
        """
        def button_command():
            try:
                if get_args_func:
                    args = get_args_func()
                    if isinstance(args, (list, tuple)):
                        self.viewmodel.execute_command(command_name, *args)
                    elif isinstance(args, dict):
                        self.viewmodel.execute_command(command_name, **args)
                    else:
                        self.viewmodel.execute_command(command_name, args)
                else:
                    self.viewmodel.execute_command(command_name)
            except Exception as e:
                self.show_error("명령 실행 오류", str(e))
        
        button.config(command=button_command)
    
    def create_input_dialog(self, title: str, prompt: str, 
                           input_type: str = "string", show_char: str = None) -> Any:
        """
        입력 다이얼로그 생성
        
        Args:
            title: 다이얼로그 제목
            prompt: 입력 안내 텍스트
            input_type: 입력 타입 ("string", "int", "float")
            show_char: 비밀번호 입력 시 표시 문자
            
        Returns:
            사용자 입력 값 또는 None (취소 시)
        """
        if input_type == "string":
            return simpledialog.askstring(title, prompt, show=show_char)
        elif input_type == "int":
            return simpledialog.askinteger(title, prompt)
        elif input_type == "float":
            return simpledialog.askfloat(title, prompt)
        else:
            return simpledialog.askstring(title, prompt, show=show_char)
    
    def create_folder_dialog(self, title: str = "폴더 선택", 
                            initial_dir: str = None) -> Optional[str]:
        """
        폴더 선택 다이얼로그 생성
        
        Args:
            title: 다이얼로그 제목
            initial_dir: 초기 디렉토리
            
        Returns:
            선택한 폴더 경로 또는 None
        """
        return filedialog.askdirectory(title=title, initialdir=initial_dir)
    
    def create_file_dialog(self, title: str = "파일 선택",
                          file_types: List[tuple] = None,
                          initial_dir: str = None) -> Optional[str]:
        """
        파일 선택 다이얼로그 생성
        
        Args:
            title: 다이얼로그 제목
            file_types: 파일 형식 목록
            initial_dir: 초기 디렉토리
            
        Returns:
            선택한 파일 경로 또는 None
        """
        if file_types is None:
            file_types = [("모든 파일", "*.*")]
        
        return filedialog.askopenfilename(
            title=title,
            filetypes=file_types,
            initialdir=initial_dir
        )
    
    def create_save_dialog(self, title: str = "파일 저장",
                          file_types: List[tuple] = None,
                          initial_dir: str = None,
                          default_extension: str = None) -> Optional[str]:
        """
        파일 저장 다이얼로그 생성
        
        Args:
            title: 다이얼로그 제목
            file_types: 파일 형식 목록
            initial_dir: 초기 디렉토리
            default_extension: 기본 확장자
            
        Returns:
            저장할 파일 경로 또는 None
        """
        if file_types is None:
            file_types = [("모든 파일", "*.*")]
        
        kwargs = {
            'title': title,
            'filetypes': file_types,
            'initialdir': initial_dir
        }
        
        if default_extension:
            kwargs['defaultextension'] = default_extension
        
        return filedialog.asksaveasfilename(**kwargs)
    
    def show_info(self, title: str, message: str):
        """정보 메시지 표시"""
        messagebox.showinfo(title, message)
    
    def show_warning(self, title: str, message: str):
        """경고 메시지 표시"""
        messagebox.showwarning(title, message)
    
    def show_error(self, title: str, message: str):
        """오류 메시지 표시"""
        messagebox.showerror(title, message)
    
    def ask_yes_no(self, title: str, message: str) -> bool:
        """예/아니오 질문"""
        return messagebox.askyesno(title, message)
    
    def ask_ok_cancel(self, title: str, message: str) -> bool:
        """확인/취소 질문"""
        return messagebox.askokcancel(title, message)
    
    def handle_property_changed(self, event: PropertyChangeEvent):
        """
        ViewModel 속성 변경 처리 (서브클래스에서 오버라이드)
        
        Args:
            event: 속성 변경 이벤트
        """
        # 기본 구현: 오류 메시지 처리
        if event.property_name == 'error_message' and event.new_value:
            self.show_error("오류", event.new_value)
    
    def handle_command_error(self, command_name: str, error: Exception):
        """
        명령 실행 오류 처리 (서브클래스에서 오버라이드)
        
        Args:
            command_name: 명령 이름
            error: 발생한 오류
        """
        self.show_error("명령 실행 오류", f"{command_name}: {str(error)}")
    
    def refresh_view(self):
        """View 새로고침 (서브클래스에서 오버라이드)"""
        if hasattr(self.viewmodel, 'refresh'):
            self.viewmodel.refresh()
    
    def cleanup(self):
        """리소스 정리"""
        try:
            # ViewModel 바인딩 해제
            for property_name, handler in self._bindings:
                self.viewmodel.unbind_property_changed(property_name, handler)
            
            self._bindings.clear()
            
            # ViewModel 정리
            if hasattr(self.viewmodel, 'cleanup'):
                self.viewmodel.cleanup()
                
        except Exception as e:
            print(f"Controller 정리 중 오류: {e}")


class TabController(BaseController):
    """
    탭 기반 Controller
    Notebook 탭에 특화된 Controller 기본 클래스
    """
    
    def __init__(self, tab_frame: tk.Frame, viewmodel: BaseViewModel,
                 tab_name: str = "Tab"):
        """
        TabController 초기화
        
        Args:
            tab_frame: 탭 프레임
            viewmodel: ViewModel
            tab_name: 탭 이름
        """
        self.tab_frame = tab_frame
        self.tab_name = tab_name
        
        super().__init__(tab_frame, viewmodel)
    
    def set_tab_active(self, is_active: bool):
        """
        탭 활성화 상태 설정
        
        Args:
            is_active: 활성화 여부
        """
        if is_active:
            self.on_tab_activated()
        else:
            self.on_tab_deactivated()
    
    def on_tab_activated(self):
        """탭 활성화 시 처리 (서브클래스에서 오버라이드)"""
        self.refresh_view()
    
    def on_tab_deactivated(self):
        """탭 비활성화 시 처리 (서브클래스에서 오버라이드)"""
        pass
    
    def get_tab_title(self) -> str:
        """탭 제목 반환"""
        return self.tab_name
    
    def update_tab_title(self, new_title: str):
        """탭 제목 업데이트"""
        self.tab_name = new_title
        # 실제 탭 제목 변경은 부모 컨트롤러에서 처리


class DialogController(BaseController):
    """
    다이얼로그 Controller
    모달 다이얼로그에 특화된 Controller 기본 클래스
    """
    
    def __init__(self, dialog: tk.Toplevel, viewmodel: BaseViewModel):
        """
        DialogController 초기화
        
        Args:
            dialog: 다이얼로그 윈도우
            viewmodel: ViewModel
        """
        self.dialog = dialog
        self.result = None
        
        super().__init__(dialog, viewmodel)
        
        # 다이얼로그 기본 설정
        self._setup_dialog()
    
    def _setup_dialog(self):
        """다이얼로그 기본 설정"""
        # 모달 설정
        self.dialog.transient(self.dialog.master)
        self.dialog.grab_set()
        
        # 닫기 이벤트 처리
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # ESC 키로 취소
        self.dialog.bind('<Escape>', lambda e: self.cancel())
    
    def show_modal(self) -> Any:
        """
        모달 다이얼로그 표시
        
        Returns:
            다이얼로그 결과
        """
        # 다이얼로그가 닫힐 때까지 대기
        self.dialog.wait_window()
        return self.result
    
    def ok(self):
        """확인 버튼 처리 (서브클래스에서 오버라이드)"""
        self.result = True
        self.dialog.destroy()
    
    def cancel(self):
        """취소 버튼 처리"""
        self.result = None
        self.dialog.destroy()
    
    def close_dialog(self, result: Any = None):
        """다이얼로그 닫기"""
        self.result = result
        self.dialog.destroy() 