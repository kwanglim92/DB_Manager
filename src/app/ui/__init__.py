"""
UI 모듈
MVVM 패턴을 사용한 사용자 인터페이스 컴포넌트들
"""

# 🎯 3단계 완료: MVVM 패턴 도입
from .viewmodels.main_viewmodel import MainViewModel
from .controllers.main_controller import MainController
from .controllers.base_controller import BaseController, TabController, DialogController

# 기본 UI 컴포넌트들
from .components.base_component import BaseComponent
from .components.menu_component import MenuComponent
from .components.treeview_component import TreeViewComponent

# 대화상자
from .dialogs.base_dialog import BaseDialog

__all__ = [
    # ViewModels
    'MainViewModel',
    
    # Controllers
    'MainController',
    'BaseController',
    'TabController', 
    'DialogController',
    
    # Components
    'BaseComponent',
    'MenuComponent',
    'TreeViewComponent',
    
    # Dialogs
    'BaseDialog',
]

# 🎯 MVVM 시스템 정보
MVVM_VERSION = "3.0.0"
MVVM_STATUS = "COMPLETED"

def get_mvvm_info():
    """MVVM 시스템 정보 반환"""
    return {
        'version': MVVM_VERSION,
        'status': MVVM_STATUS,
        'description': '3단계 완료: MVVM 패턴 도입',
        'components': [
            'MainViewModel (데이터 바인딩 및 비즈니스 로직)',
            'MainController (UI 상호작용 조정)',
            'BaseController (공통 컨트롤러 기능)',
            'UI Components (재사용 가능한 컴포넌트)',
            'Dialog Controllers (모달 다이얼로그 관리)'
        ],
        'features': [
            '속성 변경 알림 (Property Change Notification)',
            '명령 패턴 (Command Pattern)',
            '관찰 가능한 컬렉션 (Observable Collections)',
            '비동기 명령 처리',
            'UI 바인딩 시스템',
            '역할 기반 메뉴 관리',
            '서비스 레이어 통합'
        ]
    } 