"""
ViewModel 기본 클래스
MVVM 패턴의 ViewModel 계층을 위한 기반 클래스
"""

import tkinter as tk
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable, Optional, Union
from collections import defaultdict

class PropertyChangeEvent:
    """속성 변경 이벤트"""
    
    def __init__(self, property_name: str, old_value: Any, new_value: Any):
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value

class BaseViewModel(ABC):
    """
    ViewModel 기본 클래스
    데이터 바인딩, 속성 변경 알림, 명령 처리 등의 기능 제공
    """
    
    def __init__(self):
        """ViewModel 초기화"""
        self._properties = {}
        self._property_changed_handlers = defaultdict(list)
        self._commands = {}
        self._is_busy = False
        self._error_message = ""
        
        # 기본 속성들
        self._properties['is_busy'] = False
        self._properties['error_message'] = ""
    
    def get_property(self, name: str, default: Any = None) -> Any:
        """속성 값 가져오기"""
        return self._properties.get(name, default)
    
    def set_property(self, name: str, value: Any, notify: bool = True) -> bool:
        """
        속성 값 설정
        
        Args:
            name: 속성 이름
            value: 새로운 값
            notify: 변경 알림 발생 여부
            
        Returns:
            bool: 값이 실제로 변경되었는지 여부
        """
        old_value = self._properties.get(name)
        
        # 값이 동일하면 변경하지 않음
        if old_value == value:
            return False
        
        self._properties[name] = value
        
        if notify:
            self._notify_property_changed(name, old_value, value)
        
        return True
    
    def _notify_property_changed(self, property_name: str, old_value: Any, new_value: Any):
        """속성 변경 알림"""
        event = PropertyChangeEvent(property_name, old_value, new_value)
        
        # 특정 속성 핸들러 실행
        for handler in self._property_changed_handlers[property_name]:
            try:
                handler(event)
            except Exception as e:
                print(f"속성 변경 핸들러 오류 ({property_name}): {e}")
        
        # 전체 속성 변경 핸들러 실행
        for handler in self._property_changed_handlers['*']:
            try:
                handler(event)
            except Exception as e:
                print(f"전체 속성 변경 핸들러 오류: {e}")
    
    def bind_property_changed(self, property_name: str, handler: Callable[[PropertyChangeEvent], None]):
        """
        속성 변경 이벤트 핸들러 바인딩
        
        Args:
            property_name: 속성 이름 ('*'은 모든 속성)
            handler: 핸들러 함수
        """
        self._property_changed_handlers[property_name].append(handler)
    
    def unbind_property_changed(self, property_name: str, handler: Callable[[PropertyChangeEvent], None]):
        """속성 변경 이벤트 핸들러 해제"""
        if handler in self._property_changed_handlers[property_name]:
            self._property_changed_handlers[property_name].remove(handler)
    
    def register_command(self, name: str, execute_func: Callable, can_execute_func: Optional[Callable] = None):
        """
        명령 등록
        
        Args:
            name: 명령 이름
            execute_func: 실행 함수
            can_execute_func: 실행 가능 여부 확인 함수
        """
        self._commands[name] = {
            'execute': execute_func,
            'can_execute': can_execute_func or (lambda: True)
        }
    
    def execute_command(self, name: str, *args, **kwargs) -> Any:
        """
        명령 실행
        
        Args:
            name: 명령 이름
            *args, **kwargs: 명령 인자
            
        Returns:
            명령 실행 결과
        """
        if name not in self._commands:
            raise ValueError(f"명령 '{name}'이 등록되지 않았습니다.")
        
        command = self._commands[name]
        
        if not command['can_execute']():
            return None
        
        try:
            return command['execute'](*args, **kwargs)
        except Exception as e:
            self.set_property('error_message', str(e))
            raise
    
    def can_execute_command(self, name: str) -> bool:
        """명령 실행 가능 여부 확인"""
        if name not in self._commands:
            return False
        
        return self._commands[name]['can_execute']()
    
    @property
    def is_busy(self) -> bool:
        """작업 중 상태"""
        return self.get_property('is_busy', False)
    
    @is_busy.setter
    def is_busy(self, value: bool):
        """작업 중 상태 설정"""
        self.set_property('is_busy', value)
    
    @property
    def error_message(self) -> str:
        """오류 메시지"""
        return self.get_property('error_message', "")
    
    @error_message.setter
    def error_message(self, value: str):
        """오류 메시지 설정"""
        self.set_property('error_message', value)
    
    def clear_error(self):
        """오류 메시지 클리어"""
        self.error_message = ""
    
    def validate(self) -> List[str]:
        """
        ViewModel 유효성 검사
        
        Returns:
            List[str]: 오류 메시지 목록
        """
        return []
    
    def refresh(self):
        """ViewModel 새로고침 (서브클래스에서 오버라이드)"""
        pass
    
    def cleanup(self):
        """리소스 정리 (서브클래스에서 오버라이드)"""
        self._property_changed_handlers.clear()
        self._commands.clear()
        self._properties.clear()

class ObservableList(list):
    """
    관찰 가능한 리스트
    리스트 변경 시 이벤트를 발생시킴
    """
    
    def __init__(self, initial_data: Optional[List] = None):
        super().__init__(initial_data or [])
        self._change_handlers = []
    
    def bind_changed(self, handler: Callable[[], None]):
        """변경 이벤트 핸들러 바인딩"""
        self._change_handlers.append(handler)
    
    def unbind_changed(self, handler: Callable[[], None]):
        """변경 이벤트 핸들러 해제"""
        if handler in self._change_handlers:
            self._change_handlers.remove(handler)
    
    def _notify_changed(self):
        """변경 알림"""
        for handler in self._change_handlers:
            try:
                handler()
            except Exception as e:
                print(f"리스트 변경 핸들러 오류: {e}")
    
    def append(self, item):
        super().append(item)
        self._notify_changed()
    
    def extend(self, items):
        super().extend(items)
        self._notify_changed()
    
    def insert(self, index, item):
        super().insert(index, item)
        self._notify_changed()
    
    def remove(self, item):
        super().remove(item)
        self._notify_changed()
    
    def pop(self, index=-1):
        result = super().pop(index)
        self._notify_changed()
        return result
    
    def clear(self):
        super().clear()
        self._notify_changed()
    
    def __setitem__(self, index, value):
        super().__setitem__(index, value)
        self._notify_changed()
    
    def __delitem__(self, index):
        super().__delitem__(index)
        self._notify_changed()

class ObservableDict(dict):
    """
    관찰 가능한 딕셔너리
    딕셔너리 변경 시 이벤트를 발생시킴
    """
    
    def __init__(self, initial_data: Optional[Dict] = None):
        super().__init__(initial_data or {})
        self._change_handlers = []
    
    def bind_changed(self, handler: Callable[[], None]):
        """변경 이벤트 핸들러 바인딩"""
        self._change_handlers.append(handler)
    
    def unbind_changed(self, handler: Callable[[], None]):
        """변경 이벤트 핸들러 해제"""
        if handler in self._change_handlers:
            self._change_handlers.remove(handler)
    
    def _notify_changed(self):
        """변경 알림"""
        for handler in self._change_handlers:
            try:
                handler()
            except Exception as e:
                print(f"딕셔너리 변경 핸들러 오류: {e}")
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._notify_changed()
    
    def __delitem__(self, key):
        super().__delitem__(key)
        self._notify_changed()
    
    def clear(self):
        super().clear()
        self._notify_changed()
    
    def pop(self, key, default=None):
        if len(self) > 0:  # 변경이 있을 때만 알림
            result = super().pop(key, default)
            self._notify_changed()
            return result
        return default
    
    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._notify_changed()

class AsyncCommand:
    """
    비동기 명령 클래스
    백그라운드에서 실행되는 명령을 위한 래퍼
    """
    
    def __init__(self, execute_func: Callable, can_execute_func: Optional[Callable] = None,
                 on_started: Optional[Callable] = None, on_completed: Optional[Callable] = None,
                 on_error: Optional[Callable] = None):
        """
        비동기 명령 초기화
        
        Args:
            execute_func: 실행할 함수
            can_execute_func: 실행 가능 여부 확인 함수
            on_started: 시작 시 콜백
            on_completed: 완료 시 콜백
            on_error: 오류 시 콜백
        """
        self.execute_func = execute_func
        self.can_execute_func = can_execute_func or (lambda: True)
        self.on_started = on_started
        self.on_completed = on_completed
        self.on_error = on_error
        self.is_executing = False
    
    def can_execute(self) -> bool:
        """실행 가능 여부"""
        return not self.is_executing and self.can_execute_func()
    
    def execute_async(self, root: tk.Tk, *args, **kwargs):
        """비동기 실행 (Tkinter after 사용)"""
        if not self.can_execute():
            return
        
        self.is_executing = True
        
        if self.on_started:
            self.on_started()
        
        def run_command():
            try:
                result = self.execute_func(*args, **kwargs)
                
                def on_complete():
                    self.is_executing = False
                    if self.on_completed:
                        self.on_completed(result)
                
                root.after(0, on_complete)
                
            except Exception as e:
                def on_error():
                    self.is_executing = False
                    if self.on_error:
                        self.on_error(e)
                
                root.after(0, on_error)
        
        # 다음 이벤트 루프에서 실행
        root.after(1, run_command) 